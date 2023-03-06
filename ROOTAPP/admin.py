from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
import nested_admin
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from ROOTAPP.models import Phone, Messenger, Person, PersonPhone, Settlement, PersonSettlement, Warehouse
from django import forms

# from .services.telegram_servises import get_tg_username
# from asgiref.sync import sync_to_async
from orders.models import ByOneclick
from .admin_forms import PersonPhonesAdminFormset
from .forms import AddressForm

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


class WarehouseForSettlementInline(admin.TabularInline):
    model = Warehouse
    extra = 0
    fields = ('number', 'type_warehouse', 'description_ru', 'warehouse_status', 'deny_to_select', 'place_max_weight',
              'total_max_weight')

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
    inlines = (PersonPhoneInlineAdmin, PersonSettlementInline, PersonOneClickInline)
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


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    fields = (
        'type', 'description_ru', 'description_ua', 'area', 'region', 'warehouse', 'index_1', 'index_2',
        'index_coatsu_1'
    )
    readonly_fields = (
        'type', 'description_ru', 'description_ua', 'area', 'region', 'warehouse', 'index_1', 'index_2',
        'index_coatsu_1'
    )
    list_filter = ('area__description_ru', 'warehouse')
    baton_cl_includes = [
        ('ROOTAPP/button_update_cities.html', 'top',),
    ]
    search_fields = ('description_ru', 'description_ua', 'index_1')
    inlines = (WarehouseForSettlementInline,)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    # fields = ('ref',)
    baton_cl_includes = [
        ('ROOTAPP/admin_update_warehouses.html', 'top',),
    ]

    autocomplete_fields = ('settlement',)
    list_filter = ('type_warehouse',)
    search_fields = ('description_ua',)

    def changelist_view(self, request, extra_context=None):
        # extra_context = extra_context or {}
        extra_context = {'city_form': AddressForm}
        return super().changelist_view(
            request, extra_context=extra_context,
        )

    def has_change_permission(self, request, obj=None):
        return False

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'select2.min.js',)

        css = {
            "all": ("select2.min.css",)}
