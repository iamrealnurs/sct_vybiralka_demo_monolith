from __future__ import annotations

from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

# IMPORTANT:
# Подставь правильный путь к моделям под своё приложение.
from catalog.models import CarServicePackage, PackageItemCategory

from .forms import StaffPackageCreateForm, StaffPackageImageForm
from .services import get_package_list_data


def build_vehicle_context(package: CarServicePackage) -> dict:
    modification = getattr(package, "modification", None)
    configuration = getattr(modification, "configuration", None) if modification else None
    generation = getattr(configuration, "generation", None) if configuration else None
    model = getattr(generation, "model", None) if generation else None
    mark = getattr(model, "mark", None) if model else None

    parts = []
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
        "label": " / ".join(parts) if parts else "—",
    }


def build_grouped_items(package: CarServicePackage) -> list[dict]:
    """
    Группирует элементы пакета по локальным категориям.
    """
    grouped = []
    active_categories = list(package.item_categories.filter(is_deleted=False, is_active=True).order_by("sort_order", "id"))

    for category in active_categories:
        items = list(
            category.items
            .filter(is_deleted=False, is_active=True)
            .select_related("nomenclature_item")
            .order_by("sort_order", "id")
        )
        grouped.append({
            "category": category,
            "items": items,
        })

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

    def get(self, request: HttpRequest) -> HttpResponse:
        form = StaffPackageCreateForm()
        image_form = StaffPackageImageForm()

        context = {
            "form": form,
            "image_form": image_form,
        }
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

            return redirect("staff:package_detail", package_id=package.id)

        context = {
            "form": form,
            "image_form": image_form,
        }
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
        item_categories = (
            package.item_categories
            .filter(is_deleted=False, is_active=True)
            .order_by("sort_order", "id")
        )
        grouped_items = build_grouped_items(package)

        context = {
            "package": package,
            "vehicle": vehicle,
            "item_categories": item_categories,
            "grouped_items": grouped_items,
        }
        return render(request, self.template_name, context)