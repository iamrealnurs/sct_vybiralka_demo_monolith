from __future__ import annotations

from django.db import transaction
from django.db.models import QuerySet
from client.models import Client, ClientCar
from catalog.models import CarServicePackage, PackageStatus
from cars.models import Modification
from main.models import User


def get_client_primary_car(user: User) -> ClientCar | None:
    # Проверяем, есть ли у User расширение Client
    client_profile = getattr(user, 'client', None)
    if not client_profile:
        return None
        
    return client_profile.cars.filter(is_active=True, is_primary=True).select_related(
        'modification',
        'modification__configuration__generation__model__mark'
    ).first()



def get_client_garage_list(client: Client) -> QuerySet[ClientCar]:
    """
    Возвращает все автомобили в гараже клиента.
    """
    return client.cars.filter(is_active=True).select_related(
        'modification',
        'modification__configuration__generation__model__mark'
    ).order_by('-is_primary', '-created_at')


@transaction.atomic
def set_primary_client_car(client: Client, car_id: int) -> bool:
    """
    Делает выбранный автомобиль основным (is_primary=True).
    Все остальные авто клиента сбрасываются в False.
    """
    # Проверяем, что машина принадлежит именно этому клиенту
    car_to_activate = client.cars.filter(id=car_id).first()
    if not car_to_activate:
        return False

    # Сбрасываем флаг у всех машин клиента
    client.cars.update(is_primary=False)
    
    # Устанавливаем флаг выбранной машине
    car_to_activate.is_primary = True
    car_to_activate.save(update_fields=['is_primary'])
    
    return True


def get_suggested_packages_for_car(car: ClientCar) -> QuerySet[CarServicePackage]:
    """
    Ищет опубликованные пакеты услуг, которые подходят 
    под конкретную модификацию автомобиля клиента.
    """
    if not car or not car.modification:
        return CarServicePackage.objects.none()

    return CarServicePackage.objects.filter(
        modification=car.modification,
        status=PackageStatus.PUBLISHED,
        is_deleted=False
    ).select_related(
        'category', 
        'image_object'
    ).order_by('category__sort_order', 'public_title')




def get_client_dashboard_data(user: User) -> dict:
    primary_car = get_client_primary_car(user)
    suggested_packages = []

    if primary_car:
        suggested_packages = get_suggested_packages_for_car(primary_car)

    return {
        'primary_car': primary_car,
        'suggested_packages': suggested_packages,
        'has_cars': user.cars.exists() if hasattr(user, 'cars') else False,
    }




def build_client_vehicle_label(car: ClientCar) -> str:
    """
    Формирует красивую строку названия авто для клиента.
    Напр: "Toyota Camry (777AAA01)"
    """
    if not car:
        return "Автомобиль не выбран"
    
    mod = car.modification
    brand = mod.configuration.generation.model.mark.name
    model = mod.configuration.generation.model.name
    
    return f"{brand} {model} ({car.license_plate})"


