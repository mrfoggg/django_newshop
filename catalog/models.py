from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html_join
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class Country(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название страны')
    slug = models.SlugField(max_length=64, blank=True, null=True, default=None, unique=True)

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название бренда')
    country = models.ForeignKey(Country, blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Страна брэнда')

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"

    def __str__(self):
        return f'{self.name} ({self.country})'


class Category(MPTTModel):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    parent = TreeForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL,
                            related_name='children', db_index=True, verbose_name='Родительская категория')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Описание категории')
    groups = models.ManyToManyField('Group', through='GroupPlacement', related_name='categories')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True, verbose_name='Фото категории')

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


class ProductSeries(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название линейки '
                                                                                                   'товаров')
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Описание линейки товаров')


class Product(models.Model):
    RATING = (
        (1, " * "),
        (2, " * * "),
        (3, " * * * "),
        (4, " * * * * "),
        (5, " * * * * * ")
    )
    WARRANTY = (
        (1, "12 мес."),
        (2, "6 мес."),
        (3, "3 мес."),
        (4, "14 дней"),
    )
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Товар включен')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    sku = models.CharField(max_length=10, blank=True, null=True, default=None, unique=True,
                           verbose_name='Артикул товара')
    sku_manufacturer = models.CharField(max_length=10, blank=True, null=True, default=None, unique=True,
                                        verbose_name='Артикул товара в каталоге производителя')
    country_of_manufacture = models.ForeignKey(Country, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                                               verbose_name='Страна производства')
    brand = models.ForeignKey(Brand, blank=True, null=True, default=None, on_delete=models.CASCADE,
                              verbose_name='Бренд товара')
    series = models.ForeignKey(ProductSeries, blank=True, null=True, default=None, on_delete=models.CASCADE,
                               verbose_name='Товары из лиенйки', related_name='products')
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Описание товара')
    characteristics = models.JSONField(default=dict, blank=True, verbose_name='Характеристики товара')
    service_info = models.TextField(blank=True, null=True, default=None, verbose_name='Cлужебная информация')
    rating = models.SmallIntegerField(choices=RATING, default=1, db_index=True, verbose_name='Рейтинг товара')
    admin_category = TreeForeignKey(Category, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                                    verbose_name='Категория отображения в админ-панели')
    url = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                          verbose_name='Ссылка на товар на сайте производителя)')
    length = models.FloatField(blank=True, null=True, verbose_name='Длина, см')
    width = models.FloatField(blank=True, null=True, verbose_name='Ширина, см')
    height = models.FloatField(blank=True, null=True, verbose_name='Высота, см')
    warranty = models.SmallIntegerField(choices=WARRANTY, default=1, verbose_name='Срок гарантии')
    weight = models.FloatField(blank=True, null=True, verbose_name='Вес, кг')
    package_length = models.FloatField(blank=True, null=True, verbose_name='Длина упаковки, см')
    package_width = models.FloatField(blank=True, null=True, verbose_name='Ширина упаковки, см')
    package_height = models.FloatField(blank=True, null=True, verbose_name='Высота упаковки, см')
    categories = models.ManyToManyField(Category, through='ProductPlacement', related_name='products')
    combination_of_categories = models.ForeignKey(
        'CombinationOfCategory', blank=True, null=True,
        verbose_name='Связанная комбинация категорий', on_delete=models.SET_NULL)

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
            for cat_placement in self.productplacement_set.order_by('category_position'):
                for group_placement in cat_placement.category.groupplacement_set.order_by('position'):
                    group_sorted_list.append([cat_placement.category.name, group_placement.group])
        return group_sorted_list


class ProductPlacement(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    category = TreeForeignKey(Category, on_delete=models.CASCADE, verbose_name='Размещение в категории')
    category_position = models.PositiveSmallIntegerField("PositionCategory", blank=True, null=True)
    product_position = models.PositiveSmallIntegerField("PositionProduct", blank=True, null=True)

    class Meta:
        verbose_name = "Размещение товаров в категориях"
        verbose_name_plural = "Размещения товаров в категориях"
        unique_together = ('product', 'category')

    def __str__(self):
        return f'{self.product} в категории {self.category}'


class Group(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True,
                            verbose_name='Название группы атрибутов')

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
    category = TreeForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория товаров')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Группа атрибутов')
    position = models.PositiveSmallIntegerField("Position", blank=True, null=True, default=0)

    def __str__(self):
        return f'Группа атрибутов "{self.group}" размещенная в категории "{self.category}"'

    class Meta:
        verbose_name = "Размещение групп атрибутов в категориях"
        verbose_name_plural = "Размещения групп атрибутов в категориях"
        ordering = ['position']


TYPE_OF_VALUE = (
    (1, "Текст"),
    (2, "Число"),
    (3, "Логический тип"),
    (4, "Вариант из фикс. значений"),
    (5, "Набор фикс. значений")
)


class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True,
                            verbose_name='Название еденицы измерения')
    designation = models.CharField(max_length=128, default=None, unique=True, db_index=True,
                                   verbose_name='Обозначение еденицы измерения')

    class Meta:
        verbose_name = 'Еденица измерения'
        verbose_name_plural = 'Еденицы измерения'

    def __str__(self):
        return f'{self.name} ({self.designation})'


class Attribute(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название атрибута')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Группа атрибутов',
                              related_name='attributes')
    position = models.PositiveSmallIntegerField("Position", blank=True, null=True, default=0)
    type_of_value = models.SmallIntegerField(choices=TYPE_OF_VALUE, default=1, verbose_name='Тип данных')
    unit_of_measure = models.ForeignKey(UnitOfMeasure, blank=True, null=True, on_delete=models.SET_NULL,
                                        verbose_name='Еденица измерения')
    display_when_value_none = models.BooleanField('Отображать пустое поле', default=True)

    class Meta:
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"
        ordering = ['position']

    def __str__(self):
        return self.name

    @property
    @admin.display(description="Варианты предопределенных текстовых значений")
    def fixed_values_list(self):
        return tuple(self.fixed_values.order_by('position').values_list('name', flat=True)) if (
                self.type_of_value == 4 or self.type_of_value == 5) else 'Нет вариантов. Произвольное значение'


class FixedTextValue(models.Model):
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True,
                            verbose_name='Предопределенное текстовое значение атрибута')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='fixed_values')
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Подсказка в описании')
    position = models.PositiveSmallIntegerField("Position", blank=True, null=True, default=0)

    class Meta:
        verbose_name = "Значение атрибута"
        verbose_name_plural = "Значения атрибута"

    def __str__(self):
        return self.name


class MainAttribute(models.Model):
    name = models.CharField(max_length=128, default=None, verbose_name='Краткое название')
    category = TreeForeignKey(Category, on_delete=models.CASCADE)
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, verbose_name='Атрибут основных характеристик')
    position = models.PositiveIntegerField("Порядок", null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.attribute.name} из категории {self.category}'

    class Meta:
        verbose_name = 'Атрибут для отображения в блоке главных характеристик товара'
        verbose_name_plural = 'Атрибуты для отображения в блоке главных характеристик товара'
        ordering = ['position']


class ShotAttribute(models.Model):
    category = TreeForeignKey(Category, on_delete=models.CASCADE)
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, verbose_name='Атрибут кратких характеристик')
    position = models.PositiveIntegerField("Порядок", null=True, blank=True)

    def __str__(self) -> str:
        return self.attribute.name

    class Meta:
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
    name = models.CharField(max_length=128, default=None, unique=True, db_index=True, verbose_name='Название')
    url = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                          verbose_name='Ссылка на сайт конкурента)')

    def __str__(self):
        return self.name


class PricesOtherShop(models.Model):
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    product = models.ForeignKey('Product', blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Товар')
    shop = models.ForeignKey(OtherShop, blank=True, null=True, default=None, on_delete=models.CASCADE,
                             verbose_name='Магазин')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    url = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                          verbose_name='Ссылка на товар)')
    info = models.CharField(max_length=128, blank=True, null=True, default=None,
                            verbose_name='Краткое описание)')

    def __str__(self):
        return f'{self.shop.name}: {self.price}, грн'

    class Meta:
        verbose_name = "Цена конкурента"
        verbose_name_plural = "Цены конкурентов"
        ordering = ['updated']


class ProductImage(models.Model):
    name = models.CharField(max_length=128, blank=True, default='', db_index=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    product = models.ForeignKey('Product', blank=True, null=True, default=None, on_delete=models.CASCADE,
                                verbose_name='Товар', related_name='related_image')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True, verbose_name='Фото товара')
    is_main_1 = models.BooleanField(default=True, verbose_name='Главное фото')
    on_focus = models.BooleanField(default=True, verbose_name='Главное фото при наведении')
    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        ordering = ('position',)
        verbose_name = "Фотография товара"
        verbose_name_plural = "Фотографии товаров"

    def __str__(self):
        return self.name
