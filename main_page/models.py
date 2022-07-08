from django.contrib import admin
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

    def get_absolute_url(self):
        return f'{self.slug}'


class Menu(MPTTModel):
    TYPE_OF_ITEM_MENU = (
        (1, "Категория товаров"),
        (2, "Статическая страница"),
        (3, "Произвольный UPL"),
        (4, "Пункт меню без ссылки"),
    )

    title = models.CharField(max_length=128, default=None, unique=True, db_index=True,
                             verbose_name='Название пункта меню')
    type_of_item = models.SmallIntegerField(
        choices=TYPE_OF_ITEM_MENU, default=4, db_index=True, verbose_name='Тип пункта меню')
    parent = TreeForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL,
                            related_name='children', db_index=True, verbose_name='Родительский пункт меню')
    link = models.URLField(max_length=128, blank=True, null=True, default=None, unique=True,
                           verbose_name='Ссылка на которую указывает пункт меню')
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Статический СЕО трэш')
    category = TreeForeignKey(Category, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                              verbose_name='Целевая категория товаров')
    page = models.ForeignKey(StaticPage, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                             verbose_name='Целевая статическая страница')
    image = models.ImageField(upload_to='main_page/top_menu-images', blank=True, null=True, verbose_name='Логотип')

    class Meta:
        verbose_name = "Пункт меню"
        verbose_name_plural = "Конструктор меню"

    def __str__(self):
        return f'{self.title} ({self.get_type_of_item_display()})'

    @property
    @admin.display(description='Текущая ссылка')
    def get_link(self):
        match self.type_of_item:
            case 3:
                if self.link:
                    url = self.link
                else:
                    url = None
            case 4:
                url = None
            case 1:
                if self.category:
                    url = self.category.get_absolute_url
                else:
                    url = None
            case 2:
                if self.page:
                    url = self.page.get_absolute_url
                else:
                    url = None
        # return 'без ссылки' if url is None else url
        return url


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
    image = models.ImageField(upload_to='main_page/banner', blank=True, null=True, verbose_name='Фото товара')
    position = models.PositiveIntegerField("Position", null=True)

    class Meta:
        ordering = ('position',)
        verbose_name = "Баннер"
        verbose_name_plural = "Слайдер с баннерами"

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
        verbose_name = "Популярная категория"
        verbose_name_plural = "Популярные категории"

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
        verbose_name = "Популярный товар"
        verbose_name_plural = "Популярные товары"

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
        verbose_name_plural = "Новые поступления"

    def __str__(self):
        return self.product.name
