from django.urls import path
from .views import StaffCarListView

app_name = "cars"

urlpatterns = [
    path("", StaffCarListView.as_view(), name="car_list"),
]