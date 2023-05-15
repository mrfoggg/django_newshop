import uuid

from django.contrib import admin
from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from phonenumber_field.modelfields import PhoneNumberField
from phonenumbers import carrier, geocoder
from phonenumbers.phonenumberutil import region_code_for_number

from ROOTAPP.services.functions import get_full_name
from nova_poshta.models import Settlement, SettlementArea, Warehouse, City, Street

TYPES_OF_PHONE = (
    (1, "Viber"),
    (2, "Telegram"),
    (3, "WhatsUp"),
)

PERSON_SOURCE = (
    (1, "Регистрация на сайте"),
    (2, "Создан персоналом"),
    (3, "Клиент оптовика"),
    (4, "Имортированый контрагент"),
)


def get_chat_links_func(self, only_exist=True):
    def getlink(messenger):
        # ('' if only_exist else '</br>')
        return {
            1: '<a href = "viber://chat?number=%(number)s" > %(messenger)s</a> ',
            2: '<a href="tg://resolve?domain=%(telegram_username)s" target="_blank">%(messenger)s</a>'
            if self.telegram_username else '<a href="https://t.me/+%(number)s" target="_blank">%(messenger)s</a>',
            3: '<a href="https://wa.me/%(number)s" >%(messenger)s</a>'
        }[messenger.type] % {
            'number': str(self.number)[1:],
            'full_number': self.number,
            'messenger': messenger.__str__(),
            'telegram_username': self.telegram_username
        }

    return format_html(
        # ('' if only_exist else 'СВЯЗАТЬСЯ: ') +
        ', '.join([getlink(m) for m in (self.messengers.all() if only_exist else Messenger.objects.all())]) +
        ('' if only_exist else f' - <a href="tel:{self.number}">позвонить</a>')
    )


def other_person(phone_id, person_id):
    if phone_id:
        # return Person.objects.filter(phones__phone_id=phone_id).exclude(phones__person_id=person_id)
        return Person.objects.filter(phones__phone_id=phone_id).exclude(id=person_id)
    else:
        return Person.objects.none()


def other_person_login_this_phone(phone_id, person_id):
    if phone_id:
        other_person_login_this_phone_qs = Person.objects.filter(
            main_phone_id=phone_id).exclude(phones__person_id=person_id)
        if other_person_login_this_phone_qs.exists():
            op = other_person_login_this_phone_qs.first()
            op_link = mark_safe(f'<a href={op.admin_url} target="_blank">'
                                f'{op.date_joined.strftime("%d-%m-%Y")} {op.full_name}</a>')
            return op_link
        else:
            return 'Отсутствуют'
    else:
        return 'Отсутствуют'


def other_person_not_main(phone_id, other_person_qs):
    other_person_not_main_qs = other_person_qs.exclude(main_phone_id=phone_id)
    if other_person_not_main_qs.exists():
        return format_html_join("", "<li><a href={} target='_blank'>{}</a></li>", ((op.admin_url, op.__str__())
                                                                                   for op in
                                                                                   other_person_not_main_qs))
    else:
        return 'Отсутствуют'


def other_contacts(phone_id, person_id):
    other_contacts_qs = ContactPerson.objects.filter(phone_id=phone_id).exclude(person_id=person_id)
    if other_contacts_qs.exists():
        return format_html_join("", "<li><a href={} target='_blank'>{}</a></li>", ((oc.admin_url, oc.__str__())
                                                                                   for oc in other_contacts_qs))
    else:
        return 'Отсутствуют'


class PhoneInfoFieldsMixin:
    def __int__(self, phone_id, person_id, *args, **kwargs):
        super().__init__(phone_id, person_id, *args, **kwargs)
        self.phone_id = phone_id
        self.person_id = person_id

    @property
    def other_person(self):
        return other_person(self.phone_id, self.person_id)

    @property
    @admin.display(description='Контрагент использующий этот номер для входа')
    def other_person_login_this_phone(self):
        return other_person_login_this_phone(self.phone_id, self.person_id)

    @property
    @admin.display(description='Другие контрагенты указавшие этот номер')
    def other_person_not_main(self):
        return other_person_not_main(self.phone_id, self.other_person)

    @property
    @admin.display(description='Контактные лица других контргентов у которых указан этот же номер')
    def other_contacts(self):
        return other_contacts(self.phone_id, self.person_id)


class Document(models.Model):
    is_active = models.BooleanField(default=False, verbose_name='Проведен')
    mark_to_delete = models.BooleanField(default=False, verbose_name='Помечен на удаление')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    comment = models.TextField('Комментарий', blank=True, null=True, default=None)

    class Meta:
        abstract = True


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


def get_phone_str(number):
    region_code = region_code_for_number(number)
    phone_str = str(number)
    formatted_phone = f"{phone_str[0:3]} ({phone_str[3:6]}) {phone_str[6:9]} {phone_str[9:11]} {phone_str[11:]}"
    phone = formatted_phone if region_code == 'UA' else phone_str
    return phone


class Phone(models.Model):
    number = PhoneNumberField(blank=True, help_text='Номер телефона', unique=True)
    messengers = models.ManyToManyField(
        Messenger, blank=True, default=None, verbose_name='Подключенные мессенжеры')
    telegram_username = models.CharField(max_length=128, blank=True, null=True, unique=True,
                                         verbose_name='Имя пользователя в телеграмм')

    def __str__(self):
        return get_phone_full_str(self.number)

    @property
    def phone_shot_str(self):
        return get_phone_full_str(self.number)

    @property
    @admin.display(description="Ссылки на cуществующие мессенжеры")
    def get_chat_links(self):
        return get_chat_links_func(self)

    @property
    @admin.display(description="Все ссылки на мессенжеры")
    def get_all_chat_links(self):
        return get_chat_links_func(self, False)

    @property
    def admin_link(self):
        return format_html(
            f'<a href="{reverse("admin:ROOTAPP_phone_change", args=[self.id])}" target="_blank"'
            f'style="font-weight:600">{self.phone_shot_str}</a>'
        )

    class Meta:
        verbose_name = "Номер телефона"
        verbose_name_plural = "Номера телефонов"


class Person(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    middle_name = models.CharField('Отчество', max_length=128, blank=True, null=True, default=None, db_index=True)
    full_name = models.CharField('Полное имя', max_length=256, blank=True, null=True, default=None, db_index=True)
    is_buyer = models.BooleanField('Является покупателем', default=False)
    is_supplier = models.BooleanField('Является поставщиком', default=False)
    is_dropper = models.BooleanField('Является дропшипером', default=False)
    is_group_buyer = models.BooleanField('Является оптовым покупателем', default=False)
    main_phone = models.OneToOneField(Phone, null=True, blank=True, on_delete=models.SET_NULL,
                                      verbose_name='Телефон для авторизации', related_name='login_person')
    delivery_phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.SET_NULL,
                                       verbose_name='Телефон для доставки', related_name='delivery_persons')
    comment = models.TextField('Коментарий', max_length=256, blank=True, null=True, default=None)
    main_price_type = models.ForeignKey(
        'PriceTypePersonBuyer', null=True, blank=True, default=None, on_delete=models.SET_NULL,
        verbose_name='Основной тип цен оптовых продаж контрагенту', related_name='group_buyer'
    )
    main_supplier_price_type = models.ForeignKey(
        'PriceTypePersonSupplier', null=True, blank=True, default=None, on_delete=models.SET_NULL,
        verbose_name='Основной тип цен закупки у контрагента', related_name='supplier'
    )
    source_type = models.SmallIntegerField('Источник контрагента', choices=PERSON_SOURCE, default=1, db_index=True)
    source_person = models.ForeignKey('Person', blank=True, null=True, on_delete=models.SET_NULL, default=None,
                                      verbose_name='Создатель контрагента')

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        main_phone = self.main_phone.phone_shot_str if self.main_phone and not self.is_supplier and not self.is_dropper else ""
        return f'{self.date_joined.strftime("%d-%m-%Y")}: ' \
               f'{self.full_name if self.full_name else self.email} {main_phone}' \
               f'{"(поставщик)" if self.is_supplier else ""}{"(дропер)" if self.is_dropper and not self.is_supplier and not self.is_group_buyer else ""}' \
               f'{"(оптовый покупатель)" if self.is_group_buyer else ""}'

    def save(self, *args, **kwargs):
        self.full_name = get_full_name(self)
        if not self.username:
            self.username = uuid.uuid4()
        super().save(*args, **kwargs)

    @property
    def admin_url(self):
        return reverse('admin:ROOTAPP_person_change', args=[self.id])


class ContactPerson(models.Model, PhoneInfoFieldsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField('Имя', max_length=128, blank=True, null=True, default=None, db_index=True)
    last_name = models.CharField('Фамилия', max_length=128, blank=True, null=True, default=None, db_index=True)
    middle_name = models.CharField('Отчество', max_length=128, blank=True, null=True, default=None, db_index=True)
    full_name = models.CharField('Полное имя', max_length=256, blank=True, null=True, default=None, db_index=True)
    phone = models.ForeignKey(Phone, null=True, on_delete=models.SET_NULL, verbose_name='Телефон контактного лица')
    person = models.ForeignKey(Person, null=True, on_delete=models.CASCADE, related_name='contacts',
                               verbose_name='Контрагент')

    def __str__(self):
        return f'{self.full_name} ({self.phone})'

    def save(self, *args, **kwargs):
        self.full_name = get_full_name(self)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Контактное лицо контрагента'
        verbose_name_plural = 'Контактные лица контрагентов'

    @property
    def admin_url(self):
        return reverse('admin:ROOTAPP_contactperson_change', args=[self.id])


# class ContactPersonShotStr(ContactPerson):
#     class Meta:
#         proxy = True
#
#     def __str__(self):
#         return f'{self.full_name} ({self.phone})'


class SupplierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_supplier=True)


class Supplier(Person):
    objects = SupplierManager()

    class Meta:
        proxy = True

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class PersonPhone(models.Model, PhoneInfoFieldsMixin):
    person = models.ForeignKey(Person, null=True, blank=True, on_delete=models.CASCADE, related_name='phones')
    phone = models.ForeignKey(Phone, null=True, blank=True, on_delete=models.CASCADE)
    is_nova_poshta = models.BooleanField('Привязан к новой почте', default=False)

    class Meta:
        verbose_name = 'Телефон контрагента'
        verbose_name_plural = 'Телефоны контрагента'
        unique_together = ('person', 'phone')

    def __int__(self):
        super().__init__(self.phone_id, self.person_id)

    def __str__(self):
        return self.phone.__str__()

#
# class PersonPhoneShotStr(PersonPhone):
#     class Meta:
#         proxy = True
#
#     def __str__(self):
#         return self.phone.__str__()


class PersonAddress(models.Model):
    ADDRESS_TYPE = (
        (1, "На отделение или почтомат"),
        # (2, "На почтомат"),
        (2, "На адрес"),
    )
    address_type = models.SmallIntegerField('Тип доставки', choices=ADDRESS_TYPE, default=None, null=True, blank=True)
    area = models.ForeignKey(SettlementArea, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Область")
    settlement = models.ForeignKey(Settlement, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Населенный пункт")
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
                return settlement + (
                    self.warehouse.__str__() if self.warehouse else 'отделение или почтомат не указаны')
            elif self.address_type == 2:
                street = f'{self.street.__str__()}'
                build = f', дом №{self.build}' if self.build else ''
                return settlement + (street + build if self.street else 'улица не указана')
            else:
                return settlement
        else:
            return f'{self.area} обл.'


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
