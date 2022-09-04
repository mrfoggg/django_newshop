from django.contrib import messages
import json
from django.http import HttpResponseRedirect
from django.urls import reverse
import requests
from django.utils.html import format_html

from ROOTAPP.models import City


def update_cities(request):
    data = request.GET
    url = 'https://api.novaposhta.ua/v2.0/json/'
    limit = 150
    timeout_limit = 7.0
    request_dict = {
        "apiKey": "140789e313fe633ba131d5ec07465120",
        "modelName": "Address",
        "calledMethod": "getSettlements",
        "methodProperties": {
            # "FindByString": "0",
            "Limit": str(limit)
        }
    }
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
            city_to_create_list = []
            new_cities_names_list = []
            edited_cities_data_list = []
            for data in response_dict['data']:
                data_city_str = f"№{count}: {data['DescriptionRu']}/{data['Description']} ({data['AreaDescriptionRu']}, " \
                                f"{data['RegionsDescriptionRu']})"
                if search_by_descr:
                    message_text += f'Найдено {data_city_str} <br>'
                    print(f'Найдено {data_city_str}')
                if City.objects.filter(ref=data['Ref']).exists():
                    city = City.objects.get(ref=data['Ref'])
                    changed = []
                    if data['DescriptionRu']:
                        if (old := city.description_ru) != (new := data['DescriptionRu']):
                            changed.append(True)
                            m = f'Для населенного пункта {city} значение поля "Название" сменилось с /{old}/ на /{new}/'
                            print(m)
                            edited_cities_data_list.append(m)
                            city.description_ru = data['DescriptionRu']

                    if data['Description']:
                        if (old := city.description) != (new := data['Description']):
                            changed.append(True)
                            m = f'Для населенного пункта {city} значение поля "Название укр." сменилось с /{old}/ на /{new}/'
                            print(m)
                            edited_cities_data_list.append(m)
                            city.description = data['Description']

                    if data['SettlementTypeDescriptionRu']:
                        if (old := city.settlement_type_description_ru) != (new := data['SettlementTypeDescriptionRu']):
                            changed.append(True)
                            m = f'Для населенного пункта {city} значение поля "Тип населенного пункта" сменилось с /{old}/ на /{new}/'
                            print(m)
                            edited_cities_data_list.append(m)
                            city.settlement_type_description_ru = data['SettlementTypeDescriptionRu']

                    if data['SettlementTypeDescription']:
                        if (old := city.settlement_type_description) != (new := data['SettlementTypeDescription']):
                            changed.append(True)
                            m = f'Для населенного пункта {city} значение поля "Тип населенного пункта укр." сменилось с /{old}/ на /{new}/'
                            print(m)
                            edited_cities_data_list.append(m)
                            city.settlement_type_description = data['SettlementTypeDescription']

                    if data['SettlementType']:
                        if (old := city.settlement_type) != (new := data['SettlementType']):
                            m = f'Для населенного пункта {city} значение поля "Ref типа населенного пункта" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.settlement_type = data['SettlementType']

                    if data['AreaDescriptionRu']:
                        if (old := city.area_description_ru) != (new := data['AreaDescriptionRu']):
                            m = f'Для населенного пункта {city} значение поля "Область" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.area_description_ru = data['AreaDescriptionRu']

                    if data['AreaDescription']:
                        if (old := city.area_description) != (new := data['AreaDescription']):
                            m = f'Для населенного пункта {city} значение поля "Область укр." сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.area_description_ru = data['AreaDescription']

                    if data['Area']:
                        if (old := city.area) != (new := data['Area']):
                            m = f'Для населенного пункта {city} значение поля "Ref области" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.area = data['Area']

                    if data['RegionsDescriptionRu']:
                        if (old := city.region_description_ru) != (new := data['RegionsDescriptionRu']):
                            m = f'Для населенного пункта {city} значение поля "Район" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.region_description_ru = data['RegionsDescriptionRu']

                    if data['RegionsDescription']:
                        if (old := city.region_description) != (new := data['RegionsDescription']):
                            m = f'Для населенного пункта {city} значение поля "Район укр." сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.region_description = data['RegionsDescription']

                    if data['Region']:
                        if (old := city.region) != (new := data['Region']):
                            m = f'Для населенного пункта {city} значение поля "Ref района" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.region = data['Region']

                    if data['Warehouse']:
                        new = True if data['Warehouse'] == '1' else False
                        if (old := city.warehouse) != new:
                            print(f'{old=}, {new=}, {data["Warehouse"]=}')
                            m = f'Для населенного пункта {city} значение поля "Наличие отделений" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.warehouse = data['Warehouse']

                    if data['Index1']:
                        if (old := city.index_1) != (new := data['Index1']):
                            m = f'Для населенного пункта {city} значение поля "index_1" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.index_1 = data['Index1']

                    if data['Index2']:
                        if (old := city.index_2) != (new := data['Index2']):
                            m = f'Для населенного пункта {city} значение поля "index_2" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.index_1 = data['Index2']

                    if data['IndexCOATSU1']:
                        if (old := city.index_coatsu_1) != (new := data['IndexCOATSU1']):
                            m = f'Для населенного пункта {city} значение поля "IndexCOATSU1" сменилось с /{old}/ на /{new}/'
                            print(m)
                            changed.append(True)
                            edited_cities_data_list.append(m)
                            city.index_coatsu_1 = data['IndexCOATSU1']
                    if any(changed):
                        edited_count += 1
                        city.save()
                else:
                    # is_exists_new = True
                    city_to_create_list.append(City(
                        description_ru=data['DescriptionRu'], description=data['Description'], ref=data["Ref"],
                        settlement_type_description_ru=data['SettlementTypeDescriptionRu'],
                        settlement_type_description=data['SettlementTypeDescription'],
                        settlement_type=data['SettlementType'],
                        area_description_ru=data['AreaDescriptionRu'],
                        area_description=data['AreaDescription'], area=data['Area'],
                        region_description_ru=data['RegionsDescriptionRu'],
                        region_description=data['RegionsDescription'], region=data['Region'],
                        warehouse=data['Warehouse'], index_coatsu_1=data['IndexCOATSU1'],
                        index_1=data['Index1'], index_2=data['Index2']
                    ))
                    new_cities_names_list.append(data_city_str)
                    print(f'Добавлено: {data_city_str}')
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

            City.objects.bulk_create(city_to_create_list)
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
    return HttpResponseRedirect(reverse('admin:ROOTAPP_city_changelist'))
