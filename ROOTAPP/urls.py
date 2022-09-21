from django.urls import path

from ROOTAPP.views import update_cities, get_delivery_cost, product_actions

app_name = 'root_app'
urlpatterns = [
    path('update_cities/', update_cities, name='update_cities'),
    path('get_delivery_cost/', get_delivery_cost, name='get_delivery_cost'),
    path('product_actions/', product_actions, name='product_actions'),
]
