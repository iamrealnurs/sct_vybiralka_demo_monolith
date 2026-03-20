from django.urls import path

from cars.views import cars_filter_page, cars_filter_api

app_name = "cars"

urlpatterns = [
    path("cars-filter/", cars_filter_page, name="filter_page"),
    path("cars-filter/api/", cars_filter_api, name="filter_api"),
]