import math
from decimal import Decimal

from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe


def reformate_coord(dd):
    d = math.trunc(dd)
    m = math.trunc((dd - d) * 60)
    s = ((dd - d) * 60 - m) * 60
    return d, m, s


class NpDataModel(models.Model):
    ref = models.CharField('Ref', max_length=36, primary_key=True)
    updated = models.DateTimeField('Изменено', auto_now_add=False, auto_now=True)

    class Meta:
        abstract = True


class Coordinates(models.Model):
    longitude = models.DecimalField('Долгота', max_digits=18, decimal_places=15, default=None, null=True)
    latitude = models.DecimalField('Широта', max_digits=18, decimal_places=15, default=None, null=True)

    class Meta:
        abstract = True


class SettlementType(NpDataModel):
    description_ru = models.CharField('Название типа населенного пункта', max_length=64, default=None)
    description_ua = models.CharField('Название типа населенного пункта укр.', max_length=64, default=None)

    class Meta:
        verbose_name = 'Тип населенного пункта'
        verbose_name_plural = 'Населенные пункта'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ru


class SettlementOrCity(NpDataModel):
    description_ru = models.CharField('Название', max_length=64, null=True, db_index=True)
    description_ua = models.CharField('Название укр.', max_length=64, null=True, db_index=True)
    conglomerates = models.CharField('Конгломераи', max_length=64, null=True, db_index=True)
    type = models.ForeignKey(SettlementType, on_delete=models.CASCADE, db_index=True, null=True,
                             verbose_name='Тип населенного пункта')

    class Meta:
        abstract = True


class SettlementArea(NpDataModel):
    description_ru = models.CharField('Название области', max_length=64, default=None)
    description_ua = models.CharField('Название области укр.', max_length=64, default=None)

    class Meta:
        verbose_name = 'Область населенного пункта'
        verbose_name_plural = 'Областя населенніх пунктов'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ru


class CityArea(NpDataModel):
    description_ru = models.CharField('Название области', max_length=64, default=None)
    description_ua = models.CharField('Название области укр.', max_length=64, default=None)

    class Meta:
        verbose_name = 'Область города'
        verbose_name_plural = 'Областя городовов'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ua


class SettlementRegion(NpDataModel):
    description_ru = models.CharField('Название района', max_length=64, default=None)
    description_ua = models.CharField('Название района укр.', max_length=64, default=None)

    class Meta:
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ru


class Settlement(SettlementOrCity, Coordinates):
    area = models.ForeignKey(SettlementArea, on_delete=models.CASCADE, db_index=True, verbose_name="Область", null=True)
    region = models.ForeignKey(SettlementRegion, on_delete=models.CASCADE, verbose_name="Район", null=True)
    warehouse = models.BooleanField('Наличие отделений', null=True)
    index_1 = models.CharField('Начало диапазона индексов', max_length=10, null=True)
    index_2 = models.CharField('Конец диапазона индексов', max_length=10, null=True, )
    index_coatsu_1 = models.CharField('Индекс КОАТУУ', max_length=36, null=True)

    class Meta:
        verbose_name = 'Населенный пункт'
        verbose_name_plural = 'Населенные пункты'
        ordering = ('description_ru',)

    def __str__(self):
        region = f'{self.region.description_ua}, ' if self.region_id else ''
        return f'{self.type.description_ua} {self.description_ua} ({region}{self.area.description_ua})'
        # return ''

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


class TypeOfWarehouse(NpDataModel):
    description_ru = models.CharField('Название типа отделения', max_length=64, default=None)
    description_ua = models.CharField('Название типа отделения укр.', max_length=64, default=None)

    class Meta:
        verbose_name = 'Тип отделение '
        verbose_name_plural = 'Типы отделения'
        ordering = ('description_ru',)

    def __str__(self):
        return self.description_ru


class City(SettlementOrCity):
    area = models.ForeignKey(CityArea, on_delete=models.CASCADE, db_index=True, verbose_name="Область", null=True)
    city_id = models.CharField('Код города', null=True, max_length=36)
    is_branch = models.BooleanField('Филиал или партнер', null=True)
    prevent_entry_new_streets_user = models.BooleanField('Запрет ввода новых улиц', null=True)

    class Meta:
        verbose_name = 'Город новой почты'
        verbose_name_plural = 'Города новой почты'
        ordering = ('description_ru',)

    def __str__(self):
        area = f'({self.area.description_ua})' if self.area else ''
        tp = self.type.description_ua if self.type else ''
        return f'{tp} {self.description_ua} {area}'


class Warehouse(NpDataModel, Coordinates):
    number = models.PositiveIntegerField('Номер отделения', db_index=True, )
    site_key = models.CharField('Код отделения', max_length=10, default=None)
    region_city = models.CharField('Область/город', max_length=36, default=None, null=True)
    district_code = models.CharField('Код района', max_length=36, default=None, null=True)
    type_warehouse = models.ForeignKey(TypeOfWarehouse, max_length=36, default=None, on_delete=models.CASCADE,
                                       verbose_name="Тип отделения", related_name='warhauses', db_index=True)
    settlement = models.ForeignKey(Settlement, default=None, on_delete=models.CASCADE, null=True,
                                   verbose_name="Населенный пункт", related_name='warhauses', db_index=True)
    city = models.ForeignKey(City, default=None, on_delete=models.CASCADE,
                             verbose_name="Город", related_name='warhauses', db_index=True)
    description_ru = models.CharField('Название отделения', max_length=99, default=None, null=True)
    description_ua = models.CharField('Название отделения укр.', max_length=99, default=None, null=True)
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
    @admin.display(description='Населенный пункт на русском')
    def stl_descr_ru(self):
        return self.settlement.description_ru if self.settlement else 'Населенный пункт отсутствует в локальной базе'

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


class Street(NpDataModel):
    description_ua = models.CharField('Название улицы укр.', max_length=100, default=None, null=True)
    streets_type_ref = models.CharField('Ref типа улицы', max_length=36, default=None, null=True)
    streets_type = models.CharField('Название типа улицы', max_length=36, default=None, null=True)

    class Meta:
        verbose_name = 'Улица'
        verbose_name_plural = 'Улицы'
        ordering = ('description_ua',)

    def __str__(self):
        return f'{self.streets_type} {self.description_ua}'
