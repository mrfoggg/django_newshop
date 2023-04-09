from django.contrib import admin
from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.utils.html import format_html
from phonenumber_field.modelfields import PhoneNumberField
from phonenumbers import carrier, geocoder
from phonenumbers.phonenumberutil import region_code_for_number

from nova_poshta.models import Settlement, SettlementArea, Warehouse, City, Street

TYPES_OF_PHONE = (
    (1, "Viber"),
    (2, "Telegram"),
    (3, "WhatsUp"),
)


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
    main_phone = models.OneToOneField(Phone, null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name='Телефон для авторизации', related_name='login_person')
    delivery_phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.SET_NULL,
                                       verbose_name='Телефон для доставки', related_name='delivery_persons')

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        full_name = f'{self.last_name} {self.first_name} {self.middle_name if self.middle_name else ""}'
        return f'id_{self.id}: {full_name} {self.main_phone if self.main_phone else ""}'


class Supplier(Person):
    class Meta:
        proxy = True

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class PersonPhone(models.Model):
    person = models.ForeignKey(Person, null=True, blank=True, on_delete=models.CASCADE, related_name='phones')
    phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.CASCADE)
    is_nova_poshta = models.BooleanField('Привязан к новой почте', default=False)

    class Meta:
        verbose_name = 'Телефон контрагента'
        verbose_name_plural = 'Телефоны контрагента'
        unique_together = ('person', 'phone')

    def __str__(self):
        return f'Телефон контрагента {self.person} - {self.phone}'


# class Street(models.Model):
#     ref = models.CharField('Ref улицы', max_length=36, primary_key=True)


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
    ADDRESS_TYPE = (
        (1, "На отделение или почтомат"),
        # (2, "На почтомат"),
        (2, "На адрес"),
    )
    address_type = models.SmallIntegerField('Тип доставки', choices=ADDRESS_TYPE, default=None, null=True, blank=True)
    area = models.ForeignKey(SettlementArea, on_delete=models.CASCADE, verbose_name="Область")
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, null=True, verbose_name="Населенный пункт")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Отделение")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name="Контрагент")
    city = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True,
                             verbose_name="Город Новой почты откуда производится адресная доставка")
    street = models.ForeignKey(Street, on_delete=models.CASCADE, blank=True, null=True,
                               verbose_name="Улица или село адресной доставки")
    comment = models.CharField('Коментарий к адресу', max_length=128, default=None, null=True, blank=True)
    build = models.CharField('Номер дома', max_length=8, default=None, null=True, blank=True)

    class Meta:
        verbose_name = "Адрес доставки контрагента"
        verbose_name_plural = "Адреса доставки контрагента"
        unique_together = ('settlement', 'person', 'area', 'warehouse')
        ordering = ('area',)

    def __str__(self):
        if self.settlement:
            address_type = self.get_address_type_display() + ' / ' if self.address_type else "нет доступных вариантов доставки"
            settlement = f'{self.settlement} / {address_type}'
            if self.address_type == 1:
                return settlement + (self.warehouse.__str__() if self.warehouse else 'отделение или почтомат не указаны')
            elif self.address_type == 2:
                street = f'{self.street.__str__()}'
                build = f', дом №{self.build}' if self.build else ''
                return settlement + (street + build if self.street else 'улица не указана')
            else:
                return settlement
        else:
            return f'{self.area} обл.'
