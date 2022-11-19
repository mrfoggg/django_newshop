import json

import django
import ipinfo

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from oauth2client.client import AccessTokenCredentials, Credentials
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers import geocoder
# Create your views here.
from ROOTAPP.models import Phone, PersonPhone, Person
# from ROOTAPP.services.google_services import create_contact
from orders.models import OneClickUserSectionComment, ByOneclick
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
