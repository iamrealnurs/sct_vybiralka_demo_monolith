from django.urls import path

from .views import StaffPackageDetailView, StaffPackageListView, StaffPackageCreateView, StaffPackageUpdateView


app_name = "packages"

urlpatterns = [
    path("", StaffPackageListView.as_view(), name="package_list"),
    path("create/", StaffPackageCreateView.as_view(), name="package_create"),
    path("<int:package_id>/", StaffPackageDetailView.as_view(), name="package_detail"),
    path("<int:package_id>/edit/", StaffPackageUpdateView.as_view(), name="package_edit"),
]