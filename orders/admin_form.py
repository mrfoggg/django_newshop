from django import forms
from django_select2.forms import ModelSelect2Widget
from ROOTAPP.models import Person, PersonAddress


class ClientOrderAdminForm(forms.ModelForm):
    address = forms.ModelChoiceField(
        queryset=PersonAddress.objects.all(),
        label="Адрес доставки",
        widget=ModelSelect2Widget(
            model=PersonAddress,
            search_fields=('settlement__description_ua__icontains', 'settlement__description_ua__icontains'),
            dependent_fields={'person': 'person'},
            attrs={'data-placeholder': 'выберите адрес доставки контрагента', 'style': 'width: 80%;',
                   'data-minimum-input-length': '0'}
        )
    )

