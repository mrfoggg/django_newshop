from django.shortcuts import render
from catalog.models import Category
from main_page.models import Banner, Menu
from site_settings.models import SliderConfiguration


# Create your views here.
def index(request):
    banners = Banner.objects.all()
    slider_config = SliderConfiguration.get_solo()
    menu_items = Menu.objects.filter(level=0).only('title', 'image')
    return render(
        request,
        'main-page/index.html',
        context={'banners': banners, 'menu_items': menu_items,
                 'slider_config': slider_config, 'title': "Сніп-сноп | Головна", }
    )
