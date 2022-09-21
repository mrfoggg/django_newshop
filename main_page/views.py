from django.shortcuts import render

# from ROOTAPP.views import HeaderView
from django.urls import reverse

from catalog.models import Product, Category
from main_page.models import Banner, Menu, SitePhone, Schedule, PopularCategory
from site_settings.models import SliderConfiguration, HeaderConfiguration, PhotoPlug
from django.views.generic.base import TemplateView
from django.views.generic.base import ContextMixin


class HeaderView(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {'contact_phones': SitePhone.objects.all(), 'schedule': Schedule.objects.all(),
                    'menu_items': Menu.objects.filter(level=0).only('title', 'image'),
                    'header_config': HeaderConfiguration.get_solo(), 'photo_plug': PhotoPlug.get_solo().image,
                    'favorites_link': reverse('main_page:favorites'),
                    'compare_link': reverse('main_page:compare'),
                    'favorites_count': len(f) if (f := self.request.session.get('favorites', None)) else 0,
                    'compare_count': len(f) if (f := self.request.session.get('compare', None)) else 0,
                    }
        return context


class MainPageView(TemplateView, HeaderView):
    template_name = 'main-page/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banners'] = Banner.objects.all()
        context['slider_config'] = SliderConfiguration.get_solo()
        context['popular_categories'] = PopularCategory.objects.all()

        return context


class ProductListsMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {
            'fav_id_list': self.request.session.get('favorites', list()),
            'comp_id_list': self.request.session.get('compare', list()),
            'url_product_actions': reverse('root_app:product_actions'),
        }
        return context


def group_products_by_categories(id_list):
    grouped_dict = dict()
    for product in Product.objects.filter(id__in=id_list):
        product_main_category = Category.objects.filter(productplacement__product=product).order_by('level').first()
        if product_main_category.slug in grouped_dict.keys():
            grouped_dict[product_main_category.slug]['products'].append(product)
        else:
            grouped_dict[product_main_category.slug] = {
                'category': product_main_category,
                'products': [product]
            }
    return grouped_dict


class FavoritesView(TemplateView, HeaderView, ProductListsMixin):
    template_name = 'main-page/favorites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id_list = [int(product_id) for product_id in context['fav_id_list']]
        context['grouped_dict'] = group_products_by_categories(id_list)
        return context


class CompareView(TemplateView, HeaderView, ProductListsMixin):
    template_name = 'main-page/compare.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id_list = [int(product_id) for product_id in context['comp_id_list']]
        categories_data = group_products_by_categories(id_list)
        # print(categories_data)
        for category_data in categories_data.items():
            category = category_data[1]['category']
            products = category_data[1]['products']
            second_categories = [sc for sc in Category.objects.filter(
                productplacement__product__in=products).exclude(id=category.id).distinct()]
            category_data[1]['second_categories'] = second_categories

        context['grouped_dict'] = categories_data
        return context
