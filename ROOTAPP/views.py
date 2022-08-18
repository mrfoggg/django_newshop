from django.shortcuts import render
from main_page.models import SitePhone, Schedule, Menu
from site_settings.models import HeaderConfiguration
from django.views.generic.base import ContextMixin

contact_phones = SitePhone.objects.all()
schedule = Schedule.objects.all()
menu_items = Menu.objects.filter(level=0).only('title', 'image')
header_config = HeaderConfiguration.get_solo()
# header_config = 1


class HeaderView(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_phones'] = SitePhone.objects.all()
        context['schedule'] = Schedule.objects.all()
        context['menu_items'] = Menu.objects.filter(level=0).only('title', 'image')
        context['header_config'] = HeaderConfiguration.get_solo()
        return context
