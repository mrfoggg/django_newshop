from django.db.models import Subquery, OuterRef, Case, When, F
from django.urls import reverse
from catalog.models import Product, ProductImage
from main_page.models import SitePhone, Schedule, Menu
from servises import get_products_annotated_prices
from site_settings.models import HeaderConfiguration, PhotoPlug


def header_context(request):
    context = {
        'contact_phones': SitePhone.objects.all(), 'schedule': Schedule.objects.all(),
        'menu_items': Menu.objects.filter(level=0).only('parent', 'title', 'image').select_related(
            'parent').prefetch_related('children__children__children'),
        'header_config': HeaderConfiguration.get_solo(), 'photo_plug': PhotoPlug.get_solo().image,
        'favorites_link': reverse('main_page:favorites'),
        'compare_link': reverse('main_page:compare'),
        'checkout_link': reverse('root_app:checkout'),
        'favorites_count': len(f) if (f := request.session.get('favorites', None)) else 0,
        'compare_count': len(f) if (f := request.session.get('compare', None)) else 0,
    }

    return context


def product_lists_conntext(request):
    viewed_id_list = request.session.get('viewed', list())
    viewed_products_dict = {
        str(product.id): product for product
        in Product.with_price.filter(id__in=viewed_id_list)
    }
    viewed = [viewed_products_dict[id_pr] for id_pr in viewed_id_list]

    products_id_in_basket = request.session.get('basket', dict())

    annotated_basket_products_object = get_products_annotated_prices(products_id_in_basket).annotate(
        first_image_annotated=Subquery(ProductImage.objects.filter(product=OuterRef('pk')).values('image')[:1])
    ).annotate(
        thumb=Case(
            When(first_image_annotated__isnull=False, then=F('first_image_annotated')),
            default=Subquery(PhotoPlug.objects.values('image')[:1])
        )
    )

    products_in_basket_dict = {str(pr.id): pr for pr in annotated_basket_products_object}
    total_sum = 0
    total_amount = 0
    pib_list_dicts_with_amount = []

    for pr in products_id_in_basket.items():
        product = products_in_basket_dict[pr[0]]
        amount = pr[1]
        total_amount += int(pr[1])
        sum = round(product.total_price, 2) * int(pr[1])
        total_sum += sum
        pib_list_dicts_with_amount.append({
            'product': product,
            'amount': amount, 'price': round(product.total_price, 2),
            'total': sum
        })

    context = {
        'fav_id_list': request.session.get('favorites', list()),
        'comp_id_list': request.session.get('compare', list()),
        'url_product_actions': reverse('root_app:product_actions'),
        'viewed_products': viewed,
        'viewed_mode': ' viewed_slider_mode' if len(viewed) > 5 else ' viewed_grid_mode' if len(viewed) else '',
        'products_obj_in_basket': pib_list_dicts_with_amount,
        'products_id_in_basket': products_id_in_basket,
        'basket_total': {'total_amount': total_amount, 'total_sum': total_sum}
    }
    return context
