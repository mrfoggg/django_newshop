# import ipinfo
# import requests
from datetime import datetime
from decimal import Decimal
from unicodedata import decimal

from django.contrib import admin, messages
# from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Sum, F
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html_join
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from polymorphic.models import PolymorphicModel

from catalog.models import Product, ProductSupplierPriceInfo, ProductGroupPrice
from ROOTAPP.models import Person, Phone, PersonAddress, Supplier, Document, PriceTypePersonBuyer, ContactPerson, \
    PersonPhone
from finance.models import PriceTypePersonSupplier, GroupPriceChangelist, Stock
from finance.services import get_margin, get_margin_percent, get_profitability
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

SUPPLIER_ORDER_STATUSES = (
    (1, "Предзаказы"),
    (2, "Не подан поставщику"),
    (3, "Запрошен счет"),
    (4, "Ожидает оплаты"),
    (5, "Ожидает отправки"),
)

REALISATION_STATUSES = (
    (1, "Оформить доставку"),
    (2, "Передано на упаковку"),
    (3, "Упаковано, ожидает отправки"),
    (4, "В пути на перевозчика"),
    (5, "Отправлено")
)

PAYMENT_TYPE = (
    (1, "Наложенный платеж"),
    (2, "Наложенный платеж на карту"),
    (3, "Оплата по счету"),
    (4, "Оплата на карту"),
    (5, "Оплата по закрытию текущего договора"),
)


class ClientOrder(Document):
    status = models.SmallIntegerField('Статус', choices=CLIENT_ORDER_STATUSES, default=1, db_index=True)
    person = models.ForeignKey(
        Person, verbose_name="Покупатель", default=None, blank=True, null=True, on_delete=models.SET_NULL)
    extend_status = models.SmallIntegerField(
        'Подробный статус', choices=BY_ONECLICK_EXTEND_STATUSES, default=1, db_index=True)
    source = models.SmallIntegerField(
        'Источник заказ', choices=SOURCE, default=1, db_index=True)
    payment_type = models.SmallIntegerField('Способ оплаты', choices=PAYMENT_TYPE, default=1)
    address = models.ForeignKey(
        PersonAddress, verbose_name="Адрес доставки", default=None, blank=True, null=True, on_delete=models.SET_NULL)
    session_key = models.CharField('Ключ сессии', max_length=32, blank=True, null=True)
    user_ip_info = models.TextField('Информация по IP посетителя', blank=True, null=True, default=None)
    group_price_type = models.ForeignKey(PriceTypePersonBuyer, verbose_name='Тип оптовых цен',
                                         default=None, blank=True, null=True, on_delete=models.SET_NULL)
    dropper = models.ForeignKey(
        Person, limit_choices_to={"is_dropper": True}, blank=True, null=True, default=None,
        verbose_name='Дропер', on_delete=models.SET_NULL, related_name='drop_orders',
        help_text='Задать дропера нельзя для если контрагент покупатель оптовик'
    )
    contact_person = models.ForeignKey(
        ContactPerson, blank=True, null=True, default=None, verbose_name='Получатель груза',
        on_delete=models.SET_NULL
    )
    incoming_phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.CASCADE,
                                       verbose_name='Входящий номер')
    delivery_phone = models.ForeignKey(
        PersonPhone, null=True, blank=True, on_delete=models.CASCADE, verbose_name='Телефон доставки',
        help_text='Оставить пустым если надо использовать номер телефона указаного контактного лица'
    )

    class Meta:
        ordering = ('created',)
        verbose_name = "Заказ покупателя"
        verbose_name_plural = "Заказы покупателя"

    def __str__(self):
        return f'{self.created.strftime("%d-%m-%Y %H:%M")} / {self.person}'

    @property
    @admin.display(description='Всего товаров, шт')
    def total_quantity(self):
        if self.products.exists():
            return self.products.aggregate(Sum('quantity'))['quantity__sum']
        else:
            return 0

    @property
    @admin.display(description='Всего продано на сумму')
    def total_amount(self):
        if self.products.exists():
            return Money(self.products.aggregate(total_amount=Sum(F('sale_price') * F('quantity')))['total_amount'],
                         'UAH')
        else:
            return 0

    @property
    @admin.display(description='Всего товаров к закупке на сумму')
    def total_purchase_amount(self):
        products_to_purchase = self.products.filter(supplier_order__isnull=False)
        if products_to_purchase.exists():
            return Money(
                products_to_purchase.aggregate(total_purchase_amount=Sum(F('purchase_price') * F('quantity')))[
                    'total_purchase_amount'], 'UAH')
        else:
            return Money(0, 'UAH')

    @property
    @admin.display(description='Итоговая маржа по заказу')
    def total_margin(self):
        if self.products.exists():
            if self.dropper:
                return Money(
                    self.products.aggregate(total_margin=Sum((F('drop_price') - F('purchase_price')) * F('quantity')))[
                        'total_margin'], 'UAH')
            else:
                return Money(
                    self.products.aggregate(total_margin=Sum((F('sale_price') - F('purchase_price')) * F('quantity')))[
                        'total_margin'], 'UAH')
        return 0


class SupplierOrder(Document):
    person = models.ForeignKey(
        Supplier, verbose_name="Поставщик", default=None, blank=True, null=True, on_delete=models.SET_NULL)
    status = models.SmallIntegerField('Статус', choices=SUPPLIER_ORDER_STATUSES, default=1, db_index=True)
    price_type = models.ForeignKey(PriceTypePersonSupplier, null=True, on_delete=models.SET_NULL,
                                   verbose_name='Тип цен')
    stock = models.ForeignKey(Stock, null=True, on_delete=models.SET_NULL, blank=True,
                              verbose_name='Склад')

    class Meta:
        ordering = ('created',)
        verbose_name = "Заказ поставщику"
        verbose_name_plural = "Заказы поставщику"

    def __str__(self):
        comment = f'({self.comment})' if self.comment else ''
        return f'{self.created.strftime("%d-%m-%Y %H:%M")} / {self.person} {comment}'


class ProductInOrder(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар в заказе', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveSmallIntegerField('Кол-во', default=1)
    client_order = models.ForeignKey(ClientOrder, verbose_name='Заказ покупателя', on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name='products')
    client_order_position = models.PositiveSmallIntegerField("Позиция в заказе покупателя", blank=True, null=True,
                                                             db_index=True)
    supplier_order = models.ForeignKey(SupplierOrder, verbose_name='Заказ поставщику', on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='products')
    supplier_order_position = models.PositiveSmallIntegerField("Позиция в заказе постащику", blank=True, null=True,
                                                               db_index=True)
    sale_price = MoneyField('Цена продажи', max_digits=10, decimal_places=2, default_currency='UAH', default=0)
    drop_price = MoneyField('Цена дроп', max_digits=10, decimal_places=2, default_currency='UAH', default=0,
                            blank=True, null=True)
    supplier_price_variants = models.ForeignKey(ProductSupplierPriceInfo, blank=True, null=True,
                                                on_delete=models.SET_NULL,
                                                verbose_name='Цены поставщиков для расчета РЦ')
    purchase_price = MoneyField('Закупочная цена', max_digits=10, decimal_places=2, default_currency='UAH',
                                default=0)
    realization_quantity = models.PositiveSmallIntegerField('отгружено', default=0)
    arrive_quantity = models.PositiveSmallIntegerField('поступило', default=0)

    class Meta:
        verbose_name = 'Товар в заказах покупателю и поставщику'
        verbose_name_plural = 'Товары в заказах покупателю и поставщику'

    def __str__(self):
        return self.product.name

    @property
    @admin.display(description='Текущая РЦ')
    def full_current_price_info(self):
        return self.product.full_current_price_info

    @property
    @admin.display(description='Текущая цена опт')
    def current_group_price(self):
        group_price = self.client_order.group_price_type
        gp_qs = ProductGroupPrice.objects.filter(
            price_changelist__price_type_id=group_price.id,
            product=self.product
        ).order_by('price_changelist__updated')
        print('GPQS', gp_qs.exists())
        return gp_qs.last().price_full_info if (group_price and gp_qs.exists()) else '-'
        # return '333'

    @property
    @admin.display(description='Сумма продажи')
    def sale_total(self):
        return self.sale_price * self.quantity

    @property
    @admin.display(description='Сумма закупки')
    def purchase_total(self):
        return self.purchase_price * self.quantity

    @property
    @admin.display(description='Маржа за шт.')
    def margin(self):
        return get_margin(self.purchase_price, self.sale_price, self.drop_price)

    @property
    @admin.display(description='Маржа всего')
    def margin_total(self):
        return '-' if self.margin == '-' else self.margin * self.quantity

    @property
    @admin.display(description='Наценка, %')
    def margin_percent(self):
        return get_margin_percent(self.margin, self.purchase_price)

    @property
    @admin.display(description='Маржа, %')
    def profitability(self):
        return get_profitability(self.margin, self.sale_price)


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

# Arrival
class FinanceDocument(Document, PolymorphicModel):
    person = models.ForeignKey(Person, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Контрагент')
    amount = MoneyField(max_digits=14, decimal_places=2, default_currency='UAH', default=0,
                        verbose_name='Сумма документа')
    balance_after = MoneyField(max_digits=14, decimal_places=2, default_currency='UAH', default=0,
                               verbose_name='Баланс после')
    stock = models.ForeignKey(Stock, null=True, on_delete=models.SET_NULL, blank=True,
                              verbose_name='Склад')

    @property
    @admin.display(description='Баланс до')
    def balance_before(self):
        date_now = self.applied if self.applied else timezone.make_aware(datetime.now())
        before_documents = FinanceDocument.objects.filter(person=self.person, applied__lt=date_now, is_active=True)
        return before_documents.last().balance_after if before_documents.exists() else Money(0, 'UAH')

    class Meta:
        abstract = True

    class Meta:
        verbose_name = "Финансовый документ"
        verbose_name_plural = "Финансовые документы"
        ordering = ['applied']

def reapply_all_after(obj):
    documents_after = FinanceDocument.objects.filter(person=obj.person, applied__gt=obj.applied, is_active=True)
    print('DOCUMENTS_AFTER - ', documents_after)
    before = obj.balance_after
    docs_to_update = []
    for doc in documents_after:
        doc.balance_after = before + doc.amount
        docs_to_update.append(doc)
        before = doc.balance_after
    FinanceDocument.objects.bulk_update(docs_to_update, ['balance_after'])


def apply_documents(self, request, obj):
    print('APPLY')
    if "_activate" in request.POST or "_reactivate" in request.POST:
        print('_activate')
        msg = 'Проведен датой создания' if "_activate" in request.POST else 'Перепроведен'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = True
        if "_activate" in request.POST:
            obj.applied = timezone.make_aware(datetime.now())
        obj.save()
        if type(obj).__name__ in ('Arrival',):
            reapply_all_after(obj)
        return HttpResponseRedirect(request.path)

    if "_activate_now" in request.POST or "_reactivate_now" in request.POST:
        msg = 'Проведен текущей датой' if "_activate_now" in request.POST else 'Перепроведен текущей датой'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = True
        obj.applied = obj.updated
        obj.save()
        if type(obj).__name__ in ('Arrival',):
            reapply_all_after(obj)
        return HttpResponseRedirect(request.path)

    if "_deactivate" in request.POST:
        msg = 'Проведение документа отмененно'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = False
        obj.balance_after = Money(0, 'UAH')
        if type(obj).__name__ in ('Arrival',):
            reapply_all_after(obj)
        obj.save()
        return HttpResponseRedirect(request.path)

    if "_un_mark_to_delete" in request.POST:
        obj.mark_to_delete = False
        obj.save()
        return HttpResponseRedirect(request.path)

    if "_mark_to_delete" in request.POST:
        msg = f'Документ {obj} помечен на удаление'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = False
        obj.mark_to_delete = True
        obj.save()

    if 'apply_date' in request.POST:
        str_date = request.POST.get('apply_date')
        msg = f'Документ {obj} проведен датой {str_date}'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = True
        date = datetime.strptime(str_date, "%d/%m/%Y %H:%M")
        obj.applied = timezone.make_aware(date)
        obj.save()
        if type(obj).__name__ in ('Arrival',):
            reapply_all_after(obj)
        return HttpResponseRedirect(request.path)


class Realization(FinanceDocument):
    status = models.SmallIntegerField('Статус', choices=REALISATION_STATUSES, default=1, db_index=True)

    class Meta:
        ordering = ('created',)
        verbose_name = "Реализация"
        verbose_name_plural = "Реализация"

    def __str__(self):
        return f'{self.created.strftime("%d-%m-%Y %H:%M")}'


class Arrival(FinanceDocument):
    order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ('applied',)
        verbose_name = "Поступление товаров"
        verbose_name_plural = "Поступления товаров"

    def save(self, *args, **kwargs):
        # if self.id:
        #     if self.productmoveitem_set.exists():
        #         self.amount = self.productmoveitem_set.annotate(full_amount=F('quantity')*F('price')).aggregate(
        #             Sum('full_amount')
        #         )['full_amount__sum']
        #     else:
        #         self.amount = Money(0, 'UAH')

        self.balance_after = self.balance_before + self.amount if self.is_active else Money(0, 'UAH')
        super().save(*args, **kwargs)

    def delete_model(self, request, obj):
        reapply_all_after(obj)
        obj.delete()


class ProductMoveItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    document = models.ForeignKey(FinanceDocument, on_delete=models.CASCADE, null=True, blank=True)
    price = MoneyField('Цена продажи', max_digits=10, decimal_places=2, default_currency='UAH', default=0)
    quantity = models.SmallIntegerField('Количество', default=1)
    quantity_after = models.JSONField('Остаток', default=dict, blank=True, db_index=True)


    def __str__(self):
        return self.product.name if self.product else ''
        # return 'self.product.name if self.product else self.id'

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
