from django.contrib import admin
from solo.admin import SingletonModelAdmin
from site_settings.models import SliderConfiguration, HeaderConfiguration, PhotoPlug, NpAPI, APIkeyIpInfo, OAuthGoogle, \
    TwilioOTPSettings

admin.site.register(SliderConfiguration, SingletonModelAdmin)
admin.site.register(HeaderConfiguration, SingletonModelAdmin)
admin.site.register(PhotoPlug, SingletonModelAdmin)
admin.site.register(APIkeyIpInfo, SingletonModelAdmin)
admin.site.register(OAuthGoogle, SingletonModelAdmin)

admin.site.register(NpAPI)
