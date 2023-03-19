from django.urls import path

from nova_poshta.views import update_settlements, update_cities, update_warehouses, get_delivery_cost

app_name = 'nova_poshta'
urlpatterns = [
    path('update_settlements/', update_settlements, name='update_settlements'),
    path('update_cities/', update_cities, name='update_cities'),
    path('update_warehouses/', update_warehouses, name='update_warehouses'),
    path('get_delivery_cost/', get_delivery_cost, name='get_delivery_cost'),

]
