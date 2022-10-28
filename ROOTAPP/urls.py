from django.urls import path

from ROOTAPP.views import update_cities, get_delivery_cost, ProductActionsView, CheckoutView, ByNowView, ByOneClickView

app_name = 'root_app'
urlpatterns = [
    path('update_cities/', update_cities, name='update_cities'),
    path('get_delivery_cost/', get_delivery_cost, name='get_delivery_cost'),
    path('product_actions/', ProductActionsView.as_view(), name='product_actions'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('by_now/', ByNowView.as_view(), name='by_now'),
    path('by_one_click/', ByOneClickView.as_view(), name='by_one_click'),
]
