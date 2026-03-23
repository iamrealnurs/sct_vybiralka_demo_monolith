from django.urls import path

from .views import StaffPackageDetailView, StaffPackageListView

app_name = "staff"

urlpatterns = [
    path("packages/", StaffPackageListView.as_view(), name="package_list"),
    path("packages/<int:package_id>/", StaffPackageDetailView.as_view(), name="package_detail"),
]