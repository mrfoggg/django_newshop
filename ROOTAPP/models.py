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
        verbose_name = 'Контактное лицо'
        verbose_name_plural = 'Контактные лица'

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


class Settlement(models.Model):
    description_ru = models.CharField('Название', max_length=128, default=None, db_index=True)
    description_ua = models.CharField('Название укр.', max_length=128, default=None, db_index=True)
    ref = models.CharField('Ref', max_length=128, primary_key=True)
    type = models.ForeignKey(SettlementType, max_length=128, default=None, on_delete=models.CASCADE,
                             db_index=True, verbose_name='Тип населенного пункта')
    area = models.ForeignKey(SettlementArea, max_length=128, default=None, on_delete=models.CASCADE,
                             db_index=True, verbose_name="Область")
    region = models.ForeignKey(SettlementRegion, max_length=128, default=None, on_delete=models.CASCADE,
                               verbose_name="Район")
    warehouse = models.BooleanField('Наличие отделений', default=False)
    index_1 = models.CharField('Индекс', max_length=128, null=True, default=None)
    index_2 = models.CharField('Индекс-2', max_length=128, null=True, default=None)
    index_coatsu_1 = models.CharField('Индекс КОАТУУ', null=True, max_length=128, default=None)

    class Meta:
        verbose_name = 'Населенный пункт'
        verbose_name_plural = 'Населенные пункты'
        ordering = ('description_ru',)

    def __str__(self):
        region = f'{self.region.description_ua}, ' if self.region_id else ''
        print(f'{self.region_id=}')
        return f'{self.type.description_ua} {self.description_ua} ({region}{self.area.description_ua})'


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
