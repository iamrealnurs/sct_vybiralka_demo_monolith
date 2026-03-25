from __future__ import annotations

from django.contrib import admin
from django.db.models import Count, Exists, OuterRef
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    CarServicePackage,
    CarServicePackageImage,
    NomenclatureCategory,
    NomenclatureImageType,
    NomenclatureImportBatch,
    NomenclatureItem,
    NomenclatureItemImage,
    NomenclatureItemPrice,
    PackageCategory,
    PackageItem,
    PackageItemCategory,
    PackageStatus,
)


# ============================================================
# custom list filters
# ============================================================


class HasImagesFilter(admin.SimpleListFilter):
    title = _("есть изображения")
    parameter_name = "has_images"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(images__isnull=False).distinct()
        if value == "no":
            return queryset.filter(images__isnull=True)
        return queryset


class HasPricesFilter(admin.SimpleListFilter):
    title = _("есть цены")
    parameter_name = "has_prices"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(prices__isnull=False).distinct()
        if value == "no":
            return queryset.filter(prices__isnull=True)
        return queryset


class HasImportBatchFilter(admin.SimpleListFilter):
    title = _("есть импорт")
    parameter_name = "has_import_batch"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(last_import_batch__isnull=False)
        if value == "no":
            return queryset.filter(last_import_batch__isnull=True)
        return queryset


class HasPackageImageFilter(admin.SimpleListFilter):
    title = _("есть изображение пакета")
    parameter_name = "has_package_image"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(image_object__isnull=False)
        if value == "no":
            return queryset.filter(image_object__isnull=True)
        return queryset


class HasPackageItemsFilter(admin.SimpleListFilter):
    title = _("есть элементы пакета")
    parameter_name = "has_package_items"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(items__isnull=False).distinct()
        if value == "no":
            return queryset.filter(items__isnull=True)
        return queryset


class IsDeletedFilter(admin.SimpleListFilter):
    title = _("удалено")
    parameter_name = "is_deleted_flag"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Да")),
            ("no", _("Нет")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(is_deleted=True)
        if value == "no":
            return queryset.filter(is_deleted=False)
        return queryset


# ============================================================
# inlines
# ============================================================


class NomenclatureItemPriceInline(admin.TabularInline):
    model = NomenclatureItemPrice
    extra = 0
    fields = (
        "price_kzt",
        "is_active",
        "is_imported",
        "source_type",
        "source_name",
        "starts_at",
        "ends_at",
        "import_batch",
    )
    autocomplete_fields = ("import_batch",)
    ordering = ("-created_at", "-id")
    classes = ("collapse",)
    show_change_link = True


class NomenclatureItemImageInline(admin.StackedInline):
    model = NomenclatureItemImage
    extra = 0
    fields = (
        "image",
        "image_preview",
        ("image_type", "is_active"),
        ("is_main", "sort_order"),
        "alt_text",
        ("created_at", "updated_at"),
    )
    readonly_fields = ("image_preview", "created_at", "updated_at")
    ordering = ("sort_order", "id")
    classes = ("collapse",)
    show_change_link = True

    @admin.display(description=_("предпросмотр"))
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 220px; object-fit: cover; border: 1px solid #ddd; padding: 4px; background: white;" />',
                obj.image.url,
            )
        return "-"


class CarServicePackageImageInline(admin.StackedInline):
    model = CarServicePackageImage
    extra = 0
    can_delete = True
    max_num = 1
    fields = (
        "image",
        "image_preview",
        "alt_text",
        "is_active",
        ("created_at", "updated_at"),
    )
    readonly_fields = ("image_preview", "created_at", "updated_at")
    classes = ("collapse",)
    show_change_link = True

    @admin.display(description=_("предпросмотр"))
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 140px; max-width: 260px; object-fit: cover; border: 1px solid #ddd; padding: 4px; background: white;" />',
                obj.image.url,
            )
        return "-"


class PackageItemCategoryInline(admin.TabularInline):
    model = PackageItemCategory
    extra = 0
    fields = (
        "name",
        "sort_order",
        "is_active",
        "is_deleted",
    )
    ordering = ("sort_order", "id")
    classes = ("collapse",)
    show_change_link = True


class PackageItemInline(admin.TabularInline):
    model = PackageItem
    extra = 0
    fields = (
        "package_category",
        "nomenclature_item",
        "quantity",
        "discount_percent",
        "base_price_snapshot",
        "sort_order",
        "is_active",
        "is_deleted",
    )
    autocomplete_fields = ("package_category", "nomenclature_item")
    ordering = ("sort_order", "id")
    classes = ("collapse",)
    show_change_link = True


# ============================================================
# admin actions
# ============================================================


@admin.action(description=_("Активировать выбранные категории номенклатуры"))
def activate_nomenclature_categories(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные категории номенклатуры"))
def deactivate_nomenclature_categories(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Активировать выбранные элементы номенклатуры"))
def activate_nomenclature_items(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные элементы номенклатуры"))
def deactivate_nomenclature_items(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Пометить выбранные элементы номенклатуры как удалённые"))
def soft_delete_nomenclature_items(modeladmin, request, queryset):
    queryset.update(is_deleted=True)


@admin.action(description=_("Снять пометку удаления у выбранных элементов номенклатуры"))
def restore_nomenclature_items(modeladmin, request, queryset):
    queryset.update(is_deleted=False)


@admin.action(description=_("Активировать выбранные цены"))
def activate_prices(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные цены"))
def deactivate_prices(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Активировать выбранные изображения номенклатуры"))
def activate_nomenclature_images(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные изображения номенклатуры"))
def deactivate_nomenclature_images(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Активировать выбранные категории пакетов"))
def activate_package_categories(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные категории пакетов"))
def deactivate_package_categories(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Активировать выбранные пакеты"))
def activate_packages(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные пакеты"))
def deactivate_packages(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Пометить выбранные пакеты как удалённые"))
def soft_delete_packages(modeladmin, request, queryset):
    queryset.update(is_deleted=True)


@admin.action(description=_("Снять пометку удаления у выбранных пакетов"))
def restore_packages(modeladmin, request, queryset):
    queryset.update(is_deleted=False)


@admin.action(description=_("Опубликовать выбранные пакеты"))
def publish_packages(modeladmin, request, queryset):
    queryset.update(status=PackageStatus.PUBLISHED)


@admin.action(description=_("Снять с публикации выбранные пакеты"))
def unpublish_packages(modeladmin, request, queryset):
    queryset.update(status=PackageStatus.UNPUBLISHED)


@admin.action(description=_("Перевести выбранные пакеты в архив"))
def archive_packages(modeladmin, request, queryset):
    queryset.update(status=PackageStatus.ARCHIVED)


@admin.action(description=_("Перевести выбранные пакеты в черновик"))
def draft_packages(modeladmin, request, queryset):
    queryset.update(status=PackageStatus.DRAFT)


@admin.action(description=_("Активировать выбранные изображения пакетов"))
def activate_package_images(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные изображения пакетов"))
def deactivate_package_images(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Активировать выбранные локальные категории пакета"))
def activate_package_item_categories(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные локальные категории пакета"))
def deactivate_package_item_categories(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Пометить выбранные локальные категории пакета как удалённые"))
def soft_delete_package_item_categories(modeladmin, request, queryset):
    queryset.update(is_deleted=True)


@admin.action(description=_("Снять пометку удаления у выбранных локальных категорий пакета"))
def restore_package_item_categories(modeladmin, request, queryset):
    queryset.update(is_deleted=False)


@admin.action(description=_("Активировать выбранные элементы пакета"))
def activate_package_items(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные элементы пакета"))
def deactivate_package_items(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description=_("Пометить выбранные элементы пакета как удалённые"))
def soft_delete_package_items(modeladmin, request, queryset):
    queryset.update(is_deleted=True)


@admin.action(description=_("Снять пометку удаления у выбранных элементов пакета"))
def restore_package_items(modeladmin, request, queryset):
    queryset.update(is_deleted=False)


# ============================================================
# model admins
# ============================================================


@admin.register(NomenclatureImportBatch)
class NomenclatureImportBatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source_type",
        "source_name",
        "items_total",
        "created_count",
        "updated_count",
        "skipped_count",
        "failed_count",
        "items_count",
        "price_rows_count",
        "created_at",
    )
    list_filter = ("source_type",)
    search_fields = (
        "source_name",
        "source_path",
        "file_checksum",
        "raw_payload",
        "comment",
    )
    ordering = ("-created_at", "-id")
    list_per_page = 50
    readonly_fields = (
        "created_at",
        "updated_at",
        "items_count",
        "price_rows_count",
    )

    fieldsets = (
        (_("Источник"), {
            "fields": (
                ("source_type", "source_name"),
                "source_path",
                "file_checksum",
            )
        }),
        (_("Статистика"), {
            "fields": (
                ("items_total", "created_count", "updated_count"),
                ("skipped_count", "failed_count"),
                ("items_count", "price_rows_count"),
            )
        }),
        (_("Дополнительно"), {
            "fields": (
                "comment",
                "raw_payload",
            ),
            "classes": ("collapse",),
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _items_count=Count("items", distinct=True),
            _price_rows_count=Count("price_rows", distinct=True),
        )

    @admin.display(ordering="_items_count", description=_("элементов"))
    def items_count(self, obj):
        return obj._items_count

    @admin.display(ordering="_price_rows_count", description=_("цен"))
    def price_rows_count(self, obj):
        return obj._price_rows_count


@admin.register(NomenclatureCategory)
class NomenclatureCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "code",
        "is_active",
        "items_count",
        "created_at",
        "updated_at",
    )
    list_editable = ("is_active",)
    search_fields = ("name", "code", "description")
    list_filter = ("is_active",)
    ordering = ("name", "code")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    actions = (activate_nomenclature_categories, deactivate_nomenclature_categories)

    fieldsets = (
        (None, {
            "fields": (
                ("name", "code"),
                "description",
                "is_active",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_items_count=Count("items", distinct=True))

    @admin.display(ordering="_items_count", description=_("элементов"))
    def items_count(self, obj):
        return obj._items_count


@admin.register(PackageCategory)
class PackageCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "code",
        "slug",
        "sort_order",
        "is_active",
        "packages_count",
        "created_at",
    )
    list_editable = ("sort_order", "is_active")
    search_fields = ("name", "code", "slug", "short_description", "description")
    list_filter = ("is_active",)
    ordering = ("sort_order", "name", "code")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")
    actions = (activate_package_categories, deactivate_package_categories)

    fieldsets = (
        (_("Основное"), {
            "fields": (
                ("name", "code"),
                "slug",
                ("sort_order", "is_active"),
            )
        }),
        (_("Описание"), {
            "fields": (
                "short_description",
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
        return qs.annotate(_packages_count=Count("packages", distinct=True))

    @admin.display(ordering="_packages_count", description=_("пакетов"))
    def packages_count(self, obj):
        return obj._packages_count


@admin.register(NomenclatureItem)
class NomenclatureItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "article",
        "name",
        "item_type",
        "category",
        "current_price_display",
        "is_active",
        "is_deleted",
        "has_image_badge",
        "prices_count",
        "package_items_count",
    )
    list_filter = (
        "item_type",
        "category",
        "source_type",
        "is_active",
        IsDeletedFilter,
        HasImagesFilter,
        HasPricesFilter,
        HasImportBatchFilter,
    )
    search_fields = (
        "article",
        "name",
        "slug",
        "tnved",
        "barcode",
        "description",
        "description_short",
        "description_public",
        "source_name",
        "raw_payload",
        "category__name",
        "category__code",
        "category_level_1_code",
        "category_level_1_name",
        "category_level_2_code",
        "category_level_2_name",
        "category_level_3_code",
        "category_level_3_name",
    )
    autocomplete_fields = ("category", "last_import_batch")
    ordering = ("name", "article")
    list_per_page = 50
    readonly_fields = (
        "created_at",
        "updated_at",
        "slug",
        "current_price_display",
        "main_image_preview",
    )
    actions = (
        activate_nomenclature_items,
        deactivate_nomenclature_items,
        soft_delete_nomenclature_items,
        restore_nomenclature_items,
    )
    inlines = (NomenclatureItemPriceInline, NomenclatureItemImageInline)

    fieldsets = (
        (_("Идентификаторы"), {
            "fields": (
                ("article", "slug"),
                ("item_type", "category"),
            )
        }),
        (_("Основное"), {
            "fields": (
                "name",
                "unit",
                ("tnved", "barcode"),
                "current_price_display",
                "main_image_preview",
                ("is_active", "is_deleted"),
            )
        }),
        (_("Описание"), {
            "fields": (
                "description_short",
                "description",
                "description_public",
            ),
            "classes": ("collapse",),
        }),
        (_("Данные источника"), {
            "fields": (
                ("source_type", "source_name"),
                "last_import_batch",
                "raw_payload",
            ),
            "classes": ("collapse",),
        }),
        (_("Категории из источника"), {
            "fields": (
                ("category_level_1_code", "category_level_1_name"),
                ("category_level_2_code", "category_level_2_name"),
                ("category_level_3_code", "category_level_3_name"),
            ),
            "classes": ("collapse",),
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("category", "last_import_batch")
        return qs.annotate(
            _prices_count=Count("prices", distinct=True),
            _package_items_count=Count("package_items", distinct=True),
            _has_image=Exists(
                NomenclatureItemImage.objects.filter(nomenclature_item_id=OuterRef("pk"))
            ),
        )

    @admin.display(description=_("текущая цена"))
    def current_price_display(self, obj):
        return obj.current_price_kzt

    @admin.display(boolean=True, description=_("изображение"))
    def has_image_badge(self, obj):
        return bool(getattr(obj, "_has_image", False))

    @admin.display(ordering="_prices_count", description=_("цен"))
    def prices_count(self, obj):
        return obj._prices_count

    @admin.display(ordering="_package_items_count", description=_("в пакетах"))
    def package_items_count(self, obj):
        return obj._package_items_count

    @admin.display(description=_("главное изображение"))
    def main_image_preview(self, obj):
        image = obj.main_image
        if image and image.image:
            return format_html(
                '<img src="{}" style="max-height: 140px; max-width: 240px; object-fit: cover; border: 1px solid #ddd; padding: 4px; background: white;" />',
                image.image.url,
            )
        return "-"


@admin.register(NomenclatureItemPrice)
class NomenclatureItemPriceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nomenclature_item",
        "price_kzt",
        "is_active",
        "is_imported",
        "source_type",
        "source_name",
        "starts_at",
        "ends_at",
        "import_batch",
        "created_at",
    )
    list_filter = (
        "is_active",
        "is_imported",
        "source_type",
        "import_batch",
    )
    search_fields = (
        "nomenclature_item__article",
        "nomenclature_item__name",
        "source_name",
        "comment",
        "raw_payload",
    )
    autocomplete_fields = ("nomenclature_item", "import_batch")
    ordering = ("-created_at", "-id")
    list_per_page = 100
    readonly_fields = ("created_at", "updated_at")
    actions = (activate_prices, deactivate_prices)

    fieldsets = (
        (_("Связи"), {
            "fields": (
                "nomenclature_item",
                "import_batch",
            )
        }),
        (_("Цена"), {
            "fields": (
                "price_kzt",
                ("is_active", "is_imported"),
                ("starts_at", "ends_at"),
            )
        }),
        (_("Источник"), {
            "fields": (
                ("source_type", "source_name"),
                "comment",
                "raw_payload",
            ),
            "classes": ("collapse",),
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(NomenclatureItemImage)
class NomenclatureItemImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nomenclature_item",
        "image_type",
        "is_main",
        "is_active",
        "sort_order",
        "image_preview_small",
        "created_at",
        "updated_at",
    )
    list_editable = ("sort_order",)
    list_filter = ("image_type", "is_main", "is_active")
    search_fields = (
        "nomenclature_item__article",
        "nomenclature_item__name",
        "alt_text",
    )
    autocomplete_fields = ("nomenclature_item",)
    ordering = ("nomenclature_item__article", "sort_order", "id")
    list_per_page = 50
    readonly_fields = ("image_preview", "created_at", "updated_at")
    actions = (activate_nomenclature_images, deactivate_nomenclature_images)

    fieldsets = (
        (_("Связь"), {
            "fields": ("nomenclature_item",)
        }),
        (_("Изображение"), {
            "fields": (
                "image",
                "image_preview",
                ("image_type", "is_active"),
                ("is_main", "sort_order"),
                "alt_text",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("предпросмотр"))
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 180px; max-width: 320px; object-fit: cover; border: 1px solid #ddd; padding: 4px; background: white;" />',
                obj.image.url,
            )
        return "-"

    @admin.display(description=_("фото"))
    def image_preview_small(self, obj):
        if obj and obj.image:
            fit = "contain" if obj.image_type == NomenclatureImageType.ICON else "cover"
            return format_html(
                '<img src="{}" style="height: 48px; width: 86px; object-fit: {}; border-radius: 6px;" />',
                obj.image.url,
                fit,
            )
        return "-"


@admin.register(CarServicePackage)
class CarServicePackageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "public_title",
        "name",
        "category",
        "modification",
        "status",
        "is_promo",
        "package_discount_percent",
        "regular_price_display",
        "final_price_display",
        "is_active",
        "is_deleted",
        "has_image_badge",
        "items_count",
        "item_categories_count",
    )
    list_filter = (
        "status",
        "is_promo",
        "is_active",
        IsDeletedFilter,
        HasPackageImageFilter,
        HasPackageItemsFilter,
        "category",
        "modification__configuration__generation__model__mark",
    )
    search_fields = (
        "name",
        "public_title",
        "slug",
        "description",
        "description_short",
        "description_public",
        "promo_badge",
        "promo_text",
        "modification__name",
        "modification__source_id",
        "modification__group_name",
        "modification__configuration__name",
        "modification__configuration__generation__name",
        "modification__configuration__generation__model__name",
        "modification__configuration__generation__model__mark__name",
        "category__name",
        "category__code",
    )
    autocomplete_fields = ("modification", "category")
    ordering = ("-created_at", "-id")
    list_per_page = 50
    readonly_fields = (
        "created_at",
        "updated_at",
        "slug",
        "modification_source_id_display",
        "regular_price_display",
        "final_price_display",
        "package_discount_amount_display",
        "image_preview",
    )
    actions = (
        activate_packages,
        deactivate_packages,
        soft_delete_packages,
        restore_packages,
        publish_packages,
        unpublish_packages,
        archive_packages,
        draft_packages,
    )
    inlines = (
        CarServicePackageImageInline,
        PackageItemCategoryInline,
        PackageItemInline,
    )

    fieldsets = (
        (_("Связи"), {
            "fields": (
                "modification",
                "category",
                "modification_source_id_display",
            )
        }),
        (_("Основное"), {
            "fields": (
                ("name", "public_title"),
                "slug",
                "status",
                ("is_active", "is_deleted"),
            )
        }),
        (_("Описание"), {
            "fields": (
                "description_short",
                "description",
                "description_public",
            ),
            "classes": ("collapse",),
        }),
        (_("Промо"), {
            "fields": (
                "is_promo",
                "promo_badge",
                "promo_text",
                ("promo_start_at", "promo_end_at"),
                "package_discount_percent",
            )
        }),
        (_("Расчёт цены"), {
            "fields": (
                "regular_price_display",
                "package_discount_amount_display",
                "final_price_display",
                "image_preview",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            "category",
            "modification",
            "modification__configuration",
            "modification__configuration__generation",
            "modification__configuration__generation__model",
            "modification__configuration__generation__model__mark",
        )
        return qs.annotate(
            _items_count=Count("items", distinct=True),
            _item_categories_count=Count("item_categories", distinct=True),
            _has_image=Exists(
                CarServicePackageImage.objects.filter(package_id=OuterRef("pk"))
            ),
        )

    @admin.display(description=_("source id модификации"))
    def modification_source_id_display(self, obj):
        return obj.modification_source_id

    @admin.display(description=_("обычная цена"))
    def regular_price_display(self, obj):
        return obj.regular_price

    @admin.display(description=_("скидка пакета"))
    def package_discount_amount_display(self, obj):
        return obj.package_discount_amount

    @admin.display(description=_("итоговая цена"))
    def final_price_display(self, obj):
        return obj.final_price

    @admin.display(boolean=True, description=_("изображение"))
    def has_image_badge(self, obj):
        return bool(getattr(obj, "_has_image", False))

    @admin.display(ordering="_items_count", description=_("элементов"))
    def items_count(self, obj):
        return obj._items_count

    @admin.display(ordering="_item_categories_count", description=_("категорий"))
    def item_categories_count(self, obj):
        return obj._item_categories_count

    @admin.display(description=_("главное изображение"))
    def image_preview(self, obj):
        image = obj.current_main_image
        if image and image.image:
            return format_html(
                '<img src="{}" style="max-height: 160px; max-width: 300px; object-fit: cover; border: 1px solid #ddd; padding: 4px; background: white;" />',
                image.image.url,
            )
        return "-"


@admin.register(CarServicePackageImage)
class CarServicePackageImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "package",
        "package_status",
        "is_active",
        "image_preview_small",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "package__status", "package__category")
    search_fields = (
        "package__name",
        "package__public_title",
        "package__slug",
        "package__modification__name",
        "package__modification__source_id",
        "alt_text",
    )
    autocomplete_fields = ("package",)
    ordering = ("-created_at", "-id")
    list_per_page = 50
    readonly_fields = ("image_preview", "created_at", "updated_at")
    actions = (activate_package_images, deactivate_package_images)

    fieldsets = (
        (_("Связь"), {
            "fields": ("package",)
        }),
        (_("Изображение"), {
            "fields": (
                "image",
                "image_preview",
                "alt_text",
                "is_active",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("статус пакета"))
    def package_status(self, obj):
        return obj.package.get_status_display()

    @admin.display(description=_("предпросмотр"))
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 180px; max-width: 320px; object-fit: cover; border: 1px solid #ddd; padding: 4px; background: white;" />',
                obj.image.url,
            )
        return "-"

    @admin.display(description=_("фото"))
    def image_preview_small(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height: 48px; width: 86px; object-fit: cover; border-radius: 6px;" />',
                obj.image.url,
            )
        return "-"


@admin.register(PackageItemCategory)
class PackageItemCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "package",
        "sort_order",
        "is_active",
        "is_deleted",
        "items_count",
        "created_at",
    )
    list_editable = ("sort_order", "is_active")
    list_filter = (
        "is_active",
        IsDeletedFilter,
        "package__status",
        "package__category",
    )
    search_fields = (
        "name",
        "description",
        "package__name",
        "package__public_title",
        "package__slug",
        "package__modification__name",
        "package__modification__source_id",
    )
    autocomplete_fields = ("package",)
    ordering = ("package__public_title", "sort_order", "id")
    list_per_page = 100
    readonly_fields = ("created_at", "updated_at")
    actions = (
        activate_package_item_categories,
        deactivate_package_item_categories,
        soft_delete_package_item_categories,
        restore_package_item_categories,
    )

    fieldsets = (
        (_("Связь"), {
            "fields": ("package",)
        }),
        (_("Основное"), {
            "fields": (
                "name",
                "description",
                ("sort_order", "is_active", "is_deleted"),
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("package")
        return qs.annotate(_items_count=Count("items", distinct=True))

    @admin.display(ordering="_items_count", description=_("элементов"))
    def items_count(self, obj):
        return obj._items_count


@admin.register(PackageItem)
class PackageItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "package",
        "package_category",
        "nomenclature_item",
        "item_type_display",
        "quantity",
        "discount_percent",
        "current_unit_price_display",
        "base_line_total_display",
        "final_line_total_display",
        "is_active",
        "is_deleted",
        "created_at",
    )
    list_filter = (
        "is_active",
        IsDeletedFilter,
        "package__status",
        "package__category",
        "package_category",
        "nomenclature_item__item_type",
        "nomenclature_item__category",
    )
    search_fields = (
        "package__name",
        "package__public_title",
        "package__slug",
        "package_category__name",
        "nomenclature_item__article",
        "nomenclature_item__name",
        "article_snapshot",
        "name_snapshot",
        "unit_snapshot",
    )
    autocomplete_fields = ("package", "package_category", "nomenclature_item")
    ordering = ("package__public_title", "sort_order", "id")
    list_per_page = 100
    readonly_fields = (
        "created_at",
        "updated_at",
        "item_type_display",
        "current_unit_price_display",
        "snapshot_unit_price_display",
        "base_line_total_display",
        "line_discount_amount_display",
        "final_line_total_display",
    )
    actions = (
        activate_package_items,
        deactivate_package_items,
        soft_delete_package_items,
        restore_package_items,
    )

    fieldsets = (
        (_("Связи"), {
            "fields": (
                "package",
                "package_category",
                "nomenclature_item",
            )
        }),
        (_("Основное"), {
            "fields": (
                ("quantity", "sort_order"),
                "discount_percent",
                ("is_active", "is_deleted"),
            )
        }),
        (_("Снимок данных"), {
            "fields": (
                ("item_type_snapshot", "article_snapshot"),
                "name_snapshot",
                ("unit_snapshot", "base_price_snapshot"),
            ),
            "classes": ("collapse",),
        }),
        (_("Расчёты"), {
            "fields": (
                "item_type_display",
                "current_unit_price_display",
                "snapshot_unit_price_display",
                "base_line_total_display",
                "line_discount_amount_display",
                "final_line_total_display",
            )
        }),
        (_("Служебная информация"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("тип элемента"))
    def item_type_display(self, obj):
        value = obj.item_type
        if value:
            try:
                return obj.get_item_type_snapshot_display() if not obj.nomenclature_item_id else obj.nomenclature_item.get_item_type_display()
            except Exception:
                return value
        return "-"

    @admin.display(description=_("текущая цена за единицу"))
    def current_unit_price_display(self, obj):
        return obj.current_unit_price

    @admin.display(description=_("цена snapshot"))
    def snapshot_unit_price_display(self, obj):
        return obj.snapshot_unit_price

    @admin.display(description=_("сумма до скидки"))
    def base_line_total_display(self, obj):
        return obj.base_line_total

    @admin.display(description=_("скидка"))
    def line_discount_amount_display(self, obj):
        return obj.line_discount_amount

    @admin.display(description=_("итог по строке"))
    def final_line_total_display(self, obj):
        return obj.final_line_total
