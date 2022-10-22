from decimal import Decimal
from django.contrib import admin
from django.db import models
from django.db.models import Subquery, Min, Max, OuterRef, SmallIntegerField, Case, When
from django.db.models.expressions import F
from django.urls import reverse
from django.utils.html import format_html_join, format_html
from djmoney.models.fields import MoneyField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from ROOTAPP.models import Person
from finance.models import PriceChangelist
from djmoney.money import Money
from site_settings.models import PhotoPlug


def get_price_sq(outerref_field):
    return Subquery(ProductPrice.objects.filter(
        product=OuterRef(outerref_field)).order_by('price_changelist__confirmed_date').values('price')[:1]), \
           Subquery(Discount.objects.filter(product=OuterRef(outerref_field)).values('amount')[:1]), \
           Subquery(Discount.objects.filter(product=OuterRef(outerref_field)).values('type_of_amount')[:1])


def annotate_query_with_price(input_query, outerref_field):
    pr, ds, ds_type = get_price_sq(outerref_field)
    return input_query.annotate(pr=pr).annotate(
        price=Case(
            When(pr__isnull=False, then=pr),
            default=Decimal('0.00')
        )
    ).annotate(annotated_discount=ds, discount_type=ds_type).annotate(
        total_price=Case(
            When(pr__isnull=True, then=F('price')),
            # When(pr__isnull=True, then=F(Money(0, 'UAH'))),
            When(annotated_discount=None, then=pr),
            When(discount_type=1, then=pr - pr * ds / 100),
            default=pr - ds
        )
    )


class PlacementWithPriceManager(models.Manager):
    def get_queryset(self):
        return annotate_query_with_price(super().get_queryset(), 'product_id').select_related(
            'product').prefetch_related('product__images')


class ProductWithPriceManager(models.Manager):
    def get_queryset(self):
        return annotate_query_with_price(super().get_queryset(), 'pk').prefetch_related('images')


class Country(models.Model):
    name = models.CharField('Название страны', max_length=128, default=None, unique=True, db_index=True)
    slug = models.SlugField(max_length=64, unique=True)

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField('Название бренда', max_length=128, default=None, unique=True, db_index=True)
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    country = models.ForeignKey(Country, blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Страна брэнда')

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"

    def __str__(self):
        return f'{self.name} ({self.country})'


class Filter(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='filters')
    attribute = models.ForeignKey('Attribute', on_delete=models.CASCADE, verbose_name='Атрибут фильтрации')
    position = models.PositiveSmallIntegerField("Позиция фильтра", blank=True, null=True)

    class Meta:
        unique_together = ('category', 'attribute')
        verbose_name = 'Фильтр категории'
        verbose_name_plural = 'Фильтры категории'
        ordering = ('position',)

    def __str__(self):
        return f'{self.attribute} (тип {self.attribute.get_type_of_value_display()})'


class Category(MPTTModel):
    name = models.CharField('Название', max_length=128, default=None, unique=True, db_index=True)
    parent = TreeForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL,
                            related_name='children', db_index=True, verbose_name='Родительская категория')
    display_in_parent = models.BooleanField('Отображать в родительской категории', default=True)
    display_parent_filters = models.BooleanField('Отображать фильтры родительской категории', default=True)
    display_child_filters = models.BooleanField('Отображать фильтры потомков', default=True)
    slug = models.SlugField(max_length=128, unique=True)
    description = models.TextField('Описание категории', blank=True, null=True, default=None)
    groups = models.ManyToManyField('Group', through='GroupPlacement', related_name='categories')

    class Meta:
        verbose_name = "Категория товаров"
        verbose_name_plural = "Категории товаров"

    def __str__(self):
        return self.name

    @property
    @admin.display(description="Содержит группы атрибутов")
    def groups_list(self):
        return format_html_join(
            ', ', "<a href={}>{}</a>",
            (
                (reverse('admin:catalog_group_change', args=[gr.id]), gr.name)
                for gr in self.groups.values_list('id', 'name', named=True)
            )
        )

    def get_absolute_url(self):
        # return f'/category/{self.slug}'
        return reverse('main_page:category_and_product', args=(self.slug,))

    @property
    def link(self):
        return format_html(f'<a href="{self.get_absolute_url()}">{self.name}</a>')

    @property
    def parents(self):
        parents = []
        current = self
        parent = self.parent
        while parent:
            if current.display_in_parent:
                parents.append([parent.get_absolute_url, parent])
            current = current.parent
            parent = parent.parent
        parents.reverse()
        return parents

    @property
    def children_to_display(self):
        return self.children.filter(display_in_parent=True)

    @property
    def bro_categories(self):
        return self.parent.children.exclude(id=self.id)

    @property
    def prices(self):
        print('GET PRICES')
        return ProductPrice.objects.filter(
            product__productplacement__category=self).aggregate(Min('price'), Max('price'))

    @property
    def listing(self):
        # sq_min_max_price = Subquery(ProductPrice.objects.filter(
        #     product__productplacement__category_id=OuterRef('pk')).aggregate(Min('price'), Max('price')).values(
        #     'price__min', 'price__max')

        # for p in self.productplacement_set(manager='with_price').values(
        #         'product__name', 'price', 'discount', 'discount_type', 'total_price'):
        #     print(p)

        return self.productplacement_set(manager='with_price').order_by(
            'product_position')
        # return self.productplacement_set.select_related('product').order_by('product_position')

    @property
    def full_filters_list(self):
        parent_filters = list(
            self.parent.filters.select_related('attribute').prefetch_related(
                'attribute__fixed_values')) if self.display_parent_filters and self.parent else []
        filters = list(self.filters.select_related('attribute').prefetch_related('attribute__fixed_values'))
        children_filters = []
        for child_cat in self.children.prefetch_related('filters__attribute__fixed_values'):
            children_filters.extend(child_cat.filters.all())
        return parent_filters + filters + (children_filters if self.display_child_filters else [])


class ProductPrice(models.Model):
    price_changelist = models.ForeignKey(PriceChangelist, on_delete=models.CASCADE, verbose_name='Установка цен')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name="Товар")
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='UAH', default=0)
    position = models.PositiveIntegerField("Положение", null=True)

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = "Строка установки цен номенклатуры"
        verbose_name_plural = "Строки установки цен номенклатуры"
        ordering = ['position']


class ProductSeries(models.Model):
    name = models.CharField('Название линейки товаров', max_length=128, default=None, unique=True, db_index=True)
    description = models.TextField('Описание линейки товаров', blank=True, null=True, default=None)
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)

    class Meta:
        verbose_name = "Линейка товара"
        verbose_name_plural = "Линейки товаров"

    def __str__(self):
        return self.name


def get_shot_attr_name(shot_attribute):
    return shot_attribute.name if shot_attribute.name else shot_attribute.attribute.name


class Product(models.Model):
    objects = models.Manager()
    with_price = ProductWithPriceManager()

    RATING = [(i, i) for i in range(0, 100, 5)]

    WARRANTY = (
        (1, "12 мес."),
        (2, "6 мес."),
        (3, "3 мес."),
        (4, "14 дней"),
    )
    name = models.CharField('Название', max_length=128, default=None, unique=True, db_index=True)
    is_active = models.BooleanField('Товар включен', default=True, )
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    sku = models.CharField(max_length=10, blank=True, null=True, default=None, unique=True, db_index=True,
                           verbose_name='Артикул товара')
    sku_manufacturer = models.CharField('Артикул товара в каталоге производителя', max_length=10, blank=True,
                                        null=True, default=None, unique=True)
    country_of_manufacture = models.ForeignKey(Country, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                                               verbose_name='Страна производства')
    brand = models.ForeignKey(Brand, blank=True, null=True, default=None, on_delete=models.CASCADE,
                              verbose_name='Бренд товара', db_index=True)
    series = models.ForeignKey(ProductSeries, blank=True, null=True, default=None, on_delete=models.CASCADE,
                               verbose_name='Товары из лиенйки', related_name='products', db_index=True)
    description = models.TextField('Описание товара', blank=True, null=True, default=None)
    characteristics = models.JSONField('Характеристики товара', default=dict, blank=True, db_index=True)
    service_info = models.TextField('Cлужебная информация', blank=True, null=True, default=None)
    rating = models.SmallIntegerField('Рейтинг товара', choices=RATING, default=1, db_index=True, )
    admin_category = TreeForeignKey(Category, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                                    verbose_name='Категория отображения в админ-панели', db_index=True)
    url = models.URLField('Ссылка на товар на сайте производителя', max_length=128, blank=True, null=True,
                          default=None, unique=True)
    length = models.FloatField('Длина, см', blank=True, null=True)
    width = models.FloatField('Ширина, см', blank=True, null=True)
    height = models.FloatField(blank=True, null=True, verbose_name='Высота, см')
    warranty = models.SmallIntegerField('Срок гарантии', choices=WARRANTY, default=1)
    weight = models.FloatField('Вес, кг', blank=True, null=True)
    package_length = models.FloatField('Длина упаковки, см', blank=True, null=True)
    package_width = models.FloatField('Ширина упаковки, см', blank=True, null=True)
    package_height = models.FloatField('Высота упаковки, см', blank=True, null=True)
    categories = models.ManyToManyField(Category, through='ProductPlacement', related_name='products')
    combination_of_categories = models.ForeignKey(
        'CombinationOfCategory', blank=True, null=True,
        verbose_name='Связанная комбинация категорий', on_delete=models.SET_NULL, db_index=True)
    seats_amount = SmallIntegerField("Количество мест", default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def save(self, *args, **kwargs):
        if Product.objects.filter(name=self.name).exists():
            pass
            # raise ValidationError("Копия этого товара уже существует")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('main_page:category_and_product', args=(self.slug,))

    @property
    @admin.display(description='Содержится в категориях')
    def category_placement(self):
        return tuple(self.categories.values_list('name', flat=True))

    @property
    @admin.display(description='Группы атрибутов')
    def get_sorted_groups(self):
        group_sorted_list = []
        if (cc := self.combination_of_categories) and cc.is_active_custom_order_group:
            for gr_pl in cc.group_position.all():
                group_sorted_list.append([gr_pl.group_placement.category.name, gr_pl.group_placement.group])
        else:
            # фиксил 6.07.2022
            if self.id is not None:
                for cat_placement in self.productplacement_set.order_by('category_position'):
                    for group_placement in cat_placement.category.groupplacement_set.order_by('position'):
                        group_sorted_list.append([cat_placement.category.name, group_placement.group])
        return group_sorted_list

    def get_attr_string_val(self, attr):
        if (slug := attr.slug) in (ch := self.characteristics):
            value = ch[slug]
            if attr.type_of_value == 3:
                return attr.str_true if value else attr.str_false
            if value:
                match attr.type_of_value:
                    case 1:
                        return value + attr.suffix
                    case 2:
                        return str(value) + attr.suffix
                    case 4:
                        return FixedTextValue.objects.get(slug=value).name
                    case 5:
                        return ', '.join([FixedTextValue.objects.get(slug=i).name for i in value])
            else:
                return attr.default_str_value if attr.default_str_value else None
        else:
            # return attr.default_str_value
            return '-'

    @property
    def shot_attributes(self):
        shot_attr_list = []
        if (cc := self.combination_of_categories) and cc.is_active_custom_order_mini_parameters:
            for shot_pl in cc.shot_attr_positions.all():
                if str_val := self.get_attr_string_val(shot_pl.shot_attribute.attribute):
                    shot_attr_list.append([get_shot_attr_name(shot_pl.shot_attribute), str_val])
        else:
            for cat_placement in self.productplacement_set.order_by('category_position'):
                shot_attr_list.extend([[get_shot_attr_name(i), str_val]
                                       for i in cat_placement.category.shot_attributes.prefetch_related('attribute')
                                       if (str_val := self.get_attr_string_val(i.attribute))])
        # print(shot_attr_list)
        return shot_attr_list

    @property
    def shot_attributes_id_list(self):
        shot_attr_list = []
        if (cc := self.combination_of_categories) and cc.is_active_custom_order_mini_parameters:
            for shot_pl in cc.shot_attr_positions.all():
                if str_val := self.get_attr_string_val(shot_pl.shot_attribute.attribute):
                    shot_attr_list.append([get_shot_attr_name(shot_pl.shot_attribute), str_val])
        else:
            for cat_placement in self.productplacement_set.order_by('category_position').select_related(
                    'category'):
                shot_attr_list.extend(
                    [(attr, self.characteristics[attr] if attr in self.characteristics.keys() else None)
                     for attr in cat_placement.category.shot_attributes.values_list('attribute__slug', flat=True)]
                )
        # print(shot_attr_list)
        return shot_attr_list

    @property
    def main_attributes(self):
        main_attr_list = []
        if (cc := self.combination_of_categories) and cc.is_active_custom_order_main_parameters:
            for main_pl in cc.main_attr_positions.all():
                if str_val := self.get_attr_string_val(main_pl.shot_attribute.attribute):
                    main_attr_list.append([main_pl.main_attribute, str_val])
        else:
            for cat_placement in self.productplacement_set.order_by('category_position'):
                main_attr_list.extend([[i.attribute, str_val] for i in cat_placement.category.main_attributes.all()
                                       if (str_val := self.get_attr_string_val(i.attribute))])
        return main_attr_list

    @property
    def full_characteristics(self):
        characteristics = []
        for group in self.get_sorted_groups:
            characteristics.append([group[1].name, [
                [a.name, str_val] for a in group[1].attributes.all()
                if (str_val := self.get_attr_string_val(a))
            ]])
        return characteristics

    # @property
    # def price(self):
    #     return self.productprice_set.order_by(
    #         'price_changelist__confirmed_date').last().price if self.productprice_set.exists() else Money(0, 'UAH')

    @property
    def first_image(self):
        return self.images.first().image if self.images.exists() else PhotoPlug.get_solo().image


class AddictProduct(models.Model):
    main_product = models.ForeignKey(Product, on_delete=models.CASCADE, default=None, related_name='addict_product')
    addict_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, default=None, verbose_name='Сопутствующий товар')
    position = models.PositiveSmallIntegerField("Позиция опутствующего товара", blank=True, null=True)

    class Meta:
        verbose_name = "Сопуствующий товар"
        verbose_name_plural = "Сопуствующие товары"
        unique_together = ('main_product', 'addict_product')


class CategoryAddictProduct(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, default=None, verbose_name='Категория сопутсвующих товаров')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, default=None,
                                related_name='addict_product_category')
    position = models.PositiveSmallIntegerField("Позиция категории сопутствующих товаров", blank=True, null=True)

    class Meta:
        verbose_name = "Категория сопутсвующих товаров"
        verbose_name_plural = "Категория сопутсвующих товаров"
        unique_together = ('category', 'product')


class ProductPlacement(models.Model):
    objects = models.Manager()
    with_price = PlacementWithPriceManager()

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар', db_index=True)
    category = TreeForeignKey(Category, on_delete=models.CASCADE, verbose_name='Размещение в категории', db_index=True)
    category_position = models.PositiveSmallIntegerField("Позиция категории", blank=True, null=True, db_index=True)
    product_position = models.PositiveSmallIntegerField("Позиция товара", blank=True, null=True, db_index=True)

    class Meta:
        verbose_name = "Размещение товаров в категориях"
        verbose_name_plural = "Размещения товаров в категориях"
        unique_together = ('product', 'category')

    def __str__(self):
        return f'{self.product} в категории {self.category}'


class ProductSupplier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    supplier = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name='Поставщик')
    priority = models.PositiveSmallIntegerField("Приоритет поставщика", blank=True, null=True)

    class Meta:
        verbose_name = "Поставщик товара"
        verbose_name_plural = "Поставщики товара"
        unique_together = ('product', 'supplier')
        ordering = ('priority',)

    def __str__(self):
        return f'Товар {self.product}, поставщик - {self.supplier}'


class Group(models.Model):
    name = models.CharField('Название группы атрибутов', max_length=128, default=None, unique=True, db_index=True)

    class Meta:
        verbose_name = "Группа атрибутов"
        verbose_name_plural = "Группы атрибутов"

    def __str__(self):
        return self.name

    @property
    @admin.display(description="Содержит атрибуты")
    def attributes_list(self):
        return format_html_join(
            ', ', "<a href={}>{}</a>",
            (
                (reverse('admin:catalog_attribute_change', args=[attr.id]), attr.name)
                for attr in self.attributes.values_list('id', 'name', named=True)
            )
        )


class GroupPlacement(models.Model):
    category = TreeForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория товаров', db_index=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Группа атрибутов', db_index=True)
    position = models.PositiveSmallIntegerField(
        "Позиция группы атрибутов", blank=True, null=True, default=0, db_index=True)

    def __str__(self):
        return f'Группа атрибутов "{self.group}" размещенная в категории "{self.category}"'

    class Meta:
        verbose_name = "Размещение групп атрибутов в категориях"
        verbose_name_plural = "Размещения групп атрибутов в категориях"
        ordering = ('position',)


TYPE_OF_VALUE = (
    (1, "Текст"),
    (2, "Число"),
    (3, "Логический тип"),
    (4, "Вариант из фикс. значений"),
    (5, "Набор фикс. значений")
)


class UnitOfMeasure(models.Model):
    name = models.CharField('Название еденицы измерения', max_length=128, default=None, unique=True, db_index=True)
    designation = models.CharField(max_length=128, default=None, unique=True, db_index=True,
                                   verbose_name='Обозначение еденицы измерения')

    class Meta:
        verbose_name = 'Еденица измерения'
        verbose_name_plural = 'Еденицы измерения'

    def __str__(self):
        return f'{self.name} ({self.designation})'


class Attribute(models.Model):
    name = models.CharField('Название атрибута', max_length=128, default=None, unique=True, db_index=True, )
    slug = models.SlugField(max_length=128, unique=True, db_index=True)
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Группа атрибутов',
                              related_name='attributes', db_index=True)
    position = models.PositiveSmallIntegerField("Позиция атрибута", blank=True, null=True, default=0, db_index=True)
    type_of_value = models.SmallIntegerField('Тип данных', choices=TYPE_OF_VALUE, default=1, db_index=True)
    unit_of_measure = models.ForeignKey(UnitOfMeasure, blank=True, null=True, on_delete=models.SET_NULL,
                                        verbose_name='Еденица измерения', db_index=True)
    default_str_value = models.CharField(
        max_length=128, blank=True, null=True, default='Не вказано',
        verbose_name='Строка для отображения если значение не указано', db_index=True)
    str_true = models.CharField('Отображение для True', max_length=64, default='так', db_index=True)
    str_false = models.CharField('Отображение для False', max_length=64, default='ні', db_index=True)

    class Meta:
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"
        ordering = ['position']

    def __str__(self):
        return self.name

    @property
    def suffix(self):
        return f', {self.unit_of_measure.designation}' if self.unit_of_measure else ''

    @property
    @admin.display(description="Варианты предопределенных текстовых значений")
    def fixed_values_list(self):
        return tuple(self.fixed_values.order_by('position').values_list('name', flat=True)) if (
                self.type_of_value == 4 or self.type_of_value == 5) else 'Нет вариантов. Произвольное значение'


class FixedTextValue(models.Model):
    name = models.CharField('Предопределенное текстовое значение атрибута', max_length=128,
                            default=None, unique=True, db_index=True)
    slug = models.SlugField(max_length=128, unique=True, db_index=True)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='fixed_values', db_index=True)
    description = models.TextField('Подсказка в описании', blank=True, null=True, default=None)
    position = models.PositiveSmallIntegerField("Position", blank=True, null=True, default=0, db_index=True)

    class Meta:
        verbose_name = "Значение атрибута"
        verbose_name_plural = "Значения атрибута"

    def __str__(self):
        return self.name


class MainAttribute(models.Model):
    category = TreeForeignKey(Category, on_delete=models.CASCADE, related_name='main_attributes', db_index=True)
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, verbose_name='Атрибут основных характеристик', db_index=True)
    position = models.PositiveIntegerField("Порядок", null=True, blank=True, db_index=True)

    def __str__(self) -> str:
        return f'{self.attribute.name} из категории {self.category}'

    class Meta:
        unique_together = ('category', 'attribute')
        verbose_name = 'Атрибут для отображения в блоке главных характеристик товара'
        verbose_name_plural = 'Атрибуты для отображения в блоке главных характеристик товара'
        ordering = ['position']


class ShotAttribute(models.Model):
    name = models.CharField('Краткое название', max_length=128, blank=True, null=True, default=None, db_index=True)
    category = TreeForeignKey(Category, on_delete=models.CASCADE, related_name='shot_attributes', db_index=True)
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, verbose_name='Атрибут кратких характеристик', db_index=True)
    position = models.PositiveIntegerField("Порядок", null=True, blank=True, db_index=True)

    def __str__(self) -> str:
        return self.attribute.name

    class Meta:
        unique_together = ('category', 'attribute')
        verbose_name = 'Атрибут для отображения в блоке кратких характеристик товара'
        verbose_name_plural = 'Атрибуты для отображения в блоке кратких характеристик товара'
        ordering = ['position']


class CombinationOfCategory(models.Model):
    categories = models.ManyToManyField(
        'Category', blank=True, default=None, verbose_name='Список категорий', related_name='combinations')
    is_active_custom_order_group = models.BooleanField('Применить индивидуальный порядок групп атрибутов', default=True)
    is_active_custom_order_main_parameters = models.BooleanField('Применить индивидуальный порядок '
                                                                 'основных характеристик', default=True)
    is_active_custom_order_mini_parameters = models.BooleanField('Применить индивидуальный порядок '
                                                                 'кратких характеристик', default=True)

    def __str__(self):
        return f"Сочетание категорий {tuple(self.categories.values_list('name', flat=True))}"

    class Meta:
        verbose_name = 'Сочетание категорий'
        verbose_name_plural = 'Сочетания категорий'


class GroupPositionInCombinationOfCategory(models.Model):
    combination_of_category = models.ForeignKey(
        CombinationOfCategory, on_delete=models.CASCADE, related_name='group_position', )
    group_placement = models.ForeignKey(
        GroupPlacement, on_delete=models.CASCADE, verbose_name='Группы атрибутов')
    position = models.PositiveIntegerField("Порядок", null=True, blank=True)

    def __str__(self):
        return self.group_placement.group.name

    class Meta:
        verbose_name = 'Позиция группы атрибутов в общем списке всех групп всех категорий (данного сочетания ' \
                       'категорий) '
        verbose_name_plural = 'Порядок групп атрибутов в общем списке всех групп всех категорий (данного' \
                              ' сочетания категорий) '
        ordering = ['position']


class MainAttrPositionInCombinationOfCategory(models.Model):
    combination_of_category = models.ForeignKey(
        CombinationOfCategory, on_delete=models.CASCADE, related_name='main_attr_positions')
    main_attribute = models.ForeignKey(
        MainAttribute, blank=True, null=True, default=None, on_delete=models.CASCADE,
        verbose_name='Атрибут основных характеристик')
    position = models.PositiveIntegerField("Порядок", null=True, blank=True)

    def __str__(self):
        return self.main_attribute.attribute.name

    class Meta:
        verbose_name = 'Позиция атрибута основных характеристик (для данного сочетания категорий) '
        verbose_name_plural = 'Порядок атрибутов основных характеристик (для данного сочетания категорий) '
        ordering = ['position']


class ShotAttrPositionInCombinationOfCategory(models.Model):
    combination_of_category = models.ForeignKey(
        CombinationOfCategory, on_delete=models.CASCADE, related_name='shot_attr_positions')
    shot_attribute = models.ForeignKey(
        ShotAttribute, blank=True, null=True, default=None, on_delete=models.CASCADE,
        verbose_name='Атрибут кратких характеристик')
    position = models.PositiveIntegerField("Порядок", null=True, blank=True)

    def __str__(self):
        return self.shot_attribute.attribute.name

    class Meta:
        verbose_name = 'Позиция атрибута кратких характеристик (для данного сочетания категорий) '
        verbose_name_plural = 'Порядок атрибутов кратких характеристик (для данного сочетания категорий) '
        ordering = ['position']


class OtherShop(models.Model):
    name = models.CharField('Название', max_length=128, default=None, unique=True, db_index=True)
    url = models.URLField('Ссылка на сайт конкурента', max_length=128, blank=True, null=True, default=None, unique=True)

    def __str__(self):
        return self.name


class PricesOtherShop(models.Model):
    created = models.DateTimeField('Добавлено', auto_now_add=True, auto_now=False)
    product = models.ForeignKey('Product', blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Товар')
    shop = models.ForeignKey(OtherShop, blank=True, null=True, default=None, on_delete=models.CASCADE,
                             verbose_name='Магазин')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    updated = models.DateTimeField('Изменено', auto_now_add=False, auto_now=True)
    url = models.URLField('Ссылка на товар', max_length=128, blank=True, null=True, default=None, unique=True)
    info = models.CharField('Краткое описание', max_length=128, blank=True, null=True, default=None)

    def __str__(self):
        return f'{self.shop.name}: {self.price}, грн'

    class Meta:
        verbose_name = "Цена конкурента"
        verbose_name_plural = "Цены конкурентов"
        ordering = ['updated']


class ProductImage(models.Model):
    name = models.CharField('Название', max_length=128, blank=True, default='', db_index=True)
    created = models.DateTimeField('Добавлено', auto_now_add=True, auto_now=False)
    updated = models.DateTimeField('Изменено', auto_now_add=False, auto_now=True)
    product = models.ForeignKey('Product', blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Товар', related_name='images')
    image = models.ImageField('Фото товара', upload_to='product_images/', blank=True, null=True, db_index=True)
    position = models.PositiveIntegerField("Положение", null=True, db_index=True)

    class Meta:
        ordering = ('position',)
        verbose_name = "Фотография товара"
        verbose_name_plural = "Фотографии товаров"

    def __str__(self):
        return self.name


class Discount(models.Model):
    TYPES_OF_AMOUNT = {
        (1, 'Процент'),
        (2, 'Абсолютное занчение суммы скидки')
    }
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    amount = models.DecimalField(max_digits=6, decimal_places=3)
    type_of_amount = models.SmallIntegerField('Тип скидки', choices=TYPES_OF_AMOUNT)

    class Meta:
        verbose_name = "Скидка на товар"
        verbose_name_plural = "Скидки на товары"

    def __str__(self):
        val = f'{round(self.amount, 2)} %' if self.type_of_amount == 1 else str(Money(self.amount, 'UAH'))
        return f'{self.product} - {val}'
