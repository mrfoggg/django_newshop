from django.core.paginator import Paginator
from django.db.models import Q, Min, Max, F
from django.db.models.expressions import OuterRef, Case, When
from django.urls import reverse
from ROOTAPP.forms import AddressForm
from ROOTAPP.models import Settlement
from catalog.models import Category, Brand, ProductSeries, ProductPrice, Product, ShotAttribute
from django.views.generic.detail import DetailView


class CategoryView(DetailView):
    template_name = 'catalog/category.html'
    model = Category
    query_pk_and_slug = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.request.GET
        input_listing = context['category'].listing
        category = context['category']

        context |= {
            'wide_sections': data.getlist('sections-status'), 'filtered': True if data else False,
            'filters': category.full_filters_list, 'checked_filters': [],
            # 'photo_plug': PhotoPlug.get_solo().image,
            'filter_price_applied': 'false',
            'page_num': data['paginator'][0] if data and 'paginator' in data.keys() else 1,
            'page_type': 'category',
        }
        if data:
            context['listing_sort'] = data.getlist('listing_sort')[0]
        some_filter_checked = False

        # заполняем основной массив данных для фильтров товаров кроме данных о резульeтатах поиска каждого фильтра
        filters_and_val_variant = []
        full_list_filtering = Q()
        if Brand.objects.filter(product__productplacement__category=category).exists():
            filter_item = {'name': 'Бренди', 'slug': 'brands', 'type': 'brands', 'val_variants': []}
            list_selected = data.getlist('brands') if 'brands' in data.keys() else []
            brand_filter_params = Q()
            selected_brand_list_id = []
            for brand in Brand.objects.filter(product__productplacement__category=category).distinct():
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
                products__productplacement__category=category,
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

        for f in category.full_filters_list:
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
            Q(product__productplacement__category=category) & full_list_filtering).aggregate(Min('price'),
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
            price_from_filter_params = Q(total_price__gte=context['price_from'])
            full_list_filtering &= price_from_filter_params
            filter_item = {'queryset': price_from_filter_params, 'type': 'price'}
            filters_and_val_variant.append(filter_item)

        if data and 'price_to' in data.keys():
            context['price_to'] = data['price_to']
            context['filter_price_applied'] = 'true'
            price_to_filter_params = Q(total_price__lte=context['price_to'])
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
                listing_for_count = input_listing
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

        context['category_listing'] = products_with_characteristics
        context['total_pages'] = paginator.num_pages
        context['page_range'] = paginator.page_range
        context['current_page'] = int(context['page_num'])
        context['total'] = input_listing.filter(full_list_filtering).count()
        return context


class ProductView(DetailView):
    template_name = 'catalog/product.html'
    model = Product
    query_pk_and_slug = True
    queryset = Product.with_price.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context['product']
        context['settlement_from'] = None
        settlement = Settlement.objects.filter(personsettlement__person__productsupplier__product=product)

        if settlement.exists():
            settlement = settlement.first()
            # context['settlement_from'] = f'{settlement.type.description_ua} {settlement.description_ua} ' \
            #                              f'({settlement.area.description_ua})'
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
            'type_category': 'product',
            'url_get_delivery_cost': reverse('root_app:get_delivery_cost'),
            'url_product_actions': reverse('root_app:product_actions'),
            'size': True if product.width or product.length or product.height or product.weight else False,
            'package_size': True if product.package_width or product.package_length or product.package_height else False,
            'address_form': AddressForm,
            'is_loved': str(product.id) in context['fav_id_list'],
            'is_compared': str(product.id) in context['comp_id_list'],
        }
        viewed_dict = self.request.session.get('viewed', list())
        if str(product.id) not in viewed_dict[-5:]:
            viewed_dict.append(str(product.id))
        if len(viewed_dict) > 30:
            viewed_dict.pop(0)
        self.request.session['viewed'] = viewed_dict
        return context
