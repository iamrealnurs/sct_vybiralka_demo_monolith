from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from cars.models import Modification
from main.models import TimestampedModel


# ============================================================
# helpers
# ============================================================

MONEY_MAX_DIGITS = 12
MONEY_DECIMAL_PLACES = 2
PERCENT_MAX_DIGITS = 5
PERCENT_DECIMAL_PLACES = 2
ZERO = Decimal("0.00")
HUNDRED = Decimal("100.00")


def quantize_money(value: Decimal | int | float | str | None) -> Decimal:
    """
    Приводит значение к Decimal с двумя знаками после запятой.
    """
    if value is None:
        return ZERO
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def apply_percent_discount(amount: Decimal, percent: Decimal | int | float | str | None) -> Decimal:
    """
    Возвращает сумму после скидки в процентах.
    """
    amount = quantize_money(amount)
    percent_value = Decimal(str(percent or "0"))
    if percent_value <= 0:
        return amount
    discounted = amount * (HUNDRED - percent_value) / HUNDRED
    return quantize_money(discounted)


def calculate_discount_amount(amount: Decimal, percent: Decimal | int | float | str | None) -> Decimal:
    """
    Возвращает абсолютную величину скидки.
    """
    amount = quantize_money(amount)
    discounted = apply_percent_discount(amount, percent)
    return quantize_money(amount - discounted)


def generate_unique_slug(
    *,
    model_class: type[models.Model],
    value: str,
    field_name: str = "slug",
    instance_pk: int | None = None,
) -> str:
    """
    Генерирует уникальный slug для модели.
    """
    base_slug = slugify(value or "", allow_unicode=True).strip("-")
    if not base_slug:
        base_slug = "item"

    slug_candidate = base_slug
    suffix = 2

    while True:
        queryset = model_class.objects.filter(**{field_name: slug_candidate})
        if instance_pk is not None:
            queryset = queryset.exclude(pk=instance_pk)
        if not queryset.exists():
            return slug_candidate
        slug_candidate = f"{base_slug}-{suffix}"
        suffix += 1


# ============================================================
# choices
# ============================================================


class NomenclatureItemType(models.TextChoices):
    PRODUCT = "PRODUCT", _("Товар")
    SERVICE = "SERVICE", _("Услуга")


class ImportSourceType(models.TextChoices):
    FILE = "FILE", _("Файл")
    ADMIN = "ADMIN", _("Вручную через админку")
    API = "API", _("API")
    OTHER = "OTHER", _("Другое")


class PackageStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Черновик")
    PUBLISHED = "PUBLISHED", _("Опубликован")
    UNPUBLISHED = "UNPUBLISHED", _("Снят с публикации")
    ARCHIVED = "ARCHIVED", _("Архив")


class NomenclatureImageType(models.TextChoices):
    IMAGE = "IMAGE", _("Изображение")
    ICON = "ICON", _("Иконка")


# ============================================================
# abstract models
# ============================================================


class ActivatableModel(models.Model):
    is_active = models.BooleanField(_("активно"), default=True, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(_("удалено"), default=False, db_index=True)
    deleted_at = models.DateTimeField(_("удалено в"), null=True, blank=True)

    class Meta:
        abstract = True


# ============================================================
# import history
# ============================================================


class NomenclatureImportBatch(TimestampedModel):
    """
    История импортов номенклатуры.
    Нужна для аудита и последующего анализа повторных синхронизаций.
    """

    source_type = models.CharField(
        _("тип источника"),
        max_length=20,
        choices=ImportSourceType.choices,
        default=ImportSourceType.FILE,
        db_index=True,
    )

    source_name = models.CharField(
        _("имя источника"),
        max_length=255,
        blank=True,
        db_index=True,
        help_text=_("Например: spisok_tovarov.json"),
    )

    source_path = models.CharField(
        _("путь источника"),
        max_length=500,
        blank=True,
        help_text=_("Опционально: путь к файлу, URL или иное описание источника."),
    )

    file_checksum = models.CharField(
        _("контрольная сумма файла"),
        max_length=128,
        blank=True,
        db_index=True,
    )

    raw_payload = models.TextField(
        _("raw payload"),
        blank=True,
        help_text=_("Сырой текст импорта, метаданные или сводка."),
    )

    items_total = models.PositiveIntegerField(_("всего записей"), default=0)
    created_count = models.PositiveIntegerField(_("создано"), default=0)
    updated_count = models.PositiveIntegerField(_("обновлено"), default=0)
    skipped_count = models.PositiveIntegerField(_("пропущено"), default=0)
    failed_count = models.PositiveIntegerField(_("ошибок"), default=0)

    comment = models.TextField(_("комментарий"), blank=True)

    class Meta:
        verbose_name = _("пакет импорта номенклатуры")
        verbose_name_plural = _("пакеты импорта номенклатуры")
        ordering = ("-created_at", "id")
        indexes = [
            models.Index(fields=["source_type", "created_at"], name="srv_import_src_created_idx"),
            models.Index(fields=["source_name"], name="srv_import_source_name_idx"),
        ]

    def __str__(self) -> str:
        source = self.source_name or self.get_source_type_display()
        return f"Импорт #{self.pk or 'new'} — {source}"


# ============================================================
# dictionaries
# ============================================================


class NomenclatureCategory(TimestampedModel, ActivatableModel):
    """
    Простая плоская категория номенклатуры.
    Без дерева и parent-связей.
    Примеры:
      - Масло
      - Фильтры
      - Услуги
      - Антифриз
      - Тормозная жидкость
    """

    code = models.CharField(_("код"), max_length=64, unique=True, db_index=True)
    name = models.CharField(_("название"), max_length=255, unique=True, db_index=True)
    description = models.TextField(_("описание"), blank=True)

    class Meta:
        verbose_name = _("категория номенклатуры")
        verbose_name_plural = _("категории номенклатуры")
        ordering = ("name", "code")
        indexes = [
            models.Index(fields=["is_active", "name"], name="srv_nomcat_active_name_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class PackageCategory(TimestampedModel, ActivatableModel):
    """
    Справочник категорий пакетов.
    Именно по ним пакет показывается в определённом клиентском блоке услуг.
    """

    code = models.CharField(_("код"), max_length=64, unique=True, db_index=True)
    name = models.CharField(_("название"), max_length=255, unique=True, db_index=True)

    slug = models.SlugField(
        _("slug"),
        max_length=255,
        unique=True,
        allow_unicode=True,
        db_index=True,
        blank=True,
    )

    short_description = models.CharField(_("краткое описание"), max_length=500, blank=True)
    description = models.TextField(_("описание"), blank=True)

    sort_order = models.PositiveIntegerField(_("порядок сортировки"), default=0)

    class Meta:
        verbose_name = _("категория пакета")
        verbose_name_plural = _("категории пакетов")
        ordering = ("sort_order", "name", "code")
        indexes = [
            models.Index(fields=["is_active", "sort_order"], name="srv_pkgcat_active_sort_idx"),
            models.Index(fields=["name"], name="srv_pkgcat_name_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                model_class=type(self),
                value=self.name,
                field_name="slug",
                instance_pk=self.pk,
            )
        super().save(*args, **kwargs)


# ============================================================
# nomenclature
# ============================================================


class NomenclatureItem(TimestampedModel, ActivatableModel, SoftDeleteModel):
    """
    Общая номенклатура:
      - товар
      - услуга

    Бизнес-ключ:
      article
    """

    article = models.CharField(_("артикул"), max_length=128, unique=True, db_index=True)

    item_type = models.CharField(
        _("тип номенклатуры"),
        max_length=20,
        choices=NomenclatureItemType.choices,
        db_index=True,
    )

    category = models.ForeignKey(
        NomenclatureCategory,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("категория"),
    )

    name = models.CharField(_("название"), max_length=500, db_index=True)
    slug = models.SlugField(
        _("slug"),
        max_length=255,
        unique=True,
        allow_unicode=True,
        db_index=True,
        blank=True,
    )

    unit = models.CharField(_("единица измерения"), max_length=50, default="шт", blank=True)
    tnved = models.CharField(_("ТНВЭД"), max_length=64, blank=True, db_index=True)
    barcode = models.CharField(_("штрихкод"), max_length=128, blank=True, db_index=True)

    description = models.TextField(_("описание"), blank=True)
    description_short = models.CharField(_("краткое описание"), max_length=500, blank=True)
    description_public = models.TextField(_("публичное описание"), blank=True)

    # raw-поля из исходного файла — сохраняем как есть
    category_level_1_code = models.CharField(_("код категории 1"), max_length=64, blank=True)
    category_level_1_name = models.CharField(_("категория 1"), max_length=255, blank=True)
    category_level_2_code = models.CharField(_("код категории 2"), max_length=64, blank=True)
    category_level_2_name = models.CharField(_("категория 2"), max_length=255, blank=True)
    category_level_3_code = models.CharField(_("код категории 3"), max_length=64, blank=True)
    category_level_3_name = models.CharField(_("категория 3"), max_length=255, blank=True)

    source_type = models.CharField(
        _("тип источника"),
        max_length=20,
        choices=ImportSourceType.choices,
        default=ImportSourceType.FILE,
        db_index=True,
    )
    source_name = models.CharField(_("имя источника"), max_length=255, blank=True, db_index=True)

    raw_payload = models.TextField(
        _("raw payload"),
        blank=True,
        help_text=_("Сырой текст JSON-объекта или любой иной исходной записи."),
    )

    last_import_batch = models.ForeignKey(
        NomenclatureImportBatch,
        on_delete=models.SET_NULL,
        related_name="items",
        verbose_name=_("последний импорт"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("элемент номенклатуры")
        verbose_name_plural = _("элементы номенклатуры")
        ordering = ("name", "article")
        indexes = [
            models.Index(fields=["item_type"], name="srv_nomitem_type_idx"),
            models.Index(fields=["category"], name="srv_nomitem_category_idx"),
            models.Index(fields=["is_active", "item_type"], name="srv_nomitem_active_type_idx"),
            models.Index(fields=["is_deleted"], name="srv_nomitem_deleted_idx"),
            models.Index(fields=["name"], name="srv_nomitem_name_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.article} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                model_class=type(self),
                value=f"{self.article}-{self.name}",
                field_name="slug",
                instance_pk=self.pk,
            )
        super().save(*args, **kwargs)

    @property
    def latest_active_price_record(self) -> "NomenclatureItemPrice | None":
        """
        Актуальная цена = последняя активная запись цены.
        """
        return (
            self.prices.filter(is_active=True)
            .order_by("-created_at", "-id")
            .first()
        )

    @property
    def current_price_kzt(self) -> Decimal:
        price_record = self.latest_active_price_record
        if not price_record:
            return ZERO
        return price_record.price_kzt

    @property
    def main_image(self) -> "NomenclatureItemImage | None":
        return (
            self.images.filter(is_active=True, is_main=True)
            .order_by("sort_order", "id")
            .first()
        )

    @property
    def image_url(self) -> str:
        image = self.main_image
        if image and image.image:
            return image.image.url
        return ""


class NomenclatureItemPrice(TimestampedModel, ActivatableModel):
    """
    История цен номенклатуры.

    Актуальная цена выбирается как:
      последняя активная запись.
    """

    nomenclature_item = models.ForeignKey(
        NomenclatureItem,
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name=_("элемент номенклатуры"),
    )

    price_kzt = models.DecimalField(
        _("цена, KZT"),
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=ZERO,
    )

    source_type = models.CharField(
        _("тип источника"),
        max_length=20,
        choices=ImportSourceType.choices,
        default=ImportSourceType.FILE,
        db_index=True,
    )

    source_name = models.CharField(_("имя источника"), max_length=255, blank=True, db_index=True)
    is_imported = models.BooleanField(_("импортировано из внешнего источника"), default=False, db_index=True)

    starts_at = models.DateTimeField(_("действует с"), null=True, blank=True)
    ends_at = models.DateTimeField(_("действует до"), null=True, blank=True)

    comment = models.TextField(_("комментарий"), blank=True)
    raw_payload = models.TextField(_("raw payload"), blank=True)

    import_batch = models.ForeignKey(
        NomenclatureImportBatch,
        on_delete=models.SET_NULL,
        related_name="price_rows",
        verbose_name=_("импорт"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("цена номенклатуры")
        verbose_name_plural = _("цены номенклатуры")
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["nomenclature_item", "is_active"], name="srv_nomprice_item_active_idx"),
            models.Index(fields=["source_type", "created_at"], name="srv_nomprice_src_created_idx"),
            models.Index(fields=["starts_at", "ends_at"], name="srv_nomprice_dates_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.nomenclature_item.article} — {self.price_kzt} KZT"

    def clean(self):
        super().clean()
        if self.price_kzt is None:
            self.price_kzt = ZERO
        if self.price_kzt < ZERO:
            raise ValidationError({"price_kzt": _("Цена не может быть отрицательной.")})
        if self.starts_at and self.ends_at and self.starts_at > self.ends_at:
            raise ValidationError({"ends_at": _("Дата окончания не может быть раньше даты начала.")})


class NomenclatureItemImage(TimestampedModel, ActivatableModel):
    """
    Изображения и иконки номенклатуры.
    Нужны и для товаров, и для услуг.
    """

    nomenclature_item = models.ForeignKey(
        NomenclatureItem,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("элемент номенклатуры"),
    )

    image_type = models.CharField(
        _("тип изображения"),
        max_length=20,
        choices=NomenclatureImageType.choices,
        default=NomenclatureImageType.IMAGE,
        db_index=True,
    )

    image = models.ImageField(_("файл"), upload_to="services/nomenclature/")
    alt_text = models.CharField(_("alt текст"), max_length=255, blank=True)

    is_main = models.BooleanField(_("главное изображение"), default=False, db_index=True)
    sort_order = models.PositiveIntegerField(_("порядок сортировки"), default=0)

    class Meta:
        verbose_name = _("изображение номенклатуры")
        verbose_name_plural = _("изображения номенклатуры")
        ordering = ("sort_order", "id")
        indexes = [
            models.Index(fields=["nomenclature_item", "is_main"], name="srv_nomimg_item_main_idx"),
            models.Index(fields=["image_type", "is_active"], name="srv_nomimg_type_active_idx"),
        ]

    def __str__(self) -> str:
        return f"Изображение: {self.nomenclature_item.article}"

    @property
    def image_url(self) -> str:
        if self.image:
            return self.image.url
        return ""


# ============================================================
# packages
# ============================================================


class CarServicePackage(TimestampedModel, ActivatableModel, SoftDeleteModel):
    """
    Пакет услуг/товаров под конкретную модификацию автомобиля.

    Ключевое правило:
      на одну Modification + одну PackageCategory
      допускается только один НЕ удалённый пакет.
    """

    modification = models.ForeignKey(
        Modification,
        on_delete=models.CASCADE,
        related_name="service_packages",
        verbose_name=_("автомобиль / модификация"),
        db_index=True,
    )

    category = models.ForeignKey(
        PackageCategory,
        on_delete=models.CASCADE,
        related_name="packages",
        verbose_name=_("категория пакета"),
        db_index=True,
    )

    name = models.CharField(
        _("внутреннее название"),
        max_length=255,
        db_index=True,
        help_text=_("Название пакета для сотрудников."),
    )

    public_title = models.CharField(
        _("публичный заголовок"),
        max_length=255,
        db_index=True,
        help_text=_("Заголовок, который видит клиент."),
    )

    slug = models.SlugField(
        _("slug"),
        max_length=255,
        unique=True,
        allow_unicode=True,
        db_index=True,
        blank=True,
    )

    description = models.TextField(
        _("внутреннее полное описание"),
        blank=True,
        help_text=_("Описание для сотрудников / админки."),
    )

    description_short = models.CharField(
        _("краткое описание"),
        max_length=1000,
        blank=True,
        help_text=_("Короткое описание для карточки."),
    )

    description_public = models.TextField(
        _("публичное HTML-описание"),
        blank=True,
        help_text=_("Полное описание, которое видит клиент."),
    )

    status = models.CharField(
        _("статус"),
        max_length=20,
        choices=PackageStatus.choices,
        default=PackageStatus.DRAFT,
        db_index=True,
    )

    # --------------------------------------------------------
    # promo
    # --------------------------------------------------------
    is_promo = models.BooleanField(_("акция"), default=False, db_index=True)

    promo_badge = models.CharField(
        _("бейдж акции"),
        max_length=100,
        blank=True,
        help_text=_("Например: SALE, HIT, АКЦИЯ, -10%."),
    )

    promo_text = models.TextField(
        _("текст акции"),
        blank=True,
        help_text=_("Описание акции для клиента."),
    )

    promo_start_at = models.DateTimeField(_("акция с"), null=True, blank=True)
    promo_end_at = models.DateTimeField(_("акция до"), null=True, blank=True)

    package_discount_percent = models.DecimalField(
        _("общая скидка пакета, %"),
        max_digits=PERCENT_MAX_DIGITS,
        decimal_places=PERCENT_DECIMAL_PLACES,
        default=ZERO,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
        help_text=_("Общая скидка на пакет целиком."),
    )

    class Meta:
        verbose_name = _("пакет услуг")
        verbose_name_plural = _("пакеты услуг")
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=["modification", "category"],
                condition=Q(is_deleted=False),
                name="srv_package_mod_category_not_deleted_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["modification"], name="srv_package_modification_idx"),
            models.Index(fields=["category"], name="srv_package_category_idx"),
            models.Index(fields=["status"], name="srv_package_status_idx"),
            models.Index(fields=["is_promo"], name="srv_package_promo_idx"),
            models.Index(fields=["is_deleted"], name="srv_package_deleted_idx"),
            models.Index(fields=["created_at"], name="srv_package_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.public_title} — {self.modification}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                model_class=type(self),
                value=f"{self.public_title}-{self.modification.source_id}",
                field_name="slug",
                instance_pk=self.pk,
            )
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()

        if self.package_discount_percent is None:
            self.package_discount_percent = ZERO

        if self.package_discount_percent < ZERO or self.package_discount_percent > HUNDRED:
            raise ValidationError(
                {"package_discount_percent": _("Общая скидка пакета должна быть в диапазоне от 0 до 100.")}
            )

        if self.is_promo and not self.promo_text.strip():
            raise ValidationError({"promo_text": _("Если пакет акционный, необходимо указать текст акции.")})

        if self.promo_start_at and self.promo_end_at and self.promo_start_at > self.promo_end_at:
            raise ValidationError({"promo_end_at": _("Дата окончания акции не может быть раньше даты начала.")})

    @property
    def modification_source_id(self) -> str:
        return self.modification.source_id

    @property
    def display_title(self) -> str:
        return self.public_title or self.name

    @property
    def package_item_categories_active(self):
        return self.item_categories.filter(is_deleted=False, is_active=True)

    @property
    def package_items_active(self):
        return self.items.filter(is_deleted=False, is_active=True)

    @property
    def has_items(self) -> bool:
        return self.package_items_active.exists()

    @property
    def base_price(self) -> Decimal:
        total = ZERO
        for item in self.package_items_active.select_related("nomenclature_item"):
            total += item.base_line_total
        return quantize_money(total)

    @property
    def line_discount_amount(self) -> Decimal:
        total = ZERO
        for item in self.package_items_active.select_related("nomenclature_item"):
            total += item.line_discount_amount
        return quantize_money(total)

    @property
    def subtotal_after_line_discounts(self) -> Decimal:
        total = ZERO
        for item in self.package_items_active.select_related("nomenclature_item"):
            total += item.final_line_total
        return quantize_money(total)

    @property
    def package_discount_amount(self) -> Decimal:
        return calculate_discount_amount(
            self.subtotal_after_line_discounts,
            self.package_discount_percent,
        )

    @property
    def regular_price(self) -> Decimal:
        """
        Цена до общей скидки пакета.
        Учитывает текущие цены номенклатуры и скидки по строкам.
        """
        return self.subtotal_after_line_discounts

    @property
    def promo_price(self) -> Decimal:
        """
        Цена после общей скидки пакета.
        """
        return quantize_money(self.regular_price - self.package_discount_amount)

    @property
    def final_price(self) -> Decimal:
        """
        Итоговая цена, которую можно показывать клиенту.
        """
        return self.promo_price

    @property
    def current_main_image(self) -> "CarServicePackageImage | None":
        return getattr(self, "image_object", None)

    @property
    def image_url(self) -> str:
        image = self.current_main_image
        if image and image.image:
            return image.image.url
        return ""


class CarServicePackageImage(TimestampedModel, ActivatableModel):
    """
    Главная картинка пакета.
    Отдельная модель нужна, потому что пользователь отдельно просил модель изображения пакета.
    """

    package = models.OneToOneField(
        CarServicePackage,
        on_delete=models.CASCADE,
        related_name="image_object",
        verbose_name=_("пакет"),
    )

    image = models.ImageField(_("изображение"), upload_to="services/packages/")
    alt_text = models.CharField(_("alt текст"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("изображение пакета")
        verbose_name_plural = _("изображения пакетов")

    def __str__(self) -> str:
        return f"Изображение пакета: {self.package.public_title}"

    @property
    def image_url(self) -> str:
        if self.image:
            return self.image.url
        return ""


class PackageItemCategory(TimestampedModel, ActivatableModel, SoftDeleteModel):
    """
    Локальная категория элементов пакета (КЭП).
    Создаётся строго внутри конкретного пакета.
    Не является глобальным справочником.
    """

    package = models.ForeignKey(
        CarServicePackage,
        on_delete=models.CASCADE,
        related_name="item_categories",
        verbose_name=_("пакет"),
    )

    name = models.CharField(_("название"), max_length=255)
    description = models.TextField(_("описание"), blank=True)
    sort_order = models.PositiveIntegerField(_("порядок сортировки"), default=0)

    class Meta:
        verbose_name = _("категория элементов пакета")
        verbose_name_plural = _("категории элементов пакета")
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["package", "name"],
                condition=Q(is_deleted=False),
                name="srv_pkgcat_pkg_name_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["package", "sort_order"], name="cat_pic_pkg_sort_idx"),
            models.Index(fields=["is_deleted"], name="cat_pic_del_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.package.public_title} — {self.name}"


class PackageItem(TimestampedModel, ActivatableModel, SoftDeleteModel):
    """
    Конкретный элемент пакета.

    Важные правила:
      - строка всегда ссылается на общую номенклатуру;
      - один и тот же элемент номенклатуры нельзя повторять внутри одного пакета;
      - количество для услуг не может быть больше 1;
      - расчёт идёт по актуальной активной цене номенклатуры;
      - снапшоты хранятся для истории, аудита и выгрузок.
    """

    package = models.ForeignKey(
        CarServicePackage,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("пакет"),
    )

    package_category = models.ForeignKey(
        PackageItemCategory,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("категория элементов пакета"),
    )

    nomenclature_item = models.ForeignKey(
        NomenclatureItem,
        on_delete=models.CASCADE,
        related_name="package_items",
        verbose_name=_("элемент номенклатуры"),
    )

    quantity = models.PositiveIntegerField(
        _("количество"),
        default=1,
        validators=[MinValueValidator(1)],
    )

    discount_percent = models.DecimalField(
        _("скидка, %"),
        max_digits=PERCENT_MAX_DIGITS,
        decimal_places=PERCENT_DECIMAL_PLACES,
        default=ZERO,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    )

    sort_order = models.PositiveIntegerField(_("порядок сортировки"), default=0)

    # --------------------------------------------------------
    # snapshots
    # --------------------------------------------------------
    item_type_snapshot = models.CharField(
        _("тип элемента (snapshot)"),
        max_length=20,
        choices=NomenclatureItemType.choices,
        blank=True,
    )

    article_snapshot = models.CharField(_("артикул (snapshot)"), max_length=128, blank=True)
    name_snapshot = models.CharField(_("название (snapshot)"), max_length=500, blank=True)
    unit_snapshot = models.CharField(_("единица измерения (snapshot)"), max_length=50, blank=True)

    base_price_snapshot = models.DecimalField(
        _("базовая цена, KZT (snapshot)"),
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=ZERO,
    )

    class Meta:
        verbose_name = _("элемент пакета")
        verbose_name_plural = _("элементы пакета")
        ordering = ("sort_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["package", "nomenclature_item"],
                condition=Q(is_deleted=False),
                name="srv_pkgitem_package_nomenclature_not_deleted_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["package", "sort_order"], name="srv_pkgitem_package_sort_idx"),
            models.Index(fields=["package_category"], name="srv_pkgitem_category_idx"),
            models.Index(fields=["nomenclature_item"], name="srv_pkgitem_nomenclature_idx"),
            models.Index(fields=["is_deleted"], name="srv_pkgitem_deleted_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.package.public_title} — {self.nomenclature_item.name}"

    def clean(self):
        super().clean()

        errors: dict[str, str] = {}

        if self.package_category_id and self.package_id:
            if self.package_category.package_id != self.package_id:
                errors["package_category"] = _("Категория элементов пакета должна принадлежать тому же пакету.")

        if self.quantity < 1:
            errors["quantity"] = _("Количество должно быть не меньше 1.")

        if self.discount_percent < ZERO or self.discount_percent > HUNDRED:
            errors["discount_percent"] = _("Скидка должна быть в диапазоне от 0 до 100.")

        if self.nomenclature_item_id and self.nomenclature_item.item_type == NomenclatureItemType.SERVICE:
            if self.quantity > 1:
                errors["quantity"] = _("Для услуги количество не может быть больше 1.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.fill_snapshots()
        super().save(*args, **kwargs)

    def fill_snapshots(self) -> None:
        """
        Обновляет snapshot-поля на момент сохранения строки.
        """
        if not self.nomenclature_item_id:
            return

        item = self.nomenclature_item
        self.item_type_snapshot = item.item_type
        self.article_snapshot = item.article
        self.name_snapshot = item.name
        self.unit_snapshot = item.unit or ""
        self.base_price_snapshot = item.current_price_kzt

    @property
    def current_unit_price(self) -> Decimal:
        """
        Актуальная цена берётся из последней активной цены элемента номенклатуры.
        """
        if not self.nomenclature_item_id:
            return ZERO
        return self.nomenclature_item.current_price_kzt

    @property
    def snapshot_unit_price(self) -> Decimal:
        return quantize_money(self.base_price_snapshot)

    @property
    def base_line_total(self) -> Decimal:
        return quantize_money(self.current_unit_price * self.quantity)

    @property
    def line_discount_amount(self) -> Decimal:
        return calculate_discount_amount(self.base_line_total, self.discount_percent)

    @property
    def discount_value(self) -> Decimal:
        """
        Алиас для удобства в UI и админке.
        """
        return self.line_discount_amount

    @property
    def final_line_total(self) -> Decimal:
        return quantize_money(self.base_line_total - self.line_discount_amount)

    @property
    def item_url_slug(self) -> str:
        """
        Удобный алиас на случай генерации ссылок во frontend/admin.
        """
        return self.nomenclature_item.slug if self.nomenclature_item_id else ""

    @property
    def item_type(self) -> str:
        return self.nomenclature_item.item_type if self.nomenclature_item_id else self.item_type_snapshot


# ============================================================
# validation helper for package completeness
# ============================================================


def validate_package_has_items(package: CarServicePackage) -> None:
    """
    Вспомогательная функция, если ты захочешь вызывать её из forms/admin/services слоя.
    На уровне БД гарантировать "у пакета обязательно есть хотя бы одна строка"
    напрямую нельзя, потому что пакет и строки создаются в разные моменты.
    """
    if not package.items.filter(is_deleted=False).exists():
        raise ValidationError(_("У пакета должен быть хотя бы один элемент."))



