from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from client.models import ClientCar
from cars.models import Modification


class ClientTailwindMixin:
    """
    Миксин для применения Tailwind-классов к полям формы клиента.
    Аналогичен тому, что используется в Staff-интерфейсе для единообразия.
    """
    input_class = "staff-input"  # Используем те же классы из base.html
    checkbox_class = "h-5 w-5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"

    def apply_client_styles(self) -> None:
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = self.checkbox_class
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} {self.input_class}".strip()


class ClientLoginForm(ClientTailwindMixin, AuthenticationForm):
    """
    Форма авторизации клиента.
    """
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'autofocus': True}))
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_client_styles()


class ClientCarAddForm(ClientTailwindMixin, forms.ModelForm):
    """
    Форма добавления автомобиля в гараж клиента.
    Поле modification будет заполняться через JS-селектор.
    """
    
    # Скрытое поле для ID модификации, которую выберет клиент в каскадном фильтре
    modification = forms.ModelChoiceField(
        queryset=Modification.objects.all(),
        widget=forms.HiddenInput(),
        required=True,
        error_messages={'required': 'Пожалуйста, выберите автомобиль из списка выше.'}
    )

    class Meta:
        model = ClientCar
        fields = [
            "modification",
            "license_plate",
            "vin",
            "year",
            "mileage_km",
            "is_primary",
        ]
        widgets = {
            "license_plate": forms.TextInput(attrs={"placeholder": "Например: 777AAA01"}),
            "vin": forms.TextInput(attrs={"placeholder": "17 знаков (опционально)"}),
            "year": forms.NumberInput(attrs={"placeholder": "ГГГГ"}),
            "mileage_km": forms.NumberInput(attrs={"placeholder": "Текущий пробег"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_client_styles()
        
        # Делаем VIN необязательным для демо-версии
        self.fields["vin"].required = False
        
        # Если это первый автомобиль клиента, можно по умолчанию сделать его активным
        self.fields["is_primary"].label = "Сделать основным автомобилем"

    def clean_year(self):
        year = self.cleaned_data.get("year")
        import datetime
        current_year = datetime.date.today().year
        if year and (year < 1900 or year > current_year + 1):
            raise forms.ValidationError("Введите корректный год выпуска.")
        return year

    def clean_license_plate(self):
        plate = self.cleaned_data.get("license_plate", "").upper().strip()
        # Простая проверка на уникальность госномера в рамках демо
        if ClientCar.objects.filter(license_plate=plate).exists():
            raise forms.ValidationError("Автомобиль с таким госномером уже зарегистрирован.")
        return plate

