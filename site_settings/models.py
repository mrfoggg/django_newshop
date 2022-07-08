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