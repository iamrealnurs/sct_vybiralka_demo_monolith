from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from .services import get_staff_car_list_data


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