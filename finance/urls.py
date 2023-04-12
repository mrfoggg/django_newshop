from django.urls import path

from finance.views import update_prices_ajax_for_order_admin

app_name = 'finance'
urlpatterns = [
    path('update_prices_ajax_for_order_admin/', update_prices_ajax_for_order_admin,
         name='update_prices_ajax_for_order_admin'),
]
