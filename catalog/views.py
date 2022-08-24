from copy import copy, deepcopy

from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.db.models.expressions import OuterRef
from django.shortcuts import render

# Create your views here.
from ROOTAPP.views import HeaderView
from catalog.models import Category, Brand, ProductSeries, ProductPrice
from django.views.generic.detail import DetailView

from site_settings.models import PhotoPlug


class CategoryView(DetailView, HeaderView):
    template_name = 'catalog/category.html'
    model = Category
    query_pk_and_slug = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.request.GET

        print(data)
        context |= {
            'wide_sections': data.getlist('sections-status'), 'filtered': True if data else False,
            'filters': context['category'].full_filters_list, 'checked_filters': [],
            'photo_plug': PhotoPlug.get_solo().image,
            'filter_price_applied': 'false',
            'page_num': data['paginator'][0] if data and 'paginator' in data.keys() else 1
        }
        if data:
            context['listing_sort'] = data.getlist('listing_sort')[0]
        some_filter_checked = False

        # заполняем основной массив данных для фильтров товаров кроме данных о резульeтатах поиска каждого фильтра
        filters_and_val_variant = []
        full_list_filtering = Q()
        if Brand.objects.filter(product__productplacement__category=context['category']).exists():
            filter_item = {'name': 'Бренди', 'slug': 'brands', 'type': 'brands', 'val_variants': []}
            list_selected = data.getlist('brands') if 'brands' in data.keys() else []
            brand_filter_params = Q()
            selected_brand_list_id = []
            for brand in Brand.objects.filter(product__productplacement__category=context['category']).distinct():
                val_variant_item = {'slug': brand.id, 'name': brand.name, 'total_products': None, 'is_checked': False}
                if data and str(val_variant_item['slug']) in list_selected:
                    some_filter_checked = True
                    brand_filter_params |= Q(product__brand=brand)
                    val_variant_item['is_checked'] = True
                    context['checked_filters'].append([brand.name, brand.id, 'brands'])
                    selected_brand_list_id.append(brand.id)
                filter_item['val_variants'].append(val_variant_item)
            filter_item['queryset'] = brand_filter_params
            full_list_filtering &= brand_filter_params

            product_series = ProductSeries.objects.filter(
                products__productplacement__category=context['category'],
                products__brand_id__in=selected_brand_list_id
            )
            filters_and_val_variant.append(filter_item)

            if product_series.exists():
                filter_item = {'name': 'Лінійки товарів', 'slug': 'series', 'type': 'series', 'val_variants': []}
                list_selected = data.getlist('series') if 'series' in data.keys() else []
                series_filter_params = Q()

                for ser in product_series.distinct():
                    val_variant_item = {'slug': ser.id, 'name': ser.name, 'total_products': None, 'is_checked': False}
                    if data and str(val_variant_item['slug']) in list_selected:
                        series_filter_params |= Q(product__series=ser)
                        val_variant_item['is_checked'] = True
                        context['checked_filters'].append([ser.name, ser.id, 'series'])
                    filter_item['val_variants'].append(val_variant_item)
                filters_and_val_variant.append(filter_item)
                filter_item['queryset'] = series_filter_params
                full_list_filtering &= series_filter_params

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
                    some_filter_checked = True
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
                        some_filter_checked = True
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
            filter_item['queryset'] = filter_params
            filters_and_val_variant.append(filter_item)

        # if some_filter_checked:
        prices = ProductPrice.objects.filter(
            Q(product__productplacement__category=context['category']) & full_list_filtering).aggregate(Min('price'),
                                                                                                        Max('price'))
        if some_filter_checked:
            pass
        context['price_min'] = prices['price__min']
        context['price_max'] = prices['price__max']
        context['price_from'] = context['price_min']
        context['price_to'] = context['price_max']

        if data and 'price_from' in data.keys():
            context['price_from'] = data['price_from']
            context['filter_price_applied'] = 'true'
            price_from_filter_params = Q(product__productprice__price__gte=context['price_from'])
            full_list_filtering &= price_from_filter_params
            filter_item = {'queryset': price_from_filter_params, 'type': 'price'}
            filters_and_val_variant.append(filter_item)

        if data and 'price_to' in data.keys():
            context['price_to'] = data['price_to']
            context['filter_price_applied'] = 'true'
            price_to_filter_params = Q(product__productprice__price__lte=context['price_to'])
            full_list_filtering &= price_to_filter_params
            filter_item = {'queryset': price_to_filter_params, 'type': 'price'}
            filters_and_val_variant.append(filter_item)

        if data and 'price_from' in data.keys() or data and 'price_to' in data.keys():
            context['checked_filters'].append(
                [f'ціна від {context["price_from"]} грн до {context["price_to"]} грн', '', 'price'])

        context['filters_and_val_variant'] = filters_and_val_variant

        context['checked_filters_len'] = len(context['checked_filters'])
        for ff in context['filters_and_val_variant']:
            if ff['type'] == 'price':
                continue
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
                    case 'series':
                        ff['queryset'] = Q(product__series=val['slug'])
                listing_for_count = context['category'].listing
                for fff in context['filters_and_val_variant']:
                    listing_for_count = listing_for_count.filter(fff['queryset'])
                val['total_products'] = listing_for_count.count()
                if not val['total_products']:
                    val['is_checked'] = False
                    j = 0
                    for v in context['checked_filters']:
                        if v[1] == val['slug']:
                            del context['checked_filters'][j]
                        j += 1
            ff['queryset'] = prev_qs

        listing_variants = {
            "default_sort": context['category'].productplacement_set.order_by('product_position'),
            'sort_from_cheap_to_expensive': context['category'].productplacement_set.order_by(
                'product__productprice__price'),
            'sort_from_expensive_to_cheap': context['category'].productplacement_set.order_by(
                '-product__productprice__price'),
        }
        if data:
            listing = listing_variants[context['listing_sort']].filter(full_list_filtering)
        else:
            listing = context['category'].listing.filter(full_list_filtering)

        paginator = Paginator(listing, 25)

        context['category_listing'] = paginator.get_page(context['page_num'])
        context['total_pages'] = paginator.num_pages
        context['page_range'] = paginator.page_range
        context['current_page'] = int(context['page_num'])
        context['total'] = context['category'].listing.filter(full_list_filtering).count()
        return context
