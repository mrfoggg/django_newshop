import requests
import json
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html
from jsonview.decorators import json_view

from nova_poshta.services import settlement_parameters, city_parameters, warehouse_parameters, get_response, \
    get_and_apply_changes, build_objects_to_create, timeout_limit
from nova_poshta.models import Settlement, City, Warehouse


def update_np_catalogs(request, obj_type):
    types_settings = {
        'Settlement': ("getSettlements", settlement_parameters),
        'City': ("getCities", city_parameters),
        'Warehouse': ("getWarehouses", warehouse_parameters),
    }
    called_method, data_structure = types_settings[obj_type.__name__]

    print('called_method - ', called_method)

    objects_request_dict = {
        "modelName": "Address",
        "calledMethod": called_method,
        "methodProperties": {
            "Limit": '500' if obj_type == Warehouse else '150'
        }
    }
    data, message_text = request.GET, ''
    search_by_descr, search_by_settlement, search_by_city = False, False, False
    objects_position, added_objects_count, edited_objects_count = 1, 0, 0
    objects_limit = int(objects_request_dict['methodProperties']['Limit'])
    page, ln = 1, objects_limit

    if data:
        print('FORM DATA: ', data)
        if 'search_name' in data.keys():
            search_by_descr = True
            objects_request_dict['methodProperties']['FindByString'] = (search_name := data['search_name'])
            message_text = f'Обновление списка элементов справочника по запросу {search_name} <br>'
        if 'settlement' in data.keys():
            search_by_descr = True
            objects_request_dict['methodProperties']['SettlementRef'] = (search_name := data['settlement'])
            message_text = f'Обновление справочник отделений по указанному населенному пункту <br>'
        if 'city' in data.keys():
            search_by_descr = True
            objects_request_dict['methodProperties']['Ref'] = (search_name := data['city'])
            message_text = f'Обновление справочник улиц по указанному городу  <br>'

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
                if obj_type == Warehouse:
                    object_name = obj_data['DescriptionRu']
                else:
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
                    new_objects, mess_new_obj = build_objects_to_create(obj_data, obj_type, data_structure)
                    objects_to_create.append(new_objects)
                    message_text += mess_new_obj
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
    return HttpResponseRedirect(reverse('admin:nova_poshta_settlement_changelist'))


def update_cities(request):
    update_np_catalogs(request, City)
    return HttpResponseRedirect(reverse('admin:nova_poshta_city_changelist'))


def update_warehouses(request):
    update_np_catalogs(request, Warehouse)
    return HttpResponseRedirect(reverse('admin:nova_poshta_warehouse_changelist'))

@json_view
def get_delivery_cost(request):
    number_of_attempts = 1
    max_number_of_attempts = 5
    # timeout_limit = 3.0
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
            # request_json = json.dumps(data_cost, indent=4)
            # response = requests.post(url_np, data=request_json, timeout=timeout_limit)
            response_dict = get_response(data_cost)
            # response_dict = json.loads(response.text)
            print('response_dict - ', response_dict)
            return {
                'settlement_to_name': str(Settlement.objects.get(ref=request.POST.get("settlement"))),
                'cost_redelivery': response_dict['data'][0]['CostRedeliveryWarehouseWarehouse'],
                'CostWarehouseWarehouse': response_dict['data'][0]['CostWarehouseWarehouse'],
                'CostWarehouseDoors': response_dict['data'][0]['CostWarehouseDoors'],
                'Cost': request.POST.get("price"),
            }
            break
        except requests.exceptions.Timeout:
            number_of_attempts += 1
            print(f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка - ')

    return response('')

