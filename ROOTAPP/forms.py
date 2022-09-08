from django import forms
from django_select2.forms import ModelSelect2Widget

from ROOTAPP.models import Settlement, SettlementArea
from django_select2 import forms as s2forms


class SettlementForm(forms.Form):
    settlement_area = forms.ModelChoiceField(queryset=SettlementArea.objects.all(), label='Область')
    settlement = forms.ChoiceField(label='Населений пункт')


class AddressForm(forms.Form):
    area = forms.ModelChoiceField(
        queryset=SettlementArea.objects.all(),
        label="Область",
        widget=ModelSelect2Widget(
            model=SettlementArea,
            search_fields=['description_ua__icontains'],
        )
    )

    city = forms.ModelChoiceField(
        queryset=Settlement.objects.all(),
        label="Населений пункт",
        widget=ModelSelect2Widget(
            search_fields=['description_ua__icontains'],
            dependent_fields={'area': area},
            max_results=500,
        )
    )
