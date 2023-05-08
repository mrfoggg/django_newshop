import re
from collections import namedtuple
from datetime import datetime, timezone

import django
# import google_auth_oauthlib.flow
import pytz
from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import View
from jsonview.decorators import json_view
from otp_twilio.models import TwilioSMSDevice
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers import geocoder
from sorl.thumbnail import get_thumbnail

from catalog.models import Product
from ROOTAPP.forms import PersonalInfoForm, PersonEmailForm, PersonForm
from ROOTAPP.models import Person, PersonPhone, Phone, get_phone_full_str, other_person_login_this_phone, \
    other_person_not_main, ContactPerson, other_contacts, Messenger
from nova_poshta.models import Settlement, Warehouse, City
from nova_poshta.services import get_settlement_addict_info
from servises import get_products_annotated_prices
from Shop_DJ import settings
from site_settings.models import OAuthGoogle


def calculate_basket(request, basket_dict, product_id=None):
    total_sum = 0
    total_amount = 0
    products_with_prices = get_products_annotated_prices(basket_dict.keys())
    products_by_id = {str(pr.id): pr for pr in products_with_prices}
    for b_item in basket_dict.items():
        total_sum += round(products_by_id[b_item[0]].total_price * int(b_item[1]), 2)
        total_amount += int(b_item[1])
    if product_id:
        if isinstance(product_id, list):
            return total_amount, round(total_sum, 2), {
                pr: round(products_by_id[pr].total_price, 2) for pr in product_id
            }
        else:
            return total_amount, round(total_sum, 2), round(products_by_id[product_id].total_price, 2)
    else:
        return total_amount, round(total_sum, 2)


class ProductActionsView(View):
    def post(self, request):
        product_id = request.POST.get('product_id')
        fav_list = request.session.get('favorites', list())
        comp_list = request.session.get('compare', list())
        basket_dict = request.session.get('basket', dict())

        def add_basket(basket_dict, product_id, mode):
            if product_id not in basket_dict.keys():
                basket_dict[product_id] = 1
                product = Product.objects.get(id=int(product_id))
                im = get_thumbnail(product.first_image, '80x80', crop='center', quality=99)
                request.session['basket'] = basket_dict
                if mode == 'one_product':
                    total_amount, total_sum, pr_total_price = calculate_basket(request, basket_dict, product_id)
                    return {
                        'thumb': im.url, 'name': product.name, 'id': product_id, 'pr_url': product.get_absolute_url(),
                        'price': str(pr_total_price).replace('.', ','),
                        'total_sum': str(total_sum).replace('.', ','), 'total_amount': total_amount
                    }
                else:
                    return {
                        'thumb': im.url, 'name': product.name, 'id': product_id, 'pr_url': product.get_absolute_url(),
                    }

        match request.POST.get('action'):
            case 'add_basket':
                # if product_id not in basket_dict.keys():
                #     basket_dict[product_id] = 1
                #     product = Product.objects.get(id=int(product_id))
                #     im = get_thumbnail(product.first_image, '80x80', crop='center', quality=99)
                #     request.session['basket'] = basket_dict
                #     total_amount, total_sum, pr_total_price = calculate_basket(request, basket_dict, product_id)
                #     return JsonResponse({
                #         'thumb': im.url, 'name': product.name, 'id': product_id, 'pr_url': product.get_absolute_url(),
                #         'price': str(pr_total_price).replace('.', ','),
                #         'total_sum': str(total_sum).replace('.', ','), 'total_amount': total_amount
                #     }, status=200)
                return JsonResponse(add_basket(basket_dict, product_id, 'one_product'))

            case 'multi_add_basket':
                added_products_data_list = [
                    add_basket(basket_dict, product_id, '') for product_id in product_id.split(',')]
                total_amount, total_sum, prices_dict = calculate_basket(request, basket_dict, product_id.split(','))
                return JsonResponse({
                    'added_products_data_list': added_products_data_list,
                    'total_amount': total_amount, 'total_sum': total_sum, 'prices_dict': prices_dict
                })

            case 'change_amount':
                new_amount = request.POST.get('amount')
                basket_dict[product_id] = new_amount
                if new_amount == '0':
                    basket_dict.pop(product_id)
                request.session['basket'] = basket_dict
                total_amount, total_sum, pr_total_price = calculate_basket(request, basket_dict, product_id)
                return JsonResponse({
                    'sum': str(int(new_amount) * pr_total_price),
                    'total_sum': str(total_sum).replace('.', ','), 'total_amount': total_amount
                }, status=200)

            case 'remove_from_basket':
                if product_id in basket_dict.keys():
                    basket_dict.pop(product_id)
                request.session['basket'] = basket_dict
                total_amount, total_sum = calculate_basket(request, basket_dict)
                return JsonResponse({
                    'total_sum': str(total_sum).replace('.', ','), 'total_amount': total_amount
                }, status=200)

            case 'add_fav':
                if product_id not in fav_list:
                    fav_list.append(product_id)
                    request.session['favorites'] = fav_list
                return JsonResponse({'total_fav': len(fav_list)}, status=200)

            case 'remove_fav':
                fav_list.remove(str(product_id))
                request.session['favorites'] = fav_list
                return JsonResponse({'total_fav': len(fav_list)}, status=200)

            case 'add_to_compare':
                if product_id not in comp_list:
                    comp_list.append(product_id)
                    request.session['compare'] = comp_list
                return JsonResponse({'total_comp': len(comp_list)}, status=200)
            case 'remove_to_compare':
                comp_list.remove(product_id)
                request.session['compare'] = comp_list
                return JsonResponse({'total_comp': len(comp_list)}, status=200)

        request.session['favorites'] = fav_list
        request.session['compare'] = comp_list

        return JsonResponse({'product_id': product_id}, status=200)


class CheckoutView(View):
    template_name = 'checkout.html'

    def get(self, request):
        return render(
            request=request, template_name=self.template_name,
            context={'person_form': PersonForm}
        )


class ByNowView(View):
    def get(self, request):
        product_id = request.GET.get('product_id')
        basket_dict = request.session.get('basket', dict())
        for pr_id in product_id.split(','):
            if pr_id not in basket_dict.keys():
                basket_dict[pr_id] = 1
        request.session['basket'] = basket_dict
        return HttpResponseRedirect(reverse('root_app:checkout'))


# def request_google_auth(request):
#     flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
#         OAuthGoogle.get_solo().json_auth_data_file.path,
#         scopes=['https://www.googleapis.com/auth/contacts'])
#
#     flow.redirect_uri = reverse('root_app:google_response')
#     authorization_url, state = flow.authorization_url(
#         access_type='offline',
#         include_granted_scopes='true')
#     return HttpResponseRedirect(authorization_url)

#
# def google_response(request):
#     state = request.GET.get('state')
#     code = request.GET.get('code')
#     flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
#         OAuthGoogle.get_solo().json_auth_data_file.path,
#         scopes=['https://www.googleapis.com/auth/contacts'],
#         state=state)
#     flow.redirect_uri = reverse('root_app:oauth2callback')
#     authorization_response = request.build_absolute_uri()
#     flow.fetch_token(authorization_response=authorization_response)
#     credentials = flow.credentials
#     return HttpResponse(request)


def oauth2callback(request):
    pass


def get_verify_allow_time_delta(device):
    if device.verify_is_allowed()[0]:
        return None
    else:
        now = datetime.now().astimezone(pytz.timezone('Europe/Kiev'))
        next_allowed_time = device.verify_is_allowed()[1]['locked_until'].astimezone(pytz.timezone('Europe/Kiev'))
        return round((next_allowed_time - now).total_seconds())


def get_validity_time_delta(device):
    valid_until = device.valid_until.astimezone(pytz.timezone('Europe/Kiev'))
    return round((valid_until - datetime.now().astimezone(pytz.timezone('Europe/Kiev'))).total_seconds())


@json_view
# https://django-otp-official.readthedocs.io/en/stable/overview.html
# https://django-otp-twilio.readthedocs.io/en/latest/_modules/otp_twilio/models.html#TwilioSMSDevice
def get_and_check_registration_phone(request):
    data = request.POST
    clean_phone_str = ''.join(x for x in data.get('phonenumber') if x.isdigit())
    number = PhoneNumber.from_string(clean_phone_str, region='UA')
    print(number)
    if not geocoder.description_for_number(number, "ru"):
        return {'phone_is_valid': False}
    phone_full_str = get_phone_full_str(number)
    response = {'phone_is_valid': True}
    if not request.session.session_key:
        request.session.save()

    phone = Phone.objects.get_or_create(number=number.as_e164)[0]
    print('PHONE', phone)
    if Person.objects.filter(main_phone=phone).exists():
        user, is_created_user = Person.objects.get_or_create(main_phone=phone)
    else:
        user, is_created_user = Person.objects.get_or_create(main_phone=phone, username=number, is_buyer=True)
        user_phone, is_create_phone = PersonPhone.objects.get_or_create(phone=phone, person=user)
        user.delivery_phone = phone
        user.save()
    device = TwilioSMSDevice.objects.get_or_create(number=number.as_e164, name=request.session.session_key,
                                                   user=user, confirmed=False)[0]
    response['allow_verify_time_delta'] = get_verify_allow_time_delta(device)
    ask_name = is_created_user or not len(user.first_name)
    if ask_name:
        response |= {
            'ask_name': ask_name,
            'next_title_text': f"Номер {phone_full_str} доступний для регістрації. Вкажіть Ваше ім'я"
        }
    else:
        validity_time = get_validity_time_delta(device)
        if not device.token or validity_time < 5:
            print('SMS token: ', clean_phone_str, device.generate_challenge())
            validity_time = get_validity_time_delta(device)
        response |= {
            'next_title_text': f'Знайдено обліковий запис з вказаним номером {phone_full_str}.'
                               ' Для відновлення доступу, вкажіть одноразовий пароль з СМС'
                               f' який діє {settings.OTP_TWILIO_TOKEN_VALIDITY} секунд',
            'validity_time': validity_time, 'input_same_number': False
        }

    print('get_verify_allow_time_delta: ', get_verify_allow_time_delta(device))
    request.session['attempt_to_enter_data'] = {
        'user_id_to_login': user.id, 'phone_full_str': phone_full_str, 'is_created_user': is_created_user,
        'device_id_to_login': device.id,
    }
    return response


@json_view
def get_registration_name(request):
    name = request.POST.get('name').title()
    user = Person.objects.get(id=request.session.get('attempt_to_enter_data')['user_id_to_login'])
    user.first_name = name
    user.save(update_fields=['first_name'])

    device = TwilioSMSDevice.objects.get(id=request.session['attempt_to_enter_data']['device_id_to_login'])
    print('SMS token: ', device.generate_challenge())
    return {'next_title_text':
                f'{name}, для того щоб переконатись що вказаний вами номер '
                f'{request.session.get("attempt_to_enter_data")["phone_full_str"]} '
                f'належить саме Вам введіть одноразовий пароль з СМС'
                f' який діє {(validity_time := get_validity_time_delta(device))} секунд',
            'validity_time': validity_time
            }


@json_view
def regenerate_sms_token(request):
    allow_timer = False
    resent_time = settings.OTP_TWILIO_RESENT_TIME
    is_token_regenerated = 'token_time_last_regenerated' in request.session['attempt_to_enter_data']
    if is_token_regenerated:
        token_time_last_regenerated = request.session['attempt_to_enter_data']['token_time_last_regenerated']
        old_date = datetime.fromtimestamp(token_time_last_regenerated)
        time_delta = (datetime.now() - old_date).total_seconds()
        if time_delta > resent_time:
            allow_timer = True
    if not is_token_regenerated or allow_timer:
        device = TwilioSMSDevice.objects.get(
            id=request.session.get('attempt_to_enter_data')['device_id_to_login'])
        request.session['attempt_to_enter_data']['token_time_last_regenerated'] = datetime.now().timestamp()
        request.session.save()

        code = device.generate_challenge()
        device.throttle_reset()
        print('CODE: ', code)
        validity_time = get_validity_time_delta(device)
        return {'next_title_text': f'ВІдправлено новий одноразовий пароль  який діє {validity_time} секунд',
                'resent_time': resent_time, 'validity_time': validity_time}
    else:
        return {'next_title_text': 'В даний момент не можливо здійснити запит'}


@json_view
def verify_sms_token(request):
    attempt_to_enter_data = request.session.get('attempt_to_enter_data')
    device = TwilioSMSDevice.objects.get(id=attempt_to_enter_data['device_id_to_login'])
    if device.verify_is_allowed()[0]:
        result = device.verify_token(request.POST.get('token'))
        if result:
            device.confirmed = True
            device.save()
            user = Person.objects.get(id=request.session.get('attempt_to_enter_data')['user_id_to_login'])
            login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
            if attempt_to_enter_data['is_created_user']:
                next_title_text = f'{user.get_full_name()} ви успішно зареєструвались і увійшли в систему.'
            else:
                next_title_text = f'{user.get_full_name()} ви увійшли в свій особоистий кабінет'
            show_email = request.user.is_authenticated and not request.user.password and not request.user.email
            show_set_passw_link = request.user.is_authenticated and request.user.email and not request.user.password
            show_change_password_link = request.user.is_authenticated and request.user.email and request.user.password
            return {'next_title_text': next_title_text, 'result': result, 'show_email_login_section': show_email,
                    'csrf': django.middleware.csrf.get_token(request), 'show_set_passw_link': show_set_passw_link,
                    'show_change_password_link': show_change_password_link}
        else:
            if device.verify_is_allowed()[1]['locked_until'] > device.valid_until:

                return {'next_title_text': f'Спроби вводу паролю вичерпано. Ви можете запросити новий пароль ',
                        'result': result, 'interval': -1}
            else:
                return {'next_title_text': f'Невірний одноразовий пароль, ви можете повторити спробу ',
                        'result': result, 'interval': get_verify_allow_time_delta(device)}
    else:
        print("проверка НЕвозможна")
        return {'next_title_text': 'В даний момент не можливо здійснити запит', }


@json_view
def logout_view(request):
    if 'attempt_to_enter_data' in request.session.keys():
        device = TwilioSMSDevice.objects.get(
            id=request.session.get('attempt_to_enter_data')['device_id_to_login'])
        device.confirmed = False
        device.save()
    logout(request)
    next_title_text = 'Ви вийшли з облікового запису. Для входу в кабінет або щоб створити обліковий запис вкажіть ваш номер телефону'
    return {'next_title_text': next_title_text}


@json_view
def add_email(request):
    form = PersonEmailForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        if Person.objects.filter(email=email).exists():
            return {'result': False, 'result_text': [
                'Електронну пошту не додано',
                f'Електронну пошту {email} вже зареєстровано на інший акаунт',
                'Вкажіть іншу електронну пошту або увійдіть в інший акаунт'
            ]}
        else:
            request.user.email = email
            request.user.save()
            return {'result': True, 'result_text': f'Електронну пошту {email} успішно додано'}
    else:
        return {'result': False, 'result_text': form.errors['email']}


@json_view
def update_user_personal(request):
    form = PersonalInfoForm(request.POST, instance=request.user)
    if form.is_valid():
        form.cleaned_data['last_name'] = form.cleaned_data['last_name'].title()
        form.save()
        return {'result': True, 'result_text': 'Персональні дані успішно оновлено'}


@json_view
def update_user_phones(request):
    print(request.POST)
    numbers_data = {}
    request_data = request.POST
    print('=' * 20)
    print('request_data - ', request_data)
    errors_list = []
    wrong_inputs_id_list = []
    for key in request_data:
        new = True if 'new_' in key else False
        ph_key = key[:4] + key[10:] if new else key[6:]

        mess_key = key[:4] + key[15:] if new else key[11:]

        if 'phone_' in key:
            phone_inp = request_data.get(key)
            if not len(phone_inp):
                continue
            str_phone = ''.join(x for x in phone_inp if x.isdigit())
            number = PhoneNumber.from_string(str_phone, region='UA')
            if not geocoder.description_for_number(number, "ru"):
                print(f'НЕВЕРНЫЙ НОМЕР: {number}')
                errors_list.append(f'Номер {number.as_e164} не сбережено. Невірний номер')
                numbers_data[ph_key] = {'valid': False}
                wrong_inputs_id_list.append(key[6:])
            else:
                numbers_data[ph_key] = {
                    'number': number.as_e164,
                    'messengers': [],
                    'valid': True,
                    'new': new
                }
                print('KEY - ', key)
                print('numbers_data: ', numbers_data)
                if 'messengers_' in key:
                    print('mess_key -', mess_key)
                    numbers_data[mess_key]['messengers'] = request_data.getlist(key)

    print('numbers_data: ', numbers_data)

    new_person_phone_id_dict = {}

    is_old_person_phone_exists = PersonPhone.objects.filter(person_id=request.user.id).exists()
    print('IS_OLD_PERSON_PHONE_EXISTS - ', is_old_person_phone_exists)
    success_created_or_updated_person_phone_id_list = []
    error_number_person_phone_id_list = []
    for person_phone_id, data in numbers_data.items():
        if data['valid']:
            if data['new']:
                # создать номер телеофна в базе
                new_phone, created = Phone.objects.get_or_create(number=data['number'])
                if new_phone.messengers.exists():
                    old_messengers = list(new_phone.messengers.values_list('id', flat=True))
                else:
                    new_phone.messengers.set(data['messengers'])
                    old_messengers = []
                # создать телефон контрагента
                new_person_phone = PersonPhone.objects.create(phone=new_phone, person_id=request.user.id)
                new_person_phone_id_dict[person_phone_id] = {
                    'new_person_phone_id': new_person_phone.id,
                    'old_messengers': old_messengers,
                    'valid': True
                }
                success_created_or_updated_person_phone_id_list.append(new_person_phone.id)
            else:
                # если не новая строка
                # если номер не изменился то обновить месенжеры
                old_number = PersonPhone.objects.get(id=person_phone_id)

                if old_number.phone.number.as_e164 == data['number']:
                    old_number.phone.messengers.set(data['messengers'])
                else:
                    success_created_or_updated_person_phone_id_list.append(old_number.id)
                    # если изменился то получить или  создать новый номер телефона и зменить ео в телефоне контрагента
                    new_phone, created = Phone.objects.get_or_create(number=data['number'])
                    old_number.phone = new_phone
                    old_number.save()
                    # РЕАЛИЗВОАТЬ ИЗМЕНЕНИЕ МЕССЕНЖЕРОВ НА ФРОНТЕНДЕ ЕСЛИ НОВЫЙ НОМЕР СУЩЕСТВОВАЛ
                    new_phone.messengers.set(data['messengers'])
        else:
            new_person_phone_id_dict[person_phone_id] = {
                'valid': False
            }
    print('new_person_phone_id_dict - ', new_person_phone_id_dict)
    print('-' * 20)
    # если не было ранее добавленых номеров
    if not is_old_person_phone_exists:
        # перебираем даные форм новых номеров и устанавливаем первый попавшийся корректный как номер для входа и доставки
        for key in new_person_phone_id_dict.keys():
            ph_id = new_person_phone_id_dict[key]['new_person_phone_id']
            if ph_id in wrong_inputs_id_list:
                continue
            else:
                main_phone_id = ph_id
                delivery_phone_id = main_phone_id
                break
    else:
        # если это не первый добавленый номер то номерами доставки и основного задаем согласно чекбокса переданой формы
        main_phone_id_req = request_data.get('is_main_phone')
        main_phone_id = new_person_phone_id_dict[
            main_phone_id_req] if 'new_' in main_phone_id_req else main_phone_id_req
        delivery_phone_req = request_data.get('is_delivery_phone')
        delivery_phone_id = new_person_phone_id_dict[
            delivery_phone_req] if 'new_' in delivery_phone_req else delivery_phone_req
    main_phone = PersonPhone.objects.get(id=main_phone_id).phone
    new_main_phone_id = False
    new_delivery_phone_id = False
    # если номер входа ошибочный то не делаем ничего кроме вывода ошибки
    if main_phone_id in wrong_inputs_id_list:
        errors_list.append('Новий номер для входу не встановлено')
    # если номер входа корректный проверяем не занят ли он для входа
    elif Person.objects.exclude(id=request.user.id).filter(main_phone=main_phone).exists():
        errors_list.append(f'Номер {number.as_e164} не можливо встановити для входу. Номер зайнятий')
    else:
        # если все норм то задем номер как основной для текущего пользователя
        request.user.main_phone_id = PersonPhone.objects.get(id=main_phone_id).phone_id
        new_main_phone_id = main_phone_id
    if delivery_phone_id in wrong_inputs_id_list:
        errors_list.append('Новий номер для доставки не встановлено')
    else:
        request.user.delivery_phone_id = PersonPhone.objects.get(id=delivery_phone_id).phone_id
        new_delivery_phone_id = delivery_phone_id
    request.user.save()
    return {
        'is_exists_errors': False if len(errors_list) else True,
        'success_created_or_updated_person_phone_id_list': success_created_or_updated_person_phone_id_list,
        'new': new_person_phone_id_dict,
        # 'wrong_inputs_id_list': wrong_inputs_id_list,
        'errors_list': errors_list, 'main_phone_id': new_main_phone_id, 'delivery_phone_id': new_delivery_phone_id
    }


@json_view
def del_user_phone(request):
    id_to_del = request.POST.get('phone_id')
    PersonPhone.objects.get(id=id_to_del).delete()
    hide_del_btn = True if PersonPhone.objects.filter(person_id=request.user.id).count() == 1 else False
    return {'id': id_to_del, 'hide_del_btn': hide_del_btn}


@json_view
def get_settlement_info(request):
    settlement_name = Settlement.objects.get(ref=(settlement_ref := request.POST.get('settlement_ref'))).description_ua
    settlement_addict_info = get_settlement_addict_info(settlement_name, settlement_ref)
    is_warehouses_exists = Warehouse.objects.filter(settlement_id=settlement_ref).exists()
    response = {'is_warehouses_exists': is_warehouses_exists, 'errors': settlement_addict_info.errors}
    print('settlement_addict_info - ', settlement_addict_info.errors)

    if not settlement_addict_info.errors:
        response |= {
            'address_delivery_allowed': settlement_addict_info.address_delivery_allowed,
            'delivery_city_ref': settlement_addict_info.delivery_city_ref,
        }
        if settlement_addict_info.address_delivery_allowed:
            city = City.objects.get(ref=(city_ref := settlement_addict_info.delivery_city_ref))
            city_name = f'{city.type.description_ua} {city.description_ua}'
            city_url = mark_safe(reverse('admin:nova_poshta_city_change', args=[city_ref]))
            city_link = f'<a href={city_url} target="_blank">{city_name}</a>'
            response |= {'city': city_link, 'city_ref': city_ref}

    return response


# для формы редактирования кнтрагента и формы заказа
@json_view()
def ajax_updates_person_phones_info(request, mode):
    person_id = request.POST.get('person_id')
    print('MODE - ', mode)
    phone_id = request.POST.get('phone_id')
    if mode == 'other_persons':
        other_person_login = other_person_login_this_phone(phone_id, person_id)
        other_person = Person.objects.filter(phones__phone_id=phone_id).exclude(id=person_id)
        other_person_not_this_main = other_person_not_main(phone_id, other_person)
        return {
            'other_person_login': other_person_login, 'other_person_not_this_main': other_person_not_this_main,
            'contacts': other_contacts(phone_id, person_id)
        }
    elif mode == 'person_phones':
        person = Person.objects.get(id=person_id)
        PersonPhoneInfo = namedtuple(
            'PersonPhoneInfo', [
                'phone_id',
                'link', 'chats_links', 'main_number_av', 'is_main_number', 'is_delivery_number', 'viber', 'telegram',
                'whats_up'
            ], defaults=['', '', None, None, None, None, None, None]
        )
        person_phones = []
        for pp in Person.objects.get(id=person_id).phones.all():
            person_phones.append(PersonPhoneInfo(
                pp.phone_id,
                pp.phone.admin_link,  # link
                pp.phone.get_all_chat_links,  # chats_links
                not Person.objects.filter(main_phone_id=pp.phone_id).exclude(id=person_id).exists(),  # main_number_av
                person.main_phone_id == pp.phone_id,  # is_main_number
                person.delivery_phone_id == pp.phone_id,  # is_delivery_number
                1 in pp.phone.messengers.values_list('type', flat=True),  # viber
                2 in pp.phone.messengers.values_list('type', flat=True),  # telegram
                3 in pp.phone.messengers.values_list('type', flat=True),  # whats_up

            ))

        return {
            'person_phones': [pp._asdict() for pp in person_phones]
        }


@json_view()
def ajax_phone_field(request, mode):
    if mode == 'search':
        term = request.GET.get('term')
        cleaned_num = ''.join([str(i) for i in re.findall(r'\d+', term)]) if term else None
        phones = Phone.objects.filter(number__contains=cleaned_num) if cleaned_num else Phone.objects.all()
        return [{'id': f.id, 'text': f.__str__()} for f in phones]
    elif mode == 'add':
        number = PhoneNumber.from_string(request.POST.get('phone_id'), region='UA')
        if not geocoder.description_for_number(number, "ru"):
            return {'err': 'НЕВЕРНЫЙ НОМЕР'}
        else:
            created_number = Phone.objects.create(number=number)
            return {'err': None, 'added_phone_id': created_number.id, 'added_phone_str': created_number.__str__()}


@json_view()
def ajax_person_field(request, mode):
    # print('mode- ', mode)
    if mode == 'search':
        term = request.GET.get('term')
        persons = Person.objects.filter(full_name__icontains=term) if term else Person.objects.all()
    elif mode == 'add':
        full_name = request.POST.get('full_name').split()
        last_name, first_name, = full_name[0].title(), full_name[1].title(),
        middle_name = full_name[2].title() if len(full_name) > 2 else None
        created_person = Person.objects.create(last_name=last_name, first_name=first_name, middle_name=middle_name)
        return {'added_person_id': created_person.id, 'added_person_str': created_person.__str__()}
        # return {'err': 'err'}
    return [{'id': p.id, 'text': p.__str__()} for p in persons]


@json_view()
def ajax_change_phone_parameters(request):
    data = request.POST
    action = data.get('action')
    person = Person.objects.get(id=data.get('person_id'))
    phone = Phone.objects.get(id=(phone_id := data.get('phone_id')))
    match data.get('mode'):
        case 'main_phone':
            if action == 'add':
                person.main_phone_id = phone_id
            elif action == 'remove':
                person.main_phone_id = None
            person.save()
        case 'delivery_phone':
            if action == 'add':
                person.delivery_phone_id = phone_id
            elif action == 'remove':
                person.delivery_phone_id = None
            person.save()
        case 'viber':
            if action == 'add':
                phone.messengers.add(Messenger.objects.get(type=1))
            elif action == 'remove':
                phone.messengers.remove(Messenger.objects.get(type=1))
            person.save()
        case 'telegram':
            if action == 'add':
                phone.messengers.add(Messenger.objects.get(type=2))
            elif action == 'remove':
                phone.messengers.remove(Messenger.objects.get(type=2))
            person.save()
        case 'whatsapp':
            if action == 'add':
                phone.messengers.add(Messenger.objects.get(type=3))
            elif action == 'remove':
                phone.messengers.remove(Messenger.objects.get(type=3))
            person.save()

    return {'person_str': person.__str__()}
