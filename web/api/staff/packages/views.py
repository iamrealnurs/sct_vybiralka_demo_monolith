from __future__ import annotations

import json
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.views import View

from catalog.models import CarServicePackage
from cars.models import Mark

from .forms import (
    StaffPackageCreateForm,
    StaffPackageImageForm,
    StaffPackageUpdateForm,
)
from .services import (
    build_edit_context,
    get_package_for_update,
    get_package_list_data,
    parse_package_item_categories_from_post,
    parse_package_items_from_post,
    save_package_update,
)


# ============================================================
# vehicle selector helpers
# ============================================================

VEHICLE_SELECTOR_MARK_KEY = "vehicle_mark"
VEHICLE_SELECTOR_MODEL_KEY = "vehicle_model"
VEHICLE_SELECTOR_GENERATIONS_KEY = "vehicle_generations"
VEHICLE_SELECTOR_CONFIGURATIONS_KEY = "vehicle_configurations"
VEHICLE_SELECTOR_ENGINE_TYPES_KEY = "vehicle_engine_types"
VEHICLE_SELECTOR_DRIVE_TYPES_KEY = "vehicle_drive_types"
VEHICLE_SELECTOR_TRANSMISSIONS_KEY = "vehicle_transmissions"
VEHICLE_SELECTOR_MODIFICATION_KEY = "vehicle_modification"


def _get_modification_model():
    """
    Возвращает модель, на которую ссылается CarServicePackage.modification.
    Это безопаснее, чем хардкодить import конкретной модели автомобиля.
    """
    return CarServicePackage._meta.get_field("modification").remote_field.model


def _safe_reverse(name: str) -> str:
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _read_post_single(post_data, key: str) -> str:
    value = post_data.get(key)
    if value is None:
        value = post_data.get(f"{key}[]")
    return _safe_str(value)


def _read_post_list(post_data, key: str) -> list[str]:
    """
    Поддерживает оба варианта:
    - repeated params: key=1&key=2
    - key[]=1&key[]=2
    - comma separated single value
    """
    values = post_data.getlist(key)
    if not values:
        values = post_data.getlist(f"{key}[]")

    if values:
        result: list[str] = []
        for value in values:
            normalized = _safe_str(value)
            if normalized:
                result.append(normalized)
        return result

    single_value = _safe_str(post_data.get(key) or post_data.get(f"{key}[]"))
    if not single_value:
        return []

    return [part.strip() for part in single_value.split(",") if part.strip()]


def _build_vehicle_context_from_modification(modification) -> dict:
    configuration = getattr(modification, "configuration", None) if modification else None
    generation = getattr(configuration, "generation", None) if configuration else None
    model = getattr(generation, "model", None) if generation else None
    mark = getattr(model, "mark", None) if model else None

    parts: list[str] = []

    if mark and getattr(mark, "name", None):
        parts.append(mark.name)
    if model and getattr(model, "name", None):
        parts.append(model.name)
    if generation and getattr(generation, "name", None):
        parts.append(generation.name)
    if configuration and getattr(configuration, "name", None):
        parts.append(configuration.name)
    if modification and getattr(modification, "name", None):
        parts.append(modification.name)

    return {
        "mark_id": getattr(mark, "id", None) if mark else None,
        "mark": getattr(mark, "name", "—") if mark else "—",
        "model_id": getattr(model, "id", None) if model else None,
        "model": getattr(model, "name", "—") if model else "—",
        "generation_id": getattr(generation, "id", None) if generation else None,
        "generation": getattr(generation, "name", "—") if generation else "—",
        "configuration_id": getattr(configuration, "id", None) if configuration else None,
        "configuration": getattr(configuration, "name", "—") if configuration else "—",
        "modification_id": getattr(modification, "id", None) if modification else None,
        "modification": getattr(modification, "name", "—") if modification else "—",
        "source_id": getattr(modification, "source_id", "—") if modification else "—",
        "label": " / ".join(parts) if parts else "—",
    }


def build_vehicle_context(package: CarServicePackage) -> dict:
    modification = getattr(package, "modification", None)
    return _build_vehicle_context_from_modification(modification)


def _build_vehicle_selector_state_from_modification(modification) -> dict:
    configuration = getattr(modification, "configuration", None) if modification else None
    generation = getattr(configuration, "generation", None) if configuration else None
    model = getattr(generation, "model", None) if generation else None
    mark = getattr(model, "mark", None) if model else None

    engine_type = _safe_str(getattr(modification, "engine_type", None))
    drive_type = _safe_str(
        getattr(modification, "drive_type", None)
        or getattr(modification, "gear_type", None)
    )
    transmission = _safe_str(
        getattr(modification, "transmission", None)
        or getattr(modification, "transmission_code", None)
    )

    return {
        "mark": _safe_str(getattr(mark, "id", None)) or None,
        "model": _safe_str(getattr(model, "id", None)) or None,
        "generations": [_safe_str(getattr(generation, "id", None))] if generation else [],
        "configurations": [_safe_str(getattr(configuration, "id", None))] if configuration else [],
        "engine_types": [engine_type] if engine_type else [],
        "drive_types": [drive_type] if drive_type else [],
        "transmissions": [transmission] if transmission else [],
    }


def _build_vehicle_selector_state_from_post(post_data) -> dict:
    return {
        "mark": _read_post_single(post_data, VEHICLE_SELECTOR_MARK_KEY) or None,
        "model": _read_post_single(post_data, VEHICLE_SELECTOR_MODEL_KEY) or None,
        "generations": _read_post_list(post_data, VEHICLE_SELECTOR_GENERATIONS_KEY),
        "configurations": _read_post_list(post_data, VEHICLE_SELECTOR_CONFIGURATIONS_KEY),
        "engine_types": _read_post_list(post_data, VEHICLE_SELECTOR_ENGINE_TYPES_KEY),
        "drive_types": _read_post_list(post_data, VEHICLE_SELECTOR_DRIVE_TYPES_KEY),
        "transmissions": _read_post_list(post_data, VEHICLE_SELECTOR_TRANSMISSIONS_KEY),
    }


def _get_selected_modification_id_from_post(post_data) -> str | None:
    direct_value = (
        _read_post_single(post_data, VEHICLE_SELECTOR_MODIFICATION_KEY)
        or _read_post_single(post_data, "modification")
    )
    return direct_value or None


def _get_modification_for_preview(modification_id: str | int | None):
    if not modification_id:
        return None

    modification_model = _get_modification_model()

    try:
        return (
            modification_model.objects.select_related(
                "configuration",
                "configuration__generation",
                "configuration__generation__model",
                "configuration__generation__model__mark",
            )
            .filter(pk=modification_id)
            .first()
        )
    except Exception:
        return None


def _build_vehicle_selector_payload(
    *,
    mode: str,
    initial_state: dict,
    selected_modification_id: str | int | None,
    preview: dict | None = None,
) -> dict:
    normalized_selected_modification_id = (
        _safe_str(selected_modification_id) if selected_modification_id else ""
    )

    payload = {
        "mode": mode,
        "api_url": _safe_reverse("cars:filter_api"),
        "initial_state": initial_state,
        "initial_state_json": json.dumps(initial_state, ensure_ascii=False),
        "selected_modification_id": normalized_selected_modification_id,
        "selected_modification_id_json": json.dumps(
            normalized_selected_modification_id,
            ensure_ascii=False,
        ),
        "preview": preview or {},
        "preview_json": json.dumps(preview or {}, ensure_ascii=False),
    }
    return payload


def _build_vehicle_selector_for_create(
    *,
    request: HttpRequest | None,
    form: StaffPackageCreateForm,
) -> dict:
    if request and request.method == "POST":
        initial_state = _build_vehicle_selector_state_from_post(request.POST)
        selected_modification_id = (
            _get_selected_modification_id_from_post(request.POST)
            or _safe_str(form.data.get("modification"))
            or None
        )
        modification = _get_modification_for_preview(selected_modification_id)
        preview = _build_vehicle_context_from_modification(modification) if modification else {}
    else:
        initial_state = {
            "mark": None,
            "model": None,
            "generations": [],
            "configurations": [],
            "engine_types": [],
            "drive_types": [],
            "transmissions": [],
        }
        selected_modification_id = None
        preview = {}

    return _build_vehicle_selector_payload(
        mode="create",
        initial_state=initial_state,
        selected_modification_id=selected_modification_id,
        preview=preview,
    )


def _build_vehicle_selector_for_update(
    *,
    request: HttpRequest | None,
    package: CarServicePackage,
    form: StaffPackageUpdateForm,
) -> dict:
    if request and request.method == "POST":
        initial_state = _build_vehicle_selector_state_from_post(request.POST)
        selected_modification_id = (
            _get_selected_modification_id_from_post(request.POST)
            or _safe_str(form.data.get("modification"))
            or _safe_str(getattr(package, "modification_id", None))
            or None
        )
        modification = _get_modification_for_preview(selected_modification_id)
        preview = _build_vehicle_context_from_modification(modification) if modification else {}
    else:
        modification = getattr(package, "modification", None)
        initial_state = _build_vehicle_selector_state_from_modification(modification)
        selected_modification_id = getattr(package, "modification_id", None)
        preview = _build_vehicle_context_from_modification(modification) if modification else {}

    return _build_vehicle_selector_payload(
        mode="edit",
        initial_state=initial_state,
        selected_modification_id=selected_modification_id,
        preview=preview,
    )


# ============================================================
# detail helpers
# ============================================================

def build_grouped_items(package: CarServicePackage) -> list[dict]:
    """
    Группирует элементы пакета по локальным категориям.
    """
    grouped: list[dict] = []
    active_categories = list(
        package.item_categories.filter(is_deleted=False, is_active=True).order_by("sort_order", "id")
    )

    for category in active_categories:
        items = list(
            category.items.filter(is_deleted=False, is_active=True)
            .select_related("nomenclature_item")
            .order_by("sort_order", "id")
        )
        grouped.append(
            {
                "category": category,
                "items": items,
            }
        )

    return grouped


# ============================================================
# views
# ============================================================

class StaffPackageListView(LoginRequiredMixin, View):
    template_name = "staff/packages/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        result = get_package_list_data(request.GET)

        context = {
            "page_title": "Пакеты услуг",
            "page_obj": result.page_obj,
            "paginator": result.paginator,
            "rows": result.rows,
            "total_count": result.total_count,
            "published_count": result.published_count,
            "promo_count": result.promo_count,
            "draft_count": result.draft_count,
            "filters": result.filters,
            "preserved_query": result.preserved_query,
            "categories": result.categories,
            "status_choices": result.status_choices,
        }
        return render(request, self.template_name, context)


class StaffPackageCreateView(LoginRequiredMixin, View):
    template_name = "staff/packages/create.html"

    def get_context_data(
        self,
        *,
        request: HttpRequest | None,
        form: StaffPackageCreateForm,
        image_form: StaffPackageImageForm,
    ) -> dict:
        vehicle_selector = _build_vehicle_selector_for_create(
            request=request,
            form=form,
        )

        return {
            "form": form,
            "image_form": image_form,
            "marks": Mark.objects.all().order_by("name"), # Добавляем марки в контекст
            "vehicle_selector": vehicle_selector,
            "vehicle_selector_api_url": vehicle_selector["api_url"],
            "vehicle_selector_mode": vehicle_selector["mode"],
            "vehicle_selector_initial_state": vehicle_selector["initial_state"],
            "vehicle_selector_initial_state_json": vehicle_selector["initial_state_json"],
            "vehicle_selector_selected_modification_id": vehicle_selector["selected_modification_id"],
            "vehicle_selector_selected_modification_id_json": vehicle_selector["selected_modification_id_json"],
            "vehicle_selector_preview": vehicle_selector["preview"],
            "vehicle_selector_preview_json": vehicle_selector["preview_json"],
            "breadcrumbs": [
                {"label": "Staff", "url": None},
                {"label": "Packages", "url": reverse("staff:packages:package_list")},
                {"label": "Create", "url": None},
            ],
        }    



    def get(self, request: HttpRequest) -> HttpResponse:
        form = StaffPackageCreateForm()
        image_form = StaffPackageImageForm()

        context = self.get_context_data(
            request=request,
            form=form,
            image_form=image_form,
        )
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form = StaffPackageCreateForm(request.POST)
        image_form = StaffPackageImageForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            package = form.save()

            if image_form.cleaned_data.get("image"):
                image = image_form.save(commit=False)
                image.package = package
                image.save()

            messages.success(request, "Пакет успешно создан.")

            action = request.POST.get("action") or "save"

            if action == "save_open":
                return redirect("staff:packages:package_detail", package_id=package.id)

            return redirect("staff:packages:package_list")

        context = self.get_context_data(
            request=request,
            form=form,
            image_form=image_form,
        )
        return render(request, self.template_name, context, status=400)


class StaffPackageDetailView(LoginRequiredMixin, View):
    template_name = "staff/packages/detail.html"

    def get(self, request: HttpRequest, package_id: int) -> HttpResponse:
        package = get_object_or_404(
            CarServicePackage.objects.select_related(
                "category",
                "modification",
                "modification__configuration",
                "modification__configuration__generation",
                "modification__configuration__generation__model",
                "modification__configuration__generation__model__mark",
                "image_object",
            ),
            pk=package_id,
            is_deleted=False,
        )

        vehicle = build_vehicle_context(package)
        item_categories = package.item_categories.filter(is_deleted=False, is_active=True).order_by(
            "sort_order",
            "id",
        )
        grouped_items = build_grouped_items(package)

        published_value = (
            getattr(package.__class__.Status, "PUBLISHED", "PUBLISHED")
            if hasattr(package.__class__, "Status")
            else "PUBLISHED"
        )
        status_tone = "published" if package.status == published_value else "draft"

        context = {
            "package": package,
            "vehicle": vehicle,
            "item_categories": item_categories,
            "grouped_items": grouped_items,
            "breadcrumbs": [
                {"label": "Staff", "url": None},
                {"label": "Packages", "url": reverse("staff:packages:package_list")},
                {"label": f"#{package.id}", "url": None},
            ],
            "status_tone": status_tone,
        }
        return render(request, self.template_name, context)


class StaffPackageUpdateView(LoginRequiredMixin, View):
    template_name = "staff/packages/edit.html"

    def get_package(self, package_id: int) -> CarServicePackage:
        try:
            return get_package_for_update(package_id)
        except CarServicePackage.DoesNotExist as exc:
            raise Http404("Пакет не найден.") from exc

    def build_context(
        self,
        *,
        request: HttpRequest | None,
        package: CarServicePackage,
        form: StaffPackageUpdateForm,
    ) -> dict:
        edit_context = build_edit_context(package)
        vehicle_selector = _build_vehicle_selector_for_update(
            request=request,
            package=package,
            form=form,
        )

        return {
            "package": package,
            "form": form,
            "edit_context": edit_context,
            "package_items": edit_context.package_items,
            "package_item_categories": edit_context.package_item_categories,
            "nomenclature_items": edit_context.nomenclature_items,
            "vehicle_selector": vehicle_selector,
            "vehicle_selector_api_url": vehicle_selector["api_url"],
            "vehicle_selector_mode": vehicle_selector["mode"],
            "vehicle_selector_initial_state": vehicle_selector["initial_state"],
            "vehicle_selector_initial_state_json": vehicle_selector["initial_state_json"],
            "vehicle_selector_selected_modification_id": vehicle_selector["selected_modification_id"],
            "vehicle_selector_selected_modification_id_json": vehicle_selector["selected_modification_id_json"],
            "vehicle_selector_preview": vehicle_selector["preview"],
            "vehicle_selector_preview_json": vehicle_selector["preview_json"],
            "breadcrumbs": [
                {"label": "Staff", "url": None},
                {"label": "Packages", "url": reverse("staff:packages:package_list")},
                {"label": f"#{package.pk}", "url": reverse("staff:packages:package_detail", args=[package.pk])},
                {"label": "Edit", "url": None},
            ],
            "page_title": f"Редактирование пакета #{package.pk}",
        }

    def get(self, request: HttpRequest, package_id: int) -> HttpResponse:
        package = self.get_package(package_id)
        form = StaffPackageUpdateForm(instance=package)
        context = self.build_context(
            request=request,
            package=package,
            form=form,
        )
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, package_id: int) -> HttpResponse:
        package = self.get_package(package_id)
        form = StaffPackageUpdateForm(request.POST, instance=package)

        try:
            categories_data = parse_package_item_categories_from_post(request.POST)
            items_data = parse_package_items_from_post(request.POST)
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)
            context = self.build_context(
                request=request,
                package=package,
                form=form,
            )
            return render(request, self.template_name, context, status=400)

        if not form.is_valid():
            context = self.build_context(
                request=request,
                package=package,
                form=form,
            )
            return render(request, self.template_name, context, status=400)

        try:
            updated_package = save_package_update(
                form=form,
                package=package,
                items_data=items_data,
                categories_data=categories_data,
            )
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)
            context = self.build_context(
                request=request,
                package=package,
                form=form,
            )
            return render(request, self.template_name, context, status=400)

        messages.success(request, "Пакет успешно сохранён.")

        action = request.POST.get("_action", "save_continue")
        if action == "save":
            return redirect("staff:packages:package_list")
        if action == "save_view":
            return redirect("staff:packages:package_detail", package_id=updated_package.pk)
        return redirect("staff:packages:package_edit", package_id=updated_package.pk)



