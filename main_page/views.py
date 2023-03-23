import django
from django.contrib.postgres.aggregates import ArrayAgg
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView, View

from catalog.models import Category, Product, ProductImage
from catalog.views import CategoryView, ProductView
from main_page.models import (Banner, Menu, NewProduct, PopularCategory,
                              PopularProduct, Schedule, SitePhone)
from ROOTAPP.forms import PersonalInfoForm
from ROOTAPP.models import Messenger, PersonPhone
from site_settings.models import (HeaderConfiguration, PhotoPlug,
                                  SliderConfiguration)


class MainPageView(TemplateView):
    template_name = 'main-page/index.html'

    def get_context_data(self, **kwargs):
        print('CSRF = ', django.middleware.csrf.get_token(self.request))
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
    for product in Product.with_price.filter(id__in=id_list):
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


@csrf_exempt
def dispatch_view(request, slug, str_url_data=None):
    for model in (Category, Product):
        if model.objects.filter(slug=slug).exists():
            return {'product': ProductView, 'category': CategoryView}.get(
                model.__name__.lower()).as_view()(request, slug=slug, str_url_data=str_url_data)


class CabinetView(TemplateView):
    template_name = 'main-page/cabinet.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.request.user
        person_phones = PersonPhone.objects.filter(person=person).annotate(
            m_id_list=ArrayAgg('phone__messengers', ordering='phone__messengers'),
            # str_phone=models.Value(person, output_field=models.CharField())
        ).values(
            'id', 'phone__number', 'm_id_list', 'phone'
        )
        main_phone_id_query = PersonPhone.objects.filter(
                phone_id=self.request.user.main_phone, person=self.request.user
            )
        delivery_phone_id_query = PersonPhone.objects.filter(
                phone_id=self.request.user.delivery_phone, person=self.request.user
            )
        context |= {
            'personal_info_form': PersonalInfoForm(instance=person),
            'person_phones': person_phones,
            # 'person_phones': PersonPhone.objects.filter(person=person),
            'messengers': Messenger.objects.all(),
            'main_phone_id': main_phone_id_query.first().id if main_phone_id_query.exists() else None,
            'delivery_phone_id': delivery_phone_id_query.first().id if delivery_phone_id_query.exists() else None,
            'phones_one': len(person_phones) == 1
        }
        return context
