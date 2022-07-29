from django.shortcuts import render

# Create your views here.
from ROOTAPP.views import HeaderView
from catalog.models import Category
from main_page.models import SitePhone, Schedule, Menu
from site_settings.models import HeaderConfiguration
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView


def category_view(request, category_slug):
    contact_phones = SitePhone.objects.all()
    schedule = Schedule.objects.all()
    menu_items = Menu.objects.filter(level=0).only('title', 'image')
    header_config = HeaderConfiguration.get_solo()
    category = Category.objects.get(slug=category_slug)
    return render(
        request,
        'catalog/category.html',
        context={'menu_items': menu_items, 'schedule': schedule,
                 'title': "Сніп-сноп | Головна", 'category': category,
                 'contact_phones': contact_phones, 'header_config': header_config}
    )


class MainPageView(DetailView, HeaderView):
    template_name = 'catalog/category.html'
    model = Category
    # pk_url_kwarg = 'slug'
    query_pk_and_slug = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
