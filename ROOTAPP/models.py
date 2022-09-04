from django.db import models
from django.contrib import admin
from django.utils.html import format_html
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


class Phone(models.Model):
    number = PhoneNumberField(blank=True, help_text='Номер телефона')
    messengers = models.ManyToManyField(
        Messenger, blank=True, default=None, verbose_name='Подключенные мессенжеры')
    telegram_username = models.CharField(max_length=128, blank=True, null=True, unique=True,
                                         verbose_name='Имя пользователя в телеграмм')

    def __str__(self):
        region_code = region_code_for_number(self.number)
        if carrier.name_for_number(self.number, "ru"):
            phone_info = carrier.name_for_number(self.number, "ru")

        elif geocoder.description_for_number(self.number, "ru"):
            phone_info = geocoder.description_for_number(self.number, "ru")
        else:
            phone_info = None
        phone_str = str(self.number)
        formatted_phone = f"{phone_str[0:3]} ({phone_str[3:6]}) {phone_str[6:9]} {phone_str[9:11]} {phone_str[11:]}"
        phone = formatted_phone if region_code == 'UA' else phone_str
        return str(f'{phone} ({region_code}, {phone_info})')

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


class Person(models.Model):
    first_name = models.CharField('Имя', max_length=128, default=None, unique=True, db_index=True)
    last_name = models.CharField('Фамилия', max_length=128, default=None, unique=True, db_index=True)
    middle_name = models.CharField('Отчество', max_length=128, default=None, unique=True, db_index=True)
    email = models.EmailField('Электронная почта', max_length=128, null=True, blank=True, unique=True, db_index=True)
    is_customer = models.BooleanField('Является покупателем', default=True)
    is_supplier = models.BooleanField('Является поставщиком', default=False)

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        return f'N{self.id} - {self.last_name} {self.first_name} {self.middle_name}'


class PersonPhone(models.Model):
    person = models.ForeignKey(Person, null=True, blank=True, on_delete=models.SET_NULL)
    phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.SET_NULL)
    is_nova_poshta = models.BooleanField('Привязан к новой почте', default=False)

    class Meta:
        verbose_name = 'Телефон контрагента'
        verbose_name_plural = 'Телефоны контрагента'

    def __str__(self):
        return f'Телефон контрагента {self.person} - {self.phone}'


class City(models.Model):
    description_ru = models.CharField('Название', max_length=128, default=None, db_index=True)
    description = models.CharField('Название укр.', max_length=128, default=None, db_index=True)
    ref = models.CharField('Ref', max_length=128, default=None, unique=True)
    settlement_type_description_ru = models.CharField('Тип населенного пункта', max_length=128, default=None)
    settlement_type_description = models.CharField('Тип населенного пункта укр.', max_length=128, default=None)
    settlement_type = models.CharField('Ref типа населенного пункта', max_length=128, default=None)
    area_description_ru = models.CharField('Область', max_length=128, default=None)
    area_description = models.CharField('Область укр.', max_length=128, default=None)
    area = models.CharField('Ref области', max_length=128, default=None)
    region_description_ru = models.CharField('Район', max_length=128, default=None)
    region_description = models.CharField('Район укр.', max_length=128, default=None)
    region = models.CharField('Ref района', max_length=128, default=None)
    warehouse = models.BooleanField('Наличие отделений', default=False)
    index_1 = models.CharField('Index1', max_length=128, null=True, default=None)
    index_2 = models.CharField('Index2', max_length=128, null=True, default=None)
    index_coatsu_1 = models.CharField('IndexCOATSU1', null=True, max_length=128, default=None)

    class Meta:
        verbose_name = 'Населенный пункт'
        verbose_name_plural = 'Населенные пункты'
        ordering = ('description_ru',)

    def __str__(self):
        return f'{self.settlement_type_description_ru} {self.description_ru}/{self.description}' \
               f' {self.area_description_ru, self.region_description_ru}'


class PersonCity(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name='Населенный пункт')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name='Контрагент')
    priority = models.PositiveSmallIntegerField("Приоритет населенного пункта", blank=True, null=True)

    class Meta:
        verbose_name = "Населенный пункт контрагента"
        verbose_name_plural = "Населенные пункты контрагента"
        unique_together = ('city', 'person')
        ordering = ('priority',)

    def __str__(self):
        return f'Населенный пункт {self.city}, контрагента - {self.person}'
