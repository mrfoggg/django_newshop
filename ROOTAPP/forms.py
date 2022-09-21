from django import forms
from django_select2.forms import ModelSelect2Widget

from ROOTAPP.models import Settlement, SettlementArea
from django_select2 import forms as s2forms


class AddressForm(forms.Form):
    area = forms.ModelChoiceField(
        queryset=SettlementArea.objects.all(),
        label="Область",
        widget=ModelSelect2Widget(
            model=SettlementArea,
            search_fields=['description_ua__icontains', 'description_ru__icontains'],
            attrs={'data-placeholder': 'назва області'}
        )
    )

    settlement = forms.ModelChoiceField(
        queryset=Settlement.objects.all(),
        label="Населений пункт",
        widget=ModelSelect2Widget(
            model=Settlement,
            search_fields=('description_ua__icontains', 'description_ru__icontains'),
            dependent_fields={'area': 'area'},
            max_results=50,
            attrs={'data-placeholder': 'назва населеного пункту'}
        )
    )
