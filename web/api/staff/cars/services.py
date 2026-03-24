from __future__ import annotations

from dataclasses import dataclass
from django.db.models import Count, Q, QuerySet
from django.core.paginator import Paginator, Page
from django.http import QueryDict

from cars.models import Modification, Mark, CarModel, Generation, ModificationOption, OptionCategory
from catalog.models import CarServicePackage

@dataclass(slots=True)
class StaffCarListResult:
    """Результат работы сервиса для передачи в View"""
    page_obj: Page
    kpi: dict[str, int]
    marks: QuerySet[Mark]
    filters: dict[str, any]


def get_staff_car_list_data(params: QueryDict) -> StaffCarListResult:
    """
    Основная бизнес-логика получения списка автомобилей для сотрудников.
    Включает фильтрацию, расчет KPI и пагинацию.
    """
    
    # 1. Формируем базовый QuerySet со всеми оптимизациями
    # Мы используем select_related для всей иерархии и спецификаций
    qs = Modification.objects.select_related(
        'configuration',
        'configuration__generation',
        'configuration__generation__model',
        'configuration__generation__model__mark',
        'specification',
    ).annotate(
        # Считаем общее кол-во пакетов для этой модификации
        total_pkgs=Count(
            'service_packages', 
            filter=Q(service_packages__is_deleted=False), 
            distinct=True
        ),
        # Считаем только опубликованные пакеты
        pub_pkgs=Count(
            'service_packages', 
            filter=Q(service_packages__is_deleted=False, service_packages__status='PUBLISHED'), 
            distinct=True
        )
    )

    # 2. Обработка фильтров из GET-параметров
    # Собираем примененные фильтры для возврата в шаблон
    applied_filters = {
        'mark': params.get('mark', ''),
        'model': params.get('model', ''),
        'generation': params.get('generation', ''),
        'configuration': params.get('configuration', ''),
        'body_type': params.get('body_type', ''),
        'transmission': params.get('transmission', ''),
        'engine_type': params.get('engine_type', ''),
        'drive_type': params.get('drive_type', ''),
        'has_packages': params.get('has_packages') == 'on',
        'q': params.get('q', '').strip(),
    }

    if applied_filters['mark']:
        qs = qs.filter(configuration__generation__model__mark_id=applied_filters['mark'])

    if applied_filters['model']:
        qs = qs.filter(configuration__generation__model_id=applied_filters['model'])

    if applied_filters['generation']:
        qs = qs.filter(configuration__generation_id=applied_filters['generation'])

    if applied_filters['configuration']:
        qs = qs.filter(configuration_id=applied_filters['configuration'])

    if applied_filters['body_type']:
        # Поиск по коду или названию из связанной модели BodyType через Configuration
        qs = qs.filter(configuration__body_type__name__icontains=applied_filters['body_type'])

    if applied_filters['transmission']:
        qs = qs.filter(specification__transmission_type=applied_filters['transmission'])

    if applied_filters['engine_type']:
        qs = qs.filter(specification__powertrain_type=applied_filters['engine_type'])

    if applied_filters['has_packages']:
        qs = qs.filter(total_pkgs__gt=0)

    if applied_filters['drive_type']:
        qs = qs.filter(specification__drive_type=applied_filters['drive_type'])

    if applied_filters['q']:
        query = applied_filters['q']
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(source_id__icontains=query) |
            Q(configuration__generation__model__name__icontains=query) |
            Q(specification__engine_code__icontains=query)
        )

    # 3. Подсчет KPI (статистика по текущей выборке)
    # Выполняем агрегацию по отфильтрованному списку
    kpi = {
        'total_count': qs.count(),
        'with_packages': qs.filter(total_pkgs__gt=0).count(),
        'without_packages': qs.filter(total_pkgs=0).count(),
        'published_packages_total': sum(qs.values_list('pub_pkgs', flat=True)) # Сумма всех опубликованных
    }

    # 4. Сортировка и пагинация
    # Сортируем по иерархии: Марка -> Модель -> Имя модификации
    qs = qs.order_by(
        'configuration__generation__model__mark__name', 
        'configuration__generation__model__name', 
        'name'
    )

    paginator = Paginator(qs, 25)  # По 25 машин на страницу
    page_number = params.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 5. Получаем список марок для выпадающего списка фильтра
    marks = Mark.objects.all().order_by('name')

    return StaffCarListResult(
        page_obj=page_obj,
        kpi=kpi,
        marks=marks,
        filters=applied_filters
    )


def build_car_detail_label(modification: Modification) -> str:
    """
    Вспомогательный метод для формирования красивой строки описания двигателя/привода
    (Используется в ячейке таблицы 'Модификация')
    """
    spec = getattr(modification, 'specification', None)
    if not spec:
        return "Нет технических данных"
    
    parts = []
    if spec.horse_power_hp:
        parts.append(f"{spec.horse_power_hp} л.с.")
    if spec.displacement_cc:
        parts.append(f"{round(spec.displacement_cc/1000, 1)}L")
    if spec.powertrain_type:
        parts.append(spec.get_powertrain_type_display())
        
    return " / ".join(parts)


def get_car_detail_data(source_id: str) -> dict:
    # 1. Получаем модификацию со всеми базовыми связями
    car = Modification.objects.select_related(
        'configuration',
        'configuration__body_type',
        'configuration__generation',
        'configuration__generation__model',
        'configuration__generation__model__mark',
        'specification',
        'raw_specification',
    ).get(source_id=source_id)

    # 2. Получаем пакеты услуг для этого авто
    packages = car.service_packages.filter(is_deleted=False).select_related('category')

    # 3. Получаем опции и группируем их по категориям
    # Сначала берем все активные категории опций
    categories = OptionCategory.objects.filter(is_active=True).order_by('sort_order')
    
    # Берем значения опций для этой машины
    options_values = ModificationOption.objects.filter(
        modification=car
    ).select_related('option_definition', 'option_definition__category')

    # Собираем структуру: Категория -> Список опций со значениями
    grouped_options = []
    for cat in categories:
        cat_options = [opt for opt in options_values if opt.option_definition.category_id == cat.id]
        if cat_options:
            grouped_options.append({
                'category': cat,
                'items': cat_options
            })

    return {
        'car': car,
        'packages': packages,
        'grouped_options': grouped_options,
    }


