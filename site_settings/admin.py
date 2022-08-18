from django.contrib import admin
from solo.admin import SingletonModelAdmin
from site_settings.models import SliderConfiguration, HeaderConfiguration, PhotoPlug

admin.site.register(SliderConfiguration, SingletonModelAdmin)
admin.site.register(HeaderConfiguration, SingletonModelAdmin)
admin.site.register(PhotoPlug, SingletonModelAdmin)

