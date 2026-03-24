from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import NoReverseMatch, reverse

from .services import get_staff_car_list_data, get_car_detail_data


class StaffCarListView(LoginRequiredMixin, View):
    """
    Представление для отображения справочника автомобилей (модификаций)
    в интерфейсе сотрудников.
    """
    template_name = "staff/cars/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Метод GET: 
        1. Извлекает параметры фильтрации из строки запроса (request.GET).
        2. Вызывает сервисный слой для получения отфильтрованных данных и KPI.
        3. Рендерит страницу со списком автомобилей.
        """
        
        # Получаем данные из сервисного слоя
        # Мы передаем весь словарь параметров (марка, модель, поиск, страница и т.д.)
        result = get_staff_car_list_data(request.GET)

        context = {
            "page_title": "Справочник автомобилей",
            
            # Объект пагинации (содержит список машин для текущей страницы)
            "page_obj": result.page_obj,
            
            # Статистика для KPI карточек (всего, с пакетами и т.д.)
            "kpi": result.kpi,
            
            # Список всех марок для наполнения выпадающего списка в фильтре
            "marks": result.marks,
            
            # Примененные фильтры, чтобы вернуть их в поля формы (value="{{ filters.q }}")
            "filters": result.filters,
            
            # Хлебные крошки для навигации
            "breadcrumbs": [
                {"label": "Сотрудники", "url": None},
                {"label": "Автомобили", "url": None},
            ],
            
            # Сохраняем строку запроса без параметра 'page' для корректной работы ссылок пагинации
            "preserved_query": self._get_preserved_query(request),
        }

        return render(request, self.template_name, context)

    def _get_preserved_query(self, request: HttpRequest) -> str:
        """
        Вспомогательный метод: берет текущие GET-параметры и исключает 'page'.
        Это нужно, чтобы при переходе по страницам фильтры не сбрасывались.
        Пример: если сейчас ?mark=Toyota&page=2, вернет 'mark=Toyota'
        """
        query = request.GET.copy()
        query.pop("page", None)
        return query.urlencode()


class StaffCarDetailView(LoginRequiredMixin, View):
    template_name = "staff/cars/detail.html"

    def get(self, request, source_id):
        # Вызываем сервис. Если source_id неверный, get() внутри сервиса выкинет ошибку, 
        # здесь можно добавить обработку try/except для 404
        try:
            data = get_car_detail_data(source_id)
        except Modification.DoesNotExist:
            from django.http import Http404
            raise Http404("Автомобиль не найден")
            
        context = {
            **data,
            "page_title": f"Детальная информация: {data['car'].name}",
            "breadcrumbs": [
                {"label": "Сотрудники", "url": reverse("staff:packages:package_list")},
                {"label": "Автомобили", "url": reverse("staff:cars_staff:car_list")},
                {"label": source_id, "url": None},
            ],
        }
        return render(request, self.template_name, context)


