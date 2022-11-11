from django.contrib import messages
import json

from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse, resolve
import requests
from django.utils.html import format_html
from django.views import View
from otp_twilio.models import TwilioSMSDevice
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers import geocoder

from ROOTAPP.forms import PersonForm
from ROOTAPP.models import Settlement, SettlementType, SettlementArea, SettlementRegion, Phone, PersonPhone, Person, \
    get_phone_full_str
from Shop_DJ import settings
from catalog.models import Product, get_price_sq
from sorl.thumbnail import get_thumbnail

from orders.models import ByOneclick
from servises import get_products_annotated_prices

import google.oauth2.credentials
import google_auth_oauthlib.flow

from site_settings.models import OAuthGoogle

url_np = 'https://api.novaposhta.ua/v2.0/json/'


def update_cities(request):
    data = request.GET
    limit = 150
    timeout_limit = 3.0
    request_dict = {
        "modelName": "Address",
        "calledMethod": "getSettlements",
        "methodProperties": {
            "Limit": str(limit)
        }
    }
    message_text = ''
    search_by_descr = False
    if data:
        if 'search_name' in data.keys():
            search_by_descr = True
            request_dict['methodProperties']['FindByString'] = (search_name := data['search_name'])
            message_text = f'Обновление списка населенных пунктов по запросу {search_name} <br>'
        else:
            message_text = ''

    ln = limit
    count = 1
    page = 1

    added_count = 0
    edited_count = 0

    while ln == limit:
        # is_exists_new = False
        # is_exists_edited = False
        request_dict["methodProperties"]["Page"] = str(page)
        print(f'Запрос страницы сервера #{page}')

        try:
            request_json = json.dumps(request_dict, indent=4)
            response = requests.post(url_np, data=request_json, timeout=timeout_limit)
            response_dict = json.loads(response.text)
            print(f'Статус запроса {response_dict["success"]}')
            print(f'Получены данные {len(response_dict["data"])} городов, лимит: {limit}')
            print()

            message_text += f'Загрузка страницы №{page} (по {limit} населенных пунктов на старнице) - ' \
                            f'{response_dict["success"]} + <br>'
            settlement_to_create_list = []
            new_cities_names_list = []
            edited_cities_data_list = []
            for data in response_dict['data']:
                data_settlement_str = f"№{count}: {data['DescriptionRu']}/{data['Description']} ({data['AreaDescriptionRu']}, " \
                                      f"{data['RegionsDescriptionRu']})"
                if search_by_descr:
                    message_text += f'Найдено {data_settlement_str} <br>'
                    print(f'Найдено {data_settlement_str}')
                if Settlement.objects.filter(ref=data['Ref']).exists():
                    settlement = Settlement.objects.get(ref=data['Ref'])
                    changed = []
                    if data['DescriptionRu']:
                        if (old := settlement.description_ru) != (new := data['DescriptionRu']):
                            changed.append(True)
                            m = f'Для населенного пункта {settlement} значение поля "Название" сменилось с /{old}/ на /{new}/'
                            print(m)
                            edited_cities_data_list.append(m)
                            settlement.description_ru = data['DescriptionRu']

                    if data['Description']:
                        if (old := settlement.description_ua) != (new := data['Description']):
                            changed.append(True)
                            m = f'Для населенного пункта {settlement} значение поля "Название укр." сменилось с /{old}/ на /{new}/'
                            print(m)
                            edited_cities_data_list.append(m)
                            settlement.description_ua = data['Description']

                    if data['SettlementType']:
                        if (old := settlement.type.ref) != data['SettlementType']:
                            m = f'Для населенного пункта {settlement} значение поля "Тип населенного пункта" ' \
                                f'сменилось с /{old.type.description_ru}/ на /{data["SettlementTypeDescriptionRu"]}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            settlement.type.ref = data['SettlementType']

                    if data['Area']:
                        if settlement.area.ref != data['Area']:
                            m = f'Для населенного пункта {settlement} значение поля "Область" сменилось с ' \
                                f'/{settlement.area.description_ru}/ на /{data["AreaDescriptionRu"]}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            settlement.area.ref = data['Area']

                    if data['Region']:
                        if settlement.region.ref != data['Region']:
                            m = f'Для населенного пункта {settlement} значение поля "Район" сменилось с ' \
                                f'/{settlement.region.description_ru}/ на /{data["RegionDescriptionRu"]}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            settlement.region.ref = data['Region']

                    if data['Warehouse']:
                        new = True if data['Warehouse'] == '1' else False
                        if (old := settlement.warehouse) != new:
                            print(f'{old=}, {new=}, {data["Warehouse"]=}')
                            m = f'Для населенного пункта {settlement} значение поля "Наличие отделений" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            settlement.warehouse = data['Warehouse']

                    if data['Index1']:
                        if (old := settlement.index_1) != (new := data['Index1']):
                            m = f'Для населенного пункта {settlement} значение поля "index_1" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            settlement.index_1 = data['Index1']

                    if data['Index2']:
                        if (old := settlement.index_2) != (new := data['Index2']):
                            m = f'Для населенного пункта {settlement} значение поля "index_2" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            settlement.index_1 = data['Index2']

                    if data['IndexCOATSU1']:
                        if (old := settlement.index_coatsu_1) != (new := data['IndexCOATSU1']):
                            m = f'Для населенного пункта {settlement} значение поля "IndexCOATSU1" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            settlement.index_coatsu_1 = data['IndexCOATSU1']

                    if any(changed):
                        edited_count += 1
                        settlement.save()
                else:
                    settlement_type, created = SettlementType.objects.get_or_create(
                        ref=data['SettlementType'],
                        defaults={
                            'description_ru': data['SettlementTypeDescriptionRu'],
                            'description_ua': data['SettlementTypeDescription']
                        }
                    )
                    area, created = SettlementArea.objects.get_or_create(
                        ref=data['Area'],
                        defaults={
                            'description_ru': data['AreaDescriptionRu'],
                            'description_ua': data['AreaDescription']
                        }
                    )
                    region, created = SettlementRegion.objects.get_or_create(
                        ref=data['Region'],
                        defaults={
                            'description_ru': data['RegionsDescriptionRu'],
                            'description_ua': data['RegionsDescription']
                        }
                    )
                    print(data["Ref"])
                    settlement_to_create_list.append(Settlement(
                        description_ru=data['DescriptionRu'], description_ua=data['Description'], ref=data["Ref"],
                        type=settlement_type, area=area, region=region, warehouse=data['Warehouse'],
                        index_coatsu_1=data['IndexCOATSU1'], index_1=data['Index1'], index_2=data['Index2']
                    ))
                    new_cities_names_list.append(data_settlement_str)
                    print(f'Добавлено: {data_settlement_str}')
                    added_count += 1
                count += 1
                ln = len(response_dict['data'])

            print('-' * 80)

            if len(new_cities_names_list):
                message_text += 'Добавлено^<ul>'
                for added in new_cities_names_list:
                    message_text += f'<li>{added}</li>'
                message_text += '</ul>'

            if len(edited_cities_data_list):
                message_text += 'Изменено^<ul>'
                for edited in edited_cities_data_list:
                    message_text += f'<li>{edited}</li>'
                message_text += '</ul>'

            Settlement.objects.bulk_create(settlement_to_create_list)
            message_text += '<br>'
            page += 1
        except requests.exceptions.Timeout:
            print(f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка - ')
            print()
            message_text += f'Превышен лимит {timeout_limit}c врмени ожидания загрузки данных страницы №{page} ' \
                            f'/ Повторная попытка - <br>'
    message_text += '=' * 80 + '<br>'
    print('=' * 80)
    total_info = f'На сервере просмотрено {count - 1} населенных пунктов. <br> Всего добавлено населенных пунктов {added_count}, всего изменено населенных пунктов {edited_count}'
    message_text += total_info
    messages.add_message(request, messages.SUCCESS, format_html(message_text))
    print(total_info)
    return HttpResponseRedirect(reverse('admin:ROOTAPP_settlement_changelist'))


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
            "Cost": request.POST.get("price")[:-3],
            "CargoType": "Cargo",
            "SeatsAmount": request.POST.get("seats_amount"),
            'RedeliveryCalculate': {
                'CargoType': 'Money',
                'Amount': request.POST.get("price")[:-3]
            }
        }
    }
    while number_of_attempts <= max_number_of_attempts:
        try:
            request_json = json.dumps(data_cost, indent=4)
            response = requests.post(url_np, data=request_json, timeout=timeout_limit)
            response_dict = json.loads(response.text)
            return JsonResponse({
                'settlement_to_name': str(Settlement.objects.get(ref=request.POST.get("settlement"))),
                'cost_redelivery': response_dict['data'][0]['CostRedeliveryWarehouseWarehouse'],
                'CostWarehouseWarehouse': response_dict['data'][0]['CostWarehouseWarehouse'],
                'CostWarehouseDoors': response_dict['data'][0]['CostWarehouseDoors'],
                'Cost': request.POST.get("price")[:-3],
            }, status=200)
            break
        except requests.exceptions.Timeout:
            number_of_attempts += 1
            print(f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка - ')
    return JsonResponse({}, status=500)


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


# https://django-otp-official.readthedocs.io/en/stable/overview.html
# https://django-otp-twilio.readthedocs.io/en/latest/_modules/otp_twilio/models.html#TwilioSMSDevice
def get_and_check_registration_phone(request):
    data = request.POST
    clean_phone_str = ''.join(x for x in data.get('phonenumber') if x.isdigit())
    number = PhoneNumber.from_string(clean_phone_str, region='UA')
    if not geocoder.description_for_number(number, "ru"):
        return JsonResponse({'phone_is_valid': False}, status=200)
    phone_full_str = get_phone_full_str(number)
    print('phone_full_str: ', phone_full_str)
    user, is_created_user = User.objects.get_or_create(username=number.as_e164)
    attempt_to_enter_data = request.session['attempt_to_enter_data'] = {
        'user_id_to_login': user.id, 'phone_full_str': phone_full_str
    }
    request.session.save()
    # print('session_key: ', request.session.session_key)

    device = TwilioSMSDevice.objects.get_or_create(number=number.as_e164, name=request.session.session_key,
                                                   user=user, confirmed=False)[0]
    print('SMS token: ', device.generate_challenge())
    attempt_to_enter_data['device_id_to_login'] = device.id
    request.session['attempt_to_enter_data'] = attempt_to_enter_data
    return JsonResponse({'phone_is_valid': True, 'is_created_user': is_created_user,
                         'next_title_text': f"Номер {phone_full_str} доступний для регістрації. Вкажіть Ваше ім'я"},
                        status=200)


def get_registration_name(request):
    name = request.POST.get('name').title()
    user = User.objects.get(id=request.session.get('attempt_to_enter_data')['user_id_to_login'])
    print('User: ', user)
    user.first_name = name
    user.save(update_fields=['first_name'])
    return JsonResponse(
        {'next_title_text':
             f'{name}, для того щоб переконатись що вказаний вами номер '
             f'{request.session.get("attempt_to_enter_data")["phone_full_str"]} належить саме Вам введіть одноразовий пароль з СМС'
         }, status=200)


def regenerate_sms_token(request):
    # device = TwilioSMSDevice.objects.get(
    #     id=request.session.get('attempt_to_enter_data')['device_id_to_login'])
    # print(device.tro)
    code = TwilioSMSDevice.objects.get(
        id=request.session.get('attempt_to_enter_data')['device_id_to_login']).generate_challenge()
    print('New code: ', code)
    return JsonResponse({'next_title_text': f'ВІдправлено новий одноразовий пароль',}, status=200)


def verify_sms_token(request):
    device = TwilioSMSDevice.objects.get(
        id=request.session.get('attempt_to_enter_data')['device_id_to_login'])
    result = device.verify_token(request.POST.get('token'))
    print('result: ', result)
    if result:
        device.confirmed = True
        device.save()
        user = User.objects.get(id=request.session.get('attempt_to_enter_data')['user_id_to_login'])
        login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])

        return JsonResponse({'next_title_text': f'{user.first_name} ви успішно зареєструвались і увійшли в систему.',
                             'result': result}, status=200)
    else:
        return JsonResponse({'next_title_text': f'Невірний одноразовий пароль', 'result': result}, status=200)


def logout_view(request):
    logout(request)
    device = TwilioSMSDevice.objects.get(
        id=request.session.get('attempt_to_enter_data')['device_id_to_login'])
    device.confirmed = False
    device.save()
    del request.session['attempt_to_enter_data']
    return JsonResponse({'next_title_text': 'ви вийшли з облікового запису'}, status=200)
