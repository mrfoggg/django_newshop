from datetime import datetime

import pytz
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect
from django.utils import timezone
from django_select2.forms import ModelSelect2Widget

from ROOTAPP.models import PersonAddress, Person
from Shop_DJ import settings
from nova_poshta.forms import warehouse_widget, area_widget, street_widget, settlement_widget
from orders.models import ClientOrder


class DocumentForm(forms.ModelForm):
    def clean(self):
        super(DocumentForm, self).clean()
        print('cleanDocumentForm')
        return self.cleaned_data

class FullAddressForm(forms.ModelForm):
    class Meta:
        model = PersonAddress
        exclude = []
        widgets = {
            'area': area_widget,
            'settlement': settlement_widget,
            'warehouse': warehouse_widget, 'street': street_widget,
        }


class ClientOrderAdmin(forms.ModelForm):
    class Meta:
        model = ClientOrder
        exclude = []
        widgets = {
            'area': area_widget, 'settlement': settlement_widget,
        }


class PersonPhonesAdminFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                if form.cleaned_data['phone'] == self.instance.main_phone:
                    raise ValidationError('Нельзя отвязать номер указаный как номер для входа')

                if form.cleaned_data['phone'] == self.instance.delivery_phone:
                    raise ValidationError('Нельзя отвязать номер указаный как номер для доставки')


class PersonAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['main_supplier_price_type'].widget.can_add_related = False
        self.fields['main_price_type'].widget.can_add_related = False

    def clean(self):
        self.cleaned_data['first_name'] = self.cleaned_data['first_name'].title()
        self.cleaned_data['last_name'] = self.cleaned_data['last_name'].title()
        if self.cleaned_data['middle_name']:
            self.cleaned_data['middle_name'] = self.cleaned_data['middle_name'].title()
