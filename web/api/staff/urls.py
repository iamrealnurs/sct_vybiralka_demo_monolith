from django.urls import path

from .views import StaffPackageDetailView, StaffPackageListView, StaffPackageCreateView, StaffPackageUpdateView


app_name = "staff"

urlpatterns = [
    path("packages/", StaffPackageListView.as_view(), name="package_list"),
    path("packages/create/", StaffPackageCreateView.as_view(), name="package_create"),
    path("packages/<int:package_id>/", StaffPackageDetailView.as_view(), name="package_detail"),
    path("packages/<int:package_id>/edit/", StaffPackageUpdateView.as_view(), name="package_edit"),
]