import json

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils.html import format_html
from django_select2.forms import ModelSelect2Widget, Select2AdminMixin
from ROOTAPP.models import PersonAddress, ContactPerson, PersonPhone, Person
from catalog.models import ProductSupplierPrice, ProductSupplierPriceInfo
from orders.models import ClientOrder, ProductInOrder

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
        self.fields['product'].widget.can_view_related = False
        self.fields['product'].widget.can_add_related = False
        self.fields['product'].widget.can_delete_related = False
        self.fields['product'].widget.can_change_related = False
        if self.request.method == 'GET':
            if self.instance.id:
                if self.instance.supplier_order:

                    self.fields[
                        'supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items.filter(
                        id=self.instance.supplier_order.price_type.id
                    )
                else:
                    self.fields['supplier_price_variants'].queryset = self.instance.product.supplier_prices_last_items
            else:
                self.fields['supplier_price_variants'].queryset = ProductSupplierPriceInfo.objects.none()

    class Meta:
        model = ProductInOrder
        fields = '__all__'
        widgets = {
            'product': ModelSelect2Widget(
                model=ProductInOrder,
                search_fields=('name__icontains',),
                attrs={'data-placeholder': 'выберите товар', 'style': 'width: 100%;',
                       'data-minimum-input-length': '0'}
            )
        }


person_widget = ModelSelect2Widget(
    model=Person,
    search_fields=('phone__number__contains',),
    attrs={'data-placeholder': 'выберите контрагента', 'style': 'width: 80%;',
           'data-minimum-input-length': '0'}
)

class ProductMoveItemInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        super(ProductMoveItemInlineFormset, self).clean()
        # print('INST - ', self.instance.order.products.all())
        if self.instance.id:
            if self.instance.order:
                products_in_order_qs = self.instance.order.products
                total_quantity = dict()
                for form in self.forms:
                    product = form.cleaned_data['product']
                    quantity = form.cleaned_data['quantity']

                    if product in total_quantity.keys():
                        total_quantity[product]['quantity'] += quantity
                    else:
                        quantity_in_order = products_in_order_qs.filter(product=product).aggregate(Sum('quantity'))[
                            'quantity__sum']
                        total_quantity[product] = {
                            'quantity': quantity,
                            'quantity_in_order': quantity_in_order if quantity_in_order else 0
                        }
                for q in total_quantity.items():
                    # print('Q -', q)
                    if q[1]['quantity'] > q[1]['quantity_in_order']:
                        raise ValidationError(f"Не возможно получить {q[1]['quantity']} шт {q[0]}, "
                                              f"в заказе всего {q[1]['quantity_in_order']} шт")
                    else:
                        pass
                #     установить начальніе остатки
                # for form in self.forms:
                #     print('ProductMoveItemInlineFormset cleaned_data - ', form.cleaned_data)
                #     form.cleaned_data['quantity_before'] = {'111': 333}
        # print('total_quantity -', total_quantity)


