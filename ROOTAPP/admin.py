from pprint import pprint

import nested_admin
from django import forms
from django.contrib import admin
from phonenumber_field.widgets import PhoneNumberPrefixWidget
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
        # request._show_types_field_ = False
        # if obj:
        #     if obj.settlement:
        #         request._show_types_field_ = True
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
    inlines = (PersonPhoneInlineAdmin, PersonOneClickInline, PersonSettlementInline, PersonAddressInlineAdmin)
    list_display = ('__str__', 'email', 'main_phone', 'is_customer', 'is_supplier')
    list_filter = ('is_customer', 'is_supplier')

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

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term, )
        if 'model_name' in request.GET.keys():
            if request.GET['model_name'] == 'clientorder':
                queryset = queryset.filter(is_customer=True)
        return queryset, may_have_duplicates


# без использования декоратора так как перопрелеляется __init__
@admin.register(PersonAddress)
class PersonAddressAdmin(admin.ModelAdmin):
    form = FullAddressForm
    fields = ('person', 'area', 'settlement', 'address_type', 'warehouse', 'city', 'street', 'build', 'comment')
    autocomplete_fields = ('person',)
    readonly_fields = ['city']
    radio_fields = {"address_type": admin.HORIZONTAL}
    # radio_fields = {"address_type": admin.VERTICAL}

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'select2.min.js', 'notyf.min.js', 'root_app/person_address_admin_form.js')
        #   с этой строкй пишет что цсс дублируется
        # css = {"all": ("select2.min.css")}

        css = {"all": ("notyf.min.css", )}

    def get_readonly_fields(self, request, obj=None):
        new_rof = []
        if obj:
            if obj.person:
                new_rof.append('person')
        return self.readonly_fields + new_rof
