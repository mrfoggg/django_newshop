from copy import copy, deepcopy

from django.db.models import Q
from django.db.models.expressions import OuterRef
from django.shortcuts import render

# Create your views here.
from ROOTAPP.views import HeaderView
from catalog.models import Category
from django.views.generic.detail import DetailView


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

        # заполняем основной массив данных для фильтров товаров кроме данных о резульeтатах поиска каждого фильтра
        filters_and_val_variant = []
        for f in context['category'].full_filters_list:
            filter_item = {
                'name': f.attribute, 'slug': f.attribute.slug, 'type': f.attribute.type_of_value, 'val_variant': [],
                # 'checked_values_slugs': [],
            }
            list_selected = data.getlist(filter_item['slug']) if filter_item['slug'] in data.keys() else []
            filter_params = Q()

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
                filter_item['val_variant'].append(val_variant_item)
            filtered_listing = filtered_listing.filter(filter_params)
            filter_item['queryset'] = filter_params
            filters_and_val_variant.append(filter_item)

        context['filters_and_val_variant'] = filters_and_val_variant
        context['category_listing'] = filtered_listing
        for ff in context['filters_and_val_variant']:
            prev_qs = ff['queryset']
            for val in ff['val_variant']:
                match ff['type']:
                    case 4:
                        ff['queryset'] = Q(
                            product__characteristics__contains={ff['slug']: val['slug']}
                        )
                    case 5:
                        ff['queryset'] = Q(
                            product__characteristics__contains={ff['slug']: [val['slug']]}
                        )
                listing_for_count = context['category'].listing
                for fff in context['filters_and_val_variant']:
                    listing_for_count = listing_for_count.filter(fff['queryset'])
                    val['total_products'] = listing_for_count.count()
                ff['queryset'] = prev_qs
        return context
