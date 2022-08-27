from django.shortcuts import render

from ROOTAPP.views import HeaderView
from main_page.models import Banner
from site_settings.models import SliderConfiguration
from django.views.generic.base import TemplateView


class MainPageView(TemplateView, HeaderView):
    template_name = 'main-page/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banners'] = Banner.objects.all()
        context['slider_config'] = SliderConfiguration.get_solo()
        return context
