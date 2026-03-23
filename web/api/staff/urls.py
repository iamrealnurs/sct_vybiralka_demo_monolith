from django.urls import path

from .views import StaffPackageDetailView, StaffPackageListView, StaffPackageCreateView

app_name = "staff"

urlpatterns = [
    path("packages/", StaffPackageListView.as_view(), name="package_list"),
    path("packages/<int:package_id>/", StaffPackageDetailView.as_view(), name="package_detail"),
    path("packages/create/", StaffPackageCreateView.as_view(), name="package_create")
]