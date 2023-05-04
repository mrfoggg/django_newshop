from django import forms
from django_select2.forms import ModelSelect2Widget
from ROOTAPP.models import Person, PersonAddress, ContactPerson, ContactPersonShotStr, Phone
from catalog.models import ProductSupplierPrice, ProductSupplierPriceInfo


class ClientOrderAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['person'].widget.can_view_related = False
        self.fields['person'].widget.can_add_related = False
        self.fields['incoming_phone'].widget.can_add_related = False
        self.fields['incoming_phone'].widget.can_view_related = False

    address = forms.ModelChoiceField(
        queryset=PersonAddress.objects.all(),
        label="Адрес доставки",
        required=False,
        widget=ModelSelect2Widget(
            model=PersonAddress,
            search_fields=('settlement__description_ua__icontains', 'settlement__description_ua__icontains'),
            dependent_fields={'person': 'person'},
            attrs={'data-placeholder': 'выберите адрес доставки контрагента', 'style': 'width: 80%;',
                   'data-minimum-input-length': '0'}
        )
    )

    contact_person = forms.ModelChoiceField(
        queryset=ContactPersonShotStr.objects.all(),
        label="Контактное лицо",
        help_text='Добавить новое контактное лицо можно в форме редактирования контрагента',
        required=False,
        widget=ModelSelect2Widget(
            model=ContactPersonShotStr,
            search_fields=('full_name__icontains', 'phone__number__contains'),
            dependent_fields={'person': 'person'},
            attrs={
                'data-placeholder': 'выберите контактное лицо', 'style': 'width: 80%;',
                'data-minimum-input-length': '0',
            }
        )
    )


class ProductInClientOrderAdminInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            if self.instance.supplier_order:
                # self.fields['supplier_price_variants'].queryset = ProductSupplierPriceInfo.objects.filter(
                #     id=self.instance.supplier_order.price_type.id)
                self.fields['supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items.filter(
                    id=self.instance.supplier_order.price_type.id
                )

            else:
                self.fields['supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items
        else:
            self.fields['supplier_price_variants'].queryset = ProductSupplierPriceInfo.objects.none()
