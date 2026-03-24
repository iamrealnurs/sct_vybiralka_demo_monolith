from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from catalog.models import CarServicePackage

from .forms import (
    StaffPackageCreateForm,
    StaffPackageImageForm,
    StaffPackageUpdateForm,
)
from .services import (
    build_edit_context,
    get_package_for_update,
    get_package_list_data,
    parse_package_items_from_post,
    save_package_update,
    parse_package_item_categories_from_post,
)


def build_vehicle_context(package: CarServicePackage) -> dict:
    modification = getattr(package, "modification", None)
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
        "mark": getattr(mark, "name", "—") if mark else "—",
        "model": getattr(model, "name", "—") if model else "—",
        "generation": getattr(generation, "name", "—") if generation else "—",
        "configuration": getattr(configuration, "name", "—") if configuration else "—",
        "modification": getattr(modification, "name", "—") if modification else "—",
        "source_id": getattr(modification, "source_id", "—") if modification else "—",
        "label": " / ".join(parts) if parts else "—",
    }


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
        form: StaffPackageCreateForm,
        image_form: StaffPackageImageForm,
    ) -> dict:
        return {
            "form": form,
            "image_form": image_form,
            "breadcrumbs": [
                {"label": "Staff", "url": None},
                {"label": "Packages", "url": reverse("staff:package_list")},
                {"label": "Create", "url": None},
            ],
        }

    def get(self, request: HttpRequest) -> HttpResponse:
        form = StaffPackageCreateForm()
        image_form = StaffPackageImageForm()

        context = self.get_context_data(form=form, image_form=image_form)
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

            action = request.POST.get("action") or "save"

            if action == "save_open":
                return redirect("staff:package_detail", package_id=package.id)

            return redirect("staff:package_list")

        context = self.get_context_data(form=form, image_form=image_form)
        return render(request, self.template_name, context)


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
                {"label": "Packages", "url": reverse("staff:package_list")},
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
        package: CarServicePackage,
        form: StaffPackageUpdateForm,
    ) -> dict:
        edit_context = build_edit_context(package)
        return {
            "package": package,
            "form": form,
            "edit_context": edit_context,
            "package_items": edit_context.package_items,
            "package_item_categories": edit_context.package_item_categories,
            "nomenclature_items": edit_context.nomenclature_items,
            "page_title": f"Редактирование пакета #{package.pk}",
        }

    def get(self, request: HttpRequest, package_id: int) -> HttpResponse:
        package = self.get_package(package_id)
        form = StaffPackageUpdateForm(instance=package)
        context = self.build_context(package=package, form=form)
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
            context = self.build_context(package=package, form=form)
            return render(request, self.template_name, context, status=400)

        if not form.is_valid():
            context = self.build_context(package=package, form=form)
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
            context = self.build_context(package=package, form=form)
            return render(request, self.template_name, context, status=400)

        messages.success(request, "Пакет успешно сохранён.")

        action = request.POST.get("_action", "save_continue")
        if action == "save":
            return redirect("staff:package_list")
        if action == "save_view":
            return redirect("staff:package_detail", package_id=updated_package.pk)
        return redirect("staff:package_edit", package_id=updated_package.pk)


