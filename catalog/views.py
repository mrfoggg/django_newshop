from django.core.paginator import Paginator
from django.db.models import Q, Min, Max, F
from django.db.models.expressions import Case, When
from django.http.response import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from ROOTAPP.forms import AddressForm
from ROOTAPP.models import Settlement
from catalog.models import Category, Brand, ProductSeries, Product, ShotAttribute, CategoryAddictProduct
from django.views.generic.detail import DetailView


# from django.views.decorators.csrf import csrf_exempt


# from braces.views import CsrfExemptMixin


# @method_decorator(csrf_exempt, name='dispatch')

class CategoryView(View):
    template_name = 'catalog/category.html'

    # @method_decorator(csrf_exempt)
    # def dispatch(self, request, *args, **kwargs):
    #     return super(CategoryView, self).dispatch(request, *args, **kwargs)

    def get(self, request, slug, str_url_data):
        return render(
            request=request, template_name=self.template_name,
            context=self.get_context_data(slug, self.request.GET, 'get', str_url_data)
        )

    def post(self, request, slug, str_url_data):

        full_context = self.get_context_data(slug, self.request.POST, 'post', str_url_data)

        listing_html = render_to_string(
            'category_listing.html', {'category_listing': full_context['category_listing']}, request
        )
        ajax_filters_data_list = list()
        for f in full_context['filters_and_val_variant']:
            if f['type'] == 'price':
                continue
            filter_data = {'filter_slug': f['slug'], 'filter_values': []}
            for v in f['val_variants']:
                filter_data['filter_values'].append({'value_slug': v['slug'], 'total_products': v['total_products']})
            ajax_filters_data_list.append(filter_data)
        return JsonResponse({
            'listing_html': listing_html,
            'checked_filters_len': full_context['checked_filters_len'],
            'checked_filters': full_context['checked_filters'],
            'ajax_filters_data': ajax_filters_data_list,
            'total': full_context['total'], 'total_pages': full_context['total_pages'],
            'current_page': full_context['current_page'],
            'product_series': full_context['product_series'],
            'page_range': [p for p in full_context['page_range']]
            # 'current_url': full_context['category'].get_absolute_url()

        })

    def get_context_data(self, slug, data, type_of_request, str_url_data):
        context = {}
        category = Category.objects.get(slug=slug)
        input_listing = category.listing
        filter_price_applied = False

        url_data = {}
        while str_url_data:
            pos_key = str_url_data.find('__')
            if pos_key == -1:
                break
            key = str_url_data[:pos_key]
            str_url_data = str_url_data[pos_key + 2:]
            pos_val = str_url_data.find('__')
            if pos_val == -1:
                val = str_url_data.split('--')
            else:
                val = str_url_data[:pos_val].split('--')
                # val = str_url_data[:pos_val]
            str_url_data = str_url_data[pos_val + 2:]
            url_data[key] = val

        context |= {
            'category': category,
            'wide_sections': data.getlist('sections-status'), 'filtered': True if data else False,
            # 'filters': category.full_filters_list,
            'checked_filters': [],
            # 'filter_price_applied': 'false',
            'page_num': data['paginator'][0] if data and 'paginator' in data.keys() else 1,
        }
        if data:
            context['listing_sort'] = data.getlist('listing_sort', default=['default_sort'])[0]
        some_filter_checked = False

        # заполняем основной массив данных для фильтров товаров кроме данных о резульeтатах поиска каждого фильтра
        filters_and_val_variant = []
        full_list_filtering = Q()
        if Brand.objects.filter(product__productplacement__category=category).exists():
            filter_item = {'name': 'Бренди', 'slug': 'brands', 'type': 'brands', 'val_variants': []}
            # list_selected = data.getlist('brands') if 'brands' in data.keys() else []
            list_selected = url_data['brands'] if 'brands' in url_data.keys() else []
            brand_filter_params = Q()
            selected_brand_list_id = []
            for brand in Brand.objects.filter(product__productplacement__category=category).distinct():
                val_variant_item = {'slug': brand.slug, 'name': brand.name, 'total_products': None, 'is_checked': False}
                if brand.slug in list_selected:
                    some_filter_checked = True
                    brand_filter_params |= Q(product__brand=brand)
                    val_variant_item['is_checked'] = True
                    context['checked_filters'].append([brand.name, brand.slug, 'brands'])
                    selected_brand_list_id.append(brand.slug)
                filter_item['val_variants'].append(val_variant_item)
            filter_item['queryset'] = brand_filter_params
            full_list_filtering &= brand_filter_params

            product_series = ProductSeries.objects.filter(
                products__productplacement__category=category,
                products__brand__slug__in=selected_brand_list_id
            )
            filters_and_val_variant.append(filter_item)

            if product_series.exists():
                filter_item = {'name': 'Лінійки товарів', 'slug': 'series', 'type': 'series', 'val_variants': []}
                # list_selected = data.getlist('series') if 'series' in data.keys() else []
                list_selected = url_data['series'] if 'series' in url_data.keys() else []
                series_filter_params = Q()

                for ser in product_series.distinct():
                    val_variant_item = {'slug': ser.slug, 'name': ser.name, 'total_products': None, 'is_checked': False}
                    if ser.slug in list_selected:
                        series_filter_params |= Q(product__series=ser)
                        val_variant_item['is_checked'] = True
                        context['checked_filters'].append([ser.name, ser.slug, 'series'])
                    filter_item['val_variants'].append(val_variant_item)
                filters_and_val_variant.append(filter_item)
                filter_item['queryset'] = series_filter_params
                full_list_filtering &= series_filter_params

        for f in category.full_filters_list:

            filter_item = {
                'name': f.attribute, 'slug': f.attribute.slug, 'type': f.attribute.type_of_value, 'val_variants': [],
            }
            # list_selected = data.getlist(filter_item['slug']) if filter_item['slug'] in data.keys() else []
            list_selected = url_data[filter_item['slug']] if filter_item['slug'] in url_data.keys() else []
            filter_params = Q()
            if filter_item['type'] == 3:
                filter_item['val_variants'] = [
                    {'slug': 'true', 'name': f.attribute.str_true, 'total_products': None, 'is_checked': False},
                ]
                if 'true' in list_selected:
                    some_filter_checked = True
                    filter_item['val_variants'][0]['is_checked'] = True
                    context['checked_filters'].append([f'{f.attribute.name}: {f.attribute.str_true}',
                                                       'true', f.attribute.slug])
                    filter_params |= Q(product__characteristics__contains={filter_item['slug']: True})

            elif filter_item['type'] in [4, 5]:
                for val_variant in f.attribute.fixed_values.all():
                    val_variant_item = {
                        'slug': val_variant.slug, 'name': val_variant.name, 'total_products': None, 'is_checked': False
                    }
                    if val_variant.slug in list_selected:
                        some_filter_checked = True
                        val_variant_item['is_checked'] = True
                        context['checked_filters'].append([val_variant.name, val_variant.slug, f.attribute.slug])
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

        prices = input_listing.aggregate(Max('total_price'), Min('total_price'))

        context['price_min'] = context['price_from'] = prices['total_price__min']
        context['price_max'] = context['price_to'] = prices['total_price__max']

        if data and 'price_from' in data.keys():
            context |= {'price_from': data['price_from']}
            if float(context['price_min']) != float(context['price_from']):
                filter_price_applied = True
                price_from_filter_params = Q(total_price__gte=context['price_from'])
                full_list_filtering &= price_from_filter_params
                filter_item = {'queryset': price_from_filter_params, 'type': 'price'}
                filters_and_val_variant.append(filter_item)

        # if data and 'price_to' in data.keys():
        if data and 'price_to' in data.keys():
            context |= {'price_to': data['price_to']}
            if float(context['price_max']) != float(context['price_to']):
                filter_price_applied = True
                price_to_filter_params = Q(total_price__lte=context['price_to'])
                full_list_filtering &= price_to_filter_params
                filter_item = {'queryset': price_to_filter_params, 'type': 'price'}
                filters_and_val_variant.append(filter_item)

        if filter_price_applied:
            context['checked_filters'].append([[context["price_from"], context["price_to"]], 'price'])

        context['filters_and_val_variant'] = filters_and_val_variant

        context['checked_filters_len'] = len(context['checked_filters'])
        if type_of_request == 'post':
            context['product_series'] = {}
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
                        ff['queryset'] = Q(product__brand__slug=val['slug'])
                    case 'series':
                        ff['queryset'] = Q(product__series__slug=val['slug'])
                listing_for_count = input_listing
                for fff in context['filters_and_val_variant']:
                    listing_for_count = listing_for_count.filter(fff['queryset'])
                val['total_products'] = listing_for_count.count()
                if not val['total_products']:
                    val['is_checked'] = False
                    j = 0
                    for v in context['checked_filters']:
                        if v[1] == val['slug'] and v[2] == ff['type']:
                            del context['checked_filters'][j]
                        j += 1
                elif ff['type'] == 'series' and type_of_request == 'post':
                    context['product_series'][val['slug']] = {
                        'name': val['name'], 'total_products': val['total_products']}

            ff['queryset'] = prev_qs

        listing_variants = {
            "default_sort": input_listing,
            'sort_from_cheap_to_expensive': input_listing.order_by('total_price'),
            'sort_from_expensive_to_cheap': input_listing.order_by('-total_price'),
        }

        if data:
            listing = listing_variants[context['listing_sort']].filter(full_list_filtering)
        else:
            listing = input_listing.filter(full_list_filtering)

        paginator = Paginator(listing, 25)
        paginated_listing = paginator.get_page(context['page_num'])

        # для варианта 2
        listing_attributes = ShotAttribute.objects.filter(
            category__productplacement__product__productplacement__category=category).distinct().select_related(
            'attribute__unit_of_measure'
        ).annotate(
            display_name=Case(
                When(name__isnull=False, then=F('name')),
                default=F('attribute__name')
            )
        ).prefetch_related('attribute__fixed_values')

        attr_data_dict = dict()
        values_dict = dict()
        for sh_attr in listing_attributes.all():
            attr_data_dict[sh_attr.attribute.slug] = {
                'display_name': sh_attr.display_name, 'type': sh_attr.attribute.type_of_value,
                'unit_of_measure': sh_attr.attribute.unit_of_measure, 'default': sh_attr.attribute.default_str_value
            }
            for val in sh_attr.attribute.fixed_values.values('name', 'slug'):
                values_dict[val['slug']] = val['name']
        products_with_characteristics = list()
        for pr in paginated_listing:
            minidescription_data = list()
            for ch_key, ch_val in pr.product.shot_attributes_id_list:
                attr_data = attr_data_dict[ch_key]
                ch_name = attr_data['display_name']
                ch_unit_of_measure = attr_data['unit_of_measure']
                match attr_data['type']:
                    case 1:
                        text_value = ch_val
                    case 2:
                        text_value = str(ch_val) + f' {ch_unit_of_measure.name}' if ch_unit_of_measure else ''
                    case 4:
                        if not ch_val and not attr_data['default']:
                            continue
                        text_value = values_dict[ch_val] if ch_val else attr_data['default']
                    case 5:
                        if not ch_val and not attr_data['default']:
                            continue
                        text_value = ', '.join([values_dict[v] for v in ch_val]) if ch_val else attr_data['default']
                minidescription_data.append([ch_name, text_value])

            product_with_characteristics = {
                'product_obj': pr.product, 'total_price': pr.total_price, 'price': pr.price,
                'annotated_discount': pr.annotated_discount, 'discount_type': pr.discount_type,
                'minidescription_data': minidescription_data
            }
            products_with_characteristics.append(product_with_characteristics)

        context |= {
            'category_listing': products_with_characteristics, 'total_pages': paginator.num_pages,
            'page_range': paginator.page_range, 'current_page': int(context['page_num']),
            'total': input_listing.filter(full_list_filtering).count(),
            # 'checked_checkbox_string_value': data['checked-checkbox-id']
        }

        # if data:
        #     for i in data.keys():
        #         print(i, ': ', data.getlist(i))

        # print(*data, sep='\n')
        # print(*context.items(), sep='\n\n')
        # print(context['checked_filters'])
        # for d in data:
        #     print(d, end="/br")
        # print(values_dict[data['checked-filter-slug']])
        # print(values_dict[data['checked-checkbox-slug']])
        return context


class ProductView(DetailView):
    template_name = 'catalog/product.html'
    model = Product
    query_pk_and_slug = True
    queryset = Product.with_price.all()
    cont = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context['product']
        context['settlement_from'] = None
        settlement = Settlement.objects.filter(personsettlement__person__productsupplier__product=product)

        if settlement.exists():
            settlement = settlement.first()
            context['settlement_from'] = settlement

        categories = {}
        for placement in product.productplacement_set.filter(category__display_in_parent=True):
            if (level := placement.category.level) in categories.keys():
                categories[level].append(placement.category)
            else:
                categories[level] = [placement.category]
        context |= {
            'last_categories': (last_cat := categories[max(categories.keys())]),
            'category': last_cat[0],
            'type_category': 'product', 'by_one_click_link_action': reverse('orders:by_one_click'),
            'url_get_delivery_cost': reverse('root_app:get_delivery_cost'),
            'url_product_actions': reverse('root_app:product_actions'),
            'size': True if product.width or product.length or product.height or product.weight else False,
            'package_size': True if product.package_width or product.package_length or product.package_height else False,
            'address_form': AddressForm, 'addict_product_category': CategoryAddictProduct.objects.filter(
                category__productplacement__product=product
            ).select_related('category').prefetch_related()
        }
        viewed_dict = self.request.session.get('viewed', list())
        if str(product.id) not in viewed_dict[-5:]:
            viewed_dict.append(str(product.id))
        if len(viewed_dict) > 30:
            viewed_dict.pop(0)
        self.request.session['viewed'] = viewed_dict
        # print(self.request.headers)
        return context
