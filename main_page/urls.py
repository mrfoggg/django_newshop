from django.urls import path

from .views import MainPageView, FavoritesView, CompareView, dispatch_view, CabinetView

urlpatterns = [

    path('', MainPageView.as_view(), name='home'),
    # path('<slug:slug>/', CatalogRoutingVew.as_view()),
    path('favorites/', FavoritesView.as_view(), name='favorites'),
    path('compare/', CompareView.as_view(), name='compare'),
    path('cabinet/', CabinetView.as_view(), name='cabinet'),
    path('<slug:slug>/', dispatch_view, name='category_and_product'),
    path('<slug:slug>/<str:str_url_data>/', dispatch_view, name='filteres_category'),
]
app_name = 'main_page'

