from datetime import datetime, timezone
import django
import pytz
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse, resolve
from django.utils.html import format_html
from django.views import View
from jsonview.decorators import json_view
from otp_twilio.models import TwilioSMSDevice
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers import geocoder
from ROOTAPP.forms import PersonForm, PersonEmailForm, PersonalInfoForm
from Shop_DJ import settings
from catalog.models import Product, get_price_sq
from sorl.thumbnail import get_thumbnail
from servises import get_products_annotated_prices
import google_auth_oauthlib.flow
from site_settings.models import OAuthGoogle
from .services.NP_func_and_vars import *


def update_warehouses(request):
    warehouses_request_dict = {
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "Limit": str(big_limit)
        }
    }
    message_text = ''
    page = 1
    count = 0
    added_warehouses_count = 0
    edited_warehouses_count = 0
    types_of_warehouses_updated = False
    data = request.GET
    warehouses_limit = int(warehouses_request_dict["methodProperties"]["Limit"])
    ln = warehouses_limit

    # добавить в запрос к АПИ фильтр по населенному пункту если это задано
    if data:
        if 'settlement' in data.keys():
            settlement_ref = data['settlement']
            warehouses_request_dict['methodProperties']['SettlementRef'] = settlement_ref
            settlement = Settlement.objects.get(ref=settlement_ref)
            message_text = f'<h4>Обновление списка отделений в населенном пункте {settlement}</h4> <br>'
        else:
            message_text = f'<h4>Полное обновление списка отделений</h4> <br>'

    while ln == warehouses_limit:
        warehouses_request_dict["methodProperties"]["Page"] = str(page)
        print(f'Запрос страницы сервера #{page}')

        try:
            warehouse_response_dict = get_response(warehouses_request_dict)
            page += 1
            ln = len(all_warhauses_data := warehouse_response_dict['data'])
            print(f'Статус запроса {warehouse_response_dict["success"]}')
            print(f'Получены данные {ln}отделений , лимит: {warehouses_limit}')
            print()
            message_text += f'<h5> Загрузка страницы №{page} (по {warehouses_limit}' \
                            f' отделения на старнице) - {warehouse_response_dict["success"]} + </h5>>'

            for wh_data in all_warhauses_data:
                to_create_warehouses = []
                changed_warehouses = []
                changed_fields = set()
                count += 1
                # обновить отделение если оно уже есть в базе
                if Warehouse.objects.filter(ref=wh_data['Ref']).exists():
                    warehouse_change_data = get_and_apply_changes(
                        Warehouse.objects.get(ref=wh_data['Ref']), warehouse_parameters, wh_data
                    )
                    if warehouse_change_data['changed']:
                        edited_warehouses_count += 1
                        message_text += warehouse_change_data['new_message_text']
                        changed_warehouses.append(warehouse_change_data['changed_obj'])
                        changed_fields.update(warehouse_change_data['changed_fields'])

                # создать отделение
                else:
                    if wh_data['SettlementRef'] == '00000000-0000-0000-0000-000000000000':
                        continue
                    #  проверить налчиие в баще необходимой области и района
                    # если отсутвует то сделать подхапрос и создать
                    create_obj_if_not_exists(Settlement, wh_data['SettlementRef'], settlement_parameters)
                    create_obj_if_not_exists(City, wh_data['CityRef'], city_parameters)
                    # Если справочник типов отделений не обновлялся в этом запросе то проверить существует ли в базе такой тип
                    if not types_of_warehouses_updated:
                        # Если такой тип отсутсвует обновить весь справочник типов отделений
                        if not TypeOfWarehouse.objects.filter(ref=wh_data['TypeOfWarehouse']).exists():
                            print('Обновление списка типов отделений')
                            message_text += '<h5>Обновление списка типов отделений </h5>'
                            is_response_types_success = False
                            while not is_response_types_success:
                                try:
                                    response_type_dict = get_response(
                                        {
                                            "modelName": "Address",
                                            "calledMethod": "getWarehouseTypes",
                                            "methodProperties": {}
                                        }
                                    )
                                    is_response_types_success = True
                                    types_of_warehouses_updated = True
                                    print(f'Статус запроса {response_type_dict["success"]}')
                                    print(f'Получены данные {len(all_types_data := response_type_dict["data"])} типов '
                                          f'отделений')
                                    types_to_create = []
                                    for type_data in all_types_data:
                                        types_to_create.append(
                                            TypeOfWarehouse(
                                                ref=type_data['Ref'],
                                                description_ru=type_data['Description'],
                                                description_ua=type_data['DescriptionRu']
                                            )
                                        )
                                    TypeOfWarehouse.objects.bulk_create(types_to_create)
                                except requests.exceptions.Timeout:
                                    print(
                                        f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка запроса типов отд')
                    # формирование списка отделений для создания
                    warehouse = Warehouse()
                    # Пройтись по всем полям
                    for param in warehouse_parameters:
                        setattr(Warehouse, param.db_field, wh_data[param.api_field])
                    to_create_warehouses.append(warehouse)
                    added_warehouses_count += 1
            Warehouse.objects.bulk_create(to_create_warehouses)
            if edited_warehouses_count:
                Warehouse.objects.bulk_update(changed_warehouses, changed_fields)

        except requests.exceptions.Timeout:
            print(f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка - ')
            print()
            message_text += f'Превышен лимит {timeout_limit}c врмени ожидания загрузки данных страницы №{page} ' \
                            f'/ Повторная попытка - <br>'
    message_text += '=' * 80 + '<br>'
    print('=' * 80)
    total_info = f'На сервере просмотрено {count} отделений. <br> Всего добавлено отделений {added_warehouses_count}, всего ' \
                 f'изменено отделений {edited_warehouses_count} '
    message_text += total_info
    print(total_info)
    messages.add_message(request, messages.SUCCESS, format_html(message_text))
    return HttpResponseRedirect(reverse('admin:ROOTAPP_warehouse_changelist'))


def update_np_catalogs(request, obj_type):
    types_settings = {
        'Settlement': ("getSettlements", settlement_parameters),
        'City': ("getCity", city_parameters),
        'Warehouse': ("getWarehouses", warehouse_parameters),
    }
    called_method, data_structure = types_settings[obj_type.__name__]

    print('called_method - ', called_method)

    objects_request_dict = {
        "modelName": "Address",
        "calledMethod": called_method,
        "methodProperties": {
            "Limit": str(limit)
        }
    }
    data, message_text = request.GET, ''
    search_by_descr, search_by_settlement, search_by_city = False, False, False
    objects_position, added_objects_count, edited_objects_count = 1, 0, 0
    objects_limit = int(objects_request_dict['methodProperties']['Limit'])
    page, ln = 1, objects_limit

    if data:
        if 'search_name' in data.keys():
            search_by_descr = True
            objects_request_dict['methodProperties']['FindByString'] = (search_name := data['search_name'])
            message_text = f'Обновление списка элементов справочника по запросу {search_name} <br>'

    while ln == objects_limit:
        objects_to_create, changed_objects, changed_fields = [], [], set()
        new_objects_names, changed_objects_names = [], []
        objects_request_dict["methodProperties"]["Page"] = str(page)
        print(f'Запрос страницы сервера #{page}')
        try:
            objects_response_data = get_response(objects_request_dict)
            ln = len(all_objects_data := objects_response_data['data'])

            print(f'Статус запроса {objects_response_data["success"]}')
            print(f'Получены данные {ln} элементов справочника, лимит: {objects_limit}')
            print()

            message_text += f'Загрузка страницы №{page} (по {objects_limit} ' \
                            f'объектов на старнице) -  {objects_response_data["success"]} + <br>'
            page += 1

            for obj_data in all_objects_data:
                region = f", {obj_data['RegionsDescriptionRu']}" if obj_type == Settlement else ''
                object_name = f"№{objects_position}: {obj_data['DescriptionRu']}/{obj_data['Description']} " \
                                      f"({obj_data['AreaDescriptionRu']}{region})"
                if search_by_descr:
                    message_text += f'Найдено {object_name} <br>'
                    print(f'Найдено {object_name}')

                if obj_type.objects.filter(ref=obj_data['Ref']).exists():
                    object_changes_data = get_and_apply_changes(
                        obj_type.objects.get(ref=obj_data['Ref']), data_structure, obj_data
                    )
                    if object_changes_data['changed']:
                        edited_objects_count += 1
                        message_text += object_changes_data['new_message_text']
                        changed_objects.append(object_changes_data['changed_obj'])
                        changed_fields.update(object_changes_data['changed_fields'])
                        print(f'Изменено: {object_name}')
                else:
                    objects_to_create.append(build_settlement_or_city_to_create(
                        obj_data, Settlement, data_structure)
                    )
                    new_objects_names.append(object_name)
                    print(f'Добавлено: {object_name}')
                    added_objects_count += 1
                objects_position += 1

            print('-' * 80)

            if len(objects_to_create):
                obj_type.objects.bulk_create(objects_to_create)
                message_text += 'Добавлено^<ul>'
                for added in new_objects_names:
                    message_text += f'<li>{added}</li>'
                message_text += '</ul>'

            if len(changed_objects):
                obj_type.objects.bulk_update(changed_objects, changed_fields)
                message_text += 'Изменено^<ul>'
                for edited in changed_objects_names:
                    message_text += f'<li>{edited}</li>'
                message_text += '</ul>'

            message_text += '<br>'

        except requests.exceptions.Timeout:
            print(f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка - ')
            print()
            message_text += f'Превышен лимит {timeout_limit}c врмени ожидания загрузки данных страницы №{page} ' \
                            f'/ Повторная попытка - <br>'

    message_text += '=' * 80 + '<br>'
    print('=' * 80)

    total_info = f'На сервере просмотрено {objects_position - 1} элементов справочника.<br>Всего добавлено элементов' \
                 f'{added_objects_count}, всего изменено элементов {edited_objects_count} '
    message_text += total_info
    messages.add_message(request, messages.SUCCESS, format_html(message_text))
    print(total_info)


def update_settlements(request):
    update_np_catalogs(request, Settlement)
    return HttpResponseRedirect(reverse('admin:ROOTAPP_settlement_changelist'))


def update_cities(request):
    update_np_catalogs(request, City)
    return HttpResponseRedirect(reverse('admin:ROOTAPP_city_changelist'))


def get_delivery_cost(request):
    number_of_attempts = 1
    max_number_of_attempts = 5
    timeout_limit = 3.0
    data_cost = {
        "modelName": "InternetDocument",
        "calledMethod": "getDocumentPrice",
        "methodProperties": {
            "CitySender": request.POST.get("settlement_from_ref"),
            "CityRecipient": request.POST.get("settlement"),
            "Weight": request.POST.get("weight"),
            "ServiceType": '',
            "Cost": request.POST.get("price"),
            "CargoType": "Cargo",
            "SeatsAmount": request.POST.get("seats_amount"),
            'RedeliveryCalculate': {
                'CargoType': 'Money',
                'Amount': request.POST.get("price")
            }
        }
    }
    print('data_cost - ', data_cost)
    while number_of_attempts <= max_number_of_attempts:
        try:
            request_json = json.dumps(data_cost, indent=4)
            response = requests.post(url_np, data=request_json, timeout=timeout_limit)
            print('response - ', response)
            response_dict = json.loads(response.text)
            print('response_dict - ', response_dict)
            return JsonResponse({
                'settlement_to_name': str(Settlement.objects.get(ref=request.POST.get("settlement"))),
                'cost_redelivery': response_dict['data'][0]['CostRedeliveryWarehouseWarehouse'],
                'CostWarehouseWarehouse': response_dict['data'][0]['CostWarehouseWarehouse'],
                'CostWarehouseDoors': response_dict['data'][0]['CostWarehouseDoors'],
                'Cost': request.POST.get("price"),
            }, status=200)
            break
        except requests.exceptions.Timeout:
            number_of_attempts += 1
            print(f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка - ')

    return response('')


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


def request_google_auth(request):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        OAuthGoogle.get_solo().json_auth_data_file.path,
        scopes=['https://www.googleapis.com/auth/contacts'])

    flow.redirect_uri = reverse('root_app:google_response')
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    return HttpResponseRedirect(authorization_url)


def google_response(request):
    state = request.GET.get('state')
    code = request.GET.get('code')
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        OAuthGoogle.get_solo().json_auth_data_file.path,
        scopes=['https://www.googleapis.com/auth/contacts'],
        state=state)
    flow.redirect_uri = reverse('root_app:oauth2callback')
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    return HttpResponse(request)


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
        user, is_created_user = Person.objects.get_or_create(main_phone=phone, is_customer=True)
    else:
        user, is_created_user = Person.objects.get_or_create(main_phone=phone, username=number, is_customer=True)
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
        if 'messengers_' in key:
            print('mess_key -', mess_key)
            numbers_data[mess_key]['messengers'] = request_data.getlist(key)

    print('numbers_data: ', numbers_data)

    new_person_phone_id_dict = {}
    for person_phone_id, data in numbers_data.items():
        if data['valid']:
            if data['new']:
                new_phone, created = Phone.objects.get_or_create(number=data['number'])
                if new_phone.messengers.exists():
                    old_messengers = list(new_phone.messengers.values_list('id', flat=True))
                else:
                    new_phone.messengers.set(data['messengers'])
                    old_messengers = []
                new_person_phone = PersonPhone.objects.create(phone=new_phone, person_id=request.user.id)
                new_person_phone_id_dict[person_phone_id] = {
                    'new_person_phone_id': new_person_phone.id,
                    'old_messengers': old_messengers
                }
            else:
                old_number = PersonPhone.objects.get(id=person_phone_id)
                if old_number.phone.number.as_e164 == data['number']:
                    old_number.phone.messengers.set(data['messengers'])
                else:
                    new_phone, created = Phone.objects.get_or_create(number=data['number'])
                    old_number.phone = new_phone
                    old_number.save()
                    new_phone.messengers.set(data['messengers'])
    print('new_person_phone_id_dict - ', new_person_phone_id_dict)
    print('-' * 20)
    main_phone_id_req = request_data.get('is_main_phone')
    main_phone_id = new_person_phone_id_dict[main_phone_id_req] if 'new_' in main_phone_id_req else main_phone_id_req
    main_phone = PersonPhone.objects.get(id=main_phone_id).phone
    delivery_phone_req = request_data.get('is_delivery_phone')
    delivery_phone_id = new_person_phone_id_dict[
        delivery_phone_req] if 'new_' in delivery_phone_req else delivery_phone_req
    new_main_phone_id = False
    new_delivery_phone_id = False
    if main_phone_id in wrong_inputs_id_list:
        errors_list.append('Новий номер для входу не встановлено')
    elif Person.objects.exclude(id=request.user.id).filter(main_phone=main_phone).exists():
        errors_list.append(f'Номер {number.as_e164} не можливо встановити для входу. Номер зайнятий')
    else:
        request.user.main_phone_id = PersonPhone.objects.get(id=main_phone_id).phone_id
        new_main_phone_id = main_phone_id
    if delivery_phone_id in wrong_inputs_id_list:
        errors_list.append('Новий номер для доставки не встановлено')
    else:
        request.user.delivery_phone_id = PersonPhone.objects.get(id=delivery_phone_id).phone_id
        new_delivery_phone_id = delivery_phone_id
    request.user.save()
    return {
        'result': False if len(errors_list) else True, 'new': new_person_phone_id_dict,
        'errors_list': errors_list, 'main_phone_id': new_main_phone_id, 'delivery_phone_id': new_delivery_phone_id
    }


@json_view
def del_user_phone(request):
    id_to_del = request.POST.get('phone_id')
    PersonPhone.objects.get(id=id_to_del).delete()
    hide_del_btn = True if PersonPhone.objects.filter(person_id=request.user.id).count() == 1 else False
    return {'id': id_to_del, 'hide_del_btn': hide_del_btn}
