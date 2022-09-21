from django.urls import path

from .views import MainPageView, FavoritesView, CompareView

app_name = 'main_page'

urlpatterns = [
    # path('', index_view, name='home'),
    path('', MainPageView.as_view(), name='home'),
    path('favorites/', FavoritesView.as_view(), name='favorites'),
    path('compare/', CompareView.as_view(), name='compare')
]