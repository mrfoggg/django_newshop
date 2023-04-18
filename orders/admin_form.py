from django import forms
from django_select2.forms import ModelSelect2Widget
from ROOTAPP.models import Person, PersonAddress
from catalog.models import ProductSupplierPrice, ProductSupplierPriceInfo


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


class ProductInClientOrderAdminInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            if self.instance.supplier_order:
                self.fields['supplier_price_variants'].queryset = ProductSupplierPriceInfo.objects.filter(
                    id=self.instance.supplier_order.price_type.id)
            else:
                self.fields['supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items
        else:
            self.fields['supplier_price_variants'].queryset = ProductSupplierPriceInfo.objects.none()
