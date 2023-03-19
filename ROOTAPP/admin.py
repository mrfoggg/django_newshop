from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
import nested_admin
from django.urls import reverse
from django.utils.html import format_html
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from ROOTAPP.models import Phone, Messenger, Person, PersonPhone, PersonSettlement
from django import forms

# from .services.telegram_servises import get_tg_username
# from asgiref.sync import sync_to_async
from orders.models import ByOneclick
from .admin_forms import PersonPhonesAdminFormset
from .forms import PersonAddress, FullAddressForm

# from .forms import AddressForm, FullAddressForm

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


@admin.register(PersonAddress)
class PersonAddressAdmin(admin.ModelAdmin):
    form = FullAddressForm

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'select2.min.js')

        css = {
            "all": ("select2.min.css",)}


@admin.register(PersonSettlement)
class PersonAddressAdmin(admin.ModelAdmin):
    autocomplete_fields = ('settlement',)
