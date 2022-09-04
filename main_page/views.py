from django.shortcuts import render

# from ROOTAPP.views import HeaderView
from main_page.models import Banner, Menu, SitePhone, Schedule
from site_settings.models import SliderConfiguration, HeaderConfiguration, PhotoPlug
from django.views.generic.base import TemplateView
from django.views.generic.base import ContextMixin


class HeaderView(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {'contact_phones': SitePhone.objects.all(), 'schedule': Schedule.objects.all(),
                   'menu_items': Menu.objects.filter(level=0).only('title', 'image'),
                   'header_config': HeaderConfiguration.get_solo(), 'photo_plug': PhotoPlug.get_solo().image}
        return context


class MainPageView(TemplateView, HeaderView):
    template_name = 'main-page/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banners'] = Banner.objects.all()
        context['slider_config'] = SliderConfiguration.get_solo()
        return context
