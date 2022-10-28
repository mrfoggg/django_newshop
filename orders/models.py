from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html_join
from djmoney.models.fields import MoneyField

from ROOTAPP.models import Phone, Person
from catalog.models import Product

STATUSES = (
    (1, "Ожидает обработки"),
    (2, "В обработке"),
    (3, "На удержании"),
    (4, "Сформирован заказ"),
    (5, "Отменен"),
)

EXTEND_STATUSES = (
    (2, "Уточнить информацию перед звонком"),
    (3, "Клиент ожидает дополнительную информацию"),
    (4, "Товар не подходит"),
    (5, "Товар отсутсвует (алтернативных нет)"),
    (6, "Товар отсутствует (думает насчет предложенных альтернативных)"),
    (7, "Предложены другие варианты (на рассмотрении)"),
    (8, "Предложены другие варианты (не подхолит, отмена заказа)"),
)


class ByOneclick(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.SET_NULL, null=True)
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='UAH', default=0)
    phone = models.ForeignKey(Phone, verbose_name='Телефон', on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    status = models.SmallIntegerField('Статус', choices=STATUSES, default=1, db_index=True)
    extend_status = models.SmallIntegerField('Подробный статус', choices=EXTEND_STATUSES, default=1, db_index=True)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    contact = models.ForeignKey(
        Person, verbose_name="Контактное лицо", default=None, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        # ordering = ('created',)
        verbose_name = "Заказ Oneclick"
        verbose_name_plural = "Заказы Oneclick"

    def __str__(self):
        return f' {self.phone}:  {self.product}'

    @property
    @admin.display(
        ordering='last_name',
        description='Контакты с этим номером',
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


class ByOneclickComment(models.Model):
    order = models.ForeignKey(ByOneclick, verbose_name='Заказ', on_delete=models.CASCADE, null=True)
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    description = models.TextField('Комментарий', blank=True, null=True, default=None)

    class Meta:
        ordering = ('created',)
        verbose_name = "Комментарий к заказу"
        verbose_name_plural = "Комментарии к заказу"

    def __str__(self):
        return self.created
