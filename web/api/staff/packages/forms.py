from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from cars.models import Modification
from catalog.models import (
    CarServicePackage,
    CarServicePackageImage,
    PackageCategory,
)


class TailwindMixin:
    """
    Добавляет Tailwind-классы всем полям формы.
    """

    input_class = "staff-input"
    select_class = "staff-select"
    textarea_class = "staff-textarea"
    checkbox_class = "h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500"

    def apply_tailwind_classes(self) -> None:
        for field_name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.Textarea):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} {self.textarea_class}".strip()
                widget.attrs.setdefault("rows", 4)

            elif isinstance(widget, forms.Select):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} {self.select_class}".strip()

            elif isinstance(widget, forms.CheckboxInput):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} {self.checkbox_class}".strip()

            elif isinstance(
                widget,
                (
                    forms.DateTimeInput,
                    forms.DateInput,
                    forms.TimeInput,
                    forms.NumberInput,
                    forms.TextInput,
                ),
            ):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} {self.input_class}".strip()

            elif isinstance(widget, forms.ClearableFileInput):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} block w-full text-sm text-slate-700".strip()

            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} {self.input_class}".strip()


class StaffPackageCreateForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = CarServicePackage
        fields = [
            "category",
            "name",
            "public_title",
            "description",
            "description_short",
            "description_public",
            "modification",
            "status",
            "is_promo",
            "promo_badge",
            "promo_text",
            "promo_start_at",
            "promo_end_at",
            "package_discount_percent",
        ]
        widgets = {
            "promo_start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "promo_end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(),
            "description_short": forms.Textarea(attrs={"rows": 3}),
            "description_public": forms.Textarea(),
            "package_discount_percent": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "max": "100"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = (
            PackageCategory.objects.filter(is_active=True)
            .order_by("sort_order", "name", "code")
        )
        self.fields["modification"].queryset = (
            Modification.objects.select_related(
                "configuration",
                "configuration__generation",
                "configuration__generation__model",
                "configuration__generation__model__mark",
            )
            .order_by("name", "id")
        )

        self.fields["promo_badge"].required = False
        self.fields["promo_text"].required = False
        self.fields["promo_start_at"].required = False
        self.fields["promo_end_at"].required = False
        self.fields["description"].required = False
        self.fields["description_short"].required = False
        self.fields["description_public"].required = False

        self.apply_tailwind_classes()

        self.fields["name"].widget.attrs.setdefault(
            "placeholder",
            "Например: Замена масла + фильтр",
        )
        self.fields["public_title"].widget.attrs.setdefault(
            "placeholder",
            "Например: Базовое ТО",
        )
        self.fields["promo_badge"].widget.attrs.setdefault(
            "placeholder",
            "Например: -15%",
        )
        self.fields["promo_text"].widget.attrs.setdefault(
            "placeholder",
            "Короткий текст акции",
        )

    def clean(self):
        cleaned_data = super().clean()

        category = cleaned_data.get("category")
        modification = cleaned_data.get("modification")
        status = cleaned_data.get("status")
        is_promo = cleaned_data.get("is_promo")
        promo_text = (cleaned_data.get("promo_text") or "").strip()
        promo_start_at = cleaned_data.get("promo_start_at")
        promo_end_at = cleaned_data.get("promo_end_at")

        published_value = (
            getattr(CarServicePackage.Status, "PUBLISHED", "PUBLISHED")
            if hasattr(CarServicePackage, "Status")
            else "PUBLISHED"
        )

        if category and modification:
            duplicate_exists = (
                CarServicePackage.objects.filter(
                    category=category,
                    modification=modification,
                    is_deleted=False,
                ).exists()
            )
            if duplicate_exists:
                raise ValidationError(
                    "Пакет с такой категорией и этой модификацией уже существует."
                )

        if status == published_value:
            if not category:
                self.add_error(
                    "category",
                    "Для публикации пакета нужно указать категорию.",
                )
            if not modification:
                self.add_error(
                    "modification",
                    "Для публикации пакета нужно указать модификацию.",
                )

        if is_promo and not promo_text:
            self.add_error(
                "promo_text",
                "Если пакет акционный, необходимо указать текст акции.",
            )

        if promo_start_at and promo_end_at and promo_start_at > promo_end_at:
            self.add_error(
                "promo_end_at",
                "Дата окончания акции не может быть раньше даты начала.",
            )

        return cleaned_data


class StaffPackageImageForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = CarServicePackageImage
        fields = [
            "image",
            "alt_text",
        ]
        widgets = {
            "alt_text": forms.TextInput(attrs={"placeholder": "Альтернативный текст изображения"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()


class StaffPackageUpdateForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = CarServicePackage
        fields = [
            "name",
            "public_title",
            "slug",
            "category",
            "modification",
            "status",
            "description",
            "description_short",
            "description_public",
            "is_promo",
            "promo_badge",
            "promo_text",
            "promo_start_at",
            "promo_end_at",
            "package_discount_percent",
        ]
        widgets = {
            "promo_start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "promo_end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "description_short": forms.Textarea(attrs={"rows": 3}),
            "description_public": forms.Textarea(attrs={"rows": 6}),
            "package_discount_percent": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "max": "100"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = (
            PackageCategory.objects.filter(is_active=True)
            .order_by("sort_order", "name", "code")
        )
        self.fields["modification"].queryset = (
            Modification.objects.select_related(
                "configuration",
                "configuration__generation",
                "configuration__generation__model",
                "configuration__generation__model__mark",
            )
            .order_by("name", "id")
        )

        self.fields["promo_badge"].required = False
        self.fields["promo_text"].required = False
        self.fields["promo_start_at"].required = False
        self.fields["promo_end_at"].required = False
        self.fields["description"].required = False
        self.fields["description_short"].required = False
        self.fields["description_public"].required = False

        self.apply_tailwind_classes()

        self.fields["name"].widget.attrs.setdefault(
            "placeholder",
            "Внутреннее название для сотрудников",
        )
        self.fields["public_title"].widget.attrs.setdefault(
            "placeholder",
            "Публичный заголовок",
        )
        self.fields["slug"].widget.attrs.setdefault(
            "placeholder",
            "oil-change-toyota-camry-xv70",
        )
        self.fields["promo_badge"].widget.attrs.setdefault(
            "placeholder",
            "Например: HIT, SALE, -10%",
        )
        self.fields["promo_text"].widget.attrs.setdefault(
            "placeholder",
            "Текст акции для клиента",
        )
        self.fields["package_discount_percent"].widget.attrs.setdefault(
            "placeholder",
            "0.00",
        )

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        if not slug:
            raise ValidationError("Slug обязателен.")

        queryset = CarServicePackage.objects.filter(slug=slug, is_deleted=False)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError("Пакет с таким slug уже существует.")

        return slug

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get("status")
        category = cleaned_data.get("category")
        modification = cleaned_data.get("modification")
        is_promo = cleaned_data.get("is_promo")
        promo_text = (cleaned_data.get("promo_text") or "").strip()
        promo_start_at = cleaned_data.get("promo_start_at")
        promo_end_at = cleaned_data.get("promo_end_at")

        published_value = (
            getattr(CarServicePackage.Status, "PUBLISHED", "PUBLISHED")
            if hasattr(CarServicePackage, "Status")
            else "PUBLISHED"
        )

        if status == published_value:
            if not category:
                self.add_error(
                    "category",
                    "Для публикации пакета нужно указать категорию.",
                )
            if not modification:
                self.add_error(
                    "modification",
                    "Для публикации пакета нужно указать модификацию.",
                )

        if is_promo and not promo_text:
            self.add_error(
                "promo_text",
                "Если пакет акционный, необходимо указать текст акции.",
            )

        if promo_start_at and promo_end_at and promo_start_at > promo_end_at:
            self.add_error(
                "promo_end_at",
                "Дата окончания акции не может быть раньше даты начала.",
            )

        return cleaned_data

