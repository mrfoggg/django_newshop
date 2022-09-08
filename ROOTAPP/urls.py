from django.urls import path

from ROOTAPP.views import update_cities, get_cities_by_area

app_name = 'rootapp'
urlpatterns = [
    path('update_cities/', update_cities, name='update_cities'),
    path('get_cities_by_area/', get_cities_by_area, name='get_cities_by_area'),
]
