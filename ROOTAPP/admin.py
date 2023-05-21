from pprint import pprint
import nested_admin
from ai_django_core.admin.model_admins.mixins import AdminNoInlinesForCreateMixin
from django import forms
from django.contrib import admin
from django.db.models import OuterRef
from django_select2.forms import ModelSelect2Widget
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from finance.admin import PriceTypePersonBuyerInline, PriceTypePersonSupplierInline
from orders.admin_form import person_widget
# from .services.telegram_servises import get_tg_username
# from asgiref.sync import sync_to_async
from orders.models import ByOneclick, SupplierOrder
from ROOTAPP.models import Messenger, Person, PersonPhone, Phone, PersonAddress, ContactPerson, PriceTypePersonBuyer, \
    PriceTypePersonSupplier
from .admin_forms import PersonPhonesAdminFormset, FullAddressForm, PersonAdminForm

admin.site.register(Messenger)


class PersonPhoneInlineAdmin(nested_admin.NestedTabularInline):
    formset = PersonPhonesAdminFormset
    fields = ('phone', 'other_person_login_this_phone', 'other_person_not_main', 'is_nova_poshta', 'other_contacts')
    readonly_fields = ('other_person_login_this_phone', 'other_person_not_main', 'other_contacts')
    model = PersonPhone
    autocomplete_fields = ('phone',)
    extra = 0


# class PersonOneClickInline(nested_admin.NestedTabularInline):
#     model = ByOneclick
#     readonly_fields = ('product', 'created', 'updated', 'status')
#     fields = ('product', 'created', 'updated', 'status')
#     extra = 0
#     max_num = 0


class PersonAddressInlineAdmin(nested_admin.NestedTabularInline):
    fields = ('area',)
    model = PersonAddress
    autocomplete_fields = ('area',)
    extra = 0
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False


class PersonContactPersonInline(nested_admin.NestedTabularInline):
    fields = (
        'last_name', 'first_name', 'middle_name', 'phone', 'other_person_login_this_phone', 'other_person_not_main',
        'other_contacts')
    readonly_fields = ('other_person_login_this_phone', 'other_person_not_main', 'other_contacts')
    model = ContactPerson
    extra = 0
    autocomplete_fields = ('phone',)


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
class PersonAdmin(
    # AdminNoInlinesForCreateMixin,
    nested_admin.NestedModelAdmin):
    form = PersonAdminForm
    fieldsets = (
        ('Основные данные пользователя', {
            'fields': (('last_name', 'first_name', 'middle_name',),
                       ('full_name', 'date_joined', 'last_login', 'source_type', 'source_person'), ('comment', 'id')),
            'classes': ('tab-fs-none',),
        }),
        ('Роли пользователя', {
            'fields': (('is_buyer', 'is_supplier', 'is_dropper', 'is_group_buyer'),),
            'classes': ('tab-fs-none',),
        }),
        ('Права пользователя', {
            'fields': (('is_staff', 'is_superuser'),),
            'classes': ('tab-fs-none',),
        }),
        ('Типы цен контрагента', {
            'fields': (('main_supplier_price_type', 'main_price_type',),),
            'classes': ('tab-fs-prices',),
            'description': 'Типы цен по умолчанию для контрагента'
        }),
        ('Контактная информация', {
            'fields': (('email', 'main_phone', 'delivery_phone'),),
            'classes': (
                'baton-tabs-init',
                'baton-tab-group-fs-prices--inline-pricetypepersonsupplier--inline-pricetypepersonbuyer',
                'baton-tab-inline-personaddress'
            ),
            # 'description': 'Контактная информация'
        }),
    )
    search_fields = ('full_name', 'main_phone__number')
    inlines = (PersonPhoneInlineAdmin, PersonAddressInlineAdmin, PersonContactPersonInline,
               PriceTypePersonBuyerInline, PriceTypePersonSupplierInline)
    list_display = ('__str__', 'email', 'main_phone', 'is_buyer', 'is_supplier', 'is_dropper')
    list_filter = ('is_buyer', 'is_supplier', 'is_dropper')
    readonly_fields = ('full_name', 'date_joined', 'last_login', 'id', 'source_type', 'source_person')

    class Media:
        css = {"all": ("root_app/person_form.css", 'admin/order-admin-changeform.css')}
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',

            'admin/textarea-autoheight.js', 'root_app/ajax_update_person_phones_info.js')

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term, )
        if 'model_name' in request.GET.keys():
            if request.GET['model_name'] == 'clientorder':
                queryset = queryset.filter(is_buyer=True)
        return queryset, may_have_duplicates

    def changeform_view(self, request, obj_id, form_url, extra_context=None):
        if obj_id:
            print('REQUEST', request.GET)
            this_person = Person.objects.get(id=obj_id)
            extra_context = {'init_main_phone_id': this_person.main_phone_id,
                             'init_delivery_phone_id': this_person.delivery_phone_id}
        else:
            extra_context = {'init_main_phone_id': '', 'init_delivery_phone_id': ''}
        return super().changeform_view(request, obj_id, form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return self.readonly_fields + ('main_phone', 'delivery_phone')
        else:
            return self.readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        self._request_method = request.method
        self._obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if hasattr(self, '_request_method'):
            if db_field.name == "delivery_phone" and self._request_method == 'GET':
                kwargs["queryset"] = Phone.objects.filter(personphone__person=self._obj)
            if db_field.name == "main_phone" and self._request_method == 'GET':
                person_this_phone = Person.objects.filter(main_phone_id=OuterRef('id')).exclude(
                    id=self._obj.id).values('id')[:1]
                kwargs["queryset"] = Phone.objects.annotate(ptp=person_this_phone).filter(personphone__person=self._obj,
                                                                                          ptp__isnull=True)
        if db_field.name == 'main_supplier_price_type':
            if self._obj:
                qs = PriceTypePersonSupplier.objects.filter(person__id=self._obj.id)
            else:
                qs = PriceTypePersonSupplier.objects.none()
            kwargs["queryset"] = qs

        if db_field.name == 'main_price_type':
            if self._obj:
                qs = PriceTypePersonBuyer.objects.filter(person__id=self._obj.id)
            else:
                qs = PriceTypePersonBuyer.objects.none()
            kwargs["queryset"] = qs

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    baton_form_includes = [
        ('root_app/ajax_adresses_for_person_forms.html', 'id', 'top',),
    ]


# без использования декоратора так как перопрелеляется __init__
@admin.register(PersonAddress)
class PersonAddressAdmin(admin.ModelAdmin):
    form = FullAddressForm
    fields = ('person', ('area', 'settlement'), 'address_type', 'warehouse', 'city', ('street', 'build'), 'comment')
    autocomplete_fields = ('person',)
    readonly_fields = ['city']
    radio_fields = {"address_type": admin.HORIZONTAL}

    # radio_fields = {"address_type": admin.VERTICAL}

    class Media:
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
            'select2.min.js',
            'notyf.min.js',
            'root_app/person_address_admin_form.js',
        )
        #   с этой строкй пишет что цсс дублируется
        # css = {"all": ("select2.min.css")}

        css = {"all": ("notyf.min.css", 'admin/order-admin-changeform.css')}

    def get_readonly_fields(self, request, obj=None):
        new_rof = []
        if obj:
            if obj.person:
                new_rof.append('person')
        return self.readonly_fields + new_rof

    baton_form_includes = [
        ('root_app/admin_address_ajax_urls.html', 'area', 'top',),
    ]


class ContactPersonAdminForm(forms.ModelForm):
    class Meta:
        model = ContactPerson
        fields = '__all__'
        widgets = {'person': person_widget}


@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    form = ContactPersonAdminForm
    readonly_fields = ('full_name',)

    class Media:
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
            'select2.min.js',
            'jquery.maskedinput.min.js',
            'notyf.min.js',
            'js_functions_for_admin.js',
            'admin/phone_field_select2_customization.js'
        )
        css = {'all': ('select2.min.css', 'notyf.min.css')}

    baton_form_includes = [
        ('root_app/phone_field_ajax_urls.html', 'phone', 'top',),
    ]


class PersonPhoneAdminForm(forms.ModelForm):
    class Meta:
        model = PersonPhone
        fields = '__all__'
        widgets = {'person': person_widget}


@admin.register(PersonPhone)
class PersonPhoneAdmin(admin.ModelAdmin):
    form = PersonPhoneAdminForm

    class Media:
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
            'select2.min.js',
            'jquery.maskedinput.min.js',
            'notyf.min.js',
            'js_functions_for_admin.js',
            'admin/phone_field_select2_customization.js'
        )
        css = {'all': ('select2.min.css', 'notyf.min.css')}

    baton_form_includes = [
        ('root_app/phone_field_ajax_urls.html', 'phone', 'top',),
    ]
