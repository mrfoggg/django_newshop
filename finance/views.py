from django.shortcuts import render
from jsonview.decorators import json_view

from catalog.models import Product


# Create your views here.

@json_view
def update_prices_ajax_for_order_admin(request):
    return {'info': 'info'}


@json_view
def ajax_get_product_suppliers_prices(request):

    product = Product.objects.get(id=request.POST.get('productId'))
    print('productT -', [{'id': pi.id, 'str_present': pi.__str__()} for pi in product.supplier_prices_last_items])
    return {'supplier_prices_last_items': [{'id': pi.id, 'str_present': pi.__str__()} for pi in product.supplier_prices_last_items]}
