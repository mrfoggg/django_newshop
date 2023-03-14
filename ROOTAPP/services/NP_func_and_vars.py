from collections import namedtuple
import json
import requests
from ROOTAPP.models import Settlement, SettlementType, SettlementArea, SettlementRegion, Phone, PersonPhone, Person, \
    get_phone_full_str, Messenger, Warehouse, TypeOfWarehouse, City
from deepdiff import DeepDiff

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
    )
)

settlement_parameters = settlement_and_city_parameters + (
    parameter_template(
        db_field='region_id',
        api_field='Region',
        description='Район'
    ),
    parameter_template(
        db_field='warehouse',
        api_field='Warehouse',
        description='Наличие отделений'
    ),
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

warehouse_parameters = main_parameters + (
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
        db_field='longitude',
        api_field='Longitude',
        description='Долгота'
    ),
    parameter_template(
        db_field='latitude',
        api_field='Latitude',
        description='Широта'
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
)


def get_response(request_dict):
    request_json = json.dumps(request_dict, indent=4)
    response = requests.post(url_np, data=request_json, timeout=timeout_limit)
    return json.loads(response.text)


def area_create_if_not_exists(data):
    SettlementArea.objects.get_or_create(
        ref=data['Area'],
        defaults={
            'description_ru': data['AreaDescriptionRu'],
            'description_ua': data['AreaDescription']
        }
    )


def region_create_if_not_exists(data):
    SettlementRegion.objects.get_or_create(
        ref=data['Region'],
        defaults={
            'description_ru': data['RegionsDescriptionRu'],
            'description_ua': data['RegionsDescription']
        }
    )


def settlement_type_create_if_not_exists(data):
    SettlementType.objects.get_or_create(
        ref=data['SettlementType'],
        defaults={
            'description_ru': data['SettlementTypeDescriptionRu'],
            'description_ua': data['SettlementTypeDescription']
        }
    )


def get_one_settlement_api_data(settlement_ref):
    settlement_request_dict = {
        "modelName": "Address",
        "calledMethod": 'getSettlements',
        "methodProperties": {
            "Limit": '1',
            "Ref": settlement_ref
        }
    }
    return get_response(settlement_request_dict)['data'][0]


def get_one_city_api_data(city_ref):
    city_request_dict = {
        "modelName": "Address",
        "calledMethod": 'getCities',
        "methodProperties": {
            "Limit": '1',
            "Ref": city_ref
        }
    }
    return get_response(city_request_dict)['data'][0]


def build_objects_to_create(data, db_model, parameters_template, is_sub_request=None):
    match db_model.__name__:
        case 'Settlement':
            settlement_type_create_if_not_exists(data)
            area_create_if_not_exists(data)
            region_create_if_not_exists(data)
        case 'City':
            settlement_type_create_if_not_exists(data)
            area_create_if_not_exists(data)
        case 'Warehouse':
            if not Settlement.objects.filter(ref=(settlement_ref := data['SettlementRef'])).exists():
                settlement_response_data = get_one_settlement_api_data(settlement_ref)
                build_objects_to_create(settlement_response_data, Settlement, settlement_parameters, True)
                settlement_type_create_if_not_exists(settlement_response_data)

            if not City.objects.filter(ref=(city_ref := data['CityRef'])).exists():
                city_response_data = get_one_city_api_data(city_ref)
                build_objects_to_create(city_response_data, City, city_parameters, True)
                settlement_type_create_if_not_exists(city_response_data)

    obj_to_create = db_model()
    for param in parameters_template:
        setattr(obj_to_create, param.db_field, data[param.api_field])
    if is_sub_request:
        obj_to_create.save()
    return obj_to_create


def create_obj_if_not_exists(obj_model, ref, obj_parameters):
    if not obj_model.objects.filter(ref=ref).exists():
        request_result = False
        obj_parameters['methodProperties']['Ref'] = ref
        while not request_result:
            try:
                to_create_data = get_response(obj_parameters)['data'][0]
                created_obj = build_objects_to_create(to_create_data, obj_model)
                created_obj.save()
                request_result = True
                return f'<h5>Создан {obj_model._meta.verbose_name} {created_obj} </h5>'
            except requests.exceptions.Timeout:
                print(
                    f'Превышен лимит ожидания {timeout_limit}c / Повторная попытка запроса населенного пункта')


def get_and_apply_changes(obj, structure, api_data):
    changed_fields_info = ''
    obj_is_changed = False
    changed_fields = []
    for struct_field in structure:
        if struct_field[0] == 'ref':
            continue
        field_db_val = obj.__dict__[struct_field.db_field]
        api_field_val = api_data[struct_field.api_field]
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
