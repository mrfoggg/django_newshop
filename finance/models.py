from datetime import datetime

from django.db import models
# Create your models here.
from djmoney.models.fields import MoneyField
# from catalog.models import Product
from djmoney.money import Money

from ROOTAPP.models import Person


# from catalog.models import Product


class PriceChangelist(models.Model):
    confirmed_date = models.DateTimeField('Изменено', auto_now_add=False, auto_now=False)
    confirmed = models.BooleanField('Проведено', default=False)

    def __str__(self):
        return f'Установка цен номенлатуры №{self.id} от {self.date} - {"провдено" if self.confirmed else "не проведено"}'

    class Meta:
        verbose_name = "Установка цен номенклатуры"
        verbose_name_plural = "Установки цен номенклатур"
        ordering = ['confirmed_date']

    @property
    def date(self):
        return self.confirmed_date.strftime("%m/%d/%Y, (%H:%M)")


class PersonPriceType(models.Model):
    name = models.CharField('Название типа цен', max_length=128, blank=True, default='', db_index=True)
    description = models.TextField('Описание типа цен', blank=True, null=True, default=None)
    person = models.ForeignKey(
        Person, verbose_name="Контрагент", default=None, blank=True, null=True, on_delete=models.SET_NULL)
    position = models.PositiveSmallIntegerField("Позиция", blank=True, null=True)

    def __str__(self):
        return f'{self.position}. {self.name}'

    class Meta:
        abstract = True


class PriceTypePersonBuyer(PersonPriceType):
    class Meta:
        verbose_name = "Тип цен контрагента покупателя"
        verbose_name_plural = "Типы цен контрагента покупателя"


class PriceTypePersonSupplier(PersonPriceType):
    class Meta:
        verbose_name = "Тип цен контрагента поставщика"
        verbose_name_plural = "Типы цен контрагента поставщика"
