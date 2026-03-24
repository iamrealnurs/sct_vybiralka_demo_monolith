from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    ClientLoginView,
    ClientDashboardView,
    ClientGarageListView,
    ClientCarCreateView,
    ClientCarDetailView,
    ClientCarActivateView,
)

app_name = 'client'

urlpatterns = [
    # Авторизация
    path('login/', ClientLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='client:login'), name='logout'),

    # Главная страница клиента (SCT Drive / Дашборд)
    path('', ClientDashboardView.as_view(), name='dashboard'),

    # Гараж (Мои автомобили)
    path('garage/', ClientGarageListView.as_view(), name='garage_list'),
    path('garage/add/', ClientCarCreateView.as_view(), name='car_add'),
    path('garage/<int:pk>/', ClientCarDetailView.as_view(), name='car_detail'),
    
    # Действие: сделать автомобиль активным
    path('garage/<int:pk>/activate/', ClientCarActivateView.as_view(), name='car_activate'),
]