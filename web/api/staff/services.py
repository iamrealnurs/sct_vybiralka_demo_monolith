from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, Page, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Count, DecimalField, OuterRef, Prefetch, Q, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import QueryDict

from catalog.models import (
    CarServicePackage,
    NomenclatureItem,
    NomenclatureItemPrice,
    PackageCategory,
    PackageItem,
    PackageItemCategory,
    PackageStatus,
)


ZERO = Decimal("0.00")
HUNDRED = Decimal("100.00")


@dataclass(slots=True)
class PackageRow:
    package: CarServicePackage
    vehicle_label: str
    active_items_count: int
    base_price: Decimal
    line_discount_amount: Decimal
    regular_price: Decimal
    package_discount_amount: Decimal
    final_price: Decimal
    image_url: str


@dataclass(slots=True)
class StaffPackageListResult:
    page_obj: Page
    paginator: Paginator
    rows: list[PackageRow]
    total_count: int
    published_count: int
    promo_count: int
    draft_count: int
    filters: dict[str, str]
    preserved_query: str
    categories: QuerySet[PackageCategory]
    status_choices: list[tuple[str, str]]


@dataclass(slots=True)
class PackageItemInput:
    item_id: int | None
    row_index: int
    package_category_id: int | None
    nomenclature_item_id: int | None
    quantity: int
    discount_percent: Decimal
    sort_order: int
    is_active: bool
    is_deleted: bool


@dataclass(slots=True)
class PackageEditContext:
    package: CarServicePackage
    package_items: list[PackageItem]
    package_item_categories: list[PackageItemCategory]
    nomenclature_items: list[NomenclatureItem]
    vehicle_label: str
    base_price: Any
    line_discount_amount: Any
    subtotal_after_line_discounts: Any
    package_discount_amount: Any
    regular_price: Any
    promo_price: Any
    final_price: Any
    active_items_count: int


@dataclass(slots=True)
class PackageItemCategoryInput:
    category_id: int | None
    row_index: int
    name: str
    description: str
    sort_order: int
    is_active: bool
    is_deleted: bool


def quantize_money(value: Decimal | int | float | None) -> Decimal:
    if value is None:
        return ZERO
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal("0.01"))


def calculate_discount_amount(base: Decimal, percent: Decimal) -> Decimal:
    base = quantize_money(base)
    percent = quantize_money(percent)
    if percent <= ZERO:
        return ZERO
    if percent >= HUNDRED:
        return base
    return quantize_money(base * percent / HUNDRED)


def money_to_kzt_string(value: Decimal | None) -> str:
    if value is None:
        return "—"
    value = quantize_money(value)
    return f"{value:,.2f}".replace(",", " ")


def get_status_choices() -> list[tuple[str, str]]:
    field = CarServicePackage._meta.get_field("status")
    return list(field.choices)


def get_published_status_value() -> str:
    return getattr(PackageStatus, "PUBLISHED", "PUBLISHED")


def get_draft_status_value() -> str:
    return getattr(PackageStatus, "DRAFT", "DRAFT")


def get_service_item_type_value() -> str:
    return (
        getattr(NomenclatureItem.ItemType, "SERVICE", "SERVICE")
        if hasattr(NomenclatureItem, "ItemType")
        else "SERVICE"
    )


def build_vehicle_label(package: CarServicePackage) -> str:
    modification = getattr(package, "modification", None)
    if not modification:
        return "—"

    configuration = getattr(modification, "configuration", None)
    generation = getattr(configuration, "generation", None)
    model = getattr(generation, "model", None)
    mark = getattr(model, "mark", None)

    parts: list[str] = []
    if mark and getattr(mark, "name", None):
        parts.append(mark.name)
    if model and getattr(model, "name", None):
        parts.append(model.name)
    if generation and getattr(generation, "name", None):
        parts.append(generation.name)
    if configuration and getattr(configuration, "name", None):
        parts.append(configuration.name)
    if getattr(modification, "name", None):
        parts.append(modification.name)

    return " / ".join(parts) if parts else "—"


def build_base_queryset() -> QuerySet[CarServicePackage]:
    return (
        CarServicePackage.objects.filter(is_deleted=False)
        .select_related(
            "category",
            "modification",
            "modification__configuration",
            "modification__configuration__generation",
            "modification__configuration__generation__model",
            "modification__configuration__generation__model__mark",
            "image_object",
        )
        .annotate(
            active_items_count=Count(
                "items",
                filter=Q(items__is_deleted=False, items__is_active=True),
                distinct=True,
            )
        )
    )


def apply_filters(
    queryset: QuerySet[CarServicePackage],
    params: QueryDict,
) -> tuple[QuerySet[CarServicePackage], dict[str, str]]:
    q = (params.get("q") or "").strip()
    category = (params.get("category") or "").strip()
    status = (params.get("status") or "").strip()
    is_promo = (params.get("is_promo") or "").strip()
    has_items = (params.get("has_items") or "").strip()
    ordering = (params.get("ordering") or "-updated_at").strip()

    if q:
        queryset = queryset.filter(
            Q(name__icontains=q)
            | Q(public_title__icontains=q)
            | Q(slug__icontains=q)
            | Q(modification__name__icontains=q)
            | Q(modification__source_id__icontains=q)
            | Q(modification__configuration__generation__name__icontains=q)
            | Q(modification__configuration__name__icontains=q)
            | Q(modification__configuration__generation__model__name__icontains=q)
            | Q(modification__configuration__generation__model__mark__name__icontains=q)
        )

    if category:
        queryset = queryset.filter(category_id=category)

    if status:
        queryset = queryset.filter(status=status)

    if is_promo == "1":
        queryset = queryset.filter(is_promo=True)
    elif is_promo == "0":
        queryset = queryset.filter(is_promo=False)

    if has_items == "1":
        queryset = queryset.filter(active_items_count__gt=0)
    elif has_items == "0":
        queryset = queryset.filter(active_items_count=0)

    queryset = apply_ordering(queryset, ordering)

    filters = {
        "q": q,
        "category": category,
        "status": status,
        "is_promo": is_promo,
        "has_items": has_items,
        "ordering": ordering,
    }
    return queryset, filters


def apply_ordering(
    queryset: QuerySet[CarServicePackage],
    ordering: str,
) -> QuerySet[CarServicePackage]:
    allowed = {
        "updated_at": ("updated_at", "id"),
        "-updated_at": ("-updated_at", "-id"),
        "created_at": ("created_at", "id"),
        "-created_at": ("-created_at", "-id"),
        "public_title": ("public_title", "id"),
        "-public_title": ("-public_title", "-id"),
        "status": ("status", "id"),
        "-status": ("-status", "-id"),
        "category": ("category__name", "public_title", "id"),
        "-category": ("-category__name", "public_title", "id"),
    }
    order_by = allowed.get(ordering, ("-updated_at", "-id"))
    return queryset.order_by(*order_by)


def paginate_queryset(
    queryset: QuerySet[CarServicePackage],
    page_number: str | None,
    per_page: int = 20,
) -> tuple[Paginator, Page]:
    paginator = Paginator(queryset, per_page)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return paginator, page_obj


def build_preserved_query(params: QueryDict) -> str:
    query = params.copy()
    query.pop("page", None)
    return query.urlencode()


def build_kpis(queryset: QuerySet[CarServicePackage]) -> dict[str, int]:
    published_value = get_published_status_value()
    draft_value = get_draft_status_value()

    return {
        "total_count": queryset.count(),
        "published_count": queryset.filter(status=published_value).count(),
        "promo_count": queryset.filter(is_promo=True).count(),
        "draft_count": queryset.filter(status=draft_value).count(),
    }


def get_price_annotated_items_for_page(package_ids: list[int]) -> list[PackageItem]:
    if not package_ids:
        return []

    latest_active_price_subquery = (
        NomenclatureItemPrice.objects.filter(
            nomenclature_item_id=OuterRef("nomenclature_item_id"),
            is_active=True,
        )
        .order_by("-created_at", "-id")
        .values("price_kzt")[:1]
    )

    items_qs = (
        PackageItem.objects.filter(
            package_id__in=package_ids,
            is_deleted=False,
            is_active=True,
        )
        .select_related(
            "nomenclature_item",
            "package_category",
        )
        .annotate(
            current_unit_price_db=Coalesce(
                Subquery(
                    latest_active_price_subquery,
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                Value(ZERO),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .order_by("package_id", "sort_order", "id")
    )

    return list(items_qs)


def build_price_rows(page_packages: list[CarServicePackage]) -> list[PackageRow]:
    package_ids = [package.id for package in page_packages]
    items = get_price_annotated_items_for_page(package_ids)

    items_by_package: dict[int, list[PackageItem]] = {}
    for item in items:
        items_by_package.setdefault(item.package_id, []).append(item)

    rows: list[PackageRow] = []

    for package in page_packages:
        package_items = items_by_package.get(package.id, [])

        base_price = ZERO
        line_discount_amount = ZERO
        regular_price = ZERO

        for item in package_items:
            unit_price = quantize_money(getattr(item, "current_unit_price_db", ZERO))
            quantity = Decimal(item.quantity)
            base_line_total = quantize_money(unit_price * quantity)
            line_discount = calculate_discount_amount(
                base_line_total,
                quantize_money(item.discount_percent),
            )
            final_line_total = quantize_money(base_line_total - line_discount)

            base_price += base_line_total
            line_discount_amount += line_discount
            regular_price += final_line_total

        base_price = quantize_money(base_price)
        line_discount_amount = quantize_money(line_discount_amount)
        regular_price = quantize_money(regular_price)
        package_discount_amount = calculate_discount_amount(
            regular_price,
            quantize_money(package.package_discount_percent),
        )
        final_price = quantize_money(regular_price - package_discount_amount)

        rows.append(
            PackageRow(
                package=package,
                vehicle_label=build_vehicle_label(package),
                active_items_count=getattr(package, "active_items_count", 0) or 0,
                base_price=base_price,
                line_discount_amount=line_discount_amount,
                regular_price=regular_price,
                package_discount_amount=package_discount_amount,
                final_price=final_price,
                image_url=package.image_url if getattr(package, "image_object", None) else "",
            )
        )

    return rows


def get_package_list_data(params: QueryDict) -> StaffPackageListResult:
    base_queryset = build_base_queryset()
    filtered_queryset, filters = apply_filters(base_queryset, params)
    paginator, page_obj = paginate_queryset(
        filtered_queryset,
        params.get("page"),
        per_page=20,
    )
    page_packages = list(page_obj.object_list)

    rows = build_price_rows(page_packages)
    kpis = build_kpis(filtered_queryset)

    return StaffPackageListResult(
        page_obj=page_obj,
        paginator=paginator,
        rows=rows,
        total_count=kpis["total_count"],
        published_count=kpis["published_count"],
        promo_count=kpis["promo_count"],
        draft_count=kpis["draft_count"],
        filters=filters,
        preserved_query=build_preserved_query(params),
        categories=PackageCategory.objects.filter(is_active=True).order_by(
            "sort_order",
            "name",
            "code",
        ),
        status_choices=get_status_choices(),
    )


def get_package_for_update(package_id: int) -> CarServicePackage:
    queryset = (
        CarServicePackage.objects.filter(is_deleted=False)
        .select_related(
            "category",
            "modification",
            "modification__configuration",
            "modification__configuration__generation",
            "modification__configuration__generation__model",
            "modification__configuration__generation__model__mark",
            "image_object",
        )
        .prefetch_related(
            Prefetch(
                "item_categories",
                queryset=PackageItemCategory.objects.filter(is_deleted=False).order_by(
                    "sort_order",
                    "id",
                ),
            ),
            Prefetch(
                "items",
                queryset=(
                    PackageItem.objects.select_related(
                        "package_category",
                        "nomenclature_item",
                        "nomenclature_item__category",
                    )
                    .filter(is_deleted=False)
                    .order_by("sort_order", "id")
                ),
            ),
        )
    )
    return queryset.get(pk=package_id)


def build_edit_context(package: CarServicePackage) -> PackageEditContext:
    package_items = list(package.items.all())
    package_item_categories = list(package.item_categories.all())

    nomenclature_items = list(
        NomenclatureItem.objects.filter(is_deleted=False, is_active=True)
        .select_related("category")
        .order_by("name", "article")[:500]
    )

    active_items_count = sum(
        1
        for item in package_items
        if item.is_active and not item.is_deleted
    )

    return PackageEditContext(
        package=package,
        package_items=package_items,
        package_item_categories=package_item_categories,
        nomenclature_items=nomenclature_items,
        vehicle_label=build_vehicle_label(package),
        base_price=package.base_price,
        line_discount_amount=package.line_discount_amount,
        subtotal_after_line_discounts=package.subtotal_after_line_discounts,
        package_discount_amount=package.package_discount_amount,
        regular_price=package.regular_price,
        promo_price=package.promo_price,
        final_price=package.final_price,
        active_items_count=active_items_count,
    )


def _parse_int(
    value: str | None,
    field_label: str,
    errors: list[str],
    row_index: int,
) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        errors.append(
            f"Строка #{row_index + 1}: поле «{field_label}» содержит некорректное целое число."
        )
        return None


def _parse_decimal(
    value: str | None,
    field_label: str,
    errors: list[str],
    row_index: int,
) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(",", "."))
    except (TypeError, ValueError, InvalidOperation):
        errors.append(
            f"Строка #{row_index + 1}: поле «{field_label}» содержит некорректное число."
        )
        return None


def parse_package_items_from_post(post_data) -> list[PackageItemInput]:
    total_forms_raw = post_data.get("items-TOTAL_FORMS", "0")
    try:
        total_forms = int(total_forms_raw)
    except (TypeError, ValueError):
        total_forms = 0

    result: list[PackageItemInput] = []

    for i in range(total_forms):
        errors: list[str] = []

        item_id = _parse_int(post_data.get(f"items-{i}-id"), "ID строки", errors, i)
        package_category_id = _parse_int(
            post_data.get(f"items-{i}-package_category_id"),
            "Категория строки",
            errors,
            i,
        )
        nomenclature_item_id = _parse_int(
            post_data.get(f"items-{i}-nomenclature_item_id"),
            "Номенклатура",
            errors,
            i,
        )
        quantity = _parse_int(post_data.get(f"items-{i}-quantity"), "Количество", errors, i)
        sort_order = _parse_int(post_data.get(f"items-{i}-sort_order"), "Порядок", errors, i)
        discount_percent = _parse_decimal(
            post_data.get(f"items-{i}-discount_percent"),
            "Скидка",
            errors,
            i,
        )

        is_active = post_data.get(f"items-{i}-is_active") == "on"
        is_deleted = post_data.get(f"items-{i}-is_deleted") == "on"

        if errors:
            raise ValidationError(errors)

        result.append(
            PackageItemInput(
                item_id=item_id,
                row_index=i,
                package_category_id=package_category_id,
                nomenclature_item_id=nomenclature_item_id,
                quantity=quantity or 1,
                discount_percent=discount_percent or Decimal("0.00"),
                sort_order=sort_order or i,
                is_active=is_active,
                is_deleted=is_deleted,
            )
        )

    return result


def parse_package_item_categories_from_post(post_data) -> list[PackageItemCategoryInput]:
    total_forms_raw = post_data.get("item_categories-TOTAL_FORMS", "0")
    try:
        total_forms = int(total_forms_raw)
    except (TypeError, ValueError):
        total_forms = 0

    result: list[PackageItemCategoryInput] = []

    for i in range(total_forms):
        errors: list[str] = []

        category_id = _parse_int(
            post_data.get(f"item_categories-{i}-id"),
            "ID категории",
            errors,
            i,
        )
        sort_order = _parse_int(
            post_data.get(f"item_categories-{i}-sort_order"),
            "Порядок категории",
            errors,
            i,
        )

        name = (post_data.get(f"item_categories-{i}-name") or "").strip()
        description = (post_data.get(f"item_categories-{i}-description") or "").strip()
        is_active = post_data.get(f"item_categories-{i}-is_active") == "on"
        is_deleted = post_data.get(f"item_categories-{i}-is_deleted") == "on"

        if not is_deleted and not name:
            errors.append(f"Категория #{i + 1}: нужно указать название категории.")

        if sort_order is not None and sort_order < 0:
            errors.append(f"Категория #{i + 1}: sort_order не может быть отрицательным.")

        if errors:
            raise ValidationError(errors)

        result.append(
            PackageItemCategoryInput(
                category_id=category_id,
                row_index=i,
                name=name,
                description=description,
                sort_order=sort_order or i,
                is_active=is_active,
                is_deleted=is_deleted,
            )
        )

    return result


def validate_package_item_categories(
    package: CarServicePackage,
    categories_data: list[PackageItemCategoryInput],
) -> None:
    errors: list[str] = []

    existing_ids = set(
        PackageItemCategory.objects.filter(package=package).values_list("id", flat=True)
    )

    seen_names: set[str] = set()

    for row in categories_data:
        if row.category_id is not None and row.category_id not in existing_ids:
            errors.append(
                f"Категория #{row.row_index + 1}: категория не принадлежит текущему пакету."
            )

        if row.is_deleted:
            continue

        normalized_name = row.name.strip().casefold()
        if normalized_name in seen_names:
            errors.append(
                f"Категория #{row.row_index + 1}: название категории должно быть уникальным внутри пакета."
            )
        seen_names.add(normalized_name)

    if errors:
        raise ValidationError(errors)


def save_package_item_categories(
    package: CarServicePackage,
    categories_data: list[PackageItemCategoryInput],
) -> dict[int, PackageItemCategory]:
    existing_categories = {
        category.id: category
        for category in PackageItemCategory.objects.filter(package=package)
    }

    saved_categories: dict[int, PackageItemCategory] = {}

    for row in categories_data:
        if row.category_id and row.category_id in existing_categories:
            category = existing_categories[row.category_id]
        else:
            category = PackageItemCategory(package=package)

        category.name = row.name
        category.description = row.description
        category.sort_order = row.sort_order
        category.is_active = row.is_active
        category.is_deleted = row.is_deleted

        category.full_clean()
        category.save()

        if not category.is_deleted:
            saved_categories[category.id] = category

    return saved_categories


def validate_package_items(
    package: CarServicePackage,
    items_data: list[PackageItemInput],
    target_status: str | None,
) -> None:
    errors: list[str] = []

    category_ids = set(
        PackageItemCategory.objects.filter(
            package=package,
            is_deleted=False,
        ).values_list("id", flat=True)
    )

    nomenclature_map = {
        item.id: item
        for item in NomenclatureItem.objects.filter(
            id__in=[
                row.nomenclature_item_id
                for row in items_data
                if row.nomenclature_item_id is not None
            ],
            is_deleted=False,
        )
    }

    active_not_deleted_rows = [
        row
        for row in items_data
        if not row.is_deleted and row.is_active
    ]

    seen_nomenclature_ids: set[int] = set()
    service_value = get_service_item_type_value()
    published_value = get_published_status_value()

    for row in items_data:
        if row.is_deleted:
            continue

        if row.package_category_id is None:
            errors.append(f"Строка #{row.row_index + 1}: нужно выбрать категорию строки.")
        elif row.package_category_id not in category_ids:
            errors.append(
                f"Строка #{row.row_index + 1}: категория строки не принадлежит текущему пакету."
            )

        if row.nomenclature_item_id is None:
            errors.append(f"Строка #{row.row_index + 1}: нужно выбрать номенклатуру.")
        elif row.nomenclature_item_id not in nomenclature_map:
            errors.append(
                f"Строка #{row.row_index + 1}: номенклатура не найдена или удалена."
            )
        else:
            if row.nomenclature_item_id in seen_nomenclature_ids:
                errors.append(
                    f"Строка #{row.row_index + 1}: одна и та же номенклатура не может повторяться внутри пакета."
                )
            seen_nomenclature_ids.add(row.nomenclature_item_id)

            nomenclature_item = nomenclature_map[row.nomenclature_item_id]
            if nomenclature_item.item_type == service_value and row.quantity > 1:
                errors.append(
                    f"Строка #{row.row_index + 1}: для услуги количество не может быть больше 1."
                )

        if row.quantity < 1:
            errors.append(f"Строка #{row.row_index + 1}: количество должно быть не меньше 1.")

        if row.discount_percent < Decimal("0.00") or row.discount_percent > Decimal("100.00"):
            errors.append(
                f"Строка #{row.row_index + 1}: скидка должна быть в диапазоне от 0 до 100."
            )

        if row.sort_order < 0:
            errors.append(
                f"Строка #{row.row_index + 1}: sort_order не может быть отрицательным."
            )

    if target_status == published_value and not active_not_deleted_rows:
        errors.append("Нельзя публиковать пакет без хотя бы одной активной строки состава.")

    if errors:
        raise ValidationError(errors)


def save_package_items(
    package: CarServicePackage,
    items_data: list[PackageItemInput],
) -> None:
    existing_items = {
        item.id: item
        for item in PackageItem.objects.filter(package=package)
    }

    for row in items_data:
        if row.item_id and row.item_id in existing_items:
            item = existing_items[row.item_id]
        else:
            item = PackageItem(package=package)

        item.package_category_id = row.package_category_id
        item.nomenclature_item_id = row.nomenclature_item_id
        item.quantity = row.quantity
        item.discount_percent = row.discount_percent
        item.sort_order = row.sort_order
        item.is_active = row.is_active
        item.is_deleted = row.is_deleted

        item.full_clean()
        item.save()


@transaction.atomic
def save_package_update(
    *,
    form,
    package: CarServicePackage,
    items_data: list[PackageItemInput],
    categories_data: list[PackageItemCategoryInput],
) -> CarServicePackage:
    updated_package = form.save()
    updated_package.full_clean()
    updated_package.save()

    validate_package_item_categories(
        package=updated_package,
        categories_data=categories_data,
    )

    save_package_item_categories(
        package=updated_package,
        categories_data=categories_data,
    )

    validate_package_items(
        package=updated_package,
        items_data=items_data,
        target_status=form.cleaned_data.get("status"),
    )

    save_package_items(
        package=updated_package,
        items_data=items_data,
    )

    return updated_package



