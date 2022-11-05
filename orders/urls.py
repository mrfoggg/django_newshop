from django.urls import path

from orders.views import oneclick_add_comment, cancel_oneclick, create_one_click_order

urlpatterns = [
    path('by_one_click/', create_one_click_order, name='by_one_click'),
    path('oneclick_add_comment', oneclick_add_comment, name='oneclick_add_comment'),
    path('cancel_oneclick', cancel_oneclick, name='cancel_oneclick'),

]
app_name = 'orders'
