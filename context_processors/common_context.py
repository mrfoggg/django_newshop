from allauth.socialaccount.forms import DisconnectForm, SignupForm
from django.db.models import Case, F, OuterRef, Subquery, When
from django.forms import modelform_factory
from django.urls import reverse

from catalog.models import Product, ProductImage
from main_page.models import Menu, Schedule, SitePhone
from orders.models import ByOneclick
from ROOTAPP.forms import PersonEmailForm
from ROOTAPP.models import Person
from servises import get_products_annotated_prices
from site_settings.models import HeaderConfiguration, PhotoPlug


def header_context(request):
    context = {
        'contact_phones': SitePhone.objects.all(), 'schedule': Schedule.objects.all(),
        'menu_items': Menu.objects.filter(level=0).only('parent', 'title', 'image').select_related(
            'parent').prefetch_related('children__children__children'),
        'header_config': HeaderConfiguration.get_solo(), 'photo_plug': PhotoPlug.get_solo().image,
        'favorites_count': len(f) if (f := request.session.get('favorites', None)) else 0,
        'compare_count': len(f) if (f := request.session.get('compare', None)) else 0,
        'back_link': request.META.get('HTTP_REFERER') if request.META.get('HTTP_REFERER') else '/',
        'cabinet_title_text': f"Вітаємо {request.user.last_name if request.user.last_name else ''} "
                              f"{request.user.first_name}. "
                              f"Ви увійшли в свій особистий кабінет " if request.user.is_authenticated else
        "Для входу в кабінет або щоб створити обліковий запис вкажіть ваш номер телефону",
        'email_form': PersonEmailForm,
        'show_email_login_section': request.user.is_authenticated and not request.user.password and not request.user.email,
        'show_set_password_link': request.user.is_authenticated and request.user.email and not request.user.password,
        'show_change_password_link': request.user.is_authenticated and request.user.email and request.user.password,
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
        # 'one_click_id_list': (one_click_id_list := request.session.get('one_click_id_list', list())),
        'one_click_obj_list': ByOneclick.objects.filter(
            session_key=request.session.session_key, is_active=True).order_by('created'),
        'url_product_actions': reverse('root_app:product_actions'),
        'oneclick_add_comment_action_url': reverse('orders:oneclick_add_comment'),
        'cancel_oneclick_action_url': reverse('orders:cancel_oneclick'),
        'pre_create_order_action_url': reverse('orders:pre_create_order'),
        'get_and_check_registration_phone_action_url': reverse('root_app:get_and_check_registration_phone'),
        'get_registration_name_action_url': reverse('root_app:get_registration_name'),
        'verify_sms_token_action_url': reverse('root_app:verify_sms_token'),
        'regenerate_sms_token_action_url': reverse('root_app:regenerate_sms_token'),
        'logout_action_url': reverse('root_app:logout'),
        'viewed_products': viewed,
        'viewed_mode': ' viewed_slider_mode' if len(viewed) > 5 else ' viewed_grid_mode' if len(viewed) else '',
        'products_obj_in_basket': pib_list_dicts_with_amount,
        'products_id_in_basket': products_id_in_basket,
        'basket_total': {'total_amount': total_amount, 'total_sum': total_sum},
        'one_click_total_amount': ByOneclick.objects.filter(
            session_key=request.session.session_key, is_active=True).count()
    }
    return context
