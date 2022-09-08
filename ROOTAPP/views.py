from django.contrib import messages
import json
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
import requests
from django.utils.html import format_html

from ROOTAPP.models import Settlement, SettlementType, SettlementArea, SettlementRegion


def update_cities(request):
    data = request.GET
    url = 'https://api.novaposhta.ua/v2.0/json/'
    limit = 150
    timeout_limit = 3.0
    request_dict = {
        "modelName": "Address",
        "calledMethod": "getSettlements",
        "methodProperties": {
            # "FindByString": "0",
            "Limit": str(limit)
        }
    }
    message_text = ''
    search_by_descr = False
    if data:
        print(f'{data=}')
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
            response = requests.post(url, data=request_json, timeout=timeout_limit)
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


def get_cities_by_area(request):
    area_ref = request.GET.get("settlement_area")
    settlements = Settlement.objects.filter(area=area_ref).values('ref', 'description_ua', 'region__description_ua')
    return JsonResponse({"settlements": list(settlements)}, status=200)
