from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
import nested_admin
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from ROOTAPP.models import Phone, Messenger, Person, PersonPhone, City, PersonCity
from django import forms

# from .services.telegram_servises import get_tg_username
# from asgiref.sync import sync_to_async

admin.site.register(Messenger)


class PersonPhoneInlineAdmin(nested_admin.NestedTabularInline):
    model = PersonPhone
    extra = 0


class PersonCityInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = PersonCity
    extra = 2
    sortable_field_name = 'priority'
    ordering = ('priority',)
    autocomplete_fields = ('city',)


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


@admin.register(Person)
class PersonAdmin(nested_admin.NestedModelAdmin):
    fields = ('last_name', 'first_name', 'middle_name', 'email', ('is_customer', 'is_supplier'))
    search_fields = ('last_name', 'first_name', 'middle_name')
    inlines = (PersonPhoneInlineAdmin, PersonCityInline)
    list_display = ('__str__', 'is_customer', 'is_supplier')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    fields = (
        ('description_ru', 'description', 'ref'),
        ('settlement_type_description_ru', 'settlement_type_description', 'settlement_type'),
        ('area_description_ru', 'area_description', 'area'),
        ('region_description_ru', 'region_description', 'region'),
        ('index_1', 'index_2', 'index_coatsu_1'),
        ('warehouse',)
    )
    list_display = ('description_ru', 'description', 'settlement_type_description_ru', 'area_description_ru',
                    'region_description_ru', 'warehouse',)
    list_filter = ('area_description_ru', 'warehouse')
    list_display_links = ('description_ru', 'description')
    baton_cl_includes = [
        ('ROOTAPP/button_update_cities.html', 'top',),
    ]
    search_fields = ('description_ru', 'description', 'area_description_ru', 'area_description', 'index_1')
