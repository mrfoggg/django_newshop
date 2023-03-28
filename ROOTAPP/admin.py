import nested_admin
from adminsortable2.admin import SortableAdminMixin
from django import forms
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django_select2.forms import ModelSelect2Widget
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from nova_poshta.models import Warehouse, Street
from nova_poshta.services import get_city_sender_for_settlement
# from .services.telegram_servises import get_tg_username
# from asgiref.sync import sync_to_async
from orders.models import ByOneclick
from ROOTAPP.models import (Messenger, Person, PersonPhone, PersonSettlement,
                            Phone)

from .admin_forms import PersonPhonesAdminFormset
from .forms import FullAddressForm, PersonAddress

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
    inlines = (PersonPhoneInlineAdmin, PersonOneClickInline, PersonSettlementInline)
    list_display = ('__str__', 'email', 'main_phone', 'is_customer', 'is_supplier')
    list_filter = ('is_customer', 'is_supplier')

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
# @admin.register(PersonAddress)
class PersonAddressAdmin(admin.ModelAdmin):
    form = FullAddressForm
    fields = ('address_type', 'area', 'settlement', 'person')
    autocomplete_fields = ('person', 'city',)

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'select2.min.js')

        css = {
            "all": ("select2.min.css",)}

    # def get_field_queryset(
    #     self, db: Optional[str], db_field: RelatedField, request: HttpRequest
    # ) -> Optional[QuerySet]:

    def get_form(self, request, obj=None, **kwargs):
        print('+'*70)
        # obj.save()
        print('obj - ', obj)
        if obj:
            request._obj_not_exist_ = False
            request._address_type_ = obj.address_type
            # print('streets_this_city - ', streets_this_city)
            found_settlement = get_city_sender_for_settlement(obj.settlement.description_ua, obj.settlement_id)
            streets_this_city = Street.objects.filter(city_id=found_settlement.delivery_city_ref)
            obj.city_id = found_settlement.delivery_city_ref
            if not found_settlement.address_delivery_allowed:
                messages.add_message(request, messages.ERROR, 'АДРЕСНАЯ ДОСТАВКА НЕДОСТУПНА')
            if found_settlement.streets_availability:
                streets_to_select = streets_this_city
                streets_to_select_count = streets_this_city.count()
            else:
                streets_to_select = streets_this_city.filter(
                    description_ua__icontains=obj.settlement.description_ua)
                streets_to_select_count = streets_to_select.count()
                if streets_to_select_count == 1:
                    obj.street = streets_to_select.first()
                    request._is_street_field_read_only_ = True
                    messages.add_message(request, messages.SUCCESS, 'Указанный населенный пункт выбран как улица в городе '
                                                                    'доставки. Необходимую улицу доставки укажите в '
                                                                    'коментарии')
                else:
                    messages.add_message(request, messages.SUCCESS, 'Указанный населенный пункт веберете как улицу в городе '
                                                                    'доставки. Необходимую улицу доставки укажите в '
                                                                    'коментарии')
            request._streets_availability_ = found_settlement.streets_availability
            request._streets_to_select_ = streets_to_select
            request._streets_to_select_count_ = streets_to_select_count

            obj.save()
            print('obj.street - ', obj.street)
            print('streets_to_select - ', streets_to_select)
        return super().get_form(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        if obj is not None:
            if obj.address_type in (1, 2):
                return self.fields + ('warehouse', 'comment')
            else:
                return self.fields + ('city', 'street', 'comment')
        else:
            return self.fields + ('warehouse', 'comment')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request._streets_availability_:
                return ()
            else:
                print('streets_to_select_count - ', request._streets_to_select_count_)
                return ('city', 'street',) if request._streets_to_select_count_ == 1 else ('city',)
        else:
            return ()

    # def get_autocomplete_fields(self, request, obj=None):
    #     if obj:
    #         return ('city', 'street',) if request._streets_availability_ else ()
    #     else:
    #         return ()


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'warehouse':
            if request._obj_not_exist_:
                request._address_type_ = 1
            match request._address_type_:
                case 2:
                    kwargs["queryset"] = Warehouse.objects.filter(type_warehouse_id__in=
                                                                  ('95dc212d-479c-4ffb-a8ab-8c1b9073d0bc',
                                                                   'f9316480-5f2d-425d-bc2c-ac7cd29decf0')
                                                                  )
                case 1:
                    kwargs["queryset"] = Warehouse.objects.filter(type_warehouse_id__in=
                                                                  ('6f8c7162-4b72-4b0a-88e5-906948c6a92f',
                                                                   '841339c7-591a-42e2-8233-7a0a00f0ed6f',
                                                                   '9a68df70-0267-42a8-bb5c-37f427e36ee4')
                                                                  )
        if not request._obj_not_exist_:
            if db_field.name == 'street' and not request._streets_availability_ and request._streets_to_select_count_ > 1:
                kwargs["queryset"] = request._streets_to_select_
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# без использования декоратора так как перопрелеляется __init__
admin.site.register(PersonAddress, PersonAddressAdmin)

# @admin.register(PersonSettlement)
# class PersonAddressAdmin(admin.ModelAdmin):
#     autocomplete_fields = ('settlement',)
