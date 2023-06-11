from datetime import datetime

from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from djmoney.money import Money
from jsonview.decorators import json_view

from catalog.models import Product, ProductSupplierPrice, ProductGroupPrice, Category
from finance.admin_forms import MovementOfGoodsFilterForm
from finance.models import GroupPriceChangelist, Stock
from finance.services import get_margin, get_margin_percent, get_profitability
from orders.models import SupplierOrder, ProductMoveItem, FinanceDocument
from rich import print as rprint


@json_view
def ajax_get_product_price_and_suppliers_prices_variants(request):
    product = Product.objects.get(id=request.POST.get('productId'))
    gp_qs = ProductGroupPrice.objects.filter(
        price_changelist__price_type_id=group_price_id,
        product=product
    ).order_by('price_changelist__updated') if (group_price_id := request.POST.get('groupPriceId')) else \
        ProductGroupPrice.objects.none()
    current_price_amount = product.current_price.price.amount if product.current_price else None
    response = {
        'current_price': product.full_current_price_info if product.current_price else '-',
        'current_price_amount': current_price_amount,
        'group_price_info': gp_qs.last().price_full_info if (group_price_id and gp_qs.exists()) else '-',
        'group_price_val': f'{gp_qs.last().converted_price.amount:.2f}' if (
                group_price_id and gp_qs.exists()) else current_price_amount
    }
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
    print('resp', response, sep='=')
    return response


@json_view
def ajax_get_calculated_finance_for_price_list(request):
    price = Money(request.POST.get('price'), 'UAH')
    dp = request.POST.get('drop_price')
    drop_price = Money(dp if dp != '' else 0, 'UAH')
    if request.POST.get('purchase_price'):
        purchase_price = Money(request.POST.get('purchase_price'), 'UAH')
    else:
        if ps_id := request.POST.get('supplier_price_id'):
            purchase_price = ProductSupplierPrice.objects.get(id=ps_id).converted_price
        else:
            purchase_price = 0
    margin = get_margin(purchase_price, price, drop_price)
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


class MovementOfGoods(View):
    template_name = 'reports/movement_of_goods.html'
    filter_form = MovementOfGoodsFilterForm

    def get(self, request):
        return render(request, self.template_name, {'filter_form': self.filter_form()})

    def post(self, request):
        print('POST - ', request.POST)
        start, end = request.POST.get('start'), request.POST.get('end')
        product_id, category_id = request.POST.get('product'), request.POST.get('product_category')
        if not any((start, end)):
            caption = 'Движение товаров за весь период. '
        else:
            caption = 'Движение товаров за период '
            if start:
                caption += f'с {start}'
            if end:
                caption += f' до {end}. '
            else:
                caption += f'. '
        if category_id:
            caption += f'Категория товаров {Category.objects.get(id=category_id)}. '
        if product_id:
            caption += f'Товар {Product.objects.get(id=product_id)}'

        finance_documents = FinanceDocument.objects.filter(is_active=True)
        if start:
            finance_documents = finance_documents.filter(applied__gte=datetime.strptime(start, "%d.%m.%Y"))
        if end:
            finance_documents = finance_documents.filter(applied__lte=datetime.strptime(end, "%d.%m.%Y"))
        if category_id:
            finance_documents = finance_documents.filter(productmoveitem__product__admin_category=category_id).distinct()
        if product_id:
            finance_documents = finance_documents.filter(productmoveitem__product=product_id).distinct()
        data = {'before': 0, 'arrived': 0, 'sent': 0, 'stocks': []}
        for stock in Stock.objects.filter(financedocument__in=finance_documents).distinct():
            products_this_stock = Product.objects.filter(productmoveitem__document__stock=stock).distinct()
            if category_id:
                products_this_stock = products_this_stock.filter(admin_category=category_id)
            print('PRODUCT - ', product_id)
            if product_id:
                products_this_stock = products_this_stock.filter(id=product_id)
            stock_data = {'name': stock.name, 'before': 0, 'arrived': 0, 'sent': 0, 'after': 0, 'products': []}
            print('STOCK - ', stock)
            for product in products_this_stock:
                product_data = {'name': product.name, 'before': 0, 'arrived': 0, 'sent': 0, 'after': 0, 'documents': []}
                print('product - ', product)
                documents = finance_documents.filter(stock=stock, productmoveitem__product=product).distinct()
                print('documents - ', documents)
                for doc in documents:
                    move_items = ProductMoveItem.objects.filter(product=product, document=doc)
                    doc_quantity_arrived = move_items.aggregate(quantity=Sum('quantity'))['quantity']
                    product_data['arrived'] += doc_quantity_arrived
                    document_data = {
                        'name': doc.__str__(), 'before': 0,
                        'arrived': doc_quantity_arrived, 'sent': 0, 'after': 0
                    }
                    product_data['documents'].append(document_data)
                stock_data['arrived'] += product_data['arrived']
                stock_data['products'].append(product_data)
            data['arrived'] += stock_data['arrived']
            data['stocks'].append(stock_data)

            print('='*40)

        rprint('TOTAL_DATA - ', data)

        return JsonResponse({'caption': caption, 'data': data})
