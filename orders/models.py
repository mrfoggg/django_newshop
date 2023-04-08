# import ipinfo
# import requests
from django.contrib import admin
# from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.html import format_html_join
from djmoney.models.fields import MoneyField

from catalog.models import Product
from ROOTAPP.models import Person, Phone, PersonAddress
from site_settings.models import APIkeyIpInfo

CLIENT_ORDER_STATUSES = (
    (1, "Ожидает обработки"),
    (2, "В обработке"),
    (3, "На удержании"),
    (5, "Отменен"),
    (6, "Недозвон"),
    (7, "Отменено пользователем"),
    (7, "Ожидает отправки"),
)

SOURCE = (
    (1, "Заказ на сайте"),
    (2, "Заказ в один клик"),
    (3, "По телефону"),
    (4, "ОЛХ"),
)

BY_ONECLICK_STATUSES = (
    (1, "Ожидает обработки"),
    (2, "В обработке"),
    (3, "На удержании"),
    (4, "Сформирован заказ"),
    (5, "Отменен"),
    (6, "Недозвон"),
    (7, "Отменено пользователем"),
)

BY_ONECLICK_EXTEND_STATUSES = (
    (2, "Уточнить информацию перед звонком"),
    (3, "Клиент ожидает дополнительную информацию"),
    (4, "Товар не подходит"),
    (5, "Товар отсутсвует (алтернативных нет)"),
    (6, "Товар отсутствует (думает насчет предложенных альтернативных)"),
    (7, "Предложены другие варианты (на рассмотрении)"),
    (8, "Предложены другие варианты (не подхолит, отмена заказа)"),
)

BY_ONECLICK_STATUSES_CLIENT_DISPLAY = {
    1: 'очікую обробки',
    2: 'в обробці',
    3: 'заявка на утриманні',
    4: 'за заявкою створено замовлення',
    5: 'заявку відмінено',
    6: 'не можемо вам дозвонитися',
    7: 'відмінено користувачем',
}


class ClientOrder(models.Model):
    is_active = models.BooleanField(default=True, verbose_name='Проведен')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    status = models.SmallIntegerField('Статус', choices=CLIENT_ORDER_STATUSES, default=1, db_index=True)
    extend_status = models.SmallIntegerField(
        'Подробный статус', choices=BY_ONECLICK_EXTEND_STATUSES, default=1, db_index=True)
    source = models.SmallIntegerField(
        'Подробный статус', choices=SOURCE, default=1, db_index=True)
    person = models.ForeignKey(
        Person, verbose_name="Покупатель", default=None, blank=True, null=True, on_delete=models.SET_NULL)
    address = models.ForeignKey(
        PersonAddress, verbose_name="Адрес доставки", default=None, blank=True, null=True, on_delete=models.SET_NULL)
    session_key = models.CharField('Ключ сессии', max_length=32, blank=True, null=True)
    user_ip_info = models.TextField('Информация по IP посетителя', blank=True, null=True, default=None)

    class Meta:
        ordering = ('created',)
        verbose_name = "Заказ покупателя"
        verbose_name_plural = "Заказы покупателя"

    def __str__(self):
        return f'{self.created} - {self.person}'


class ByOneclick(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.SET_NULL, null=True)
    price = MoneyField('Цена на момент создания заявки', max_digits=14, decimal_places=2, default_currency='UAH',
                       default=0)
    phone = models.ForeignKey(Phone, verbose_name='Телефон', on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    status = models.SmallIntegerField('Статус', choices=BY_ONECLICK_STATUSES, default=1, db_index=True)
    extend_status = models.SmallIntegerField(
        'Подробный статус', choices=BY_ONECLICK_EXTEND_STATUSES, default=1, db_index=True)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    person = models.ForeignKey(
        Person, verbose_name="Пользователь", default=None, blank=True, null=True, on_delete=models.SET_NULL)
    session_key = models.CharField('Ключ сессии', max_length=32, blank=True, null=True)
    user_ip_info = models.TextField('Информация по IP посетителя', blank=True, null=True, default=None)

    class Meta:
        # ordering = ('created',)
        verbose_name = "Заказ Oneclick"
        verbose_name_plural = "Заказы Oneclick"

    def __str__(self):
        return f'№{self.id}: {self.phone} - {self.product} // {self.get_status_display()}'

    @property
    @admin.display(
        ordering='last_name',
        description='Пользователи с этим номером',
    )
    def this_number_contacts(self):
        if self.phone.personphone_set.count():
            return format_html_join(
                ', ', "<a href={}>{}</a>",
                (
                    (reverse('admin:ROOTAPP_person_change', args=[p.person_id]), p.person)
                    for p in self.phone.personphone_set.all()
                )
            )
        else:
            return 'отстутствуют'

    @property
    @admin.display(
        description="Другие заявки с этим ключем сессии"
    )
    def this_session_oneclicks(self):
        # return ByOneclick.objects.filter(session_key=self.session_key).exclude(id=self.id)
        return format_html_join(
            '', "<a href={}>{}</a> </br>",
            (
                (reverse('admin:orders_byoneclick_change', args=[o.id]), o)
                for o in ByOneclick.objects.filter(session_key=self.session_key).exclude(id=self.id)
            )
        ) if ByOneclick.objects.filter(session_key=self.session_key).exclude(id=self.id).exists() else "отстутствуют"

    @property
    def client_display_status(self):
        return BY_ONECLICK_STATUSES_CLIENT_DISPLAY[self.status]


TYPES_USER_SECTION_COMMENTS = (
    (1, "Зміна статусу"),
    (2, "Ваш коментар"),
)


class OneClickUserSectionComment(models.Model):
    order = models.ForeignKey(
        ByOneclick, verbose_name='Заказ', on_delete=models.CASCADE, null=True, related_name='user_comments')
    comment_type = models.SmallIntegerField('Тип коментария', choices=TYPES_USER_SECTION_COMMENTS, default=1)
    description = models.CharField('Текст коментария', max_length=128, default=None)
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')

    class Meta:
        ordering = ('created',)
        verbose_name = "Комментарий к заказу отображаемый пользователю"
        verbose_name_plural = "Комментарии к заказу отображаемые пользователю"

    def __str__(self):
        return self.description


class ByOneclickPersonalComment(models.Model):
    order = models.ForeignKey(ByOneclick, verbose_name='Заказ', on_delete=models.CASCADE, null=True)
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    description = models.TextField('Комментарий', blank=True, null=True, default=None)

    class Meta:
        ordering = ('created',)
        verbose_name = "Комментарий к заказу"
        verbose_name_plural = "Комментарии к заказу"

    def __str__(self):
        return str(self.created)


class Basket(models.Model):
    customer = models.ForeignKey(Person, verbose_name="Пользователь", on_delete=models.SET_NULL, null=True)
    # customer = models.ForeignKey(get_user_model(), verbose_name="Пользователь", on_delete=models.SET_NULL, null=True)

# В заказе должно быть поле тип заказа: на сайте, ванклик или по телефону
