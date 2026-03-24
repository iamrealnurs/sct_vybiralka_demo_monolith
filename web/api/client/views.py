from __future__ import annotations

import json
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View

from cars.models import Mark, Modification
from client.models import ClientCar
from .forms import ClientLoginForm, ClientCarAddForm
from .services import (
    get_client_dashboard_data,
    get_client_garage_list,
    set_primary_client_car,
    get_client_primary_car
)


class ClientLoginView(LoginView):
    """
    Страница входа для клиента.
    """
    form_class = ClientLoginForm
    template_name = "client/auth/login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        return reverse_lazy("client:dashboard")


class ClientDashboardView(LoginRequiredMixin, View):
    """
    Главная страница клиента (SCT Drive).
    Отображает активный автомобиль и подходящие пакеты услуг.
    """
    template_name = "client/dashboard.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        # Получаем данные через сервис (активное авто, пакеты и флаг наличия машин вообще)
        data = get_client_dashboard_data(request.user)
        
        context = {
            "page_title": "Мой Сервис",
            **data
        }
        return render(request, self.template_name, context)


class ClientGarageListView(LoginRequiredMixin, View):
    """
    Гараж: список всех автомобилей клиента.
    """
    template_name = "client/garage/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        cars = get_client_garage_list(request.user)
        
        context = {
            "page_title": "Мой гараж",
            "cars": cars,
        }
        return render(request, self.template_name, context)


class ClientCarCreateView(LoginRequiredMixin, View):
    """
    Добавление автомобиля в гараж.
    Использует каскадный селектор модификаций.
    """
    template_name = "client/garage/create.html"

    def get_context_data(self, form: ClientCarAddForm) -> dict:
        # Для работы каскадного фильтра нам нужны все марки и URL к API (из staff/cars)
        return {
            "form": form,
            "marks": Mark.objects.all().order_by("name"),
            "page_title": "Добавить автомобиль",
            # Прокидываем настройки для JS селектора (аналогично Staff-части)
            "vehicle_selector_api_url": reverse("staff:cars_staff:car_list"),
        }

    def get(self, request: HttpRequest) -> HttpResponse:
        form = ClientCarAddForm()
        return render(request, self.template_name, self.get_context_data(form))

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ClientCarAddForm(request.POST)
        if form.is_valid():
            car = form.save(commit=False)
            car.client = request.user  # Привязываем машину к текущему пользователю
            
            # Если это первая машина, делаем её основной принудительно
            if not request.user.cars.exists():
                car.is_primary = True
            
            car.save()
            
            # Если пользователь отметил "сделать основной", сервис переключит остальные
            if car.is_primary:
                set_primary_client_car(request.user, car.id)
                
            messages.success(request, f"Автомобиль {car.license_plate} успешно добавлен в гараж.")
            return redirect("client:garage_list")

        return render(request, self.template_name, self.get_context_data(form))


class ClientCarDetailView(LoginRequiredMixin, View):
    """
    Страница конкретного автомобиля клиента с его данными и тех. характеристиками.
    """
    template_name = "client/garage/detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        # Проверяем, что машина принадлежит клиенту
        car = get_object_or_404(ClientCar, pk=pk, client=request.user)
        
        context = {
            "page_title": f"Автомобиль {car.license_plate}",
            "car": car,
            "specification": getattr(car.modification, 'specification', None),
        }
        return render(request, self.template_name, context)


class ClientCarActivateView(LoginRequiredMixin, View):
    """
    Переключение основного автомобиля.
    """
    def post(self, request: HttpRequest, pk: int) -> HttpResponseRedirect:
        if set_primary_client_car(request.user, pk):
            messages.success(request, "Активный автомобиль изменен.")
        else:
            messages.error(request, "Ошибка при смене автомобиля.")
        
        return redirect("client:garage_list")