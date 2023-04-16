from django_select2.forms import ModelSelect2Widget
from djmoney.forms import MoneyWidget
from django import forms

from catalog.models import ProductSupplierPriceInfo, Product

money_widget_only_uah = MoneyWidget(
    amount_widget=forms.TextInput(attrs={'size': 7, 'class': 'form-class'}),
    currency_widget=forms.Select(attrs={}, choices=[('UAH', 'UAH ₴')]),
)


class ProductPriceChangelistInlineAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items
