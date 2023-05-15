import json

from django import forms
from django.utils.html import format_html
from django_select2.forms import ModelSelect2Widget, Select2AdminMixin
from ROOTAPP.models import PersonAddress, ContactPerson, PersonPhone
from catalog.models import ProductSupplierPrice, ProductSupplierPriceInfo
from orders.models import ClientOrder

# class Select2AdminWidget(ModelSelect2Widget, Select2AdminMixin):
#     extra_attrs = {'placeholder': "номер для поиска или создания"}
#     def build_attrs(self, base_attrs, extra_attrs=extra_attrs):
#         return super().build_attrs(base_attrs, extra_attrs)


contact_person_widget = ModelSelect2Widget(
    model=ContactPerson,
    search_fields=('full_name__icontains', 'phone__number__contains'),
    dependent_fields={'person': 'person'},
    attrs={
        'data-placeholder': 'выберите контактное лицо',
        'data-format-no-matches': 'выберите контактное лицо',
        'data-allowClear': True,  # doesn't work
        'style': 'width: 80%;',
        'data-minimum-input-length': '0',
    }
)

address_widget = ModelSelect2Widget(
    model=PersonAddress,
    search_fields=('settlement__description_ua__icontains',),
    dependent_fields={'person': 'person'},
    attrs={'data-placeholder': 'выберите адрес доставки контрагента', 'style': 'width: 80%;',
           'data-minimum-input-length': '0'}
)

delivery_phone_widget = ModelSelect2Widget(
    model=PersonPhone,
    search_fields=('phone__number__contains',),
    dependent_fields={'person': 'person'},
    attrs={'data-placeholder': 'выберите телефон контрагента', 'style': 'width: 80%;',
           'data-minimum-input-length': '0'}
)


class ClientOrderAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['person'].widget.can_view_related = False
        self.fields['person'].widget.can_add_related = False
        self.fields['incoming_phone'].widget.can_add_related = False
        self.fields['incoming_phone'].widget.can_view_related = False

    class Meta:
        model = ClientOrder
        fields = '__all__'
        widgets = {'contact_person': contact_person_widget, 'address': address_widget,
                   'delivery_phone': delivery_phone_widget}


class ProductInClientOrderAdminInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            if self.instance.supplier_order:
                # self.fields['supplier_price_variants'].queryset = ProductSupplierPriceInfo.objects.filter(
                #     id=self.instance.supplier_order.price_type.id)
                self.fields[
                    'supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items.filter(
                    id=self.instance.supplier_order.price_type.id
                )

            else:
                self.fields['supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items
        else:
            self.fields['supplier_price_variants'].queryset = ProductSupplierPriceInfo.objects.none()
