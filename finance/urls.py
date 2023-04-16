from django.urls import path

from finance.views import update_prices_ajax_for_order_admin, ajax_get_product_suppliers_prices, \
    ajax_get_calculated_finance_for_price_list

app_name = 'finance'
urlpatterns = [
    path('update_prices_ajax_for_order_admin/', update_prices_ajax_for_order_admin,
         name='update_prices_ajax_for_order_admin'),
    path('ajax_get_product_suppliers_prices/', ajax_get_product_suppliers_prices,
         name='ajax_get_product_suppliers_prices'),
    path('ajax_get_calculated_finance_for_price_list/', ajax_get_calculated_finance_for_price_list,
         name='ajax_get_calculated_finance_for_price_list'),
]
