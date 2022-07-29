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
