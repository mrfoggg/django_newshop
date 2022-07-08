from django.contrib import admin
from solo.admin import SingletonModelAdmin
from site_settings.models import SliderConfiguration


admin.site.register(SliderConfiguration, SingletonModelAdmin)

# Register your models here.
