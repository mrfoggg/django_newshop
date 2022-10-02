from django.contrib import messages
import json
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
import requests
from django.utils.html import format_html

from ROOTAPP.models import Settlement, SettlementType, SettlementArea, SettlementRegion
from catalog.models import Product
from sorl.thumbnail import get_thumbnail

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


def product_actions(request):
    if request.method == 'POST':
        print('GET FORM DATA')
        print(request.POST.get('action'))
        product_id = request.POST.get('product_id')
        fav_list = request.session.get('favorites', list())
        comp_list = request.session.get('compare', list())
        basket_dict = request.session.get('basket', dict())

        match request.POST.get('action'):
            case 'add_basket':
                if product_id not in basket_dict.keys():
                    basket_dict[product_id] = 1
                    product = Product.objects.get(id=int(product_id))
                    product_img = product.images.first().image
                    im = get_thumbnail(product_img, '100x100', crop='center', quality=99)
                    request.session['basket'] = basket_dict
                    # print(str(product.price))
                    return JsonResponse({
                        'thumb': im.url, 'name': product.name, 'id': product_id, 'price': str(product.price),
                    }, status=200)

            case 'add_fav':
                if product_id not in fav_list:
                    fav_list.append(product_id)
            case 'remove_fav':
                fav_list.remove(product_id)
            case 'add_to_compare':
                if product_id not in comp_list:
                    comp_list.append(product_id)
            case 'remove_to_compare':
                comp_list.remove(product_id)

        request.session['favorites'] = fav_list
        request.session['compare'] = comp_list

    return JsonResponse({'product_id': product_id}, status=200)
