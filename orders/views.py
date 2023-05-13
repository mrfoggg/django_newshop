import json
from collections import namedtuple

import django
import ipinfo
import jsonview
import requests
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from jsonview.decorators import json_view
# from oauth2client.client import AccessTokenCredentials, Credentials
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers import geocoder

# from nova_poshta.services.google_services import create_contact
from orders.models import ByOneclick, OneClickUserSectionComment
from ROOTAPP.models import Person, PersonPhone, Phone, Messenger
from site_settings.models import APIkeyIpInfo, OAuthGoogle


def create_one_click_order(request):
    clean_phone_str = ''.join(x for x in request.POST.get('phonenumber') if x.isdigit())
    number = PhoneNumber.from_string(clean_phone_str, region='UA')

    if not geocoder.description_for_number(number, "ru"):
        return JsonResponse({'result': False}, status=200)
    else:
        phone_obj = Phone.objects.get_or_create(number=number.as_e164)[0]
        persons = PersonPhone.objects.filter(phone=phone_obj)

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        access_token = APIkeyIpInfo.get_solo().api_key
        handler = ipinfo.getHandler(access_token)

        details_ip = ip

        one_click = ByOneclick(phone=phone_obj, product_id=int(request.POST.get('product_id')),
                               session_key=request.session.session_key, user_ip_info=details_ip)

        if persons.count() == 1:
            one_click.contact_id = persons.values_list('person', flat=True)[0]

        one_click.save()
        one_clicks_amount = ByOneclick.objects.filter(session_key=request.session.session_key, is_active=True).count()
        new_item_html = render_to_string(
            'one_click_user_section_item.html', {'oneclick': one_click}, request
        )
        # create_contact()
        return JsonResponse({'result': True, 'phone': str(phone_obj), 'one_click_id': one_click.id,
                             'product': one_click.product.name, 'new_item_html': new_item_html,
                             'one_clicks_amount': one_clicks_amount}, status=200)


def oneclick_add_comment(request):
    new_user_comment = OneClickUserSectionComment(
        order_id=request.POST.get("one_click_id"), comment_type=2, description=request.POST.get("comment_text")
    )
    # credentials = AccessTokenCredentials('<an access token>',
    #                                      'my-user-agent/1.0')
    new_user_comment.save()
    # print('django.middleware.csrf.get_token(request) === ', django.middleware.csrf.get_token(request))
    return JsonResponse({'posted_time': new_user_comment.created.strftime("%Y-%m-%d %H:%M"),
                         'posted_text': new_user_comment.description, 'csrf': django.middleware.csrf.get_token(request)
                         }, status=200)


def cancel_oneclick(request):
    oneclick = ByOneclick.objects.get(id=request.POST.get('one_click_id'))
    oneclick.status = 7
    oneclick.is_active = False
    oneclick.save()
    one_clicks_amount = ByOneclick.objects.filter(session_key=request.session.session_key, is_active=True).count()
    return JsonResponse({'cancel_text': 'Заявку відмінено', 'one_clicks_amount': one_clicks_amount}, status=200)


def pre_create_order(request):
    new_contact = Person(
        first_name=request.POST.get('first_name'), last_name=request.POST.get('first_name'),

    )
    print(request)
    return JsonResponse({}, status=200)


@json_view
def get_person_info_ajax(request):
    person_id = request.POST.get('person_id')
    person = Person.objects.get(id=person_id) if person_id else Person.objects.none()
    dropper_available = not (person.is_dropper or person.is_group_buyer) if person_id else False
    group_price_types = list(person.pricetypepersonbuyer_set.values('id', 'name')) if person_id else []
    # print('GET_PERSON_INFO_AJAX ', group_price_types)
    return {
        'dropper_available': dropper_available, 'group_price_types': group_price_types
    }


@json_view
def get_persons_and_contacts_by_phone_ajax(request):
    phone_id = request.POST.get('phone_id')
    p_items = []
    PersonObj = namedtuple('PersonObj', 'id name link is_main_phone is_delivery_phone')
    for p in Person.objects.filter(phones__phone_id=phone_id):
        p_items.append(PersonObj(
            p.id, p.__str__(), p.admin_url, str(p.main_phone_id) == phone_id, str(p.delivery_phone_id) == phone_id
        )._asdict())
    return {'persons': p_items}


# для buttonAddNumberToPersonAjax в client_order_admin_form
@json_view
def button_add_number_to_person_ajax(request):
    data = request.POST
    mode = data.get('mode')
    person_id, phone_id = data.get('person_id'), data.get('phone_id')
    # person = Person.objects.get(id=person_id)
    phone = Phone.objects.get(id=phone_id)
    action = data.get('action')
    PersonPhoneInfo = namedtuple(
        'PersonPhoneInfo', [
            'number', 'chats_links', 'added', 'viber', 'telegram', 'whats_up'
        ], defaults=['', '', None, None, None, None]
    )
    print('MODE - ', mode)
    print('action - ', action)
    if mode == 'check':
        return PersonPhoneInfo(
            str(phone.number)[4:], phone.get_all_chat_links,
            PersonPhone.objects.filter(person_id=person_id, phone_id=phone_id).exists() if person_id else None,
            1 in phone.messengers.values_list('type', flat=True),  # viber
            2 in phone.messengers.values_list('type', flat=True),  # telegram
            3 in phone.messengers.values_list('type', flat=True),  # whats_up
        )._asdict()
        # show_button = not PersonPhone.objects.filter(person_id=person_id, phone_id=phone_id).exists()
        # return {'show_button': show_button}
    else:
        match data.get('mode'):
            case 'add_to_person':
                if action == 'add':
                    PersonPhone.objects.create(person_id=person_id, phone_id=phone_id)
                elif action == 'remove':
                    removed_pp = PersonPhone.objects.get(person_id=person_id, phone_id=phone_id).delete()
            case 'viber':
                if action == 'add':
                    phone.messengers.add(Messenger.objects.get(type=1))
                elif action == 'remove':
                    phone.messengers.remove(Messenger.objects.get(type=1))
            case 'telegram':
                if action == 'add':
                    phone.messengers.add(Messenger.objects.get(type=2))
                elif action == 'remove':
                    phone.messengers.remove(Messenger.objects.get(type=2))
            case 'whatsapp':
                if action == 'add':
                    phone.messengers.add(Messenger.objects.get(type=3))
                elif action == 'remove':
                    phone.messengers.remove(Messenger.objects.get(type=3))
        return {}

