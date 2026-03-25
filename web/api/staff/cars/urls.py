from django.urls import path
from .views import StaffCarListView, StaffCarDetailView

app_name = "cars_staff"

urlpatterns = [
    # Теперь этот URL обрабатывает и отображение списка, и AJAX-фильтрацию
    path("", StaffCarListView.as_view(), name="car_list"), 
    path("<str:source_id>/", StaffCarDetailView.as_view(), name="car_detail"),
]
