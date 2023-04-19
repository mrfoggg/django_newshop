from django.shortcuts import render
from djmoney.money import Money
from jsonview.decorators import json_view

from catalog.models import Product, ProductSupplierPrice
from finance.services import get_margin, get_margin_percent, get_profitability
from orders.models import SupplierOrder


# Create your views here.

# при выборе товара обновитть цены продажи и варинаты закупочных цен поставщиков
@json_view
def update_prices_ajax_for_order_admin(request):
    return {'price': 'info'}


@json_view
def ajax_get_product_price_and_suppliers_prices_variants(request):
    product = Product.objects.get(id=request.POST.get('productId'))
    response = {'current_price': product.full_current_price_info if product.current_price else '-'}
    if supplier_order_id := request.POST.get('supplierOrderId'):

        price_type = SupplierOrder.objects.get(id=supplier_order_id).price_type
        price_item_qs = product.supplier_prices_last_items.filter(price_changelist__price_type=price_type)
        if price_item_qs.exists():
            price_item = price_item_qs.last()
            response['supplier_prices_last_items'] = [{'id': price_item.id, 'str_present': price_item.__str__()}]
        else:
            response['supplier_prices_last_items'] = []
    else:
        response['supplier_prices_last_items'] = [{'id': pi.id, 'str_present': pi.__str__()} for pi in
                                                  product.supplier_prices_last_items]
    return response


@json_view
def ajax_get_calculated_finance_for_price_list(request):
    price = Money(request.POST.get('price'), 'UAH')
    if request.POST.get('purchase_price'):
        purchase_price = Money(request.POST.get('purchase_price'), 'UAH')
    else:
        if ps_id := request.POST.get('supplier_price_id'):
            purchase_price = ProductSupplierPrice.objects.get(id=ps_id).converted_price
        else:
            purchase_price = 0
    margin = get_margin(purchase_price, price)
    margin_percent = get_margin_percent(margin, purchase_price)
    profitability = get_profitability(margin, price)
    response = {'margin': str(margin), 'margin_percent': str(margin_percent), 'profitability': str(profitability)}
    if quantity := int(request.POST.get('quantity')):
        response |= {
            'sale_total': str(price * quantity), 'margin_total': str(margin * quantity),
            'purchase_total': str(purchase_price * quantity)
        }
    # print('request', request.POST)
    # print('response', response)
    return response


@json_view
def ajax_get_supplier_price_by_price_item_id(request):
    if price_item_id := request.POST.get('price_item_id'):
        return {
            'price': f"{ProductSupplierPrice.objects.get(id=price_item_id).converted_price.amount:.2f}"}
    else:
        return {'price': f"{Money(0, 'UAH').amount:.2f}"}

@json_view
def ajax_get_supplier_price_item_by_supplier_price_id(request):

    return {'id', 'id'}
