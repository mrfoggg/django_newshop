from django import forms
from django.contrib.auth.models import User
from django_select2.forms import ModelSelect2Widget

from ROOTAPP.models import Person, PersonAddress
# from nova_poshta.forms import address_for_order_widget
# from orders.models import ClientOrder


class ClientOrderAdminForm(forms.ModelForm):
    # person = forms.ModelChoiceField(
    #     queryset=Person.objects.filter(is_customer=True),
    #     label="Покупатель",
    #     widget=ModelSelect2Widget(
    #         model=Person,
    #         search_fields=['last_name__icontains', 'main_phone__number__contains'],
    #         attrs={'data-placeholder': 'выберите пользователя', 'style': 'width: 80%;',
    #                'data-minimum-input-length': '0'}
    #     )
    # )
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

