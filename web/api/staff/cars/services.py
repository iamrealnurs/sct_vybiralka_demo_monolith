from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.core.paginator import Paginator, Page
from django.db.models import (
    Count, Q, QuerySet, Value, CharField, 
    OuterRef, Subquery, IntegerField
)
from django.db.models.functions import Concat, Coalesce, Cast
from django.http import QueryDict

from cars.models import (
    Modification, Mark, CarModel, Generation, 
    ModificationOption, OptionCategory, ModificationSpecification, Configuration
)
from catalog.models import CarServicePackage

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class StaffCarListResult:
    """Результат работы сервиса для передачи в View"""
    page_obj: Page
    kpi: dict[str, int]
    marks: QuerySet[Mark]
    filters: dict[str, Any]
    # Опции для динамических фильтров (зависимых списков)
    filter_options: dict[str, list]


def get_staff_car_list_data(params: QueryDict) -> StaffCarListResult:
    """
    Основная бизнес-логика получения списка автомобилей для сотрудников.
    Включает сложную фильтрацию, расчет зависимых опций фильтра, KPI и пагинацию.
    """
    
    # 1. Сбор параметров из QueryDict
    mark_id = params.get('mark', '')
    model_id = params.get('model', '')
    
    # Обработка списков для множественного выбора
    generation_ids = params.getlist('generations') or params.getlist('generation')
    configuration_ids = params.getlist('configurations') or params.getlist('configuration')
    engine_types = params.getlist('engine_types') or params.getlist('engine_type')
    drive_types = params.getlist('drive_types') or params.getlist('drive_type')
    transmissions = params.getlist('transmissions') or params.getlist('transmission')
    
    q = params.get('q', '').strip()
    has_packages = params.get('has_packages') == 'on' or params.get('has_packages') == '1'
    body_type_query = params.get('body_type', '')

    # 2. Подзапросы для корректного отображения счетчиков в таблице (не ломают фильтрацию)
    pkgs_count_subquery = CarServicePackage.objects.filter(
        modification=OuterRef('pk'),
        is_deleted=False
    ).order_by().values('modification').annotate(cnt=Count('id')).values('cnt')

    published_pkgs_count_subquery = CarServicePackage.objects.filter(
        modification=OuterRef('pk'),
        is_deleted=False,
        status='PUBLISHED'
    ).order_by().values('modification').annotate(cnt=Count('id')).values('cnt')

    # 3. Базовый QuerySet
    qs = Modification.objects.select_related(
        'configuration__generation__model__mark',
        'configuration__body_type',
        'specification',
    ).annotate(
        total_pkgs=Coalesce(Subquery(pkgs_count_subquery, output_field=IntegerField()), 0),
        pub_pkgs=Coalesce(Subquery(published_pkgs_count_subquery, output_field=IntegerField()), 0)
    )

    # 4. Применение фильтрации
    if mark_id:
        qs = qs.filter(configuration__generation__model__mark_id=mark_id)
    if model_id:
        qs = qs.filter(configuration__generation__model_id=model_id)
    if generation_ids:
        qs = qs.filter(configuration__generation_id__in=generation_ids)
    if configuration_ids:
        qs = qs.filter(configuration_id__in=configuration_ids)
    if body_type_query:
        qs = qs.filter(configuration__body_type__name__icontains=body_type_query)
    if transmissions:
        qs = qs.filter(specification__transmission_type__in=transmissions)
    if engine_types:
        qs = qs.filter(specification__powertrain_type__in=engine_types)
    if drive_types:
        qs = qs.filter(specification__drive_type__in=drive_types)
    
    # Фильтр "Только с пакетами" через прямое наличие связей (наиболее надежный метод)
    if has_packages:
        mod_ids_with_packages = CarServicePackage.objects.filter(
            is_deleted=False
        ).values_list('modification_id', flat=True).distinct()
        qs = qs.filter(id__in=mod_ids_with_packages)

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(source_id__icontains=q) |
            Q(configuration__generation__model__name__icontains=q) |
            Q(specification__engine_code__icontains=q)
        )

    # 5. Подсчет KPI на основе отфильтрованного QuerySet
    total_count = qs.count()
    # Считаем сколько из отфильтрованных авто имеют пакеты (на случай если применены другие фильтры)
    with_pkgs_count = qs.filter(total_pkgs__gt=0).count()
    
    kpi = {
        'total_count': total_count,
        'with_packages': with_pkgs_count,
        'without_packages': total_count - with_pkgs_count,
        'published_packages_total': sum(qs.values_list('pub_pkgs', flat=True))
    }

    # 6. Формирование зависимых опций для фильтров
    filter_options = {
        "marks": list(Mark.objects.all().order_by("name").values("id", "name")),
        
        "models": list(CarModel.objects.filter(
            generations__configurations__modifications__in=qs
        ).distinct().order_by("name").values("id", "name", "mark_id")),

        "generations": list(Generation.objects.filter(
            configurations__modifications__in=qs
        ).distinct().order_by("year_from").annotate(
            annotated_display_name=Concat(
                Coalesce('name', Value(''), output_field=CharField()),
                Value(' ('),
                Coalesce(Cast('year_from', CharField()), Value('?')),
                Value('-'),
                Coalesce(Cast('year_to', CharField()), Value('?')),
                Value(')'),
                output_field=CharField()
            )
        ).values("id", "name", "year_from", "year_to", "model_id", "annotated_display_name")),

        "configurations": list(Configuration.objects.filter(
            modifications__in=qs
        ).distinct().order_by("name").values("id", "name", "generation_id")),
        
        "engine_types": list(ModificationSpecification.objects.filter(
            modification__in=qs
        ).exclude(powertrain_type="").values_list("powertrain_type", flat=True).distinct().order_by("powertrain_type")),
        
        "drive_types": list(ModificationSpecification.objects.filter(
            modification__in=qs
        ).exclude(drive_type="").values_list("drive_type", flat=True).distinct().order_by("drive_type")),
        
        "transmissions": list(ModificationSpecification.objects.filter(
            modification__in=qs
        ).exclude(transmission_type="").values_list("transmission_type", flat=True).distinct().order_by("transmission_type")),
    }

    # 7. Сортировка и пагинация
    qs = qs.order_by(
        'configuration__generation__model__mark__name', 
        'configuration__generation__model__name', 
        'name'
    )

    paginator = Paginator(qs, 25)
    page_number = params.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 8. Сбор примененных фильтров для возврата
    applied_filters = {k: v for k, v in params.items() if v}

    return StaffCarListResult(
        page_obj=page_obj,
        kpi=kpi,
        marks=Mark.objects.all().order_by('name'),
        filters=applied_filters,
        filter_options=filter_options
    )


def build_car_detail_label(modification: Modification) -> str:
    """Вспомогательный метод для формирования красивой строки описания двигателя/привода."""
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
    """Получение полной детальной информации об автомобиле (модификации)."""
    car = Modification.objects.select_related(
        'configuration',
        'configuration__body_type',
        'configuration__generation',
        'configuration__generation__model',
        'configuration__generation__model__mark',
        'specification',
        'raw_specification',
    ).get(source_id=source_id)

    packages = car.service_packages.filter(is_deleted=False).select_related('category')
    categories = OptionCategory.objects.filter(is_active=True).order_by('sort_order')
    
    options_values = ModificationOption.objects.filter(
        modification=car
    ).select_related('option_definition', 'option_definition__category')

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