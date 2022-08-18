from copy import copy, deepcopy

from django.db.models import Q
from django.db.models.expressions import OuterRef
from django.shortcuts import render

# Create your views here.
from ROOTAPP.views import HeaderView
from catalog.models import Category, Brand
from django.views.generic.detail import DetailView

from site_settings.models import PhotoPlug


class CategoryView(DetailView, HeaderView):
    template_name = 'catalog/category.html'
    model = Category
    query_pk_and_slug = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.request.GET

        context['wide_sections'] = data.getlist('sections-status')
        context['filtered'] = True if data else False
        filtered_listing = context['category'].listing

        context['filters'] = context['category'].full_filters_list
        context['checked_filters'] = []
        context['photo_plug'] = PhotoPlug.get_solo().image

        # заполняем основной массив данных для фильтров товаров кроме данных о резульeтатах поиска каждого фильтра
        filters_and_val_variant = []
        full_list_filtering = Q()

        context['brands_exists'] = Brand.objects.filter(product__productplacement__category=context['category']).exists()
        if context['brands_exists']:
            filter_item = {'name': 'Бренди', 'slug': 'brands', 'type': 'brands', 'val_variants': []}
            list_selected = data.getlist('brands') if 'brands' in data.keys() else []
            brand_filter_params = Q()
            for brand in Brand.objects.filter(product__productplacement__category=context['category']).distinct():
                val_variant_item = {'slug': brand.id, 'name': brand.name, 'total_products': None, 'is_checked': False}
                if data and str(val_variant_item['slug']) in list_selected:
                    brand_filter_params = Q(product__brand=brand)
                    val_variant_item['is_checked'] = True
                    context['checked_filters'].append([brand.name, brand.id, 'brands'])
                filter_item['val_variants'].append(val_variant_item)
            filters_and_val_variant.append(filter_item)
            filter_item['queryset'] = brand_filter_params
            full_list_filtering &= brand_filter_params

        for f in context['category'].full_filters_list:
            filter_item = {
                'name': f.attribute, 'slug': f.attribute.slug, 'type': f.attribute.type_of_value, 'val_variants': [],
            }
            list_selected = data.getlist(filter_item['slug']) if filter_item['slug'] in data.keys() else []
            filter_params = Q()
            if filter_item['type'] == 3:
                filter_item['val_variants'] = [
                    {'slug': 'true', 'name': f.attribute.str_true, 'total_products': None, 'is_checked': False},
                ]
                if data and 'true' in list_selected:
                    filter_item['val_variants'][0]['is_checked'] = True
                    context['checked_filters'].append([f'{f.attribute.name}: {f.attribute.str_true}',
                                                       'true', f.attribute.slug])
                    filter_params |= Q(
                        product__characteristics__contains={filter_item['slug']: True}
                    )

            elif filter_item['type'] in [4, 5]:
                for val_variant in f.attribute.fixed_values.all():
                    val_variant_item = {
                        'slug': val_variant.slug, 'name': val_variant.name, 'total_products': None, 'is_checked': False
                    }
                    if data and val_variant_item['slug'] in list_selected:
                        val_variant_item['is_checked'] = True
                        context['checked_filters'].append([val_variant.name, val_variant.slug, f.attribute.slug])
                        # filter_item['checked_values_slugs'].append(val_variant.slug)
                        match filter_item['type']:
                            case 4:
                                filter_params |= Q(
                                    product__characteristics__contains={filter_item['slug']: val_variant_item['slug']}
                                )
                            case 5:
                                filter_params |= Q(
                                    product__characteristics__contains={filter_item['slug']: [val_variant_item['slug']]}
                                )
                    filter_item['val_variants'].append(val_variant_item)
            full_list_filtering &= filter_params
            # filtered_listing = filtered_listing.filter(filter_params)
            filter_item['queryset'] = filter_params
            filters_and_val_variant.append(filter_item)

        context['filters_and_val_variant'] = filters_and_val_variant
        context['category_listing'] = filtered_listing
        context['checked_filters_len'] = len(context['checked_filters'])
        for ff in context['filters_and_val_variant']:
            # if ff['slug'] == 'brands':
            #     continue
            prev_qs = ff['queryset']
            for val in ff['val_variants']:
                match ff['type']:
                    case 3:
                        ff['queryset'] = Q(product__characteristics__contains={ff['slug']: True})
                    case 4:
                        ff['queryset'] = Q(product__characteristics__contains={ff['slug']: val['slug']})
                    case 5:
                        ff['queryset'] = Q(product__characteristics__contains={ff['slug']: [val['slug']]})
                    case 'brands':
                        ff['queryset'] = Q(product__brand=val['slug'])
                listing_for_count = context['category_listing']
                for fff in context['filters_and_val_variant']:
                    listing_for_count = listing_for_count.filter(fff['queryset'])
                val['total_products'] = listing_for_count.count()
            ff['queryset'] = prev_qs
        context['category_listing'] = context['category_listing'].filter(full_list_filtering)
        return context
