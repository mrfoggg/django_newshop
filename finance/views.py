from django.shortcuts import render
from djmoney.money import Money
from jsonview.decorators import json_view

from catalog.models import Product, ProductSupplierPrice
from finance.services import get_margin, get_margin_percent, get_profitability


# Create your views here.

# при выборе товара обновитть цены продажи и варинаты закупочных цен поставщиков
@json_view
def update_prices_ajax_for_order_admin(request):
    return {'price': 'info'}


@json_view
def ajax_get_product_price_and_suppliers_prices_variants(request):
    product = Product.objects.get(id=request.POST.get('productId'))
    return {
        'supplier_prices_last_items': [{'id': pi.id, 'str_present': pi.__str__()} for pi in
                                       product.supplier_prices_last_items],
        'current_price': product.full_current_price_info if product.current_price else '-'
    }


@json_view
def ajax_get_calculated_finance_for_price_list(request):
    price = Money(request.POST.get('price'), 'UAH')
    suppler_price = ProductSupplierPrice.objects.get(id=request.POST.get('supplier_price_id')).converted_price
    margin = get_margin(suppler_price, price)
    margin_percent = get_margin_percent(margin, suppler_price)
    profitability = get_profitability(margin, price)
    return {'margin': str(margin), 'margin_percent': str(margin_percent), 'profitability': str(profitability)}


@json_view
def ajax_get_supplier_price_by_price_item_id(request):
    return {'price': f"{ProductSupplierPrice.objects.get(id=request.POST.get('price_item_id')).converted_price.amount:.2f}"}
