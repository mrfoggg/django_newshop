import json
from collections import namedtuple

import requests
from deepdiff import DeepDiff

from nova_poshta.models import (CityArea, Settlement, SettlementArea,
                                SettlementRegion, SettlementType,
                                TypeOfWarehouse)

url_np = 'https://api.novaposhta.ua/v2.0/json/'

pml = '<p style="margin-left: 2rem;">'


def replace_str_dict(s):
    return str(s).replace('{', '').replace('}', '')


limit = 150
big_limit = 500
timeout_limit = 3.0

parameter_template = namedtuple('parameter_template', 'db_field api_field description')

main_parameters = (
    parameter_template(
        db_field='ref',
        api_field='Ref',
        description=''
    ),
    parameter_template(
        db_field='description_ru',
        api_field='DescriptionRu',
        description='Название на русском'
    ),
    parameter_template(
        db_field='description_ua',
        api_field='Description',
        description='Название на украинском'
    )
)

settlement_and_city_parameters = main_parameters + (
    parameter_template(
        db_field='type_id',
        api_field='SettlementType',
        description='Тип населенного пункта'
    ),
    parameter_template(
        db_field='area_id',
        api_field='Area',
        description='Область'
    ),
    parameter_template(
        db_field='conglomerates',
        api_field='Conglomerates',
        description='Конгломерат'
    ),
)

coordinates_parameters = (
    parameter_template(
        db_field='longitude',
        api_field='Longitude',
        description='Долгота'
    ),
    parameter_template(
        db_field='latitude',
        api_field='Latitude',
        description='Широта'
    ),
)

settlement_parameters = settlement_and_city_parameters + coordinates_parameters + (
    parameter_template(
        db_field='region_id',
        api_field='Region',
        description='Район'
    ),
    # parameter_template(
    #     db_field='warehouse',
    #     api_field='Warehouse',
    #     description='Наличие отделений'
    # ),
    parameter_template(
        db_field='index_1',
        api_field='Index1',
        description='Начало диапазона индексов'
    ),
    parameter_template(
        db_field='index_2',
        api_field='Index2',
        description='Конец диапазона индексов'
    ),
    parameter_template(
        db_field='index_coatsu_1',
        api_field='IndexCOATSU1',
        description='Индекс КОАТУУ'
    )
)

city_parameters = settlement_and_city_parameters + (
    parameter_template(
        db_field='city_id',
        api_field='CityID',
        description='Код города'
    ),
    parameter_template(
        db_field='is_branch',
        api_field='IsBranch',
        description='Филиал или партнер'
    ),
    parameter_template(
        db_field='prevent_entry_new_streets_user',
        api_field='PreventEntryNewStreetsUser',
        description='Запрет ввода новых улицр'
    ),

)

warehouse_parameters = main_parameters + coordinates_parameters + (
    parameter_template(
        db_field='site_key',
        api_field='SiteKey',
        description='Код отделения'
    ),
    parameter_template(
        db_field='type_warehouse_id',
        api_field='TypeOfWarehouse',
        description='Код отделения'
    ),
    parameter_template(
        db_field='settlement_id',
        api_field='SettlementRef',
        description='Населенный пункт'
    ),
    parameter_template(
        db_field='city_id',
        api_field='CityRef',
        description='Город'
    ),
    parameter_template(
        db_field='number',
        api_field='Number',
        description='Номер отделения'
    ),
    parameter_template(
        db_field='post_finance',
        api_field='PostFinance',
        description='Наличие кассы PostFinance'
    ),
    parameter_template(
        db_field='payment_access',
        api_field='PaymentAccess',
        description='Возможность оплаты на отделении'
    ),
    parameter_template(
        db_field='pos_terminal',
        api_field='POSTerminal',
        description='Наличие терминала на отделени'
    ),
    parameter_template(
        db_field='international_shipping',
        api_field='InternationalShipping',
        description='Международная отправка'
    ),
    parameter_template(
        db_field='self_service_workplaces',
        api_field='SelfServiceWorkplacesCount',
        description='Терминал самообслуживания'
    ),
    parameter_template(
        db_field='total_max_weight',
        api_field='TotalMaxWeightAllowed',
        description='Максимальный вес'
    ),
    parameter_template(
        db_field='place_max_weight',
        api_field='PlaceMaxWeightAllowed',
        description='Максимальный вес на место'
    ),
    parameter_template(
        db_field='sending_limitations_on_dimensions',
        api_field='SendingLimitationsOnDimensions',
        description='Максимальные габбариты для отправки'
    ),
    parameter_template(
        db_field='receiving_limitations_on_dimensions',
        api_field='ReceivingLimitationsOnDimensions',
        description='Максимальные габбариты для получения'
    ),
    parameter_template(
        db_field='reception',
        api_field='Reception',
        description='График приема посылок'
    ),
    parameter_template(
        db_field='delivery',
        api_field='Delivery',
        description='График привема день в день'
    ),
    parameter_template(
        db_field='schedule',
        api_field='Schedule',
        description='График работы'
    ),
    parameter_template(
        db_field='warehouse_status',
        api_field='WarehouseStatus',
        description='Статус отделения'
    ),
    parameter_template(
        db_field='warehouse_status_date',
        api_field='WarehouseStatusDate',
        description='Дата статуса отделения'
    ),
    parameter_template(
        db_field='category_warehouse',
        api_field='CategoryOfWarehouse',
        description='Категория отделения'
    ),
    parameter_template(
        db_field='category_warehouse',
        api_field='CategoryOfWarehouse',
        description='Запрет выбора отделения'
    ),
    parameter_template(
        db_field='only_receiving_parcel',
        api_field='OnlyReceivingParcel',
        description='Работает только на выдачу'
    ),
    parameter_template(
        db_field='post_machine_type',
        api_field='PostMachineType',
        description='Тип почтомата'
    ),
    parameter_template(
        db_field='index',
        api_field='WarehouseIndex',
        description='Цифровой адрес склада'
    ),
    parameter_template(
        db_field='region_city',
        api_field='RegionCity',
        description='Область/город'
    ),
    parameter_template(
        db_field='district_code',
        api_field='DistrictCode',
        description='Код района'
    ),
)


def get_response(request_dict):
    request_json = json.dumps(request_dict, indent=4)
    response = requests.post(url_np, data=request_json, timeout=timeout_limit)
    return json.loads(response.text)


def settlement_area_create_if_not_exists(data):
    obj, created = SettlementArea.objects.get_or_create(
        ref=data['Area'],
        defaults={
            'description_ru': data['AreaDescriptionRu'],
            'description_ua': data['AreaDescription']
        }
    )
    return f'<h5>Создана область {obj} </h5>' if created else ''


def city_area_create_if_not_exists(data):
    obj, created = CityArea.objects.get_or_create(
        ref=data['Area'],
        defaults={
            'description_ru': data['AreaDescriptionRu'],
            'description_ua': data['AreaDescription']
        }
    )
    return f'<h5>Создана область {obj} </h5>' if created else ''


def region_create_if_not_exists(data):
    obj, created = SettlementRegion.objects.get_or_create(
        ref=data['Region'],
        defaults={
            'description_ru': data['RegionsDescriptionRu'],
            'description_ua': data['RegionsDescription']
        }
    )
    return f'<h5>Создан район {obj} </h5>' if created else ''


def settlement_type_create_if_not_exists(data):
    obj, created = SettlementType.objects.get_or_create(
        ref=data['SettlementType'],
        defaults={
            'description_ru': data['SettlementTypeDescriptionRu'],
            'description_ua': data['SettlementTypeDescription']
        }
    )
    return f'<h5>Создан тип населенного пункта {obj} </h5>' if created else ''


def update_all_warehouses_types():
    print('Обновление списка типов отделений')
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
            return '<h5>Справочник типов отделений обновлен</h5>'
        except requests.exceptions.Timeout:
            print(
                f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка запроса типов отд')


def get_one_settlement_api_data(settlement_ref):
    print('Запрос данных отсутствующего в справочнике населенного пункта')
    settlement_request_dict = {
        "modelName": "Address",
        "calledMethod": 'getSettlements',
        "methodProperties": {
            "Limit": '1',
            "Ref": settlement_ref
        }
    }
    is_success = False
    while not is_success:
        try:
            is_success = True
            return get_response(settlement_request_dict)['data'][0]
        except requests.exceptions.Timeout:
            print(f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка - ')
            print()


def get_one_city_api_data(city_ref):
    print('Запрос данных отсутствующего в справочнике города')
    city_request_dict = {
        "modelName": "Address",
        "calledMethod": 'getCities',
        "methodProperties": {
            "Limit": '1',
            "Ref": city_ref
        }
    }
    is_success = False
    while not is_success:
        try:
            is_success = True
            resp_data = get_response(city_request_dict)['data']
            return resp_data[0] if resp_data else False
        except requests.exceptions.Timeout:
            print(f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка - ')
            print()


def build_objects_to_create(data, db_model, parameters_template, is_sub_request=False, fix=False):
    messages = ''
    match db_model.__name__:
        case 'Settlement':
            messages += settlement_type_create_if_not_exists(data)
            messages += settlement_area_create_if_not_exists(data)
            messages += region_create_if_not_exists(data)
            if is_sub_request:
                messages += f'<h5>Создан населенный пункт {data["DescriptionRu"]}</h5>'
        case 'City':
            if not fix:
                messages += settlement_type_create_if_not_exists(data)
                messages += city_area_create_if_not_exists(data)
            if is_sub_request:
                messages = f'<h5>Создан город {data["DescriptionRu"]}</h5>'
        case 'Warehouse':
            if not (settlement_ref := data['SettlementRef']) == '00000000-0000-0000-0000-000000000000':
                if not Settlement.objects.filter(ref=settlement_ref).exists():
                    settlement_response_data = get_one_settlement_api_data(settlement_ref)
                    new_msg = \
                        build_objects_to_create(settlement_response_data, Settlement, settlement_parameters, True)[1]
                    new_msg_2 = settlement_type_create_if_not_exists(settlement_response_data)
                    messages += new_msg
                    messages += new_msg_2
            else:
                data['SettlementRef'] = None

            # if not City.objects.filter(ref=(city_ref := data['CityRef'])).exists():
            #     city_response_data = get_one_city_api_data(city_ref)
            #     # тут делаю fix багов API - находится отделение в городе Высокие Байраки но такого города нет в справонике городов
            #     city_data = city_response_data if city_response_data else {
            #         'Ref': data['CityRef'], 'DescriptionRu': data['CityDescriptionRu'],
            #         'Description': data['CityDescription'], 'Area': None, 'CityID': None, 'IsBranch': None,
            #         'PreventEntryNewStreetsUser': None, 'SettlementType': None,
            #     }
            #     new_msg = build_objects_to_create(city_data, City, city_parameters, True, True)[1]
            #     messages += new_msg

            # if not TypeOfWarehouse.objects.filter(ref=data['TypeOfWarehouse']).exists():
            #     messages += update_all_warehouses_types()

    obj_to_create = db_model()
    for param in parameters_template:
        setattr(obj_to_create, param.db_field, data[param.api_field] if param.api_field in data.keys() else None)
    if is_sub_request:
        obj_to_create.save()
    return obj_to_create, messages


# def create_obj_if_not_exists(obj_model, ref, obj_parameters):
#     if not obj_model.objects.filter(ref=ref).exists():
#         request_result = False
#         obj_parameters['methodProperties']['Ref'] = ref
#         while not request_result:
#             try:
#                 to_create_data = get_response(obj_parameters)['data'][0]
#                 created_obj = build_objects_to_create(to_create_data, obj_model)
#                 created_obj.save()
#                 request_result = True
#                 return f'<h5>Создан {obj_model._meta.verbose_name} {created_obj} </h5>'
#             except requests.exceptions.Timeout:
#                 print(
#                     f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка запроса населенного пункта')


def get_and_apply_changes(obj, structure, api_data):
    changed_fields_info = ''
    obj_is_changed = False
    changed_fields = []
    for struct_field in structure:
        if struct_field[0] == 'ref':
            continue
        # print('obj.__dict__ - ', obj.__dict__)
        field_db_val = obj.__dict__[struct_field.db_field]
        api_field_val = api_data[struct_field.api_field] if struct_field.api_field in api_data.keys() else None
        match str(type(field_db_val)):
            case "<class 'bool'>":
                if field_db_val is not None:
                    field_val_to_check = '1' if field_db_val else '0'
                else:
                    field_val_to_check = str(field_db_val)
                field_changed = False if field_val_to_check == api_field_val else True
                diff = f'{pml}Старое значение: {field_val_to_check}</p>' \
                       f'{pml}Новое значение: {api_field_val}</p>'
            case "<class 'dict'>":
                difff = DeepDiff(field_db_val, api_field_val, ignore_order=True)
                df = any(
                    ('values_changed' in difff, 'dictionary_item_added' in difff,
                     'dictionary_item_removed' in difff))
                field_changed = True if df else False
                if field_changed:
                    diff = f'{pml}старое значение: </p> {pml}{replace_str_dict(field_db_val)}</p>' \
                           f'{pml}Новое значение:</p>{pml}{replace_str_dict(api_field_val)}</p>'
            case "<class 'str'>":
                field_val_to_check = field_db_val if field_db_val is not None else ''
                field_changed = False if api_field_val == field_db_val else True
                diff = f'{pml}Старое значение: {field_val_to_check}</p>' \
                       f'{pml}Новое значение: {api_field_val}</p>'
            case "<class 'NoneType'>":
                field_changed = False if field_db_val == api_field_val else True
                diff = f'{pml}Старое значение: {field_db_val}</p>' \
                       f'{pml}Новое значение: {api_field_val}</p>'
            case _:
                field_val_to_check = str(field_db_val)
                field_changed = False if api_field_val == str(field_db_val) else True
                diff = f'{pml}Старое значение: {str(field_val_to_check)}</p>' \
                       f'{pml}Новое значение: {api_field_val}</p>'

        if field_changed:
            # changed_fields.add(struct_field.db_field)
            changed_fields_info += f'<p>Изменилось поле {struct_field.description} </p> <p>{diff}</p>'
            setattr(obj, struct_field.db_field, api_field_val)
            changed_fields.append(struct_field.db_field)
            obj_is_changed = True

    if obj_is_changed:
        # changed_objects.append(obj)
        new_message_text = f'<h6>Изменились данные {obj._meta.verbose_name} ({obj})' + changed_fields_info
        return {
            'changed': True, 'new_message_text': new_message_text,
            'changed_fields': changed_fields, 'changed_obj': obj
        }
    else:
        return {'changed': False}
