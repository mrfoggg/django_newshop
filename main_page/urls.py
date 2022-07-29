from django.urls import path

from .views import MainPageView

urlpatterns = [
    # path('', index_view, name='home'),
    path('', MainPageView.as_view(), name='home'),
]