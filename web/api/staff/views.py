from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

# IMPORTANT:
# Подставь правильный путь к моделям под своё приложение.
from catalog.models import CarServicePackage

from .services import get_package_list_data, get_vehicle_label, money_to_kzt_string


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


class StaffPackageDetailView(LoginRequiredMixin, View):
    """
    Пока заглушка под будущую detail-страницу.
    Route уже рабочий, поэтому список можно собирать сразу корректно.
    """

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

        vehicle_label = get_vehicle_label(package)

        return HttpResponse(
            f"""
            <html lang="ru">
            <head>
                <meta charset="utf-8">
                <title>Пакет #{package.pk}</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-slate-50 text-slate-900">
                <div class="max-w-4xl mx-auto px-6 py-8">
                    <a href="/staff/packages/" class="text-sm text-blue-600 hover:underline">← Назад к списку</a>
                    <h1 class="mt-4 text-3xl font-bold">{package.display_title}</h1>
                    <div class="mt-4 space-y-2 text-sm">
                        <p><strong>ID:</strong> {package.pk}</p>
                        <p><strong>Внутреннее имя:</strong> {package.name}</p>
                        <p><strong>Slug:</strong> {package.slug}</p>
                        <p><strong>Категория:</strong> {package.category.name}</p>
                        <p><strong>Автомобиль:</strong> {vehicle_label}</p>
                        <p><strong>Статус:</strong> {package.get_status_display()}</p>
                    </div>
                    <div class="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
                        Это временная заглушка. Потом сюда можно вынести полноценную страницу
                        /staff/packages/&lt;int:package_id&gt;/ со списком номенклатуры, ценами,
                        промо-блоком, картинкой и историей изменений.
                    </div>
                </div>
            </body>
            </html>
            """
        )