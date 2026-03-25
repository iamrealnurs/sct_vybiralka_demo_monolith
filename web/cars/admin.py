from __future__ import annotations

from django.contrib import admin
from django.db.models import Count, Exists, OuterRef
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from catalog.models import CarServicePackage

from .models import (
    BodyType,
    CarModel,
    Configuration,
    ConfigurationPhoto,
    Generation,
    Mark,
    MarkLogo,
    Modification,
    ModificationOption,
    ModificationRawSpecification,
    ModificationSpecification,
    OptionCategory,
    OptionDefinition,
)


# ============================================================
# custom list filters
# ============================================================


class HasSpecificationFilter(admin.SimpleListFilter):
    title = _("есть нормализованные характеристики")
    parameter_name = "has_spec"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(specification__isnull=False)
        if value == "no":
            return queryset.filter(specification__isnull=True)
        return queryset


class HasRawSpecificationFilter(admin.SimpleListFilter):
    title = _("есть raw-характеристики")
    parameter_name = "has_raw_spec"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(raw_specification__isnull=False)
        if value == "no":
            return queryset.filter(raw_specification__isnull=True)
        return queryset


class HasOptionsFilter(admin.SimpleListFilter):
    title = _("есть опции")
    parameter_name = "has_options"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(option_values__isnull=False).distinct()
        if value == "no":
            return queryset.filter(option_values__isnull=True)
        return queryset


class HasServicePackagesFilter(admin.SimpleListFilter):
    title = _("есть пакеты услуг")
    parameter_name = "has_service_packages"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(service_packages__isnull=False).distinct()
        if value == "no":
            return queryset.filter(service_packages__isnull=True)
        return queryset


class BodyTypeCodeFilter(admin.SimpleListFilter):
    title = _("тип кузова")
    parameter_name = "body_type_code"

    def lookups(self, request, model_admin):
        qs = BodyType.objects.order_by("name", "code").values_list("code", "name")
        return [(code, name or code) for code, name in qs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(configuration__body_type__code=self.value())
        return queryset


class CountryRawFallbackFilter(admin.SimpleListFilter):
    title = _("страна")
    parameter_name = "country_choice"

    def lookups(self, request, model_admin):
        return Mark._meta.get_field("country").choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(country=self.value())
        return queryset


# ============================================================
# inlines
# ============================================================


class CarModelInline(admin.TabularInline):
    model = CarModel
    extra = 0
    fields = (
        "name",
        "name_ru",
        "source_id",
        "class_code",
        "year_from",
        "year_to",
    )
    show_change_link = True
    ordering = ("name",)
    autocomplete_fields = ()
    classes = ("collapse",)


class GenerationInline(admin.TabularInline):
    model = Generation
    extra = 0
    fields = (
        "name",
        "source_id",
        "year_from",
        "year_to",
    )
    show_change_link = True
    ordering = ("year_from", "name")
    classes = ("collapse",)


class ConfigurationInline(admin.TabularInline):
    model = Configuration
    extra = 0
    fields = (
        "name",
        "source_id",
        "body_type",
        "doors_count",
    )
    show_change_link = True
    autocomplete_fields = ("body_type",)
    ordering = ("name",)
    classes = ("collapse",)


class ModificationInline(admin.TabularInline):
    model = Modification
    extra = 0
    fields = (
        "name",
        "source_id",
        "group_name",
        "is_closed",
        "price_from",
        "price_to",
    )
    show_change_link = True
    ordering = ("name",)
    classes = ("collapse",)


class CarServicePackageInline(admin.TabularInline):
    model = CarServicePackage
    extra = 0
    fk_name = "modification"
    show_change_link = True
    can_delete = False
    classes = ("collapse",)

    fields = (
        "category",
        "name",
        "public_title",
        "status",
        "is_promo",
        "package_discount_percent",
        "regular_price_display",
        "final_price_display",
        "is_active",
        "is_deleted",
    )

    readonly_fields = (
        "category",
        "name",
        "public_title",
        "status",
        "is_promo",
        "package_discount_percent",
        "regular_price_display",
        "final_price_display",
        "is_active",
        "is_deleted",
    )

    verbose_name = _("пакет услуг")
    verbose_name_plural = _("пакеты услуг")

    @admin.display(description=_("обычная цена"))
    def regular_price_display(self, obj):
        return obj.regular_price

    @admin.display(description=_("итоговая цена"))
    def final_price_display(self, obj):
        return obj.final_price


class ModificationSpecificationInline(admin.StackedInline):
    model = ModificationSpecification
    extra = 0
    can_delete = False
    max_num = 1

    fieldsets = (
        (_("Общая классификация"), {
            "fields": (
                ("auto_class", "auto_class_raw"),
                ("steering_wheel_position", "steering_wheel_position_raw"),
            )
        }),
        (_("Кузов и размеры"), {
            "fields": (
                "body_size_raw",
                ("length_mm", "width_mm", "height_mm"),
                ("wheelbase_mm", "ground_clearance_mm"),
                ("front_track_mm", "rear_track_mm"),
                ("doors_count", "seats_count"),
                ("boot_volume_raw", "trunk_volume_min_l", "trunk_volume_max_l"),
                ("fuel_tank_volume_l", "curb_weight_kg", "gross_weight_kg"),
                "origin_tires_size_raw",
                "landing_wheels_size_raw",
                "disk_size_raw",
                "wheel_size_raw",
            ),
            "classes": ("collapse",),
        }),
        (_("Трансмиссия и привод"), {
            "fields": (
                ("transmission_type", "transmission_type_raw"),
                ("transmission_code", "transmission_code_raw"),
                ("gears_count", "drive_type", "drive_type_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("Подвеска и тормоза"), {
            "fields": (
                ("front_suspension_type", "front_suspension_type_raw"),
                ("rear_suspension_type", "rear_suspension_type_raw"),
                ("front_brake_type", "front_brake_type_raw"),
                ("rear_brake_type", "rear_brake_type_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("Динамика и расход"), {
            "fields": (
                ("max_speed_kmh", "acceleration_0_to_100_sec"),
                "consumption_raw",
                ("consumption_city_l_100km", "consumption_highway_l_100km", "consumption_mixed_l_100km"),
                ("electric_consumption_kwh_100km", "co2_emission_g_km"),
                ("fuel_type", "fuel_type_raw"),
                ("emission_standard", "emission_standard_raw"),
                ("consumption_calc_type", "consumption_calc_type_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("Двигатель"), {
            "fields": (
                ("powertrain_type", "powertrain_type_raw"),
                ("engine_position_layout", "displacement_cc"),
                ("aspiration_type", "aspiration_type_raw"),
                ("max_power_raw", "horse_power_hp", "power_kw", "power_rpm_raw"),
                ("torque_raw", "torque_nm", "torque_rpm_raw"),
                ("cylinders_layout", "cylinders_layout_raw"),
                ("cylinders_count", "valves_count"),
                ("fuel_injection_type", "fuel_injection_type_raw"),
                ("compression_ratio",),
                ("diameter_raw", "cylinder_bore_mm", "piston_stroke_mm"),
                ("engine_code", "engine_code_secondary"),
                ("valvetrain_type", "valvetrain_type_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("EV и батарея"), {
            "fields": (
                ("battery_capacity_kwh", "battery_capacity_usable_kwh"),
                ("battery_type", "battery_type_raw"),
                ("electric_range_km", "max_charge_power_kw"),
                ("ac_charge_time_raw", "dc_fast_charge_time_raw"),
                "quickcharge_description",
                "charging_port_types_raw",
                ("battery_charge_cycles", "battery_temp_raw"),
            ),
            "classes": ("collapse",),
        }),
    )


class ModificationRawSpecificationInline(admin.StackedInline):
    model = ModificationRawSpecification
    extra = 0
    can_delete = False
    max_num = 1
    readonly_fields = ("raw_payload_pretty", "unparsed_payload_pretty")
    fields = (
        "raw_payload_pretty",
        "unparsed_payload_pretty",
        "parse_notes",
    )
    classes = ("collapse",)

    @admin.display(description=_("raw payload"))
    def raw_payload_pretty(self, obj):
        if not obj:
            return "-"
        return obj.raw_payload

    @admin.display(description=_("unparsed payload"))
    def unparsed_payload_pretty(self, obj):
        if not obj:
            return "-"
        return obj.unparsed_payload


class ModificationOptionInline(admin.TabularInline):
    model = ModificationOption
    extra = 0
    fields = (
        "option_definition",
        "value_bool",
        "raw_value",
        "source_column",
    )
    autocomplete_fields = ("option_definition",)
    ordering = ("option_definition__name",)
    classes = ("collapse",)


class MarkLogoInline(admin.StackedInline):
    model = MarkLogo
    extra = 0
    can_delete = True
    max_num = 1
    readonly_fields = ("logo_preview", "created_at", "updated_at")
    fields = (
        "image",
        "logo_preview",
        ("source_file_name", "source_mark_id"),
        "alt_text",
        "is_active",
        ("created_at", "updated_at"),
    )
    classes = ("collapse",)

    @admin.display(description=_("предпросмотр"))
    def logo_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 180px; object-fit: contain; border: 1px solid #ddd; padding: 4px; background: white;" />',
                obj.image.url,
            )
        return "-"


class ConfigurationPhotoInline(admin.StackedInline):
    model = ConfigurationPhoto
    extra = 0
    can_delete = True
    max_num = 1
    readonly_fields = ("photo_preview", "created_at", "updated_at")
    fields = (
        "image",
        "photo_preview",
        ("source_file_name", "source_configuration_id"),
        "alt_text",
        ("is_main", "sort_order"),
        ("created_at", "updated_at"),
    )
    classes = ("collapse",)

    @admin.display(description=_("предпросмотр"))
    def photo_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 220px; object-fit: cover; border: 1px solid #ddd; padding: 4px; background: white;" />',
                obj.image.url,
            )
        return "-"


# ============================================================
# admin actions
# ============================================================


@admin.action(description=_("Пометить выбранные модификации как закрытые"))
def mark_modifications_closed(modeladmin, request, queryset):
    queryset.update(is_closed=True)


@admin.action(description=_("Пометить выбранные модификации как открытые"))
def mark_modifications_open(modeladmin, request, queryset):
    queryset.update(is_closed=False)


@admin.action(description=_("Активировать выбранные категории"))
def activate_categories(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные категории"))
def deactivate_categories(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Активировать выбранные опции"))
def activate_option_definitions(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные опции"))
def deactivate_option_definitions(modeladmin, request, queryset):
    queryset.update(is_active=False)


# ============================================================
# model admins
# ============================================================


@admin.register(BodyType)
class BodyTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "created_at", "updated_at")
    search_fields = ("code", "name", "description")
    ordering = ("name", "code")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("code", "name", "description")
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(OptionCategory)
class OptionCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "code",
        "sort_order",
        "is_active",
        "options_count",
        "created_at",
    )
    list_editable = ("sort_order", "is_active")
    search_fields = ("name", "code", "description")
    list_filter = ("is_active",)
    ordering = ("sort_order", "name")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    actions = (activate_categories, deactivate_categories)
    inlines = ()

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "code",
                ("sort_order", "is_active"),
                "description",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_options_count=Count("options", distinct=True))

    @admin.display(ordering="_options_count", description=_("опций"))
    def options_count(self, obj):
        return obj._options_count


@admin.register(OptionDefinition)
class OptionDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "code",
        "category",
        "sort_order",
        "is_active",
        "modifications_count",
    )
    list_editable = ("sort_order", "is_active")
    search_fields = (
        "name",
        "code",
        "full_name",
        "description",
        "category__name",
        "category__code",
    )
    list_filter = ("is_active", "category")
    autocomplete_fields = ("category",)
    ordering = ("sort_order", "name", "code")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    actions = (activate_option_definitions, deactivate_option_definitions)

    fieldsets = (
        (None, {
            "fields": (
                "category",
                ("name", "code"),
                "full_name",
                "description",
                ("sort_order", "is_active"),
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_modifications_count=Count("modification_values", distinct=True))

    @admin.display(ordering="_modifications_count", description=_("использований"))
    def modifications_count(self, obj):
        return obj._modifications_count


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "name_ru",
        "source_id",
        "source_numeric_id",
        "country",
        "is_popular",
        "year_from",
        "year_to",
        "has_logo_badge",
        "models_count",
    )
    list_filter = (CountryRawFallbackFilter, "is_popular")
    search_fields = (
        "name",
        "name_ru",
        "source_id",
        "source_numeric_id",
        "country_raw",
    )
    ordering = ("name",)
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    inlines = (MarkLogoInline, CarModelInline)

    fieldsets = (
        (_("Идентификаторы"), {
            "fields": (
                "source_id",
                "source_numeric_id",
            )
        }),
        (_("Основное"), {
            "fields": (
                ("name", "name_ru"),
                ("country", "country_raw"),
                ("is_popular",),
                ("year_from", "year_to"),
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _models_count=Count("car_models", distinct=True),
            _has_logo=Exists(MarkLogo.objects.filter(mark_id=OuterRef("pk"))),
        )

    @admin.display(ordering="_models_count", description=_("моделей"))
    def models_count(self, obj):
        return obj._models_count

    @admin.display(boolean=True, description=_("лого"))
    def has_logo_badge(self, obj):
        return bool(getattr(obj, "_has_logo", False))


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "name_ru",
        "mark",
        "source_id",
        "class_code",
        "year_from",
        "year_to",
        "generations_count",
    )
    list_filter = ("class_code", "mark")
    search_fields = (
        "name",
        "name_ru",
        "source_id",
        "mark__name",
        "mark__name_ru",
        "mark__source_id",
    )
    autocomplete_fields = ("mark",)
    ordering = ("mark__name", "name")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    inlines = (GenerationInline,)

    fieldsets = (
        (_("Идентификаторы"), {
            "fields": ("source_id",)
        }),
        (_("Связи"), {
            "fields": ("mark",)
        }),
        (_("Основное"), {
            "fields": (
                ("name", "name_ru"),
                ("class_code", "class_code_raw"),
                ("year_from", "year_to"),
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_generations_count=Count("generations", distinct=True))

    @admin.display(ordering="_generations_count", description=_("поколений"))
    def generations_count(self, obj):
        return obj._generations_count


@admin.register(Generation)
class GenerationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "model",
        "source_id",
        "year_from",
        "year_to",
        "configurations_count",
    )
    list_filter = ("model__mark", "year_from", "year_to")
    search_fields = (
        "name",
        "source_id",
        "model__name",
        "model__name_ru",
        "model__source_id",
        "model__mark__name",
        "model__mark__name_ru",
    )
    autocomplete_fields = ("model",)
    ordering = ("model__mark__name", "model__name", "year_from", "name")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    inlines = (ConfigurationInline,)

    fieldsets = (
        (_("Идентификаторы"), {
            "fields": ("source_id",)
        }),
        (_("Связи"), {
            "fields": ("model",)
        }),
        (_("Основное"), {
            "fields": (
                "name",
                ("year_from", "year_to"),
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_configurations_count=Count("configurations", distinct=True))

    @admin.display(ordering="_configurations_count", description=_("конфигураций"))
    def configurations_count(self, obj):
        return obj._configurations_count


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "generation",
        "source_id",
        "body_type",
        "doors_count",
        "has_photo_badge",
        "modifications_count",
    )
    list_filter = ("body_type", "doors_count", "generation__model__mark")
    search_fields = (
        "name",
        "source_id",
        "generation__name",
        "generation__source_id",
        "generation__model__name",
        "generation__model__mark__name",
        "body_type__code",
        "body_type__name",
    )
    autocomplete_fields = ("generation", "body_type")
    ordering = ("generation__model__mark__name", "generation__model__name", "name")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    inlines = (ConfigurationPhotoInline, ModificationInline)

    fieldsets = (
        (_("Идентификаторы"), {
            "fields": ("source_id",)
        }),
        (_("Связи"), {
            "fields": (
                "generation",
                "body_type",
            )
        }),
        (_("Основное"), {
            "fields": (
                "name",
                "doors_count",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _modifications_count=Count("modifications", distinct=True),
            _has_photo=Exists(ConfigurationPhoto.objects.filter(configuration_id=OuterRef("pk"))),
        )

    @admin.display(ordering="_modifications_count", description=_("модификаций"))
    def modifications_count(self, obj):
        return obj._modifications_count

    @admin.display(boolean=True, description=_("фото"))
    def has_photo_badge(self, obj):
        return bool(getattr(obj, "_has_photo", False))


@admin.register(Modification)
class ModificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "group_name",
        "mark_name",
        "model_name",
        "configuration",
        "source_id",
        "is_closed",
        "price_from",
        "price_to",
        "has_spec_badge",
        "has_raw_spec_badge",
        "options_count",
        "service_packages_count",
    )
    list_filter = (
        "is_closed",
        HasSpecificationFilter,
        HasRawSpecificationFilter,
        HasOptionsFilter,
        HasServicePackagesFilter,
        BodyTypeCodeFilter,
        "configuration__generation__model__mark",
    )
    search_fields = (
        "name",
        "group_name",
        "source_id",
        "configuration__name",
        "configuration__source_id",
        "configuration__generation__name",
        "configuration__generation__source_id",
        "configuration__generation__model__name",
        "configuration__generation__model__name_ru",
        "configuration__generation__model__source_id",
        "configuration__generation__model__mark__name",
        "configuration__generation__model__mark__name_ru",
        "configuration__generation__model__mark__source_id",
        "service_packages__name",
        "service_packages__public_title",
        "service_packages__slug",
    )
    autocomplete_fields = ("configuration",)
    ordering = (
        "configuration__generation__model__mark__name",
        "configuration__generation__model__name",
        "name",
    )
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at", "full_title")
    actions = (mark_modifications_closed, mark_modifications_open)
    inlines = (
        ModificationSpecificationInline,
        ModificationRawSpecificationInline,
        ModificationOptionInline,
        CarServicePackageInline,
    )

    fieldsets = (
        (_("Идентификаторы"), {
            "fields": (
                "source_id",
                "full_title",
            )
        }),
        (_("Связи"), {
            "fields": ("configuration",)
        }),
        (_("Основное"), {
            "fields": (
                "name",
                "group_name",
                "is_closed",
                ("price_from", "price_to"),
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            "configuration",
            "configuration__body_type",
            "configuration__generation",
            "configuration__generation__model",
            "configuration__generation__model__mark",
        )
        qs = qs.annotate(
            _options_count=Count("option_values", distinct=True),
            _service_packages_count=Count("service_packages", distinct=True),
            _has_spec=Exists(
                ModificationSpecification.objects.filter(modification_id=OuterRef("pk"))
            ),
            _has_raw_spec=Exists(
                ModificationRawSpecification.objects.filter(modification_id=OuterRef("pk"))
            ),
        )
        return qs

    @admin.display(description=_("марка"), ordering="configuration__generation__model__mark__name")
    def mark_name(self, obj):
        return obj.configuration.generation.model.mark.name

    @admin.display(description=_("модель"), ordering="configuration__generation__model__name")
    def model_name(self, obj):
        return obj.configuration.generation.model.name

    @admin.display(boolean=True, description=_("spec"))
    def has_spec_badge(self, obj):
        return bool(getattr(obj, "_has_spec", False))

    @admin.display(boolean=True, description=_("raw"))
    def has_raw_spec_badge(self, obj):
        return bool(getattr(obj, "_has_raw_spec", False))

    @admin.display(ordering="_options_count", description=_("опций"))
    def options_count(self, obj):
        return obj._options_count

    @admin.display(ordering="_service_packages_count", description=_("пакетов"))
    def service_packages_count(self, obj):
        return obj._service_packages_count


@admin.register(ModificationSpecification)
class ModificationSpecificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "modification",
        "auto_class",
        "powertrain_type",
        "fuel_type",
        "transmission_type",
        "drive_type",
        "horse_power_hp",
        "displacement_cc",
        "electric_range_km",
    )
    list_filter = (
        "auto_class",
        "powertrain_type",
        "fuel_type",
        "transmission_type",
        "drive_type",
        "battery_type",
        "steering_wheel_position",
    )
    search_fields = (
        "modification__name",
        "modification__source_id",
        "modification__group_name",
        "modification__configuration__generation__model__name",
        "modification__configuration__generation__model__mark__name",
        "engine_code",
        "engine_code_secondary",
        "max_power_raw",
        "torque_raw",
    )
    autocomplete_fields = ("modification",)
    list_per_page = 50
    readonly_fields = (
        "created_at",
        "updated_at",
        "full_title",
        "display_power",
        "display_torque",
        "display_range",
    )

    fieldsets = (
        (_("Связь"), {
            "fields": (
                "modification",
                "full_title",
            )
        }),
        (_("Общая классификация"), {
            "fields": (
                ("auto_class", "auto_class_raw"),
                ("steering_wheel_position", "steering_wheel_position_raw"),
            )
        }),
        (_("Кузов и размеры"), {
            "fields": (
                "body_size_raw",
                ("length_mm", "width_mm", "height_mm"),
                ("wheelbase_mm", "ground_clearance_mm"),
                ("front_track_mm", "rear_track_mm"),
                ("doors_count", "seats_count"),
                ("boot_volume_raw", "trunk_volume_min_l", "trunk_volume_max_l"),
                ("fuel_tank_volume_l", "curb_weight_kg", "gross_weight_kg"),
                "origin_tires_size_raw",
                "landing_wheels_size_raw",
                "disk_size_raw",
                "wheel_size_raw",
            ),
            "classes": ("collapse",),
        }),
        (_("Трансмиссия и привод"), {
            "fields": (
                ("transmission_type", "transmission_type_raw"),
                ("transmission_code", "transmission_code_raw"),
                ("gears_count", "drive_type", "drive_type_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("Подвеска и тормоза"), {
            "fields": (
                ("front_suspension_type", "front_suspension_type_raw"),
                ("rear_suspension_type", "rear_suspension_type_raw"),
                ("front_brake_type", "front_brake_type_raw"),
                ("rear_brake_type", "rear_brake_type_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("Динамика и расход"), {
            "fields": (
                ("max_speed_kmh", "acceleration_0_to_100_sec"),
                "consumption_raw",
                ("consumption_city_l_100km", "consumption_highway_l_100km", "consumption_mixed_l_100km"),
                ("electric_consumption_kwh_100km", "co2_emission_g_km"),
                ("fuel_type", "fuel_type_raw"),
                ("emission_standard", "emission_standard_raw"),
                ("consumption_calc_type", "consumption_calc_type_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("Двигатель"), {
            "fields": (
                ("powertrain_type", "powertrain_type_raw"),
                ("engine_position_layout", "displacement_cc"),
                ("aspiration_type", "aspiration_type_raw"),
                ("max_power_raw", "horse_power_hp", "power_kw", "power_rpm_raw"),
                ("display_power",),
                ("torque_raw", "torque_nm", "torque_rpm_raw"),
                ("display_torque",),
                ("cylinders_layout", "cylinders_layout_raw"),
                ("cylinders_count", "valves_count"),
                ("fuel_injection_type", "fuel_injection_type_raw"),
                ("compression_ratio",),
                ("diameter_raw", "cylinder_bore_mm", "piston_stroke_mm"),
                ("engine_code", "engine_code_secondary"),
                ("valvetrain_type", "valvetrain_type_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("EV и батарея"), {
            "fields": (
                ("battery_capacity_kwh", "battery_capacity_usable_kwh"),
                ("battery_type", "battery_type_raw"),
                ("electric_range_km", "max_charge_power_kw"),
                ("display_range",),
                ("ac_charge_time_raw", "dc_fast_charge_time_raw"),
                "quickcharge_description",
                "charging_port_types_raw",
                ("battery_charge_cycles", "battery_temp_raw"),
            ),
            "classes": ("collapse",),
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("полный заголовок"))
    def full_title(self, obj):
        if not obj or not obj.modification_id:
            return "-"
        return obj.modification.full_title

    @admin.display(description=_("мощность"))
    def display_power(self, obj):
        parts: list[str] = []
        if obj.horse_power_hp is not None:
            parts.append(f"{obj.horse_power_hp} л.с.")
        if obj.power_kw is not None:
            parts.append(f"{obj.power_kw} кВт")
        if obj.power_rpm_raw:
            parts.append(str(obj.power_rpm_raw))
        if obj.max_power_raw:
            parts.append(f"raw: {obj.max_power_raw}")
        return " | ".join(parts) if parts else "-"

    @admin.display(description=_("крутящий момент"))
    def display_torque(self, obj):
        parts: list[str] = []
        if obj.torque_nm is not None:
            parts.append(f"{obj.torque_nm} Н·м")
        if obj.torque_rpm_raw:
            parts.append(str(obj.torque_rpm_raw))
        if obj.torque_raw:
            parts.append(f"raw: {obj.torque_raw}")
        return " | ".join(parts) if parts else "-"

    @admin.display(description=_("запас хода"))
    def display_range(self, obj):
        parts: list[str] = []
        if obj.electric_range_km is not None:
            parts.append(f"{obj.electric_range_km} км")
        if obj.consumption_calc_type:
            try:
                parts.append(obj.get_consumption_calc_type_display())
            except Exception:
                parts.append(str(obj.consumption_calc_type))
        return " | ".join(parts) if parts else "-"


@admin.register(ModificationRawSpecification)
class ModificationRawSpecificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "modification",
        "raw_keys_count",
        "unparsed_keys_count",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "modification__name",
        "modification__source_id",
        "modification__configuration__generation__model__name",
        "modification__configuration__generation__model__mark__name",
        "parse_notes",
    )
    autocomplete_fields = ("modification",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "raw_payload",
        "unparsed_payload",
        "raw_keys_count",
        "unparsed_keys_count",
    )
    list_per_page = 50

    fieldsets = (
        (_("Связь"), {
            "fields": ("modification",)
        }),
        (_("Сырые данные"), {
            "fields": (
                "raw_keys_count",
                "raw_payload",
                "unparsed_keys_count",
                "unparsed_payload",
                "parse_notes",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("ключей raw"))
    def raw_keys_count(self, obj):
        return len(obj.raw_payload or {})

    @admin.display(description=_("ключей unparsed"))
    def unparsed_keys_count(self, obj):
        return len(obj.unparsed_payload or {})


@admin.register(ModificationOption)
class ModificationOptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "modification",
        "option_definition",
        "category_name",
        "value_bool",
        "source_column",
        "created_at",
    )
    list_filter = (
        "value_bool",
        "option_definition__category",
    )
    search_fields = (
        "modification__name",
        "modification__source_id",
        "modification__configuration__generation__model__name",
        "modification__configuration__generation__model__mark__name",
        "option_definition__name",
        "option_definition__code",
        "option_definition__category__name",
        "source_column",
        "raw_value",
    )
    autocomplete_fields = ("modification", "option_definition")
    list_per_page = 100
    readonly_fields = ("created_at", "updated_at", "display_value")

    fieldsets = (
        (_("Связи"), {
            "fields": (
                "modification",
                "option_definition",
            )
        }),
        (_("Значение"), {
            "fields": (
                "value_bool",
                "display_value",
                "raw_value",
                "source_column",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("категория"))
    def category_name(self, obj):
        if obj.option_definition and obj.option_definition.category:
            return obj.option_definition.category.name
        return "-"

    @admin.display(description=_("значение"))
    def display_value(self, obj):
        parts: list[str] = []
        if obj.value_bool is not None:
            parts.append(str(_("Да")) if obj.value_bool else str(_("Нет")))
        if obj.raw_value:
            parts.append(f"raw: {obj.raw_value}")
        return " | ".join(parts) if parts else "-"


@admin.register(MarkLogo)
class MarkLogoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "mark",
        "source_mark_id",
        "is_active",
        "logo_preview_small",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "mark__name",
        "mark__name_ru",
        "mark__source_id",
        "source_mark_id",
        "source_file_name",
        "alt_text",
    )
    list_filter = ("is_active",)
    autocomplete_fields = ("mark",)
    readonly_fields = ("logo_preview", "created_at", "updated_at")
    list_per_page = 50

    fieldsets = (
        (_("Связь"), {
            "fields": ("mark",)
        }),
        (_("Изображение"), {
            "fields": (
                "image",
                "logo_preview",
                ("source_file_name", "source_mark_id"),
                "alt_text",
                "is_active",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("предпросмотр"))
    def logo_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 240px; object-fit: contain; border: 1px solid #ddd; padding: 4px; background: white;" />',
                obj.image.url,
            )
        return "-"

    @admin.display(description=_("лого"))
    def logo_preview_small(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height: 36px; max-width: 80px; object-fit: contain;" />',
                obj.image.url,
            )
        return "-"


@admin.register(ConfigurationPhoto)
class ConfigurationPhotoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "configuration",
        "configuration_source_id",
        "source_configuration_id",
        "is_main",
        "photo_preview_small",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "configuration__name",
        "configuration__source_id",
        "configuration__generation__name",
        "configuration__generation__model__name",
        "configuration__generation__model__mark__name",
        "source_configuration_id",
        "source_file_name",
        "alt_text",
    )
    list_filter = ("is_main", "configuration__generation__model__mark")
    autocomplete_fields = ("configuration",)
    readonly_fields = ("photo_preview", "created_at", "updated_at")
    list_per_page = 50

    fieldsets = (
        (_("Связь"), {
            "fields": ("configuration",)
        }),
        (_("Изображение"), {
            "fields": (
                "image",
                "photo_preview",
                ("source_file_name", "source_configuration_id"),
                "alt_text",
                ("is_main", "sort_order"),
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("source id конфигурации"))
    def configuration_source_id(self, obj):
        return obj.configuration.source_id

    @admin.display(description=_("предпросмотр"))
    def photo_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 180px; max-width: 320px; object-fit: cover; border: 1px solid #ddd; padding: 4px; background: white;" />',
                obj.image.url,
            )
        return "-"

    @admin.display(description=_("фото"))
    def photo_preview_small(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height: 48px; width: 86px; object-fit: cover; border-radius: 6px;" />',
                obj.image.url,
            )
        return "-"


# ============================================================
# admin site branding
# ============================================================

admin.site.site_header = _("SCT Cars Admin")
admin.site.site_title = _("SCT Cars Admin")
admin.site.index_title = _("Управление автомобильным каталогом")