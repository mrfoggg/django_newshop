from django.urls import path

from ROOTAPP.views import update_cities

app_name = 'rootapp'
urlpatterns = [
    path('update_cities/', update_cities),
]
