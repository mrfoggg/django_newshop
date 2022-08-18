from django.db import models
from solo.models import SingletonModel


# Create your models here.
class SliderConfiguration(SingletonModel):
    autoplay_speed = models.PositiveSmallIntegerField(default=0, db_index=True, verbose_name='Задержка перлистівания')
    autoplay = models.BooleanField(default=False, verbose_name='Автоперелистывание')

    def __str__(self):
        return "SliderConfiguration"

    class Meta:
        verbose_name = "Настройки слайдера"


class HeaderConfiguration(SingletonModel):
    header_height = models.CharField(max_length=128, blank=True, null=True, unique=True, db_index=True,
                                     verbose_name='Высота верхней шапки')
    sub_header_height = models.CharField(max_length=128, blank=True, null=True, unique=True, db_index=True,
                                         verbose_name='Высота нижней шапки')
    menu_height = models.CharField(max_length=128, blank=True, null=True, unique=True, db_index=True,
                                   verbose_name='Высота нижней шапки')

    def __str__(self):
        return "HeaderConfiguration"

    class Meta:
        verbose_name = "Настройки шапки"


class PhotoPlug(SingletonModel):
    image = models.ImageField(upload_to='main_page', verbose_name='Фото заглушка')

    def __str__(self):
        return "PhotoPlug"

    class Meta:
        verbose_name = "Фото заглушка"
