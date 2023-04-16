from django.db import models
from ROOTAPP.models import Person, Document, Supplier


class Stock(models.Model):
    name = models.CharField('Название склада', max_length=128, db_index=True)
    person = models.ManyToManyField(
        Person, verbose_name="Ответсвенные по складу", default=None, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Склад хранения"
        verbose_name_plural = "Склады хранения"


class PriceChangelist(Document):

    def __str__(self):
        return f'Установка розничных цен номенклатуры №{self.id} от {self.date}'

    class Meta:
        verbose_name = "Установка цен номенклатуры розницы"
        verbose_name_plural = "Установки цен номенклатур розницы"
        ordering = ['created']

    @property
    def date(self):
        return self.created.strftime("%m/%d/%Y, (%H:%M)")


class PersonPriceType(models.Model):
    name = models.CharField('Название типа цен', max_length=128, blank=True, default='', db_index=True)
    description = models.TextField('Описание типа цен', max_length=256, blank=True, null=True, default=None)
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


class SupplierPriceChangelist(Document):
    person = models.ForeignKey(
        Supplier, verbose_name="Поставщик", default=None, blank=True, null=True, on_delete=models.SET_NULL,)
    price_type = models.ForeignKey(PriceTypePersonSupplier, null=True, on_delete=models.SET_NULL, verbose_name='Тип цен')

    def __str__(self):
        return f'Установка цен №{self.id} {self.created.strftime("%d.%m.%Y")} ' \
               f'/ {self.person.full_name}  ("{self.price_type.name}")'

    class Meta:
        verbose_name = "Установка цен номенклатуры поставщика"
        verbose_name_plural = "Установки цен номенклатуры поставщиков"
        ordering = ['created']

