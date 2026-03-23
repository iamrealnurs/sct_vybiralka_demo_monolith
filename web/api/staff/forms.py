from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

# IMPORTANT:
# Подставь правильный путь к моделям под своё приложение.
from catalog.models import (
    CarServicePackage,
    CarServicePackageImage,
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

            elif isinstance(widget, (forms.DateTimeInput, forms.DateInput, forms.TimeInput, forms.NumberInput, forms.TextInput)):
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
            "package_discount_percent": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "100"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_tailwind_classes()

        self.fields["name"].widget.attrs.setdefault("placeholder", "Например: Замена масла + фильтр")
        self.fields["public_title"].widget.attrs.setdefault("placeholder", "Например: Базовое ТО")
        self.fields["promo_badge"].widget.attrs.setdefault("placeholder", "Например: -15%")
        self.fields["promo_text"].widget.attrs.setdefault("placeholder", "Короткий текст акции")

    def clean(self):
        cleaned_data = super().clean()

        category = cleaned_data.get("category")
        modification = cleaned_data.get("modification")

        if category and modification:
            duplicate_exists = (
                CarServicePackage.objects
                .filter(
                    category=category,
                    modification=modification,
                    is_deleted=False,
                )
                .exists()
            )
            if duplicate_exists:
                raise ValidationError(
                    "Пакет с такой категорией и этой модификацией уже существует."
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
            "alt_text": forms.TextInput(attrs={"placeholder": "Alt text изображения"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_tailwind_classes()