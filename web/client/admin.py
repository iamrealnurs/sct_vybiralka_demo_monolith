from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Client, ClientCar, ClientPackageOrder


# ============================================================
# inlines
# ============================================================

class ClientCarInline(admin.TabularInline):
    model = ClientCar
    extra = 0
    fields = (
        "license_plate",
        "modification",
        "year",
        "mileage_km",
        "is_primary",
        "is_active",
    )
    autocomplete_fields = ("modification",)
    show_change_link = True
    classes = ("collapse",)


class ClientPackageOrderInline(admin.TabularInline):
    model = ClientPackageOrder
    extra = 0
    fields = (
        "package_public_title_snapshot",
        "status",
        "final_price_snapshot",
        "created_at",
    )
    readonly_fields = fields
    can_delete = False
    show_change_link = True
    classes = ("collapse",)


# ============================================================
# model admins
# ============================================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "is_active",
        "cars_count",
        "orders_count",
        "date_joined",
    )
    search_fields = ("full_name", "email")
    list_filter = ("is_active", "date_joined")
    ordering = ("-id",)
    list_per_page = 50
    inlines = (ClientCarInline, ClientPackageOrderInline)

    fieldsets = (
        (_("Личные данные"), {
            "fields": ("full_name", "email", "password")
        }),
        (_("Статус и права"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",),
        }),
        (_("Даты"), {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        from django.db.models import Count
        qs = super().get_queryset(request)
        return qs.annotate(
            _cars_count=Count("cars", distinct=True),
            _orders_count=Count("package_orders", distinct=True),
        )

    @admin.display(ordering="_cars_count", description=_("машин"))
    def cars_count(self, obj):
        return obj._cars_count

    @admin.display(ordering="_orders_count", description=_("заказов"))
    def orders_count(self, obj):
        return obj._orders_count


@admin.register(ClientCar)
class ClientCarAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "license_plate",
        "client_display",
        "modification",
        "year",
        "mileage_km",
        "is_primary",
        "is_active",
    )
    list_filter = (
        "is_primary",
        "is_active",
        "year",
        "modification__configuration__generation__model__mark",
    )
    search_fields = (
        "license_plate",
        "vin",
        "client__full_name",
        "client__email",
        "modification__name",
    )
    autocomplete_fields = ("client", "modification")
    ordering = ("-created_at",)
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (_("Владелец и авто"), {
            "fields": (
                "client",
                "modification",
                "is_primary",
                "is_active",
            )
        }),
        (_("Идентификация"), {
            "fields": (
                "license_plate",
                "vin",
            )
        }),
        (_("Характеристики"), {
            "fields": (
                "year",
                "mileage_km",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("клиент"), ordering="client__full_name")
    def client_display(self, obj):
        return obj.client.email if not hasattr(obj.client, 'full_name') else obj.client.full_name


@admin.register(ClientPackageOrder)
class ClientPackageOrderAdmin(admin.ModelAdmin):
    """
    Админка для заказов пакетов. 
    Почти все поля — snapshot, поэтому они только для чтения.
    """
    list_display = (
        "id",
        "status",
        "client_name_display",
        "package_title_display",
        "car_display",
        "final_price_snapshot",
        "is_promo_snapshot",
        "created_at",
    )
    list_filter = (
        "status",
        "is_promo_snapshot",
        "created_at",
        "package__category",
    )
    search_fields = (
        "client_full_name_snapshot",
        "client_email_snapshot",
        "car_license_plate_snapshot",
        "package_public_title_snapshot",
    )
    autocomplete_fields = ("client", "client_car", "package")
    ordering = ("-created_at",)
    list_per_page = 50

    # Заказы — это история, лучше запретить редактирование снапшотов вручную
    readonly_fields = (
        "created_at",
        "updated_at",
        "client_full_name_snapshot",
        "client_email_snapshot",
        "car_license_plate_snapshot",
        "car_vin_snapshot",
        "car_year_snapshot",
        "car_mileage_km_snapshot",
        "car_modification_source_id_snapshot",
        "car_modification_title_snapshot",
        "package_name_snapshot",
        "package_public_title_snapshot",
        "package_category_name_snapshot",
        "package_slug_snapshot",
        "regular_price_snapshot",
        "final_price_snapshot",
        "is_promo_snapshot",
        "promo_text_snapshot",
        "package_items_snapshot",
    )

    fieldsets = (
        (_("Основная связь"), {
            "fields": (
                "status",
                ("client", "client_car", "package"),
            )
        }),
        (_("Снимок клиента"), {
            "fields": (
                "client_full_name_snapshot",
                "client_email_snapshot",
            ),
            "classes": ("collapse",),
        }),
        (_("Снимок автомобиля"), {
            "fields": (
                "car_license_plate_snapshot",
                "car_vin_snapshot",
                "car_year_snapshot",
                "car_mileage_km_snapshot",
                "car_modification_title_snapshot",
                "car_modification_source_id_snapshot",
            ),
            "classes": ("collapse",),
        }),
        (_("Снимок пакета и цена"), {
            "fields": (
                "package_public_title_snapshot",
                "package_category_name_snapshot",
                "package_slug_snapshot",
                ("regular_price_snapshot", "final_price_snapshot"),
                ("is_promo_snapshot", "promo_text_snapshot"),
            ),
            "classes": ("collapse",),
        }),
        (_("Состав пакета (JSON)"), {
            "fields": ("package_items_snapshot",),
            "classes": ("collapse",),
        }),
        (_("Даты"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("клиент"), ordering="client_full_name_snapshot")
    def client_name_display(self, obj):
        return obj.client_full_name_snapshot

    @admin.display(description=_("пакет"), ordering="package_public_title_snapshot")
    def package_title_display(self, obj):
        return obj.package_public_title_snapshot

    @admin.display(description=_("авто"), ordering="car_license_plate_snapshot")
    def car_display(self, obj):
        return obj.car_license_plate_snapshot