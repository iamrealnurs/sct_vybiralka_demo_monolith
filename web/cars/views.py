from __future__ import annotations

import json
import logging

from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from cars.models import (
    CarModel,
    Configuration,
    Generation,
    Mark,
    Modification,
    ModificationSpecification,
)

logger = logging.getLogger(__name__)


# ============================================================
# helpers
# ============================================================

def _clean_str(value: str | None) -> str:
    return (value or "").strip()


def _get_list_param(request, key: str) -> list[str]:
    values = [_clean_str(v) for v in request.GET.getlist(key) if _clean_str(v)]
    logger.debug("GET list param %s=%s", key, values)
    return values


def _get_single_param(request, key: str) -> str:
    value = _clean_str(request.GET.get(key))
    logger.debug("GET single param %s=%s", key, value)
    return value


def _apply_filters(base_qs, *, mark_id: str, model_id: str,
                   generation_ids: list[str], configuration_ids: list[str],
                   engine_types: list[str], drive_types: list[str], transmissions: list[str]):
    """
    Применяет все фильтры к queryset модификаций.
    """

    logger.info(
        "Applying filters: mark_id=%s, model_id=%s, generation_ids=%s, configuration_ids=%s, engine_types=%s, drive_types=%s, transmissions=%s",
        mark_id,
        model_id,
        generation_ids,
        configuration_ids,
        engine_types,
        drive_types,
        transmissions,
    )

    qs = base_qs

    if mark_id:
        qs = qs.filter(configuration__generation__model__mark__id=mark_id)
        logger.debug("Applied mark filter")

    if model_id:
        qs = qs.filter(configuration__generation__model__id=model_id)
        logger.debug("Applied model filter")

    if generation_ids:
        qs = qs.filter(configuration__generation__id__in=generation_ids)
        logger.debug("Applied generation filter")

    if configuration_ids:
        qs = qs.filter(configuration__id__in=configuration_ids)
        logger.debug("Applied configuration filter")

    if engine_types:
        qs = qs.filter(specification__powertrain_type__in=engine_types)
        logger.debug("Applied engine_types filter")

    if drive_types:
        qs = qs.filter(specification__drive_type__in=drive_types)
        logger.debug("Applied drive_types filter")

    if transmissions:
        qs = qs.filter(specification__transmission_type__in=transmissions)
        logger.debug("Applied transmissions filter")

    qs = qs.distinct()

    logger.info("Filtered queryset count=%s", qs.count())
    return qs


def _serialize_modification(modification: Modification) -> dict:
    spec = getattr(modification, "specification", None)
    configuration = modification.configuration
    generation = configuration.generation
    model = generation.model
    mark = model.mark

    return {
        "id": modification.id,
        "source_id": modification.source_id,
        "name": modification.name,
        "group_name": modification.group_name,
        "mark": {
            "id": mark.id,
            "name": mark.name,
            "name": mark.name,
        },
        "model": {
            "id": model.id,
            "name": model.name,
            "name": model.name,
        },
        "generation": {
            "id": generation.id,
            "name": generation.name,
            "year_from": generation.year_from,
            "year_to": generation.year_to,
        },
        "configuration": {
            "id": configuration.id,
            "name": configuration.name,
        },
        "specification": {
            "powertrain_type": spec.powertrain_type if spec else "",
            "drive_type": spec.drive_type if spec else "",
            "transmission_type": spec.transmission_type if spec else "",
            "horse_power_hp": spec.horse_power_hp if spec else None,
            "displacement_cc": spec.displacement_cc if spec else None,
            "fuel_type": spec.fuel_type if spec else "",
        },
    }


def _build_options(filtered_qs):
    """
    Строит опции для всех дропдаунов уже по текущему отфильтрованному набору.
    Это гарантирует зависимость фильтров.
    """

    logger.info("Building filter options")

    marks = (
        Mark.objects.filter(
            car_models__generations__configurations__modifications__in=filtered_qs
        )
        .distinct()
        .order_by("name")
        .values("id", "name")
    )

    models = (
        CarModel.objects.filter(
            generations__configurations__modifications__in=filtered_qs
        )
        .select_related("mark")
        .distinct()
        .order_by("name")
        .values("id", "name", "mark_id")
    )

    generations = (
        Generation.objects.filter(
            configurations__modifications__in=filtered_qs
        )
        .select_related("model", "model__mark")
        .distinct()
        .order_by("year_from", "name")
        .values("id", "name", "year_from", "year_to", "model_id")
    )

    configurations = (
        Configuration.objects.filter(
            modifications__in=filtered_qs
        )
        .select_related("generation", "generation__model", "generation__model__mark")
        .distinct()
        .order_by("name")
        .values("id", "name", "generation_id")
    )

    engine_types = (
        ModificationSpecification.objects.filter(
            modification__in=filtered_qs
        )
        .exclude(powertrain_type="")
        .exclude(powertrain_type__isnull=True)
        .values_list("powertrain_type", flat=True)
        .distinct()
        .order_by("powertrain_type")
    )

    drive_types = (
        ModificationSpecification.objects.filter(
            modification__in=filtered_qs
        )
        .exclude(drive_type="")
        .exclude(drive_type__isnull=True)
        .values_list("drive_type", flat=True)
        .distinct()
        .order_by("drive_type")
    )

    transmissions = (
        ModificationSpecification.objects.filter(
            modification__in=filtered_qs
        )
        .exclude(transmission_type="")
        .exclude(transmission_type__isnull=True)
        .values_list("transmission_type", flat=True)
        .distinct()
        .order_by("transmission_type")
    )

    options_payload = {
        "marks": list(marks),
        "models": list(models),
        "generations": list(generations),
        "configurations": list(configurations),
        "engine_types": list(engine_types),
        "drive_types": list(drive_types),
        "transmissions": list(transmissions),
    }

    logger.info(
        "Options built: marks=%s models=%s generations=%s configurations=%s engine_types=%s drive_types=%s transmissions=%s",
        len(options_payload["marks"]),
        len(options_payload["models"]),
        len(options_payload["generations"]),
        len(options_payload["configurations"]),
        len(options_payload["engine_types"]),
        len(options_payload["drive_types"]),
        len(options_payload["transmissions"]),
    )

    return options_payload


# ============================================================
# views
# ============================================================

@require_GET
def cars_filter_page(request):
    logger.info("Opening cars filter page")
    return render(request, "cars/filter.html", {})


@require_GET
def cars_filter_api(request):
    logger.info("cars_filter_api called")
    logger.debug("Raw request.GET = %s", dict(request.GET))

    mark_id = _get_single_param(request, "mark")
    model_id = _get_single_param(request, "model")

    generation_ids = _get_list_param(request, "generations")
    configuration_ids = _get_list_param(request, "configurations")
    engine_types = _get_list_param(request, "engine_types")
    drive_types = _get_list_param(request, "drive_types")
    transmissions = _get_list_param(request, "transmissions")

    base_qs = (
        Modification.objects.select_related(
            "configuration",
            "configuration__generation",
            "configuration__generation__model",
            "configuration__generation__model__mark",
            "specification",
        )
        .all()
    )

    logger.info("Base queryset count=%s", base_qs.count())

    filtered_qs = _apply_filters(
        base_qs,
        mark_id=mark_id,
        model_id=model_id,
        generation_ids=generation_ids,
        configuration_ids=configuration_ids,
        engine_types=engine_types,
        drive_types=drive_types,
        transmissions=transmissions,
    )

    count = filtered_qs.count()

    results = [_serialize_modification(obj) for obj in filtered_qs[:100]]
    logger.info("Serialized results count=%s", len(results))

    options = _build_options(filtered_qs)

    payload = {
        "ok": True,
        "count": count,
        "results": results,
        "options": options,
        "applied_filters": {
            "mark": mark_id,
            "model": model_id,
            "generations": generation_ids,
            "configurations": configuration_ids,
            "engine_types": engine_types,
            "drive_types": drive_types,
            "transmissions": transmissions,
        },
    }

    logger.debug("cars_filter_api response payload keys=%s", list(payload.keys()))
    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})

