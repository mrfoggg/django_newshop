from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
import nested_admin
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from ROOTAPP.models import Phone, Messenger, Person, PersonPhone, Settlement, PersonSettlement
from django import forms

# from .services.telegram_servises import get_tg_username
# from asgiref.sync import sync_to_async

admin.site.register(Messenger)


class PersonPhoneInlineAdmin(nested_admin.NestedTabularInline):
    model = PersonPhone
    extra = 0


class PersonSettlementInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = PersonSettlement
    extra = 2
    sortable_field_name = 'priority'
    ordering = ('priority',)
    autocomplete_fields = ('settlement',)


class PhoneAdminForm(forms.ModelForm):
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


@admin.register(Person)
class PersonAdmin(nested_admin.NestedModelAdmin):
    fields = ('last_name', 'first_name', 'middle_name', 'email', ('is_customer', 'is_supplier'))
    search_fields = ('last_name', 'first_name', 'middle_name')
    inlines = (PersonPhoneInlineAdmin, PersonSettlementInline)
    list_display = ('__str__', 'is_customer', 'is_supplier')
    list_filter = ('is_customer', 'is_supplier')


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    fields = (
        ('type', 'description_ru', 'description_ua', ),
        ('area', 'region', ),
        'warehouse',
        ('index_1', 'index_2', 'index_coatsu_1'),
    )
    list_filter = ('area__description_ru', 'warehouse')
    baton_cl_includes = [
        ('ROOTAPP/button_update_cities.html', 'top',),
    ]
    search_fields = ('description_ru', 'description_ua', 'area__description_ru', 'area__description_ua',
                     'region__description_ru', 'region__description_ua', 'index_1')
