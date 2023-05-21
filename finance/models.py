from django.db import models
from ROOTAPP.models import Person, Document, Supplier, PriceTypePersonSupplier, PriceTypePersonBuyer


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
        return self.applied.strftime("%m/%d/%Y, (%H:%M)") if self.applied else self.created.strftime("%m/%d/%Y, (%H:%M)")


class SupplierPriceChangelist(Document):
    person = models.ForeignKey(
        Supplier, verbose_name="Поставщик", default=None, blank=True, null=True, on_delete=models.SET_NULL, )
    price_type = models.ForeignKey(PriceTypePersonSupplier, null=True, on_delete=models.SET_NULL,
                                   verbose_name='Тип цен')

    def __str__(self):
        return f'Установка цен №{self.id} {self.applied.strftime("%m/%d/%Y, (%H:%M)") if self.applied else self.created.strftime("%m/%d/%Y, (%H:%M)")} ' \
               f'/ {self.person.full_name}  ("{self.price_type.name}")'

    class Meta:
        verbose_name = "Установка цен номенклатуры поставщика"
        verbose_name_plural = "Установки цен номенклатуры поставщиков"
        ordering = ['created']


class GroupPriceChangelist(Document):
    person = models.ForeignKey(
        Person, verbose_name="Оптовый покупатель", default=None, blank=True, null=True, on_delete=models.SET_NULL,
        limit_choices_to={"is_group_buyer": True},
    )
    price_type = models.ForeignKey(PriceTypePersonBuyer, null=True, on_delete=models.SET_NULL,
                                   verbose_name='Тип цен')

    def __str__(self):
        return f'Установка цен №{self.id} {self.applied.strftime("%m/%d/%Y, (%H:%M)") if self.applied else self.created.strftime("%m/%d/%Y, (%H:%M)")} ' \
               f'/ {self.person.full_name}  ("{self.price_type.name}")'

    class Meta:
        verbose_name = "Установка индивидуальных оптовых цен номенклатуры"
        verbose_name_plural = "Установки индивидуальных оптовых цен номенклатуры"
        ordering = ['created']
