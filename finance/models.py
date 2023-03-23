from datetime import datetime

from django.db import models
# Create your models here.
from djmoney.models.fields import MoneyField
# from catalog.models import Product
from djmoney.money import Money

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




# class ProductPrice(models.Model):
#     price_changelist = models.ForeignKey(PriceChangelist, on_delete=models.CASCADE, verbose_name='Установка цен')
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
#     price = MoneyField(max_digits=14, decimal_places=2, default_currency='UAH', default=0)
#     position = models.PositiveIntegerField("Положение", null=True)
#
#     def __str__(self):
#         return self.product.name
#
#     class Meta:
#         verbose_name = "Строка установки цен номенклатуры"
#         verbose_name_plural = "Строки установки цен номенклатуры"
#         ordering = ['position']
