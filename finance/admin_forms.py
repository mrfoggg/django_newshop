from django_select2.forms import ModelSelect2Widget
from djmoney.forms import MoneyWidget
from django import forms

from catalog.models import ProductSupplierPriceInfo, Product, ProductSupplierPrice, Category

money_widget_only_uah = MoneyWidget(
    amount_widget=forms.TextInput(attrs={'size': 7, 'class': 'form-class'}),
    currency_widget=forms.Select(attrs={}, choices=[('UAH', 'UAH ₴')]),
)


class ProductPriceChangelistInlineAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items
        else:
            self.fields['supplier_price_variants'].queryset = ProductSupplierPrice.objects.none()


class MovementOfGoodsFilterForm(forms.Form):
    start = forms.DateField(label='Начало периода', required=False)
    end = forms.DateField(label='Конец периода', required=False)
    product_category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Категория товаров",
        required=False
    )

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Товар",
        required=False,
        widget=ModelSelect2Widget(
            model=Product,
            search_fields=('name__icontains',),
            max_results=50,
            depended_fields=('product_category',),
            attrs={'style': 'width: 25rem;', 'data-minimum-input-length': '0'}
        )
    )



