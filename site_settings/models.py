from django.db import models
from solo.models import SingletonModel

# Create your models here.
from ROOTAPP.models import Person


class SliderConfiguration(SingletonModel):
    autoplay_speed = models.PositiveSmallIntegerField(default=0, db_index=True, verbose_name='Задержка перлистівания')
    autoplay = models.BooleanField(default=False, verbose_name='Автоперелистывание')

    def __str__(self):
        return "SliderConfiguration"

    class Meta:
        verbose_name = "Настройки слайдера"


class HeaderConfiguration(SingletonModel):
    header_height = models.CharField('Высота верхней шапки', max_length=128, blank=True, null=True, unique=True,
                                     db_index=True)
    sub_header_height = models.CharField('Высота нижней шапки', max_length=128, blank=True, null=True, unique=True,
                                         db_index=True)
    menu_height = models.CharField('Высота меню', max_length=128, blank=True, null=True, unique=True, db_index=True)

    def __str__(self):
        return "HeaderConfiguration"

    class Meta:
        verbose_name = "Настройки шапки"


class PhotoPlug(SingletonModel):
    image = models.ImageField('Фото заглушка', upload_to='main_page')

    def __str__(self):
        return "PhotoPlug"

    class Meta:
        verbose_name = "Фото заглушка"


class NpAPI(models.Model):
    api_key = models.CharField('Ключ API', max_length=128, unique=True)
    valid_date = models.DateTimeField('Изменено', auto_now_add=False, auto_now=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def __str__(self):
        return f"Кабинет новой почты - {self.person}"

    class Meta:
        verbose_name = "Учетная запись кабинета новой почты"
        verbose_name_plural = "Учетные записи кабинетов новой почты"


class APIkeyIpInfo(SingletonModel):
    api_key = models.CharField('Ключ API', max_length=128, unique=True)

    def __str__(self):
        return f"ключ API сервиса ipinfo.io- {self.api_key}"

    class Meta:
        verbose_name = "ключ API сервиса ipinfo.io"


class OAuthGoogle(SingletonModel):
    json_auth_data_file = models.FileField("Учетные данные", upload_to='uploads/', null=True)
    email = models.EmailField("Єлектронная почта", null=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "OAuth 2.0 сервисов Google"
