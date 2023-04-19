from django.urls import path

from finance.views import update_prices_ajax_for_order_admin, ajax_get_product_price_and_suppliers_prices_variants, \
    ajax_get_calculated_finance_for_price_list, ajax_get_supplier_price_by_price_item_id

app_name = 'finance'
urlpatterns = [
    path('ajax_get_product_price_and_suppliers_prices_variants/', ajax_get_product_price_and_suppliers_prices_variants,
         name='ajax_get_product_price_and_suppliers_prices_variants'),
    path('ajax_get_calculated_finance_for_price_list/', ajax_get_calculated_finance_for_price_list,
         name='ajax_get_calculated_finance_for_price_list'),
    path('ajax_get_supplier_price_by_price_item_id/', ajax_get_supplier_price_by_price_item_id,
         name='ajax_get_supplier_price_by_price_item_id'),
    # path('ajax_get_supplier_price_item_id_by_supplier_price_id/', ajax_get_supplier_price_item_id_by_supplier_price_id,
    #      name='ajax_get_supplier_price_item_id_by_supplier_price_id'),
]
