from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django.urls import NoReverseMatch, reverse

# Импортируем модель Modification для обработки исключений
from cars.models import Modification
from .services import get_staff_car_list_data, get_car_detail_data

logger = logging.getLogger(__name__)


class StaffCarListView(LoginRequiredMixin, View):
    """
    Унифицированное представление для работы со справочником автомобилей.
    Поддерживает:
    1. Обычный GET-запрос: возвращает полную HTML-страницу.
    2. AJAX/JSON запрос: возвращает отфильтрованные данные и динамические опции фильтров.
    """
    template_name = "staff/cars/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        # 1. Вызываем единый сервисный слой для получения данных
        # Теперь сервис возвращает не только список и KPI, но и filter_options
        result = get_staff_car_list_data(request.GET)

        # 2. Проверяем, является ли запрос AJAX-запросом или требует JSON-формата
        # Это позволяет использовать один и тот же URL для страницы и для API фильтрации
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        is_json_requested = request.GET.get('format') == 'json'

        if is_ajax or is_json_requested:
            return self._render_json_response(result)

        # 3. Стандартный рендеринг HTML-страницы
        context = {
            "page_title": "Справочник автомобилей",
            "page_obj": result.page_obj,
            "kpi": result.kpi,
            "marks": result.marks,
            "filters": result.filters,
            "filter_options": result.filter_options,  # Передаем для начальной инициализации JS
            "breadcrumbs": [
                {"label": "Сотрудники", "url": reverse("staff:packages:package_list")},
                {"label": "Автомобили", "url": None},
            ],
            "preserved_query": self._get_preserved_query(request),
        }
        return render(request, self.template_name, context)

    def _render_json_response(self, result: Any) -> JsonResponse:
        """
        Формирует JSON-ответ для динамического обновления интерфейса.
        Включает в себя сериализованные объекты автомобилей и обновленные списки опций.
        """
        return JsonResponse({
            "ok": True,
            "count": result.kpi.get('total_count', 0),
            "results": [self._serialize_car(car) for car in result.page_obj],
            "options": result.filter_options,
            "kpi": result.kpi,
            "applied_filters": result.filters,
        })

    def _serialize_car(self, car: Modification) -> dict[str, Any]:
        """
        Глубокая сериализация объекта модификации для отображения в JS-компонентах.
        """
        spec = getattr(car, 'specification', None)
        
        return {
            "id": car.id,
            "source_id": car.source_id,
            "name": car.name,
            "group_name": car.group_name,
            "mark": {
                "id": car.configuration.generation.model.mark.id,
                "name": car.configuration.generation.model.mark.name,
            },
            "model": {
                "id": car.configuration.generation.model.id,
                "name": car.configuration.generation.model.name,
            },
            "generation": {
                "id": car.configuration.generation.id,
                "name": car.configuration.generation.name,
            },
            "configuration": {
                "id": car.configuration.id,
                "name": car.configuration.name,
            },
            "total_pkgs": getattr(car, 'total_pkgs', 0),
            "pub_pkgs": getattr(car, 'pub_pkgs', 0),
            "specification": {
                "powertrain_type": spec.get_powertrain_type_display() if spec else "—",
                "transmission_type": spec.get_transmission_type_display() if spec else "—",
                "drive_type": spec.get_drive_type_display() if spec else "—",
                "horse_power": spec.horse_power_hp if spec else None,
                "displacement": spec.displacement_cc if spec else None,
            }
        }

    def _get_preserved_query(self, request: HttpRequest) -> str:
        """
        Копирует GET-параметры, исключая 'page', для сохранения фильтрации при пагинации.
        """
        query = request.GET.copy()
        query.pop("page", None)
        return query.urlencode()


class StaffCarDetailView(LoginRequiredMixin, View):
    """
    Детальное представление модификации автомобиля.
    Использует расширенный сервис для получения характеристик и сгруппированных опций.
    """
    template_name = "staff/cars/detail.html"

    def get(self, request: HttpRequest, source_id: str) -> HttpResponse:
        try:
            # Получаем данные (car, packages, grouped_options) через сервис
            data = get_car_detail_data(source_id)
        except Modification.DoesNotExist:
            from django.http import Http404
            logger.warning(f"StaffCarDetailView: Modification with source_id {source_id} not found.")
            raise Http404("Автомобиль не найден")
            
        context = {
            **data,
            "page_title": f"Детальная информация: {data['car'].mark.name} {data['car'].name}",
            "breadcrumbs": [
                {"label": "Сотрудники", "url": reverse("staff:packages:package_list")},
                {"label": "Автомобили", "url": reverse("staff:cars_staff:car_list")},
                {"label": source_id, "url": None},
            ],
        }
        return render(request, self.template_name, context)

