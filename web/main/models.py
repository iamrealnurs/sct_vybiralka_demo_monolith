from typing import TypeVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager

UserType = TypeVar('UserType', bound='User')


class User(AbstractUser):
    username = None  # type: ignore
    email = models.EmailField(_('Email address'), unique=True)

    USERNAME_FIELD: str = 'email'
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()  # type: ignore

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return super().get_full_name()


# ============================================================
# abstract models
# ============================================================


class TimestampedModel(models.Model):
    # created_at:
    #   когда запись была создана в БД
    # Пример:
    #   2026-03-19 12:34:56
    # Зачем:
    #   для аудита, отладки, контроля импорта
    created_at = models.DateTimeField(_("создано"), auto_now_add=True)

    # updated_at:
    #   когда запись последний раз обновлялась
    # Пример:
    #   2026-03-20 09:10:11
    # Зачем:
    #   для понимания актуальности данных
    updated_at = models.DateTimeField(_("обновлено"), auto_now=True)

    class Meta:
        # Эта модель не создаёт свою таблицу.
        # Она только даёт общие поля дочерним моделям.
        abstract = True

