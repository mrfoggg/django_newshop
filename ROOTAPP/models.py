import math
from decimal import Decimal

from django.contrib.auth.models import User, AbstractUser
from django.db import models
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from phonenumber_field.modelfields import PhoneNumberField

from phonenumbers import carrier
from phonenumbers import geocoder
from phonenumbers.phonenumberutil import region_code_for_number

TYPES_OF_PHONE = (
    (1, "Viber"),
    (2, "Telegram"),
    (3, "WhatsUp"),
)


# Create your models here.
class Messenger(models.Model):
    type = models.SmallIntegerField(
        choices=TYPES_OF_PHONE, default=4, db_index=True, verbose_name='Мессенжер')

    def __str__(self):
        return str(self.get_type_display())

    class Meta:
        verbose_name = "Мессенжер"
        verbose_name_plural = "Мессенжеры"


def get_phone_full_str(number):
    region_code = region_code_for_number(number)
    if carrier.name_for_number(number, "ru"):
        phone_info = carrier.name_for_number(number, "ru")

    elif geocoder.description_for_number(number, "ru"):
        phone_info = geocoder.description_for_number(number, "ru")
    else:
        phone_info = None
    phone_str = str(number)
    formatted_phone = f"{phone_str[0:3]} ({phone_str[3:6]}) {phone_str[6:9]} {phone_str[9:11]} {phone_str[11:]}"
    phone = formatted_phone if region_code == 'UA' else phone_str
    return str(f'{phone} ({region_code}, {phone_info})')


class Phone(models.Model):
    number = PhoneNumberField(blank=True, help_text='Номер телефона', unique=True)
    messengers = models.ManyToManyField(
        Messenger, blank=True, default=None, verbose_name='Подключенные мессенжеры')
    telegram_username = models.CharField(max_length=128, blank=True, null=True, unique=True,
                                         verbose_name='Имя пользователя в телеграмм')

    def __str__(self):
        return get_phone_full_str(self.number)

    @property
    @admin.display(description="Ссылки на мессенжеры")
    def get_chat_links(self):
        def getlink(messenger):
            return {
                       1: '<a href = "viber://chat?number=%(number)s" > %(messenger)s</a> ',
                       2: '<a href="tg://resolve?domain=%(telegram_username)s">%(messenger)s</a>'
                       if self.telegram_username else "Telegram: не указан логин",
                       3: '<a href="https://wa.me/%(number)s" target="_blank">%(messenger)s</a>'
                   }[messenger.type] % {
                       'number': str(self.number)[1:],
                       'full_number': self.number,
                       'messenger': messenger.__str__(),
                       'telegram_username': self.telegram_username
                   }

        return format_html(', '.join([getlink(m) for m in self.messengers.all()]))

    class Meta:
        verbose_name = "Номер телефона"
        verbose_name_plural = "Номера телефонов"


class Person(AbstractUser):
    middle_name = models.CharField('Отчество', max_length=128, blank=True, null=True, default=None, db_index=True)
    is_customer = models.BooleanField('Является покупателем', default=False)
    is_supplier = models.BooleanField('Является поставщиком', default=False)
    main_phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.SET_NULL, unique=True,
                                   verbose_name='Телефон для авторизации', related_name='login_person')
    delivery_phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.SET_NULL,
                                       verbose_name='Телефон для доставки', related_name='delivery_persons')

    # first_name = models.CharField('Имя', max_length=128, blank=True, null=True, default=None, db_index=True)
    # last_name = models.CharField('Фамилия', max_length=128,  blank=True, null=True, default=None, db_index=True)

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        return f'N{self.id} - {self.last_name} {self.first_name} {self.middle_name}'


class PersonPhone(models.Model):
    person = models.ForeignKey(Person, null=True, blank=True, on_delete=models.SET_NULL, related_name='phones')
    phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.SET_NULL)
    is_nova_poshta = models.BooleanField('Привязан к новой почте', default=False)

    class Meta:
        verbose_name = 'Телефон контрагента'
        verbose_name_plural = 'Телефоны контрагента'
        unique_together = ('person', 'phone')

    def __str__(self):
        return f'Телефон контрагента {self.person} - {self.phone}'


class SettlementType(models.Model):
    ref = models.CharField('Ref типа населенного пункта', max_length=128, primary_key=True)
    description_ru = models.CharField('Название типа населенного пункта', max_length=128, default=None)
    description_ua = models.CharField('Название типа населенного пункта укр.', max_length=128, default=None)

    class Meta:
        verbose_name = 'Тип населенного пункта'
        verbose_name_plural = 'Населенные пункта'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ru


class SettlementArea(models.Model):
    ref = models.CharField('Ref области', max_length=128, primary_key=True)
    description_ru = models.CharField('Название области', max_length=128, default=None)
    description_ua = models.CharField('Название области укр.', max_length=128, default=None)

    class Meta:
        verbose_name = 'Область'
        verbose_name_plural = 'Области'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ua


class SettlementRegion(models.Model):
    ref = models.CharField('Ref района', max_length=128, primary_key=True)
    description_ru = models.CharField('Название района', max_length=128, default=None)
    description_ua = models.CharField('Название района укр.', max_length=128, default=None)

    class Meta:
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ru


class SettlementOrCity(models.Model):
    description_ru = models.CharField('Название', max_length=50, null=True, db_index=True)
    description_ua = models.CharField('Название укр.', max_length=50, null=True, db_index=True)
    ref = models.CharField('Ref', max_length=36, primary_key=True)
    type = models.ForeignKey(SettlementType, on_delete=models.CASCADE, db_index=True, null=True,
                             verbose_name='Тип населенного пункта')
    area = models.ForeignKey(SettlementArea, on_delete=models.CASCADE, db_index=True, verbose_name="Область", null=True)


    class Meta:
        abstract = True
        ordering = ('description_ru',)


class Settlement(SettlementOrCity):
    region = models.ForeignKey(SettlementRegion, on_delete=models.CASCADE, verbose_name="Район", null=True)
    warehouse = models.BooleanField('Наличие отделений', null=True)
    index_1 = models.CharField('Начало диапазона индексов', max_length=10, null=True)
    index_2 = models.CharField('Конец диапазона индексов', max_length=10, null=True, )
    index_coatsu_1 = models.CharField('Индекс КОАТУУ', max_length=36, null=True)

    class Meta:
        verbose_name = 'Населенный пункт'
        verbose_name_plural = 'Населенные пункты'

    def __str__(self):
        region = f'{self.region.description_ua}, ' if self.region_id else ''
        return f'{self.type.description_ua} {self.description_ua} ({region}{self.area.description_ua})'
        # return ''


class City(SettlementOrCity):
    city_id = models.CharField('Код города', null=True, max_length=128)
    is_branch = models.BooleanField('Филиал или партнер')
    prevent_entry_new_streets_user = models.BooleanField('Запрет ввода новых улиц')

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self):
        return f'{self.type.description_ua} {self.description_ua} ({self.area.description_ua})'


class TypeOfWarehouse(models.Model):
    ref = models.CharField('Ref типа отделения', max_length=128, primary_key=True)
    description_ru = models.CharField('Название типа отделения', max_length=128, default=None)
    description_ua = models.CharField('Название типа отделения укр.', max_length=128, default=None)

    class Meta:
        verbose_name = 'Тип отделение '
        verbose_name_plural = 'Типы отделения'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ru


def reformate_coord(dd):
    d = math.trunc(dd)
    m = math.trunc((dd - d) * 60)
    s = ((dd - d) * 60 - m) * 60
    return d, m, s


# class Street(models.Model):
#     ref = models.CharField('Ref улицы', max_length=36, primary_key=True)


class Warehouse(models.Model):
    ref = models.CharField('Ref отделения', max_length=36, primary_key=True)
    site_key = models.CharField('Код отделения', max_length=10, default=None)
    type_warehouse = models.ForeignKey(TypeOfWarehouse, max_length=36, default=None, on_delete=models.CASCADE,
                                       verbose_name="Тип отделения", related_name='warhauses', db_index=True)
    settlement = models.ForeignKey(Settlement, default=None, on_delete=models.CASCADE,
                                   verbose_name="Населенный пункт", related_name='warhauses', db_index=True)
    city = models.ForeignKey(City, default=None, on_delete=models.CASCADE,
                                   verbose_name="Город", related_name='warhauses', db_index=True)
    number = models.PositiveIntegerField('Номер отделения', db_index=True, )
    description_ru = models.CharField('Название отделения', max_length=99, default=None, null=True)
    description_ua = models.CharField('Название отделения укр.', max_length=99, default=None, null=True)
    longitude = models.DecimalField('Долгота', max_digits=18, decimal_places=15, default=None, null=True)
    latitude = models.DecimalField('Широта', max_digits=18, decimal_places=15, default=None, null=True)
    post_finance = models.BooleanField('Наличие кассы NovaPay', null=True)
    payment_access = models.BooleanField('Возможность оплаты на отделении', null=True)
    pos_terminal = models.BooleanField('Наличие терминала на отделении', null=True)
    international_shipping = models.BooleanField('Международная отправка', null=True)
    self_service_workplaces = models.BooleanField('Терминал самообслуживания', null=True)
    total_max_weight = models.PositiveSmallIntegerField('Максимальный вес', null=True)
    place_max_weight = models.PositiveSmallIntegerField('Максимальный вес на место', null=True)
    sending_limitations_on_dimensions = models.JSONField('Максимальные габбариты для отправки', default=dict,
                                                         blank=True, db_index=True, null=True)
    receiving_limitations_on_dimensions = models.JSONField('Максимальные габбариты для получения', default=dict,
                                                           blank=True, db_index=True, null=True)
    reception = models.JSONField('График приема посылок', default=dict, blank=True, db_index=True, null=True)
    delivery = models.JSONField('График привема день в день', default=dict, blank=True, db_index=True, null=True)
    schedule = models.JSONField('График работы', default=dict, blank=True, db_index=True, null=True)
    warehouse_status = models.CharField('Статус отделения', max_length=36, default=None, null=True)
    warehouse_status_date = models.CharField('Дата статуса отделения', max_length=36, default=None, null=True)
    category_warehouse = models.CharField('Категория отделения', max_length=36, default=None, null=True)
    deny_to_select = models.BooleanField('Запрет выбора отделения', null=True)
    only_receiving_parcel = models.BooleanField('Работает только на выдачу', null=True)
    post_machine_type = models.CharField('Тип почтомата', max_length=36, default='', null=True, blank=True)
    index = models.CharField('Цифровой адрес склада', max_length=36, default='', null=True, blank=True)

    @property
    def long(self):
        long = reformate_coord(self.longitude) if self.longitude else False
        return f"{long[0]}°{long[1]}'0{str(long[2].quantize(Decimal('1.0')))}\"E" if long else False

    @property
    def alt(self):
        alt = reformate_coord(self.latitude) if self.latitude else False
        return f"{alt[0]}°{alt[1]}'0{str(alt[2].quantize(Decimal('1.0')))}\"N" if alt else False

    @property
    @admin.display(description='Координаты')
    def map_link(self):
        if self.long and self.alt:
            ln = 'https://www.google.com.ua/maps/place/' + f'{self.alt}+{self.long}' if self.alt and self.long else False
            return mark_safe(f'<a href={ln} target="_blank">Показать на карте</a>') if ln else 'Нет координат'
        else:
            return 'Координаты не указаны'

    class Meta:
        verbose_name = 'Отделение Новой почты'
        verbose_name_plural = 'Отделения Новой почты'
        ordering = ('number',)

    def __str__(self):
        return f'{self.description_ua} ({self.type_warehouse})'


class PersonSettlement(models.Model):
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, verbose_name='Населенный пункт')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name='Контрагент')
    priority = models.PositiveSmallIntegerField("Приоритет населенного пункта", blank=True, null=True)

    class Meta:
        verbose_name = "Населенный пункт контрагента"
        verbose_name_plural = "Населенные пункты контрагента"
        unique_together = ('settlement', 'person')
        ordering = ('priority',)

    def __str__(self):
        return f'Населенный пункт {self.settlement}, контрагента - {self.person}'


class PersonAddress(models.Model):
    area = models.ForeignKey(SettlementArea, on_delete=models.CASCADE, verbose_name="Область")
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, verbose_name="Населенный пункт", )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Отделение", )
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name="Контрагент")

    class Meta:
        verbose_name = "Адрес доставки контрагента"
        verbose_name_plural = "Адреса доставки контрагента"
        unique_together = ('settlement', 'person', 'area', 'warehouse')
        ordering = ('area',)

    def __str__(self):
        return f'{self.settlement}, {self.warehouse}'
