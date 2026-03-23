from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlencode

from django.core.paginator import EmptyPage, Page, PageNotAnInteger, Paginator
from django.db.models import (
    Count,
    DecimalField,
    F,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce
from django.http import QueryDict

# -------------------------------------------------------------------
# IMPORTANT:
# Подставь правильный путь к моделям под своё приложение.
# Ниже я использую services.models как наиболее вероятный вариант.
# Если у тебя модели лежат не там - поменяй только этот import.
# -------------------------------------------------------------------
from catalog.models import (
    CarServicePackage,
    NomenclatureItemPrice,
    PackageCategory,
    PackageItem,
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


def build_base_queryset() -> QuerySet[CarServicePackage]:
    return (
        CarServicePackage.objects
        .filter(is_deleted=False)
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


def get_vehicle_label(package: CarServicePackage) -> str:
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
        NomenclatureItemPrice.objects
        .filter(
            nomenclature_item_id=OuterRef("nomenclature_item_id"),
            is_active=True,
        )
        .order_by("-created_at", "-id")
        .values("price_kzt")[:1]
    )

    items_qs = (
        PackageItem.objects
        .filter(
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
                Subquery(latest_active_price_subquery, output_field=DecimalField(max_digits=12, decimal_places=2)),
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
            line_discount = calculate_discount_amount(base_line_total, quantize_money(item.discount_percent))
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
                vehicle_label=get_vehicle_label(package),
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
    paginator, page_obj = paginate_queryset(filtered_queryset, params.get("page"), per_page=20)
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
        categories=PackageCategory.objects.filter(is_active=True).order_by("sort_order", "name", "code"),
        status_choices=get_status_choices(),
    )