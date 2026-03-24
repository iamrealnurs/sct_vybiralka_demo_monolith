from django.urls import include, path


app_name = "staff"

urlpatterns = [
    path("packages/", include('api.staff.packages.urls')),
    path("cars/", include("api.staff.cars.urls")),
]


