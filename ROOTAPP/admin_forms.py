from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect

from ROOTAPP.models import PersonAddress
from nova_poshta.forms import warehouse_widget, area_widget, street_widget, settlement_widget


class FullAddressForm(forms.ModelForm):
    class Meta:
        model = PersonAddress
        exclude = []
        widgets = {
            'area': area_widget, 'settlement': settlement_widget,
            'warehouse': warehouse_widget, 'street': street_widget,
            # 'address_type': RadioSelect
        }


class PersonPhonesAdminFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                if form.cleaned_data['phone'] == self.instance.main_phone:
                    raise ValidationError('Нельзя отвязать номер указаный как номер для входа')

                if form.cleaned_data['phone'] == self.instance.delivery_phone:
                    raise ValidationError('Нельзя отвязать номер указаный как номер для доставки')


# class PersonAddressInlineForm(forms.ModelForm):
#     class Meta:
#         model: PersonAddress
#         widgets = {
#             'area': area_widget, 'settlement': settlement_widget
#         }
