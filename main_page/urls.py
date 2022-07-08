from django.urls import path

from main_page import views

urlpatterns = [
    path('', views.index, name='home'),
]