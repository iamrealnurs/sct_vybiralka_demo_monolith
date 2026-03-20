from __future__ import annotations
# Позволяет использовать современные аннотации типов,
# включая ссылки на классы, объявленные ниже по файлу.

from django.db import models
# Базовый модуль Django ORM: модели, поля, индексы, связи и т.д.

from django.utils.translation import gettext_lazy as _
# Ленивый перевод строк для verbose_name и других подписей.


from main.models import TimestampedModel

# ============================================================
# choices
# ============================================================
# Здесь мы описываем нормализованные перечисления значений.
# Это нужно, чтобы:
# - не хранить хаотичные строки в БД;
# - иметь единообразные значения;
# - проще фильтровать;
# - проще строить формы и API.


class SteeringWheelPosition(models.TextChoices):
    # Что хранит:
    #   положение руля автомобиля
    # Примеры:
    #   "Левый", "Правый", "Левый/Правый"
    # Зачем:
    #   для фильтрации и отображения в карточке автомобиля
    LEFT = "LEFT", _("Левый")
    RIGHT = "RIGHT", _("Правый")
    LEFT_RIGHT = "LEFT_RIGHT", _("Левый/Правый")
    RIGHT_LEFT = "RIGHT_LEFT", _("Правый/Левый")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class TransmissionType(models.TextChoices):
    # Что хранит:
    #   тип коробки передач
    # Примеры:
    #   "Автомат", "Механика", "Робот"
    # Зачем:
    #   один из ключевых фильтров в каталоге
    AUTOMATIC = "AUTOMATIC", _("Автомат")
    VARIATOR = "VARIATOR", _("Вариатор")
    MANUAL = "MANUAL", _("Механика")
    ROBOT = "ROBOT", _("Робот")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class TransmissionCode(models.TextChoices):
    # Что хранит:
    #   технический код типа трансмиссии из источника
    # Примеры:
    #   "AUTOMATIC", "MECHANICAL"
    # Зачем:
    #   не терять оригинальную классификацию источника
    AUTOMATIC = "AUTOMATIC", _("AUTOMATIC")
    MECHANICAL = "MECHANICAL", _("MECHANICAL")
    ROBOT = "ROBOT", _("ROBOT")
    VARIATOR = "VARIATOR", _("VARIATOR")
    UNKNOWN = "UNKNOWN", _("UNKNOWN")


class DriveType(models.TextChoices):
    # Что хранит:
    #   тип привода
    # Примеры:
    #   "Передний", "Задний", "Полный"
    # Зачем:
    #   это важный фильтр и важная характеристика машины
    REAR = "REAR", _("Задний")
    FRONT = "FRONT", _("Передний")
    ALL_WHEEL = "ALL_WHEEL", _("Полный")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class PowertrainType(models.TextChoices):
    # Что хранит:
    #   тип силовой установки / общий тип двигателя
    # Примеры:
    #   "Бензиновый", "Дизельный", "Электро", "Гибридный"
    # Зачем:
    #   помогает фильтровать и логически разделять авто по типу тяги
    PETROL = "PETROL", _("Бензиновый")
    HYDROGEN = "HYDROGEN", _("Водородный")
    LPG = "LPG", _("ГБО")
    HYBRID = "HYBRID", _("Гибридный")
    DIESEL = "DIESEL", _("Дизельный")
    ELECTRIC = "ELECTRIC", _("Электро")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class FuelType(models.TextChoices):
    # Что хранит:
    #   конкретный вид топлива
    # Примеры:
    #   "АИ-92", "АИ-95", "ДТ", "Водород"
    # Зачем:
    #   нужен для более точного описания машины
    AI_76 = "AI_76", _("АИ-76")
    AI_80 = "AI_80", _("АИ-80")
    AI_92 = "AI_92", _("АИ-92")
    AI_95 = "AI_95", _("АИ-95")
    AI_98 = "AI_98", _("АИ-98")
    HYDROGEN = "HYDROGEN", _("Водород")
    GASOLINE_GAS = "GASOLINE_GAS", _("Газ (бензин)")
    DIESEL = "DIESEL", _("ДТ")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class VehicleClass(models.TextChoices):
    # Что хранит:
    #   класс автомобиля / модели
    # Примеры:
    #   "A", "C", "D", "J"
    # Зачем:
    #   для классификации, фильтров и аналитики
    A = "A", "A"
    B = "B", "B"
    C = "C", "C"
    D = "D", "D"
    E = "E", "E"
    F = "F", "F"
    J = "J", "J"
    M = "M", "M"
    S = "S", "S"
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class EmissionEuroClass(models.TextChoices):
    # Что хранит:
    #   экологический стандарт
    # Примеры:
    #   "Euro 4", "Euro 5", "Euro 6"
    # Зачем:
    #   важно для характеристик, фильтрации и совместимости с рынками
    EURO_1 = "EURO_1", _("Euro 1")
    EURO_2 = "EURO_2", _("Euro 2")
    EURO_3 = "EURO_3", _("Euro 3")
    EURO_4 = "EURO_4", _("Euro 4")
    EURO_5 = "EURO_5", _("Euro 5")
    EURO_6 = "EURO_6", _("Euro 6")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class AspirationType(models.TextChoices):
    # Что хранит:
    #   тип наддува двигателя
    # Примеры:
    #   "нет", "Турбонаддув", "Компрессор"
    # Зачем:
    #   для технической спецификации двигателя
    COMPRESSOR = "COMPRESSOR", _("Компрессор")
    NONE = "NONE", _("нет")
    TURBO = "TURBO", _("Турбонаддув")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class FuelInjectionType(models.TextChoices):
    # Что хранит:
    #   систему подачи топлива / тип впрыска
    # Примеры:
    #   "Common rail", "Непосредственный впрыск", "Карбюратор"
    # Зачем:
    #   даёт более техническое описание двигателя
    COMMON_RAIL = "COMMON_RAIL", _("Common rail (дизель)")
    CARBURETOR = "CARBURETOR", _("Карбюратор")
    COMBINED_INJECTION = "COMBINED_INJECTION", _("Комбинированный впрыск (непосредственно-распределенный)")
    UNIT_INJECTOR = "UNIT_INJECTOR", _("Насос-форсунка (дизель)")
    DIRECT_INJECTION = "DIRECT_INJECTION", _("Непосредственный впрыск (прямой)")
    MULTIPOINT_INJECTION = "MULTIPOINT_INJECTION", _("Распределенный впрыск (многоточечный)")
    DIESEL_PUMP = "DIESEL_PUMP", _("ТНВД (дизель)")
    SINGLE_POINT_INJECTION = "SINGLE_POINT_INJECTION", _("Центральный впрыск (моновпрыск или одноточечный)")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class CylindersLayout(models.TextChoices):
    # Что хранит:
    #   компоновку цилиндров
    # Примеры:
    #   "Рядное", "V-образное", "Оппозитное"
    # Зачем:
    #   для технической классификации двигателя
    V = "V", _("V-образное")
    VR = "VR", _("V-образное с малым углом")
    W = "W", _("W-образное")
    BOXER = "BOXER", _("Оппозитное")
    ROTARY = "ROTARY", _("Ротор")
    INLINE = "INLINE", _("Рядное")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class ValvetrainType(models.TextChoices):
    # Что хранит:
    #   тип ГРМ / valvetrain
    # Примеры:
    #   "DOHC", "SOHC", "OHV"
    # Зачем:
    #   для тех. характеристик двигателя
    DOHC = "DOHC", "DOHC"
    OHC = "OHC", "OHC"
    OHV = "OHV", "OHV"
    SOHC = "SOHC", "SOHC"
    SV = "SV", "SV"
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class ConsumptionCalcType(models.TextChoices):
    # Что хранит:
    #   стандарт измерения расхода/запаса хода
    # Примеры:
    #   "WLTP", "NEDC", "EPA", "CLTC"
    # Зачем:
    #   особенно важно для EV и гибридов
    CLTC = "CLTC", "CLTC"
    EPA = "EPA", "EPA"
    NEDC = "NEDC", "NEDC"
    WLTP = "WLTP", "WLTP"
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class EvBatteryType(models.TextChoices):
    # Что хранит:
    #   химический тип батареи
    # Примеры:
    #   "LFP", "Li-ion", "Li-NMC"
    # Зачем:
    #   характеристика EV/гибридов
    HFC = "HFC", _("Водородные элементы (HFC)")
    LFP = "LFP", _("Литий-железо-фосфатная (LFP)")
    LI_ION = "LI_ION", _("Литий-ионная (Li-ion)")
    LI_NMC = "LI_NMC", _("Литий-никель-марганец-кобальт-оксидная (Li-NMC)")
    LI_POL = "LI_POL", _("Литий-полимерная (Li-pol)")
    NA_ION = "NA_ION", _("Натрий-ионная (Na-ion)")
    NIH2 = "NIH2", _("Никель-водородная (NiH2)")
    NICD = "NICD", _("Никель-кадмиевая (NiCd)")
    NIMH = "NIMH", _("Никель-металлогидридная (NiMH)")
    LEAD_ACID = "LEAD_ACID", _("Свинцово-кислотная (Lead-acid)")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class CountryChoices(models.TextChoices):
    # Что хранит:
    #   нормализованную страну происхождения
    # Примеры:
    #   "GERMANY", "JAPAN", "CHINA"
    # Зачем:
    #   чтобы не хранить хаотичные строки и иметь единый справочник
    AUSTRALIA = "AUSTRALIA", _("Австралия")
    AUSTRIA = "AUSTRIA", _("Австрия")
    BELARUS = "BELARUS", _("Беларусь")
    BRAZIL = "BRAZIL", _("Бразилия")
    UNITED_KINGDOM = "UNITED_KINGDOM", _("Великобритания")
    VIETNAM = "VIETNAM", _("Вьетнам")
    GERMANY = "GERMANY", _("Германия")
    DENMARK = "DENMARK", _("Дания")
    ISRAEL = "ISRAEL", _("Израиль")
    INDIA = "INDIA", _("Индия")
    IRAN = "IRAN", _("Иран")
    SPAIN = "SPAIN", _("Испания")
    ITALY = "ITALY", _("Италия")
    CHINA = "CHINA", _("Китай")
    LATVIA = "LATVIA", _("Латвия")
    MALAYSIA = "MALAYSIA", _("Малайзия")
    MEXICO = "MEXICO", _("Мексика")
    NETHERLANDS = "NETHERLANDS", _("Нидерланды")
    NORWAY = "NORWAY", _("Норвегия")
    UAE = "UAE", _("Объединённые Арабские Эмираты")
    PAKISTAN = "PAKISTAN", _("Пакистан")
    POLAND = "POLAND", _("Польша")
    RUSSIA = "RUSSIA", _("Россия")
    ROMANIA = "ROMANIA", _("Румыния")
    SERBIA = "SERBIA", _("Сербия")
    USA = "USA", _("США")
    THAILAND = "THAILAND", _("Таиланд")
    TAIWAN = "TAIWAN", _("Тайвань")
    TURKEY = "TURKEY", _("Турция")
    UZBEKISTAN = "UZBEKISTAN", _("Узбекистан")
    UKRAINE = "UKRAINE", _("Украина")
    FRANCE = "FRANCE", _("Франция")
    CROATIA = "CROATIA", _("Хорватия")
    CZECHIA = "CZECHIA", _("Чехия")
    SWITZERLAND = "SWITZERLAND", _("Швейцария")
    SWEDEN = "SWEDEN", _("Швеция")
    SOUTH_KOREA = "SOUTH_KOREA", _("Южная Корея")
    JAPAN = "JAPAN", _("Япония")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class BrakeType(models.TextChoices):
    # Что хранит:
    #   тип тормозов
    # Примеры:
    #   "Дисковые", "Барабанные", "Керамические"
    # Зачем:
    #   для тех. характеристик ходовой
    DRUM = "DRUM", _("Барабанные")
    DISC = "DISC", _("Дисковые")
    VENTILATED_DISC = "VENTILATED_DISC", _("Дисковые вентилируемые")
    CERAMIC = "CERAMIC", _("Керамические")
    VENTILATED_CERAMIC = "VENTILATED_CERAMIC", _("Керамические вентилируемые")
    UNKNOWN = "UNKNOWN", _("Неизвестно")


class SuspensionType(models.TextChoices):
    # Что хранит:
    #   тип подвески
    # Примеры:
    #   "Независимая, пружинная", "Полунезависимая, торсионная"
    # Зачем:
    #   это часть тех. описания машины
    DEPENDENT_SPRING = "DEPENDENT_SPRING", _("Зависимая, пружинная")
    DEPENDENT_LEAF = "DEPENDENT_LEAF", _("Зависимая, рессорная")
    DEPENDENT_PNEUMATIC = "DEPENDENT_PNEUMATIC", _("Зависимая, пневмоэлемент")
    INDEPENDENT_HYDROPNEUMATIC = "INDEPENDENT_HYDROPNEUMATIC", _("Независимая, гидропневмоэлемент")
    INDEPENDENT_PNEUMATIC = "INDEPENDENT_PNEUMATIC", _("Независимая, пневмоэлемент")
    INDEPENDENT_SPRING = "INDEPENDENT_SPRING", _("Независимая, пружинная")
    INDEPENDENT_LEAF = "INDEPENDENT_LEAF", _("Независимая, рессорная")
    INDEPENDENT_TORSION = "INDEPENDENT_TORSION", _("Независимая, торсионная")
    SEMI_INDEPENDENT_SPRING = "SEMI_INDEPENDENT_SPRING", _("Полунезависимая, пружинная")
    SEMI_INDEPENDENT_TORSION = "SEMI_INDEPENDENT_TORSION", _("Полунезависимая, торсионная")
    UNKNOWN = "UNKNOWN", _("Неизвестно")



# ============================================================
# dictionaries
# ============================================================


class BodyType(TimestampedModel):
    # code:
    #   технический код кузова
    # Пример:
    #   "SEDAN", "WAGON_5_DOORS", "CABRIO"
    # Зачем:
    #   это нормализованный справочник кузовов
    code = models.CharField(_("код"), max_length=64, unique=True, db_index=True)

    # name:
    #   человекочитаемое название кузова
    # Пример:
    #   "Седан", "Универсал 5 дв.", "Кабриолет"
    # Зачем:
    #   отображение в UI, карточке авто, фильтрах
    name = models.CharField(_("название"), max_length=255, blank=True)

    # description:
    #   дополнительное описание кузова
    # Пример:
    #   "Пятидверный универсал"
    # Зачем:
    #   опционально, если понадобится расширенное описание
    description = models.TextField(_("описание"), blank=True)

    class Meta:
        verbose_name = _("тип кузова")
        verbose_name_plural = _("типы кузова")
        ordering = ("name", "code")
        indexes = [
            models.Index(fields=["name"], name="cars_bodytype_name_idx"),
        ]

    def __str__(self) -> str:
        return self.name or self.code


class OptionCategory(TimestampedModel):
    # code:
    #   технический код категории опций
    # Пример:
    #   "safety", "interior", "multimedia"
    # Зачем:
    #   нужен для структурирования словаря опций
    code = models.CharField(_("код"), max_length=64, unique=True, db_index=True)

    # name:
    #   отображаемое имя категории
    # Пример:
    #   "Безопасность", "Интерьер", "Мультимедиа"
    # Зачем:
    #   для группировки опций в интерфейсе
    name = models.CharField(_("название"), max_length=255, db_index=True)

    # sort_order:
    #   порядок вывода категории
    # Пример:
    #   10, 20, 30
    # Зачем:
    #   чтобы контролировать порядок категорий в UI
    sort_order = models.PositiveIntegerField(_("порядок сортировки"), default=0)

    # description:
    #   пояснение к категории
    # Пример:
    #   "Опции, связанные с пассивной и активной безопасностью"
    # Зачем:
    #   опционально для админки и внутренней документации
    description = models.TextField(_("описание"), blank=True)

    # is_active:
    #   активна ли категория
    # Пример:
    #   True
    # Зачем:
    #   позволяет скрывать категорию без удаления
    is_active = models.BooleanField(_("активна"), default=True)

    class Meta:
        verbose_name = _("категория опций")
        verbose_name_plural = _("категории опций")
        ordering = ("sort_order", "name", "code")
        indexes = [
            models.Index(fields=["is_active", "sort_order"], name="cars_optcat_active_sort_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class OptionDefinition(TimestampedModel):
    # category:
    #   к какой категории относится опция
    # Пример:
    #   "Безопасность"
    # Зачем:
    #   группировка опций по смыслу
    category = models.ForeignKey(
        OptionCategory,
        on_delete=models.PROTECT,
        related_name="options",
        verbose_name=_("категория"),
        null=True,
        blank=True,
    )

    # code:
    #   технический код опции
    # Пример:
    #   "abs", "bluetooth", "rear_camera"
    # Зачем:
    #   это основная нормализованная идентичность опции
    code = models.CharField(_("код"), max_length=128, unique=True, db_index=True)

    # name:
    #   краткое имя опции
    # Пример:
    #   "ABS", "Bluetooth", "Камера заднего вида"
    # Зачем:
    #   отображение в интерфейсе
    name = models.CharField(_("название"), max_length=255, db_index=True)

    # full_name:
    #   полное название опции
    # Пример:
    #   "Антиблокировочная система тормозов"
    # Зачем:
    #   расширенное отображение и документация
    full_name = models.CharField(_("полное название"), max_length=255, blank=True)

    # description:
    #   описание опции
    # Пример:
    #   "Система предотвращения блокировки колес при торможении"
    # Зачем:
    #   полезно для админки и расширенного UI
    description = models.TextField(_("описание"), blank=True)

    # sort_order:
    #   порядок внутри категории
    # Пример:
    #   100
    # Зачем:
    #   контролировать порядок отображения опций
    sort_order = models.PositiveIntegerField(_("порядок сортировки"), default=0)

    # is_active:
    #   активна ли опция
    # Пример:
    #   True
    # Зачем:
    #   можно скрыть устаревшую опцию, не удаляя
    is_active = models.BooleanField(_("активна"), default=True)

    class Meta:
        verbose_name = _("опция")
        verbose_name_plural = _("опции")
        ordering = ("sort_order", "name", "code")
        indexes = [
            models.Index(fields=["category", "is_active"], name="cars_optdef_cat_active_idx"),
        ]

    def __str__(self) -> str:
        return self.name or self.code


# ============================================================
# vehicle catalog hierarchy
# ============================================================


class Mark(TimestampedModel):
    # source_id:
    #   внешний строковый ID марки из каталога-источника
    # Пример:
    #   "AUDI", "BMW", "TOYOTA"
    # Зачем:
    #   нужен для стабильного импорта и синхронизации
    source_id = models.CharField(_("source id"), max_length=64, unique=True, db_index=True)

    # source_numeric_id:
    #   внешний числовой ID марки
    # Пример:
    #   3139
    # Зачем:
    #   помогает при сопоставлении с исходной системой
    source_numeric_id = models.BigIntegerField(_("source numeric id"), null=True, blank=True, db_index=True)

    # name:
    #   основное имя марки
    # Пример:
    #   "Audi", "BMW"
    # Зачем:
    #   базовое отображение бренда
    name = models.CharField(_("название"), max_length=255, db_index=True)

    # name_ru:
    #   русское имя марки
    # Пример:
    #   "Ауди", "БМВ"
    # Зачем:
    #   локализованное отображение
    name_ru = models.CharField(_("название (RU)"), max_length=255, blank=True)

    # year_from:
    #   год начала существования / присутствия марки в источнике
    # Пример:
    #   1927
    # Зачем:
    #   дополнительная справочная информация
    year_from = models.PositiveSmallIntegerField(_("год начала"), null=True, blank=True)

    # year_to:
    #   год окончания / верхняя граница в источнике
    # Пример:
    #   2026
    # Зачем:
    #   дополнительная справочная информация
    year_to = models.PositiveSmallIntegerField(_("год окончания"), null=True, blank=True)

    # is_popular:
    #   популярна ли марка по данным источника
    # Пример:
    #   True
    # Зачем:
    #   можно использовать для витрин и приоритизации
    is_popular = models.BooleanField(_("популярная"), default=False)

    # country:
    #   нормализованная страна происхождения
    # Пример:
    #   CountryChoices.GERMANY
    # Зачем:
    #   фильтрация, отображение, аналитика
    country = models.CharField(
        _("страна"),
        max_length=64,
        choices=CountryChoices.choices,
        default=CountryChoices.UNKNOWN,
        db_index=True,
    )

    # country_raw:
    #   исходное строковое значение страны
    # Пример:
    #   "Германия"
    # Зачем:
    #   не терять оригинал из источника
    country_raw = models.CharField(_("страна (raw)"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("марка")
        verbose_name_plural = _("марки")
        ordering = ("name", "source_id")
        indexes = [
            models.Index(fields=["is_popular"], name="cars_mark_popular_idx"),
            models.Index(fields=["year_from", "year_to"], name="cars_mark_years_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        # Удобное отображаемое имя:
        # сначала русское, если есть, иначе основное
        return self.name_ru or self.name


class CarModel(TimestampedModel):
    # mark:
    #   ссылка на марку
    # Пример:
    #   Audi
    # Зачем:
    #   модель всегда принадлежит определённой марке
    mark = models.ForeignKey(
        Mark,
        on_delete=models.CASCADE,
        related_name="car_models",
        verbose_name=_("марка"),
    )

    # source_id:
    #   внешний ID модели
    # Пример:
    #   "AUDI_A4", "BMW_3ER"
    # Зачем:
    #   нужен для стабильного импорта
    source_id = models.CharField(_("source id"), max_length=128, unique=True, db_index=True)

    # name:
    #   имя модели
    # Пример:
    #   "A4", "Camry", "Tucson"
    # Зачем:
    #   основное отображение модели
    name = models.CharField(_("название"), max_length=255, db_index=True)

    # name_ru:
    #   русское имя модели
    # Пример:
    #   "А4", "Камри"
    # Зачем:
    #   локализованное отображение
    name_ru = models.CharField(_("название (RU)"), max_length=255, blank=True)

    # year_from/year_to:
    #   диапазон лет существования модели
    # Пример:
    #   1994 ... 2025
    # Зачем:
    #   справочная информация и фильтрация
    year_from = models.PositiveSmallIntegerField(_("год начала"), null=True, blank=True)
    year_to = models.PositiveSmallIntegerField(_("год окончания"), null=True, blank=True)

    # class_code:
    #   класс модели
    # Пример:
    #   VehicleClass.D
    # Зачем:
    #   классификация модели
    class_code = models.CharField(
        _("класс модели"),
        max_length=16,
        choices=VehicleClass.choices,
        default=VehicleClass.UNKNOWN,
        db_index=True,
    )

    # class_code_raw:
    #   исходное значение класса
    # Пример:
    #   "D"
    # Зачем:
    #   сохранить оригинал из источника
    class_code_raw = models.CharField(_("класс модели (raw)"), max_length=10, blank=True)

    class Meta:
        verbose_name = _("модель автомобиля")
        verbose_name_plural = _("модели автомобилей")
        ordering = ("mark__name", "name", "source_id")
        indexes = [
            models.Index(fields=["mark", "name"], name="cars_carmodel_mark_name_idx"),
            models.Index(fields=["year_from", "year_to"], name="cars_carmodel_years_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.mark.name} {self.name}"

    @property
    def display_name(self) -> str:
        return f"{self.mark.display_name} {self.name_ru or self.name}"


class Generation(TimestampedModel):
    # model:
    #   ссылка на модель автомобиля
    # Пример:
    #   Audi A4
    # Зачем:
    #   поколение всегда внутри модели
    model = models.ForeignKey(
        CarModel,
        on_delete=models.CASCADE,
        related_name="generations",
        verbose_name=_("модель"),
    )

    # source_id:
    #   внешний ID поколения
    # Пример:
    #   "20637504"
    # Зачем:
    #   нужен для импорта и связи с источником
    source_id = models.CharField(_("source id"), max_length=64, unique=True, db_index=True)

    # name:
    #   название поколения
    # Пример:
    #   "V (B9)", "IV", "F22 Рестайлинг"
    # Зачем:
    #   человекочитаемое отображение поколения
    name = models.CharField(_("название"), max_length=255, blank=True, db_index=True)

    # year_from/year_to:
    #   диапазон лет поколения
    # Пример:
    #   2015 ... 2020
    # Зачем:
    #   фильтрация и отображение
    year_from = models.PositiveSmallIntegerField(_("год начала"), null=True, blank=True)
    year_to = models.PositiveSmallIntegerField(_("год окончания"), null=True, blank=True)

    class Meta:
        verbose_name = _("поколение")
        verbose_name_plural = _("поколения")
        ordering = ("model__mark__name", "model__name", "year_from", "name", "source_id")
        indexes = [
            models.Index(fields=["model", "year_from", "year_to"], name="cars_gen_model_yrs_idx"),
        ]

    def __str__(self) -> str:
        if self.name:
            return f"{self.model} — {self.name}"
        if self.year_from or self.year_to:
            return f"{self.model} — {self.year_from or '?'}-{self.year_to or '?'}"
        return f"{self.model} — {self.source_id}"

    @property
    def display_name(self) -> str:
        return self.name or f"{self.year_from or '?'}-{self.year_to or '?'}"


class Configuration(TimestampedModel):
    # generation:
    #   ссылка на поколение
    # Пример:
    #   Audi A4 V (B9)
    # Зачем:
    #   конфигурация всегда находится внутри поколения
    generation = models.ForeignKey(
        Generation,
        on_delete=models.CASCADE,
        related_name="configurations",
        verbose_name=_("поколение"),
    )

    # source_id:
    #   внешний ID конфигурации
    # Пример:
    #   "20637615"
    # Зачем:
    #   нужен для стабильного импорта
    source_id = models.CharField(_("source id"), max_length=64, unique=True, db_index=True)

    # name:
    #   название конфигурации кузова
    # Пример:
    #   "Универсал 5 дв.", "Седан", "Кабриолет"
    # Зачем:
    #   отображение варианта кузова внутри поколения
    name = models.CharField(_("название"), max_length=255, db_index=True)

    # body_type:
    #   ссылка на нормализованный тип кузова
    # Пример:
    #   WAGON_5_DOORS
    # Зачем:
    #   фильтры и единый справочник кузовов
    body_type = models.ForeignKey(
        BodyType,
        on_delete=models.PROTECT,
        related_name="configurations",
        verbose_name=_("тип кузова"),
        null=True,
        blank=True,
    )

    # doors_count:
    #   количество дверей на уровне конфигурации
    # Пример:
    #   4, 5
    # Зачем:
    #   структурное свойство кузова
    doors_count = models.PositiveSmallIntegerField(_("количество дверей"), null=True, blank=True)

    class Meta:
        verbose_name = _("конфигурация")
        verbose_name_plural = _("конфигурации")
        ordering = ("generation__model__mark__name", "generation__model__name", "name", "source_id")
        indexes = [
            models.Index(fields=["generation", "name"], name="cars_cfg_gen_name_idx"),
            models.Index(fields=["body_type"], name="cars_config_bodytype_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.generation} — {self.name}"

    @property
    def full_title(self) -> str:
        return f"{self.generation.model.mark.name} {self.generation.model.name} {self.name}".strip()


class Modification(TimestampedModel):
    # configuration:
    #   ссылка на конфигурацию
    # Пример:
    #   Audi A4 V (B9) -> Универсал 5 дв.
    # Зачем:
    #   модификация всегда относится к конкретной конфигурации
    configuration = models.ForeignKey(
        Configuration,
        on_delete=models.CASCADE,
        related_name="modifications",
        verbose_name=_("конфигурация"),
    )

    # source_id:
    #   внешний ID модификации
    # Пример:
    #   "20637615__20674985"
    # Зачем:
    #   основной ключ для импорта из внешнего каталога
    source_id = models.CharField(_("source id"), max_length=128, unique=True, db_index=True)

    # name:
    #   название модификации
    # Пример:
    #   "2.0d MT (150 л.с.)"
    # Зачем:
    #   главное текстовое имя конкретной версии авто
    name = models.CharField(_("название"), max_length=255, db_index=True)

    # group_name:
    #   название комплектации / группы
    # Пример:
    #   "High-Tech", "Standard Edition"
    # Зачем:
    #   маркетинговая группировка модификаций
    group_name = models.CharField(_("группа / комплектация"), max_length=255, blank=True, db_index=True)

    # is_closed:
    #   закрыта/снята/недоступна ли модификация
    # Пример:
    #   True / False / None
    # Зачем:
    #   важно для бизнес-логики витрины
    is_closed = models.BooleanField(_("закрыта"), null=True, blank=True)

    # price_from:
    #   минимальная цена модификации
    # Пример:
    #   12500000
    # Зачем:
    #   фильтр и отображение цены
    price_from = models.BigIntegerField(_("цена от"), null=True, blank=True)

    # price_to:
    #   максимальная цена модификации
    # Пример:
    #   13800000
    # Зачем:
    #   диапазон цены в каталоге
    price_to = models.BigIntegerField(_("цена до"), null=True, blank=True)

    class Meta:
        verbose_name = _("модификация")
        verbose_name_plural = _("модификации")
        ordering = (
            "configuration__generation__model__mark__name",
            "configuration__generation__model__name",
            "configuration__name",
            "name",
            "source_id",
        )
        indexes = [
            models.Index(fields=["configuration", "name"], name="cars_modif_config_name_idx"),
            models.Index(fields=["group_name"], name="cars_modif_group_name_idx"),
            models.Index(fields=["is_closed"], name="cars_modif_closed_idx"),
            models.Index(fields=["price_from", "price_to"], name="cars_modif_prices_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.configuration.generation.model.mark.name} {self.configuration.generation.model.name} — {self.name}"

    @property
    def full_title(self) -> str:
        # Полный удобный заголовок для UI / логов / отладки
        parts = [
            self.configuration.generation.model.mark.name,
            self.configuration.generation.model.name,
            self.configuration.generation.display_name,
            self.configuration.name,
            self.name,
        ]
        return " | ".join(part for part in parts if part)

    @property
    def mark(self) -> Mark:
        # Удобный доступ к марке без ручного прохода по всей цепочке
        return self.configuration.generation.model.mark

    @property
    def car_model(self) -> CarModel:
        # Удобный доступ к модели
        return self.configuration.generation.model

    @property
    def generation(self) -> Generation:
        # Удобный доступ к поколению
        return self.configuration.generation

    @property
    def body_type_object(self) -> BodyType | None:
        # Удобный доступ к кузову
        return self.configuration.body_type

    @property
    def photo(self):
        return getattr(self.configuration, "photo", None)


# ============================================================
# media assets
# ============================================================


class ConfigurationPhoto(TimestampedModel):
    configuration = models.OneToOneField(
        Configuration,
        on_delete=models.CASCADE,
        related_name="photo",
        verbose_name=_("конфигурация"),
    )

    image = models.ImageField(
        _("изображение"),
        upload_to="cars/configuration_photos/",
    )

    source_file_name = models.CharField(
        _("имя исходного файла"),
        max_length=255,
        blank=True,
        db_index=True,
    )

    source_configuration_id = models.CharField(
        _("source configuration id"),
        max_length=64,
        blank=True,
        db_index=True,
    )

    alt_text = models.CharField(
        _("alt текст"),
        max_length=255,
        blank=True,
    )

    is_main = models.BooleanField(
        _("главное фото"),
        default=True,
    )

    sort_order = models.PositiveIntegerField(
        _("порядок сортировки"),
        default=0,
    )

    class Meta:
        verbose_name = _("фото конфигурации")
        verbose_name_plural = _("фото конфигураций")
        ordering = ("sort_order", "id")
        indexes = [
            models.Index(fields=["source_configuration_id"], name="cars_cfgphoto_src_cfg_idx"),
            models.Index(fields=["is_main", "sort_order"], name="cars_cfgphoto_main_sort_idx"),
        ]

    def __str__(self) -> str:
        return f"Фото: {self.configuration}"

    @property
    def image_url(self) -> str:
        if self.image:
            return self.image.url
        return ""


class MarkLogo(TimestampedModel):
    mark = models.OneToOneField(
        Mark,
        on_delete=models.CASCADE,
        related_name="logo",
        verbose_name=_("марка"),
    )

    image = models.ImageField(
        _("логотип"),
        upload_to="cars/mark_logos/",
    )

    source_file_name = models.CharField(
        _("имя исходного файла"),
        max_length=255,
        blank=True,
        db_index=True,
    )

    source_mark_id = models.CharField(
        _("source mark id"),
        max_length=64,
        blank=True,
        db_index=True,
    )

    alt_text = models.CharField(
        _("alt текст"),
        max_length=255,
        blank=True,
    )

    is_active = models.BooleanField(
        _("активен"),
        default=True,
    )

    class Meta:
        verbose_name = _("логотип марки")
        verbose_name_plural = _("логотипы марок")
        ordering = ("mark__name",)
        indexes = [
            models.Index(fields=["source_mark_id"], name="cars_marklogo_src_mark_idx"),
            models.Index(fields=["is_active"], name="cars_marklogo_active_idx"),
        ]

    def __str__(self) -> str:
        return f"Логотип: {self.mark.name}"

    @property
    def image_url(self) -> str:
        if self.image:
            return self.image.url
        return ""


# ============================================================
# specifications
# ============================================================


class ModificationSpecification(TimestampedModel):
    # modification:
    #   связь 1-к-1 с модификацией
    # Пример:
    #   для одной модификации есть одна запись нормализованных характеристик
    # Зачем:
    #   отделяет широкий блок характеристик от основной сущности Modification
    modification = models.OneToOneField(
        Modification,
        on_delete=models.CASCADE,
        related_name="specification",
        verbose_name=_("модификация"),
    )

    # --------------------------------------------------------
    # general classification
    # --------------------------------------------------------

    # auto_class:
    #   класс автомобиля
    # Пример:
    #   "C", "D", "J"
    # Зачем:
    #   фильтр и классификация
    auto_class = models.CharField(
        _("класс авто"),
        max_length=16,
        choices=VehicleClass.choices,
        default=VehicleClass.UNKNOWN,
        db_index=True,
    )

    # auto_class_raw:
    #   исходное значение класса из источника
    # Пример:
    #   "D"
    # Зачем:
    #   не терять оригинал
    auto_class_raw = models.CharField(_("класс авто (raw)"), max_length=10, blank=True)

    # steering_wheel_position:
    #   положение руля
    # Пример:
    #   LEFT, RIGHT
    # Зачем:
    #   фильтр и карточка авто
    steering_wheel_position = models.CharField(
        _("положение руля"),
        max_length=20,
        choices=SteeringWheelPosition.choices,
        default=SteeringWheelPosition.UNKNOWN,
        db_index=True,
    )

    # steering_wheel_position_raw:
    #   исходная строка из источника
    # Пример:
    #   "Левый"
    # Зачем:
    #   сохранить оригинальное значение
    steering_wheel_position_raw = models.CharField(_("положение руля (raw)"), max_length=50, blank=True)

    # --------------------------------------------------------
    # body and dimensions
    # --------------------------------------------------------

    # body_size_raw:
    #   сырая строка габаритов кузова
    # Пример:
    #   "4725x1842x1434"
    # Зачем:
    #   хранить оригинальное представление
    body_size_raw = models.CharField(_("размер кузова (raw)"), max_length=255, blank=True)

    # length_mm:
    #   длина автомобиля в миллиметрах
    # Пример:
    #   4725
    # Зачем:
    #   фильтры, сравнение, отображение
    length_mm = models.PositiveIntegerField(_("длина, мм"), null=True, blank=True)

    # width_mm:
    #   ширина автомобиля в миллиметрах
    # Пример:
    #   1842
    # Зачем:
    #   характеристика кузова
    width_mm = models.PositiveIntegerField(_("ширина, мм"), null=True, blank=True)

    # height_mm:
    #   высота автомобиля в миллиметрах
    # Пример:
    #   1434
    # Зачем:
    #   характеристика кузова
    height_mm = models.PositiveIntegerField(_("высота, мм"), null=True, blank=True)

    # wheelbase_mm:
    #   колёсная база
    # Пример:
    #   2820
    # Зачем:
    #   важная характеристика шасси и размеров
    wheelbase_mm = models.PositiveIntegerField(_("колёсная база, мм"), null=True, blank=True)

    # ground_clearance_mm:
    #   клиренс / дорожный просвет
    # Пример:
    #   140
    # Зачем:
    #   фильтрация и тех. описание
    ground_clearance_mm = models.PositiveIntegerField(_("клиренс, мм"), null=True, blank=True)

    # front_track_mm:
    #   передняя колея
    # Пример:
    #   1572
    # Зачем:
    #   тех. характеристика ходовой
    front_track_mm = models.PositiveIntegerField(_("передняя колея, мм"), null=True, blank=True)

    # rear_track_mm:
    #   задняя колея
    # Пример:
    #   1555
    # Зачем:
    #   тех. характеристика ходовой
    rear_track_mm = models.PositiveIntegerField(_("задняя колея, мм"), null=True, blank=True)

    # doors_count:
    #   количество дверей
    # Пример:
    #   4, 5
    # Зачем:
    #   фильтр и описание кузова
    doors_count = models.PositiveSmallIntegerField(_("количество дверей"), null=True, blank=True)

    # seats_count:
    #   количество мест
    # Пример:
    #   5, 7
    # Зачем:
    #   фильтр и описание салона
    seats_count = models.PositiveSmallIntegerField(_("количество мест"), null=True, blank=True)

    # origin_tires_size_raw:
    #   исходные размеры штатных шин
    # Пример:
    #   "225/50 R17, 245/40 R18"
    # Зачем:
    #   хранение сложного значения без потери
    origin_tires_size_raw = models.TextField(_("размер штатных шин (raw)"), blank=True)

    # landing_wheels_size_raw:
    #   посадочный размер колёс / параметры крепления
    # Пример:
    #   "DIA66.5 5x112"
    # Зачем:
    #   тех. информация по колёсам
    landing_wheels_size_raw = models.TextField(_("посадочный размер колёс (raw)"), blank=True)

    # disk_size_raw:
    #   размер дисков
    # Пример:
    #   "7.5x17 ET38"
    # Зачем:
    #   тех. информация по дискам
    disk_size_raw = models.TextField(_("размер дисков (raw)"), blank=True)

    # wheel_size_raw:
    #   обобщённое raw-поле по размеру колёс
    # Пример:
    #   "205/60/R16"
    # Зачем:
    #   сохранить оригинальное значение из альтернативных источников
    wheel_size_raw = models.TextField(_("wheel size (raw)"), blank=True)

    # boot_volume_raw:
    #   сырой объём багажника
    # Пример:
    #   "505/1510"
    # Зачем:
    #   не терять исходную строку
    boot_volume_raw = models.CharField(_("объём багажника (raw)"), max_length=255, blank=True)

    # trunk_volume_min_l:
    #   минимальный объём багажника
    # Пример:
    #   505
    # Зачем:
    #   фильтр и карточка машины
    trunk_volume_min_l = models.PositiveIntegerField(_("объём багажника min, л"), null=True, blank=True)

    # trunk_volume_max_l:
    #   максимальный объём багажника
    # Пример:
    #   1510
    # Зачем:
    #   тех. описание трансформации багажного отсека
    trunk_volume_max_l = models.PositiveIntegerField(_("объём багажника max, л"), null=True, blank=True)

    # fuel_tank_volume_l:
    #   объём топливного бака в литрах
    # Пример:
    #   54
    # Зачем:
    #   тех. характеристика
    fuel_tank_volume_l = models.DecimalField(
        _("объём бака, л"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # curb_weight_kg:
    #   масса автомобиля
    # Пример:
    #   1475
    # Зачем:
    #   тех. характеристика
    curb_weight_kg = models.PositiveIntegerField(_("масса, кг"), null=True, blank=True)

    # gross_weight_kg:
    #   полная масса
    # Пример:
    #   2095
    # Зачем:
    #   тех. характеристика
    gross_weight_kg = models.PositiveIntegerField(_("полная масса, кг"), null=True, blank=True)

    # --------------------------------------------------------
    # transmission and drive
    # --------------------------------------------------------

    # transmission_type:
    #   тип коробки передач
    # Пример:
    #   AUTOMATIC, MANUAL
    # Зачем:
    #   один из главных фильтров каталога
    transmission_type = models.CharField(
        _("тип трансмиссии"),
        max_length=20,
        choices=TransmissionType.choices,
        default=TransmissionType.UNKNOWN,
        db_index=True,
    )

    # transmission_type_raw:
    #   исходное строковое значение коробки
    # Пример:
    #   "Автомат"
    # Зачем:
    #   не терять оригинал источника
    transmission_type_raw = models.CharField(_("тип трансмиссии (raw)"), max_length=50, blank=True)

    # gears_count:
    #   количество передач
    # Пример:
    #   6, 8
    # Зачем:
    #   дополнительная характеристика коробки
    gears_count = models.PositiveSmallIntegerField(_("количество передач"), null=True, blank=True)

    # drive_type:
    #   тип привода
    # Пример:
    #   FRONT, REAR, ALL_WHEEL
    # Зачем:
    #   один из ключевых фильтров
    drive_type = models.CharField(
        _("тип привода"),
        max_length=20,
        choices=DriveType.choices,
        default=DriveType.UNKNOWN,
        db_index=True,
    )

    # drive_type_raw:
    #   исходная строка привода
    # Пример:
    #   "Передний"
    # Зачем:
    #   сохранить оригинальное значение
    drive_type_raw = models.CharField(_("тип привода (raw)"), max_length=50, blank=True)

    # transmission_code:
    #   технический код коробки
    # Пример:
    #   "AUTOMATIC"
    # Зачем:
    #   хранить машинно-ориентированное значение источника
    transmission_code = models.CharField(
        _("код трансмиссии"),
        max_length=20,
        choices=TransmissionCode.choices,
        default=TransmissionCode.UNKNOWN,
        db_index=True,
    )

    # transmission_code_raw:
    #   raw-значение технического кода
    # Пример:
    #   "AUTOMATIC"
    # Зачем:
    #   не терять оригинал
    transmission_code_raw = models.CharField(_("код трансмиссии (raw)"), max_length=50, blank=True)

    # --------------------------------------------------------
    # suspension and brakes
    # --------------------------------------------------------

    # front_suspension_type:
    #   тип передней подвески
    # Пример:
    #   INDEPENDENT_SPRING
    # Зачем:
    #   тех. описание
    front_suspension_type = models.CharField(
        _("передняя подвеска"),
        max_length=40,
        choices=SuspensionType.choices,
        default=SuspensionType.UNKNOWN,
    )

    # front_suspension_type_raw:
    #   исходное значение передней подвески
    # Пример:
    #   "Независимая, пружинная"
    # Зачем:
    #   сохранить оригинал
    front_suspension_type_raw = models.CharField(_("передняя подвеска (raw)"), max_length=255, blank=True)

    # rear_suspension_type:
    #   тип задней подвески
    # Пример:
    #   SEMI_INDEPENDENT_TORSION
    # Зачем:
    #   тех. описание
    rear_suspension_type = models.CharField(
        _("задняя подвеска"),
        max_length=40,
        choices=SuspensionType.choices,
        default=SuspensionType.UNKNOWN,
    )

    # rear_suspension_type_raw:
    #   исходное значение задней подвески
    # Пример:
    #   "Полунезависимая, торсионная"
    # Зачем:
    #   сохранить оригинал
    rear_suspension_type_raw = models.CharField(_("задняя подвеска (raw)"), max_length=255, blank=True)

    # front_brake_type:
    #   тип передних тормозов
    # Пример:
    #   VENTILATED_DISC
    # Зачем:
    #   тех. описание
    front_brake_type = models.CharField(
        _("передние тормоза"),
        max_length=30,
        choices=BrakeType.choices,
        default=BrakeType.UNKNOWN,
    )

    # front_brake_type_raw:
    #   исходная строка передних тормозов
    # Пример:
    #   "Дисковые вентилируемые"
    # Зачем:
    #   сохранить оригинал
    front_brake_type_raw = models.CharField(_("передние тормоза (raw)"), max_length=255, blank=True)

    # rear_brake_type:
    #   тип задних тормозов
    # Пример:
    #   DISC, DRUM
    # Зачем:
    #   тех. описание
    rear_brake_type = models.CharField(
        _("задние тормоза"),
        max_length=30,
        choices=BrakeType.choices,
        default=BrakeType.UNKNOWN,
    )

    # rear_brake_type_raw:
    #   исходная строка задних тормозов
    # Пример:
    #   "Дисковые"
    # Зачем:
    #   сохранить оригинал
    rear_brake_type_raw = models.CharField(_("задние тормоза (raw)"), max_length=255, blank=True)

    # --------------------------------------------------------
    # performance and consumption
    # --------------------------------------------------------

    # max_speed_kmh:
    #   максимальная скорость в км/ч
    # Пример:
    #   215
    # Зачем:
    #   тех. характеристика, фильтр, сравнение
    max_speed_kmh = models.PositiveIntegerField(_("максимальная скорость, км/ч"), null=True, blank=True)

    # acceleration_0_to_100_sec:
    #   разгон до 100 км/ч в секундах
    # Пример:
    #   9.2
    # Зачем:
    #   динамическая характеристика
    acceleration_0_to_100_sec = models.DecimalField(
        _("разгон 0-100, сек"),
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # consumption_raw:
    #   сырая строка расхода топлива
    # Пример:
    #   "4.8/3.8/4.0"
    # Зачем:
    #   хранить оригинальное представление
    consumption_raw = models.CharField(_("расход (raw)"), max_length=255, blank=True)

    # consumption_city_l_100km:
    #   расход в городе
    # Пример:
    #   4.8
    # Зачем:
    #   фильтр и карточка характеристик
    consumption_city_l_100km = models.DecimalField(
        _("расход в городе, л/100км"),
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # consumption_highway_l_100km:
    #   расход на трассе
    # Пример:
    #   3.8
    # Зачем:
    #   тех. характеристика
    consumption_highway_l_100km = models.DecimalField(
        _("расход на трассе, л/100км"),
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # consumption_mixed_l_100km:
    #   смешанный расход
    # Пример:
    #   4.0
    # Зачем:
    #   удобная агрегированная характеристика
    consumption_mixed_l_100km = models.DecimalField(
        _("смешанный расход, л/100км"),
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # electric_consumption_kwh_100km:
    #   расход электроэнергии на 100 км
    # Пример:
    #   12.8
    # Зачем:
    #   для EV и гибридов
    electric_consumption_kwh_100km = models.DecimalField(
        _("расход электроэнергии, кВт⋅ч/100км"),
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # co2_emission_g_km:
    #   выбросы CO2
    # Пример:
    #   104
    # Зачем:
    #   тех. и экологическая характеристика
    co2_emission_g_km = models.DecimalField(
        _("выбросы CO₂, г/км"),
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # fuel_type:
    #   тип топлива
    # Пример:
    #   AI_95, DIESEL
    # Зачем:
    #   важный фильтр
    fuel_type = models.CharField(
        _("тип топлива"),
        max_length=20,
        choices=FuelType.choices,
        default=FuelType.UNKNOWN,
        db_index=True,
    )

    # fuel_type_raw:
    #   исходная строка топлива
    # Пример:
    #   "АИ-95"
    # Зачем:
    #   не терять оригинал
    fuel_type_raw = models.CharField(_("тип топлива (raw)"), max_length=100, blank=True)

    # emission_standard:
    #   экологический стандарт
    # Пример:
    #   EURO_5, EURO_6
    # Зачем:
    #   экология, тех. фильтр
    emission_standard = models.CharField(
        _("экологический стандарт"),
        max_length=20,
        choices=EmissionEuroClass.choices,
        default=EmissionEuroClass.UNKNOWN,
    )

    # emission_standard_raw:
    #   исходная строка стандарта
    # Пример:
    #   "Euro 6"
    # Зачем:
    #   сохранить оригинал
    emission_standard_raw = models.CharField(_("экологический стандарт (raw)"), max_length=50, blank=True)

    # consumption_calc_type:
    #   стандарт расчёта расхода/запаса хода
    # Пример:
    #   WLTP, NEDC
    # Зачем:
    #   особенно важно для EV
    consumption_calc_type = models.CharField(
        _("методика расчёта расхода"),
        max_length=20,
        choices=ConsumptionCalcType.choices,
        default=ConsumptionCalcType.UNKNOWN,
    )

    # consumption_calc_type_raw:
    #   исходная строка методики
    # Пример:
    #   "WLTP"
    # Зачем:
    #   сохранить оригинал
    consumption_calc_type_raw = models.CharField(_("методика расчёта расхода (raw)"), max_length=50, blank=True)

    # --------------------------------------------------------
    # engine
    # --------------------------------------------------------

    # powertrain_type:
    #   общий тип силовой установки
    # Пример:
    #   PETROL, DIESEL, ELECTRIC
    # Зачем:
    #   один из самых важных фильтров
    powertrain_type = models.CharField(
        _("тип силовой установки"),
        max_length=20,
        choices=PowertrainType.choices,
        default=PowertrainType.UNKNOWN,
        db_index=True,
    )

    # powertrain_type_raw:
    #   исходная строка типа силовой установки
    # Пример:
    #   "Бензиновый"
    # Зачем:
    #   сохранить оригинал
    powertrain_type_raw = models.CharField(_("тип силовой установки (raw)"), max_length=100, blank=True)

    # engine_position_layout:
    #   расположение двигателя
    # Пример:
    #   "Переднее, продольное"
    # Зачем:
    #   тех. характеристика компоновки автомобиля
    engine_position_layout = models.CharField(_("расположение двигателя"), max_length=100, blank=True)

    # displacement_cc:
    #   рабочий объём двигателя в куб. см
    # Пример:
    #   1998
    # Зачем:
    #   фильтр и характеристика двигателя
    displacement_cc = models.PositiveIntegerField(_("объём двигателя, см³"), null=True, blank=True, db_index=True)

    # aspiration_type:
    #   тип наддува
    # Пример:
    #   TURBO, NONE
    # Зачем:
    #   описание двигателя
    aspiration_type = models.CharField(
        _("тип наддува"),
        max_length=20,
        choices=AspirationType.choices,
        default=AspirationType.UNKNOWN,
    )

    # aspiration_type_raw:
    #   исходная строка наддува
    # Пример:
    #   "Турбонаддув"
    # Зачем:
    #   сохранить оригинал
    aspiration_type_raw = models.CharField(_("тип наддува (raw)"), max_length=100, blank=True)

    # max_power_raw:
    #   сырая строка мощности
    # Пример:
    #   "150 л.с. (110 кВт) при 4200 об/мин"
    # Зачем:
    #   не терять оригинальный формат
    max_power_raw = models.CharField(_("мощность (raw)"), max_length=255, blank=True)

    # horse_power_hp:
    #   мощность в лошадиных силах
    # Пример:
    #   150
    # Зачем:
    #   фильтрация и числовое сравнение
    horse_power_hp = models.PositiveIntegerField(_("мощность, л.с."), null=True, blank=True, db_index=True)

    # power_kw:
    #   мощность в киловаттах
    # Пример:
    #   110
    # Зачем:
    #   стандартная тех. характеристика, особенно для EV
    power_kw = models.DecimalField(_("мощность, кВт"), max_digits=8, decimal_places=2, null=True, blank=True)

    # power_rpm_raw:
    #   обороты мощности в raw-виде
    # Пример:
    #   "4200"
    # Зачем:
    #   сохранить исходную информацию
    power_rpm_raw = models.CharField(_("обороты мощности (raw)"), max_length=100, blank=True)

    # torque_raw:
    #   сырая строка момента
    # Пример:
    #   "320 Н⋅м при 3250 об/мин"
    # Зачем:
    #   сохранить оригинальное представление
    torque_raw = models.CharField(_("крутящий момент (raw)"), max_length=255, blank=True)

    # torque_nm:
    #   крутящий момент в Н·м
    # Пример:
    #   320
    # Зачем:
    #   числовая фильтрация и сравнение
    torque_nm = models.PositiveIntegerField(_("крутящий момент, Н⋅м"), null=True, blank=True)

    # torque_rpm_raw:
    #   обороты момента raw
    # Пример:
    #   "3250"
    # Зачем:
    #   сохранить оригинальную информацию
    torque_rpm_raw = models.CharField(_("обороты момента (raw)"), max_length=100, blank=True)

    # cylinders_layout:
    #   компоновка цилиндров
    # Пример:
    #   INLINE, V
    # Зачем:
    #   тех. описание двигателя
    cylinders_layout = models.CharField(
        _("расположение цилиндров"),
        max_length=20,
        choices=CylindersLayout.choices,
        default=CylindersLayout.UNKNOWN,
    )

    # cylinders_layout_raw:
    #   исходная строка
    # Пример:
    #   "Рядное"
    # Зачем:
    #   сохранить оригинал
    cylinders_layout_raw = models.CharField(_("расположение цилиндров (raw)"), max_length=100, blank=True)

    # cylinders_count:
    #   количество цилиндров
    # Пример:
    #   4, 6, 8
    # Зачем:
    #   числовая характеристика двигателя
    cylinders_count = models.PositiveSmallIntegerField(_("количество цилиндров"), null=True, blank=True)

    # valves_count:
    #   количество клапанов
    # Пример:
    #   8, 16, 24
    # Зачем:
    #   тех. характеристика двигателя
    valves_count = models.PositiveSmallIntegerField(_("количество клапанов"), null=True, blank=True)

    # fuel_injection_type:
    #   тип впрыска / подачи топлива
    # Пример:
    #   DIRECT_INJECTION, COMMON_RAIL
    # Зачем:
    #   тех. детализация двигателя
    fuel_injection_type = models.CharField(
        _("тип впрыска"),
        max_length=30,
        choices=FuelInjectionType.choices,
        default=FuelInjectionType.UNKNOWN,
    )

    # fuel_injection_type_raw:
    #   исходная строка впрыска
    # Пример:
    #   "Непосредственный впрыск (прямой)"
    # Зачем:
    #   сохранить оригинал
    fuel_injection_type_raw = models.CharField(_("тип впрыска (raw)"), max_length=255, blank=True)

    # compression_ratio:
    #   степень сжатия
    # Пример:
    #   16.2
    # Зачем:
    #   тех. характеристика двигателя
    compression_ratio = models.DecimalField(
        _("степень сжатия"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # diameter_raw:
    #   сырая строка bore x stroke
    # Пример:
    #   "81.0x95.5"
    # Зачем:
    #   сохранить оригинальное представление
    diameter_raw = models.CharField(_("diameter (raw)"), max_length=100, blank=True)

    # cylinder_bore_mm:
    #   диаметр цилиндра в мм
    # Пример:
    #   81.0
    # Зачем:
    #   parsed-значение из diameter
    cylinder_bore_mm = models.DecimalField(_("диаметр цилиндра, мм"), max_digits=8, decimal_places=2, null=True, blank=True)

    # piston_stroke_mm:
    #   ход поршня в мм
    # Пример:
    #   95.5
    # Зачем:
    #   parsed-значение из diameter или отдельного поля
    piston_stroke_mm = models.DecimalField(_("ход поршня, мм"), max_digits=8, decimal_places=2, null=True, blank=True)

    # engine_code:
    #   основной код двигателя
    # Пример:
    #   "B47D20", "G4KN"
    # Зачем:
    #   важная справочная и поисковая характеристика
    engine_code = models.CharField(_("код двигателя"), max_length=255, blank=True, db_index=True)

    # engine_code_secondary:
    #   дополнительный код двигателя
    # Пример:
    #   альтернативный код или второе значение из источника
    # Зачем:
    #   сохранить доп. идентификатор
    engine_code_secondary = models.CharField(_("код двигателя 2"), max_length=255, blank=True)

    # valvetrain_type:
    #   тип ГРМ
    # Пример:
    #   DOHC, SOHC
    # Зачем:
    #   тех. характеристика двигателя
    valvetrain_type = models.CharField(
        _("тип ГРМ"),
        max_length=20,
        choices=ValvetrainType.choices,
        default=ValvetrainType.UNKNOWN,
    )

    # valvetrain_type_raw:
    #   исходная строка типа ГРМ
    # Пример:
    #   "DOHC"
    # Зачем:
    #   сохранить оригинал
    valvetrain_type_raw = models.CharField(_("тип ГРМ (raw)"), max_length=50, blank=True)

    # --------------------------------------------------------
    # EV and battery
    # --------------------------------------------------------

    # battery_capacity_kwh:
    #   общая ёмкость батареи
    # Пример:
    #   53.6
    # Зачем:
    #   ключевая характеристика EV
    battery_capacity_kwh = models.DecimalField(
        _("ёмкость батареи, кВт⋅ч"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
    )

    # battery_capacity_usable_kwh:
    #   полезная ёмкость батареи
    # Пример:
    #   50.2
    # Зачем:
    #   более точная характеристика батареи
    battery_capacity_usable_kwh = models.DecimalField(
        _("полезная ёмкость батареи, кВт⋅ч"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # battery_type:
    #   химический тип батареи
    # Пример:
    #   LFP, LI_ION
    # Зачем:
    #   характеристика EV/гибрида
    battery_type = models.CharField(
        _("тип батареи"),
        max_length=20,
        choices=EvBatteryType.choices,
        default=EvBatteryType.UNKNOWN,
    )

    # battery_type_raw:
    #   исходная строка типа батареи
    # Пример:
    #   "Литий-железо-фосфатная (LFP)"
    # Зачем:
    #   сохранить оригинал
    battery_type_raw = models.CharField(_("тип батареи (raw)"), max_length=255, blank=True)

    # electric_range_km:
    #   запас хода в км
    # Пример:
    #   418
    # Зачем:
    #   один из главных фильтров для EV
    electric_range_km = models.PositiveIntegerField(_("запас хода, км"), null=True, blank=True, db_index=True)

    # ac_charge_time_raw:
    #   время обычной зарядки raw
    # Пример:
    #   "7.0"
    # Зачем:
    #   сохранить значение как пришло
    ac_charge_time_raw = models.CharField(_("время AC-зарядки (raw)"), max_length=255, blank=True)

    # dc_fast_charge_time_raw:
    #   время быстрой зарядки raw
    # Пример:
    #   "30"
    # Зачем:
    #   сохранить значение как пришло
    dc_fast_charge_time_raw = models.CharField(_("время быстрой DC-зарядки (raw)"), max_length=255, blank=True)

    # quickcharge_description:
    #   текстовое описание быстрой зарядки
    # Пример:
    #   "30 минут от 30% до 80%"
    # Зачем:
    #   удобно для карточки EV
    quickcharge_description = models.TextField(_("описание быстрой зарядки"), blank=True)

    # charging_port_types_raw:
    #   типы зарядных портов raw
    # Пример:
    #   "GB/T AC, GB/T DC"
    # Зачем:
    #   сохранить сложное текстовое значение
    charging_port_types_raw = models.TextField(_("типы зарядных портов (raw)"), blank=True)

    # max_charge_power_kw:
    #   максимальная мощность зарядки
    # Пример:
    #   100
    # Зачем:
    #   характеристика EV
    max_charge_power_kw = models.DecimalField(
        _("максимальная мощность зарядки, кВт"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # battery_charge_cycles:
    #   количество циклов заряда
    # Пример:
    #   1500
    # Зачем:
    #   доп. характеристика батареи
    battery_charge_cycles = models.PositiveIntegerField(_("циклы заряда"), null=True, blank=True)

    # battery_temp_raw:
    #   raw-описание температуры батареи
    # Пример:
    #   "от -20 до +45"
    # Зачем:
    #   сохранить оригинальную информацию, если она есть
    battery_temp_raw = models.CharField(_("температура батареи (raw)"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("характеристики модификации")
        verbose_name_plural = _("характеристики модификаций")
        indexes = [
            models.Index(fields=["auto_class"], name="cars_spec_auto_class_idx"),
            models.Index(fields=["steering_wheel_position"], name="cars_spec_steering_idx"),
            models.Index(fields=["transmission_type"], name="cars_spec_transmission_idx"),
            models.Index(fields=["drive_type"], name="cars_spec_drive_idx"),
            models.Index(fields=["powertrain_type"], name="cars_spec_powertrain_type_idx"),
            models.Index(fields=["fuel_type"], name="cars_spec_fuel_type_idx"),
            models.Index(fields=["horse_power_hp"], name="cars_spec_hp_idx"),
            models.Index(fields=["displacement_cc"], name="cars_spec_displacement_idx"),
            models.Index(fields=["electric_range_km"], name="cars_spec_ev_range_idx"),
            models.Index(fields=["battery_capacity_kwh"], name="cars_spec_battery_idx"),
            models.Index(fields=["seats_count"], name="cars_spec_seats_idx"),
            models.Index(fields=["max_speed_kmh"], name="cars_spec_speed_idx"),
        ]

    def __str__(self) -> str:
        return f"Характеристики: {self.modification}"

    @property
    def full_title(self) -> str:
        # Просто делегируем красивый заголовок модификации
        return self.modification.full_title

    @property
    def display_power(self) -> str:
        # Готовое отображение мощности для UI
        if self.horse_power_hp and self.power_kw:
            return f"{self.horse_power_hp} л.с. / {self.power_kw} кВт"
        if self.horse_power_hp:
            return f"{self.horse_power_hp} л.с."
        if self.power_kw:
            return f"{self.power_kw} кВт"
        return self.max_power_raw

    @property
    def display_torque(self) -> str:
        # Готовое отображение момента для UI
        if self.torque_nm:
            return f"{self.torque_nm} Н⋅м"
        return self.torque_raw

    @property
    def display_range(self) -> str:
        # Готовое отображение запаса хода
        if self.electric_range_km:
            return f"{self.electric_range_km} км"
        return ""


class ModificationRawSpecification(TimestampedModel):
    # modification:
    #   связь с конкретной модификацией
    # Зачем:
    #   одна raw-спецификация на одну модификацию
    modification = models.OneToOneField(
        Modification,
        on_delete=models.CASCADE,
        related_name="raw_specification",
        verbose_name=_("модификация"),
    )

    # raw_payload:
    #   полный словарь сырых данных из источника
    # Пример:
    #   {"max_power": "150 л.с. (110 кВт)", "moment": "320 Н⋅м", ...}
    # Зачем:
    #   не потерять ни одно исходное значение
    raw_payload = models.JSONField(_("raw payload"), default=dict, blank=True)

    # unparsed_payload:
    #   значения, которые не удалось корректно распарсить
    # Пример:
    #   {"diameter": "81.0x95.5", "unknown_field": "..."}
    # Зачем:
    #   можно дорабатывать парсер позже
    unparsed_payload = models.JSONField(_("unparsed payload"), default=dict, blank=True)

    # parse_notes:
    #   заметки о проблемах парсинга
    # Пример:
    #   "conflict between displacement and engine_capacity"
    # Зачем:
    #   удобно для дебага и улучшения импорта
    parse_notes = models.TextField(_("заметки парсинга"), blank=True)

    class Meta:
        verbose_name = _("сырые характеристики модификации")
        verbose_name_plural = _("сырые характеристики модификаций")

    def __str__(self) -> str:
        return f"Raw характеристики: {self.modification}"


# ============================================================
# options
# ============================================================


class ModificationOption(TimestampedModel):
    # modification:
    #   у какой модификации хранится значение опции
    # Пример:
    #   Hyundai Tucson 2.5 AT 4WD
    # Зачем:
    #   связать опцию с конкретной машиной
    modification = models.ForeignKey(
        Modification,
        on_delete=models.CASCADE,
        related_name="option_values",
        verbose_name=_("модификация"),
    )

    # option_definition:
    #   какая именно опция
    # Пример:
    #   ABS, Bluetooth, Rear Camera
    # Зачем:
    #   это ссылка на словарь опций
    option_definition = models.ForeignKey(
        OptionDefinition,
        on_delete=models.CASCADE,
        related_name="modification_values",
        verbose_name=_("опция"),
    )

    # value_bool:
    #   значение опции в tri-state формате
    # Пример:
    #   True / False / None
    # Зачем:
    #   True = есть, False = нет, None = неизвестно
    value_bool = models.BooleanField(_("значение"), null=True, blank=True)

    # raw_value:
    #   исходное значение из CSV/SQL
    # Пример:
    #   "1", "0", ""
    # Зачем:
    #   не терять оригинальное значение
    raw_value = models.CharField(_("raw value"), max_length=255, blank=True)

    # source_column:
    #   имя исходной колонки
    # Пример:
    #   "opt_abs", "opt_bluetooth"
    # Зачем:
    #   удобно для отладки импорта
    source_column = models.CharField(_("source column"), max_length=128, blank=True)

    class Meta:
        verbose_name = _("значение опции модификации")
        verbose_name_plural = _("значения опций модификации")
        constraints = [
            # Одна и та же опция не должна дублироваться у одной модификации
            models.UniqueConstraint(
                fields=["modification", "option_definition"],
                name="cars_modoption_modification_option_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["modification"], name="cars_modoption_modif_idx"),
            models.Index(fields=["option_definition"], name="cars_modoption_optdef_idx"),
            models.Index(fields=["option_definition", "value_bool"], name="cars_modoption_opt_val_idx"),
        ]

    def __str__(self) -> str:
        value = "Да" if self.value_bool is True else "Нет" if self.value_bool is False else "Неизвестно"
        return f"{self.modification} — {self.option_definition}: {value}"

    @property
    def display_value(self) -> str:
        # Удобное человекочитаемое значение для UI
        if self.value_bool is True:
            return "Да"
        if self.value_bool is False:
            return "Нет"
        return "Неизвестно"


