from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from cars.models import Modification
from main.models import TimestampedModel, User
from catalog.models import CarServicePackage


# ============================================================
# helpers
# ============================================================

MONEY_MAX_DIGITS = 12
MONEY_DECIMAL_PLACES = 2
ZERO = Decimal("0.00")


# ============================================================
# choices
# ============================================================


class ClientPackageOrderStatus(models.TextChoices):
    # Что хранит:
    #   текущий статус покупки / заявки клиента на пакет
    # Примеры:
    #   NEW, CANCELLED
    # Зачем:
    #   для истории покупок и базовой обработки MVP
    NEW = "NEW", _("Новая")
    CANCELLED = "CANCELLED", _("Отменена")


# ============================================================
# client
# ============================================================


class Client(User):
    """
    Клиент автосервиса.

    В MVP используем multi-table inheritance:
    - базовая модель пользователя лежит в main.models.User
    - клиент расширяет её дополнительными клиентскими полями

    Важно:
    - email остаётся в User
    - full_name хранится отдельно именно у клиента
    - роль клиента фиксируем флагом is_client=True
    """

    # full_name:
    #   полное имя клиента одной строкой
    # Пример:
    #   "Нурсултан Кужагалиев"
    # Зачем:
    #   это минимально достаточное поле имени для MVP
    full_name = models.CharField(_("полное имя"), max_length=255)

    class Meta:
        verbose_name = _("клиент")
        verbose_name_plural = _("клиенты")

    def __str__(self) -> str:
        if self.full_name:
            return self.full_name
        if self.email:
            return self.email
        return f"Client #{self.pk}"

    def save(self, *args, **kwargs):
        # Клиентская запись всегда должна быть помечена как клиент
        self.is_client = True
        super().save(*args, **kwargs)


# ============================================================
# client garage
# ============================================================


class ClientCar(TimestampedModel):
    """
    Автомобиль клиента в его гараже.

    MVP-правила:
    - машина всегда привязана к конкретной cars.Modification
    - у клиента может быть несколько машин
    - у клиента может быть только одна активная основная машина (is_primary=True)
    - госномер уникален глобально
    - VIN опционален, но если указан — уникален глобально
    """

    # client:
    #   владелец машины
    # Пример:
    #   Client(full_name="Нурсултан")
    # Зачем:
    #   гараж принадлежит конкретному клиенту
    client = models.ForeignKey(
        'main.User',  # Привязываем к базовому User
        on_delete=models.CASCADE,
        related_name="cars",
        verbose_name=_("клиент"),
    )

    # modification:
    #   точная модификация из каталога автомобилей
    # Пример:
    #   Toyota | Camry | VIII (XV70) | ...
    # Зачем:
    #   именно по ней потом ищутся релевантные пакеты
    modification = models.ForeignKey(
        Modification,
        on_delete=models.CASCADE,
        related_name="client_cars",
        verbose_name=_("модификация"),
    )

    # license_plate:
    #   государственный номер автомобиля
    # Пример:
    #   "123ABC02"
    # Зачем:
    #   идентификация конкретной машины клиента
    license_plate = models.CharField(
        _("госномер"),
        max_length=32,
        unique=True,
        db_index=True,
    )

    # vin:
    #   VIN автомобиля
    # Пример:
    #   "JTDBR32E720123456"
    # Зачем:
    #   дополнительная точная идентификация машины
    vin = models.CharField(
        _("VIN"),
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    # mileage_km:
    #   текущий пробег автомобиля
    # Пример:
    #   135000
    # Зачем:
    #   базовая сервисная информация по машине
    mileage_km = models.PositiveIntegerField(
        _("пробег, км"),
        validators=[MinValueValidator(0)],
    )

    # year:
    #   год выпуска автомобиля
    # Пример:
    #   2018
    # Зачем:
    #   дополнительная характеристика конкретной машины
    year = models.PositiveSmallIntegerField(_("год выпуска"))

    # is_primary:
    #   активный автомобиль клиента
    # Пример:
    #   True
    # Зачем:
    #   именно по активному автомобилю клиент видит опубликованные пакеты
    is_primary = models.BooleanField(_("активный автомобиль"), default=False, db_index=True)

    # is_active:
    #   активна ли запись в гараже
    # Пример:
    #   True
    # Зачем:
    #   можно временно скрыть машину без удаления логики на уровне бизнеса
    is_active = models.BooleanField(_("активна"), default=True, db_index=True)

    class Meta:
        verbose_name = _("автомобиль клиента")
        verbose_name_plural = _("автомобили клиентов")
        ordering = ("-is_primary", "-created_at", "-id")
        constraints = [
            # У клиента единовременно только одна основная машина
            models.UniqueConstraint(
                fields=["client"],
                condition=Q(is_primary=True),
                name="clients_clientcar_one_primary_per_client_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["client", "is_primary"], name="clients_car_client_primary_idx"),
            models.Index(fields=["client", "is_active"], name="clients_car_client_active_idx"),
            models.Index(fields=["modification"], name="clients_car_modification_idx"),
            models.Index(fields=["year"], name="clients_car_year_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.license_plate} — {self.modification}"

    def clean(self):
        super().clean()

        errors: dict[str, str] = {}

        if self.year < 1900:
            errors["year"] = _("Год выпуска не может быть меньше 1900.")

        if self.mileage_km < 0:
            errors["mileage_km"] = _("Пробег не может быть отрицательным.")

        if errors:
            raise ValidationError(errors)

    @property
    def display_name(self) -> str:
        return f"{self.license_plate} — {self.modification}"

    @property
    def modification_source_id(self) -> str:
        return self.modification.source_id


# ============================================================
# client package orders / purchase history
# ============================================================


class ClientPackageOrder(TimestampedModel):
    """
    История покупки / заявки клиента на пакет.
    """

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="package_orders",
        verbose_name=_("клиент"),
    )

    client_car = models.ForeignKey(
        ClientCar,
        on_delete=models.CASCADE,
        related_name="package_orders",
        verbose_name=_("автомобиль клиента"),
    )

    package = models.ForeignKey(
        CarServicePackage,
        on_delete=models.CASCADE,
        related_name="client_orders",
        verbose_name=_("пакет"),
    )

    status = models.CharField(
        _("статус"),
        max_length=20,
        choices=ClientPackageOrderStatus.choices,
        default=ClientPackageOrderStatus.NEW,
        db_index=True,
    )

    client_full_name_snapshot = models.CharField(_("имя клиента (snapshot)"), max_length=255)
    client_email_snapshot = models.EmailField(_("email клиента (snapshot)"))

    car_license_plate_snapshot = models.CharField(_("госномер (snapshot)"), max_length=32)
    car_vin_snapshot = models.CharField(_("VIN (snapshot)"), max_length=64, blank=True)
    car_year_snapshot = models.PositiveSmallIntegerField(_("год выпуска (snapshot)"))
    car_mileage_km_snapshot = models.PositiveIntegerField(_("пробег, км (snapshot)"))

    car_modification_source_id_snapshot = models.CharField(
        _("source_id модификации (snapshot)"),
        max_length=128,
        db_index=True,
    )

    car_modification_title_snapshot = models.CharField(
        _("название модификации (snapshot)"),
        max_length=1000,
    )

    package_name_snapshot = models.CharField(_("внутреннее название пакета (snapshot)"), max_length=255)
    package_public_title_snapshot = models.CharField(_("публичный заголовок пакета (snapshot)"), max_length=255)
    package_category_name_snapshot = models.CharField(_("категория пакета (snapshot)"), max_length=255)
    package_slug_snapshot = models.SlugField(
        _("slug пакета (snapshot)"),
        max_length=255,
        allow_unicode=True,
    )

    regular_price_snapshot = models.DecimalField(
        _("обычная цена (snapshot)"),
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=ZERO,
    )

    final_price_snapshot = models.DecimalField(
        _("итоговая цена (snapshot)"),
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=ZERO,
    )

    is_promo_snapshot = models.BooleanField(_("акция (snapshot)"), default=False)
    promo_text_snapshot = models.TextField(_("текст акции (snapshot)"), blank=True)

    package_items_snapshot = models.TextField(
        _("состав пакета (snapshot)"),
        blank=True,
        help_text=_("JSON-строка со статичным составом пакета на момент покупки."),
    )

    class Meta:
        verbose_name = _("покупка пакета клиентом")
        verbose_name_plural = _("покупки пакетов клиентами")
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["client", "status"], name="cl_ord_cli_stat_idx"),
            models.Index(fields=["client_car"], name="cl_ord_car_idx"),
            models.Index(fields=["package"], name="cl_ord_pkg_idx"),
            models.Index(fields=["status", "created_at"], name="cl_ord_stat_cr_idx"),
            models.Index(fields=["car_modification_source_id_snapshot"], name="cl_ord_modsrc_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.client_full_name_snapshot} — {self.package_public_title_snapshot}"

    def clean(self):
        super().clean()

        errors: dict[str, str] = {}

        if self.client_car_id and self.package_id:
            if self.client_car.modification_id != self.package.modification_id:
                errors["package"] = _(
                    "Выбранный пакет не относится к модификации автомобиля клиента."
                )

        if self.package_id and self.package.status != "PUBLISHED":
            errors["package"] = _("Нельзя оформить покупку на неопубликованный пакет.")

        if self.regular_price_snapshot < ZERO:
            errors["regular_price_snapshot"] = _("Обычная цена не может быть отрицательной.")

        if self.final_price_snapshot < ZERO:
            errors["final_price_snapshot"] = _("Итоговая цена не может быть отрицательной.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.fill_snapshots()
        super().save(*args, **kwargs)

    def fill_snapshots(self) -> None:
        if self.client_id:
            self.client_full_name_snapshot = self.client.full_name
            self.client_email_snapshot = self.client.email

        if self.client_car_id:
            self.car_license_plate_snapshot = self.client_car.license_plate
            self.car_vin_snapshot = self.client_car.vin or ""
            self.car_year_snapshot = self.client_car.year
            self.car_mileage_km_snapshot = self.client_car.mileage_km
            self.car_modification_source_id_snapshot = self.client_car.modification.source_id
            self.car_modification_title_snapshot = str(self.client_car.modification)

        if self.package_id:
            self.package_name_snapshot = self.package.name
            self.package_public_title_snapshot = self.package.public_title
            self.package_category_name_snapshot = self.package.category.name
            self.package_slug_snapshot = self.package.slug
            self.regular_price_snapshot = self.package.regular_price
            self.final_price_snapshot = self.package.final_price
            self.is_promo_snapshot = self.package.is_promo
            self.promo_text_snapshot = self.package.promo_text or ""

    @property
    def is_cancelled(self) -> bool:
        return self.status == ClientPackageOrderStatus.CANCELLED

    @property
    def current_package_final_price(self) -> Decimal:
        if not self.package_id:
            return ZERO
        return self.package.final_price

    @property
    def price_difference(self) -> Decimal:
        return self.current_package_final_price - self.final_price_snapshot







