from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin

from phonenumber_field.widgets import PhoneNumberPrefixWidget

from ROOTAPP.models import Phone, Messenger
from django import forms
# from .services.telegram_servises import get_tg_username
# from asgiref.sync import sync_to_async

admin.site.register(Messenger)


class PhoneAdminForm(forms.ModelForm):
    # def clean(self):
    #     super(PhoneAdminForm, self).clean()
    #     if not self.cleaned_data['telegram_username']:
    #         number = str(self.cleaned_data['number'])[1:]
    #         self.cleaned_data['telegram_username'] = get_tg_username(number)

    class Meta:
        model = Phone
        fields = ('number', 'telegram_username', 'messengers')
        widgets = {
            'number': PhoneNumberPrefixWidget
        }


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    form = PhoneAdminForm
    readonly_fields = ('get_chat_links',)
    list_display = ('__str__', 'get_chat_links',)
    list_display_links = ('__str__',)

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'jquery.maskedinput.min.js',
              'phone-field-formater.js',)
