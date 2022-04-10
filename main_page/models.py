from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from catalog.models import Category, Product


class StaticPage(models.Model):
    title = models.CharField(max_length=128, default=None, unique=True, db_index=True,
                             verbose_name='Заголовок страницы')
    slug = models.SlugField(max_length=128, blank=True, null=True, default=None, unique=True)
    image = models.ImageField(upload_to='pages_images/', blank=True, null=True, verbose_name='Фото страницы')
    is_active = models.BooleanField(default=True, verbose_name='Видимость на сайте')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    text = models.TextField(blank=True, null=True, default=None, verbose_name='Текст страницы')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Текстовая страница"
        verbose_name_plural = "Текстовые страницы"


class Menu(MPTTModel):
    TYPE_OF_ITEM_MENU = (
        (1, "Категория товаров"),
        (2, "Статическая страница"),
        (3, "Произвольный UPL"),
    )

    title = models.CharField(max_length=128, default=None, unique=True, db_index=True,
                             verbose_name='Название пункта меню')
    type_of_item = models.SmallIntegerField(
        choices=TYPE_OF_ITEM_MENU, default=1, db_index=True, verbose_name='Тип пункта меню')
    parent = TreeForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL,
                            related_name='children', db_index=True, verbose_name='Родительский пункт меню')
    link = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                           verbose_name='Ссылка на отфильрованую выдачу')
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Статический СЕО трэш')
    category = TreeForeignKey(Category, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                              verbose_name='Целевая категория товаров')
    page = models.ForeignKey(StaticPage, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                             verbose_name='Целевая статическая страница')

    class Meta:
        verbose_name = "Пункт меню"
        verbose_name_plural = "Пункты меню"

    def __str__(self):
        return f'{self.title} ({self.get_type_of_item_display()})'


class Banner(models.Model):
    title = models.CharField(
        max_length=128, blank=True, default='', db_index=True, verbose_name='Заголовок баннера')
    link = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                           verbose_name='Ссылка на целевую страницуу')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Добавлено')
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name='Изменено')
    date_from = models.DateTimeField(auto_now_add=False, auto_now=False, verbose_name='Отображать с даты')
    date_to = models.DateTimeField(auto_now_add=False, auto_now=False, verbose_name='Отображать до даты')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True, verbose_name='Фото товара')
    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        ordering = ('position',)
        verbose_name = "Баннер"
        verbose_name_plural = "Фотографии баннеров"

    def __str__(self):
        return self.title


class PopularCategory(models.Model):
    category = TreeForeignKey(Category, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                              verbose_name='Категория товаров')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    date_from = models.DateTimeField(auto_now_add=False, auto_now=False, verbose_name='Отображать с даты')
    date_to = models.DateTimeField(auto_now_add=False, auto_now=False, verbose_name='Отображать до даты')
    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        ordering = ('position',)
        verbose_name = "Поулярная сейчас категория"
        verbose_name_plural = "Поулярные сейчас категории"

    def __str__(self):
        return self.category.name


class PopularProduct(models.Model):
    product = models.ForeignKey(Product, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                             verbose_name='Товар')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    date_from = models.DateTimeField(auto_now_add=False, auto_now=False, verbose_name='Отображать с даты')
    date_to = models.DateTimeField(auto_now_add=False, auto_now=False, verbose_name='Отображать до даты')
    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        ordering = ('position',)
        verbose_name = "Поулярный товар"
        verbose_name_plural = "Поулярные товары"

    def __str__(self):
        return self.product.name


class NewProduct(models.Model):
    product = models.ForeignKey(Product, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                             verbose_name='Товар')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    date_from = models.DateTimeField(auto_now_add=False, auto_now=False, verbose_name='Отображать с даты')
    date_to = models.DateTimeField(auto_now_add=False, auto_now=False, verbose_name='Отображать до даты')
    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        ordering = ('position',)
        verbose_name = "Новый товар"
        verbose_name_plural = "Новые постаупления"

    def __str__(self):
        return self.product.name
