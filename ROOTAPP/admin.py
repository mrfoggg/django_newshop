from pprint import pprint

import nested_admin
from adminsortable2.admin import SortableAdminMixin
from django import forms
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django_select2.forms import ModelSelect2Widget
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from nova_poshta.models import Warehouse, Street
from nova_poshta.services import get_settlement_addict_info
# from .services.telegram_servises import get_tg_username
# from asgiref.sync import sync_to_async
from orders.models import ByOneclick
from ROOTAPP.models import (Messenger, Person, PersonPhone, PersonSettlement,
                            Phone, PersonAddress)

from .admin_forms import PersonPhonesAdminFormset, FullAddressForm

admin.site.register(Messenger)


class PersonPhoneInlineAdmin(nested_admin.NestedTabularInline):
    formset = PersonPhonesAdminFormset
    model = PersonPhone
    autocomplete_fields = ('phone',)
    extra = 0


class PersonSettlementInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = PersonSettlement
    extra = 2
    sortable_field_name = 'priority'
    ordering = ('priority',)
    autocomplete_fields = ('settlement',)


class PersonOneClickInline(nested_admin.NestedTabularInline):
    model = ByOneclick
    readonly_fields = ('product', 'created', 'updated', 'status')
    fields = ('product', 'created', 'updated', 'status')
    extra = 0


class PersonAddressInlineAdmin(nested_admin.NestedTabularInline):
    fields = ('area',)
    model = PersonAddress
    autocomplete_fields = ('area',)
    extra = 0
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False


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
    search_fields = ('number',)

    def get_form(self, request, obj=None, **kwargs):
        request._show_types_field_ = False
        if obj:
            if obj.settlement:
                request._show_types_field_ = True
        form = super(PhoneAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['messengers'].widget = forms.CheckboxSelectMultiple()
        return form

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'jquery.maskedinput.min.js',
              'phone-field-formater.js',)


@admin.register(Person)
class PersonAdmin(nested_admin.NestedModelAdmin):
    fields = (
        ('last_name', 'first_name', 'middle_name'), ('email', 'username'),
        ('is_customer', 'is_supplier', 'is_staff', 'is_superuser'), 'main_phone', 'delivery_phone'
    )
    search_fields = ('last_name', 'first_name', 'middle_name')
    # autocomplete_fields = ('main_phone',)
    inlines = (PersonPhoneInlineAdmin, PersonOneClickInline, PersonSettlementInline, PersonAddressInlineAdmin)
    list_display = ('__str__', 'email', 'main_phone', 'is_customer', 'is_supplier')
    list_filter = ('is_customer', 'is_supplier')

    # class Media:
    #     js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
    #           'select2.min.js', 'select2_inline_fix.js')
    # js = ('select2_inline_fix.js',)

    # read

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            request._person_phones = Phone.objects.filter(personphone__person=obj)
        else:
            request._person_phones = Phone.objects.none()
        return super(PersonAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ('main_phone', 'delivery_phone'):
            kwargs["queryset"] = request._person_phones
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# без использования декоратора так как перопрелеляется __init__
@admin.register(PersonAddress)
class PersonAddressAdmin(admin.ModelAdmin):
    form = FullAddressForm
    fields = ('person', 'area', 'settlement', 'address_type', 'warehouse', 'city', 'street', 'build', 'comment')
    autocomplete_fields = ('person', 'city',)
    readonly_fields = ['city']
    radio_fields = {"address_type": admin.HORIZONTAL}

    # radio_fields = {"address_type": admin.VERTICAL}

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'select2.min.js',
              'root_app/person_address_admin_form.js')
        #   с этой строкй пишет что цсс дублируется
        # css = {
        #     "all": ("select2.min.css")}

    def get_form(self, request, obj=None, **kwargs):
        # print('+'*70)
        print('GET FORM')
        request._obj_not_exist_ = True
        form = super().get_form(request, obj, **kwargs)
        if obj:
            if obj.settlement:
                request._obj_not_exist_ = False
                request._address_type_ = obj.address_type
                settlement_addict_info = get_settlement_addict_info(obj.settlement.index_1, obj.settlement_id)
                obj.city_id = settlement_addict_info.delivery_city_ref

                # проверка доступности видов доставки и задание соответсвующийх варианов выбора
                # будет передалано под AJAX
                # types_to_choice = ()
                # all_settlement_warehouses = obj.settlement.warehouses.all()
                # print('all_settlement_warehouses - ', all_settlement_warehouses)
                # if all_settlement_warehouses.exists():
                #     types_to_choice += ((1, "На отделение"),)
                #     if all_settlement_warehouses.filter(
                #             type_warehouse_id__in=('95dc212d-479c-4ffb-a8ab-8c1b9073d0bc',
                #                                    'f9316480-5f2d-425d-bc2c-ac7cd29decf0'
                #                                    )
                #     ).exists():
                #         types_to_choice += ((1, "На почтомат"),)
                # form.base_fields["address_type"].choices = types_to_choice

            #     задание вариантов выбора улиц в зависимости от города
            if obj.city and "street" in form.base_fields:
                form.base_fields["street"].queryset = Street.objects.filter(city=obj.city)

            # будет передалано под AJAX
            # для типов отделение илт почтомат
            # match obj.address_type:
            #     case 1:
            #         form.base_fields["warehouse"].queryset = Warehouse.objects.filter(
            #             type_warehouse_id__in=('6f8c7162-4b72-4b0a-88e5-906948c6a92f',
            #                                    '841339c7-591a-42e2-8233-7a0a00f0ed6f',
            #                                    '9a68df70-0267-42a8-bb5c-37f427e36ee4')
            #         )
            #     case 2:
            #         form.base_fields["warehouse"].queryset = Warehouse.objects.filter(
            #             type_warehouse_id__in=('95dc212d-479c-4ffb-a8ab-8c1b9073d0bc',
            #                                    'f9316480-5f2d-425d-bc2c-ac7cd29decf0'
            #                                    )
            #         )

        return form
    # будет передалано под AJAX
    # def get_fields(self, request, obj=None):
    #     new_fields = []
    #     if obj is not None:
    #         new_fields.append('address_type')
    #         if obj.address_type == 1:
    #             new_fields.extend(['warehouse', 'comment'])
    #         else:
    #             new_fields.extend(['city', 'street', 'build', 'comment'])
    #     return self.fields + new_fields

    def get_readonly_fields(self, request, obj=None):
        new_rof = []
        if obj:
            if obj.person:
                new_rof.append('person')
        return self.readonly_fields + new_rof

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == 'warehouse':
    #         if request._obj_not_exist_:
    #             request._address_type_ = 1
    #         match request._address_type_:
    #             case 2:
    #                 print('WAREHOUS')
    #                 kwargs["queryset"] = Warehouse.objects.filter(type_warehouse_id__in=
    #                                                               ('95dc212d-479c-4ffb-a8ab-8c1b9073d0bc',
    #                                                                'f9316480-5f2d-425d-bc2c-ac7cd29decf0')
    #                                                               )
    #             case 1:
    #                 print('PPOSHTOMAT')
    #                 kwargs["queryset"] = Warehouse.objects.filter(type_warehouse_id__in=
    #                                                               ('6f8c7162-4b72-4b0a-88e5-906948c6a92f',
    #                                                                '841339c7-591a-42e2-8233-7a0a00f0ed6f',
    #                                                                '9a68df70-0267-42a8-bb5c-37f427e36ee4')
    #                                                               )
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

# без использования декоратора так как перопрелеляется __init__
# admin.site.register(PersonAddress, PersonAddressAdmin)

# @admin.register(PersonSettlement)
# class PersonAddressAdmin(admin.ModelAdmin):
#     autocomplete_fields = ('settlement',)
