from django.db.models import Subquery, When, ImageField, ExpressionWrapper
from django.db.models.expressions import OuterRef, Case, F
from django.shortcuts import render

# from ROOTAPP.views import HeaderView
from django.urls import reverse

from catalog.models import Product, Category, ProductImage
from main_page.models import Banner, Menu, SitePhone, Schedule, PopularCategory, PopularProduct, NewProduct
from servises import get_products_annotated_prices
from site_settings.models import SliderConfiguration, HeaderConfiguration, PhotoPlug
from django.views.generic.base import TemplateView
from django.views.generic.base import ContextMixin


class MainPageView(TemplateView):
    template_name = 'main-page/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {
            'banners': Banner.objects.all(),
            'slider_config': SliderConfiguration.get_solo(),
            'popular_categories': PopularCategory.objects.all(),
            'popular_products': PopularProduct.with_price.all(),
            'new_products': NewProduct.with_price.all(),
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


class FavoritesView(TemplateView):
    template_name = 'main-page/favorites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id_list = [int(product_id) for product_id in self.request.session.get('favorites', list())]
        context['grouped_dict'] = group_products_by_categories(id_list)
        return context


class CompareView(TemplateView):
    template_name = 'main-page/compare.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(context)
        id_list = [int(product_id) for product_id in self.request.session.get('compare', list())]
        categories_data = group_products_by_categories(id_list)
        for category_data in categories_data.items():
            category = category_data[1]['category']
            products = category_data[1]['products']
            second_categories = [sc for sc in Category.objects.filter(
                productplacement__product__in=products).exclude(id=category.id).distinct()]
            category_data[1]['second_categories'] = second_categories

        context['grouped_dict'] = categories_data
        return context
