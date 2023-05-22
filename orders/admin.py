import nested_admin
from django import forms
from django.contrib import admin
from django.db import models
from djmoney.forms import MoneyField
from ROOTAPP.models import Person, Phone
from finance.admin_forms import money_widget_only_uah
from .admin_form import ClientOrderAdminForm, ProductInClientOrderAdminInlineForm
from .models import (BY_ONECLICK_STATUSES_CLIENT_DISPLAY, ByOneclick,
                     ByOneclickPersonalComment, OneClickUserSectionComment, ClientOrder, SupplierOrder, Realization,
                     ProductInOrder)


class ByOneclickCommentAdminInline(admin.TabularInline):
    model = ByOneclickPersonalComment
    extra = 1
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': '1'})}
    }


class OneClickUserSectionCommentInline(admin.TabularInline):
    model = OneClickUserSectionComment
    readonly_fields = ('comment_type', 'description', 'created')
    extra = 0
    max_num = 0


class ProductInClientOrder(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    form = ProductInClientOrderAdminInlineForm
    fields = ('product', 'full_current_price_info', 'current_group_price', 'sale_price',
              'group_price',
              'quantity', 'sale_total', 'margin', 'margin_total',
              'margin_percent', 'profitability',
              'supplier_order', 'supplier_price_variants',
              'purchase_price', 'client_order_position', 'purchase_total')
    readonly_fields = (
        'full_current_price_info', 'sale_total', 'purchase_total', 'margin', 'margin_total', 'margin_percent',
        'profitability', 'current_group_price'
    )
    model = ProductInOrder
    extra = 0
    # autocomplete_fields = ('product', 'supplier_order')
    sortable_field_name = 'client_order_position'
    verbose_name = 'Товар в заказе'
    verbose_name_plural = 'Товары в заказе'

    def formfield_for_dbfield(self, db_field, **kwargs):
        # This method will turn all TextFields into giant TextFields
        if db_field.name == 'quantity':
            return forms.CharField(widget=forms.widgets.NumberInput(attrs={'size': 4, }), initial=1)
        if db_field.name in ('sale_price', 'purchase_price'):
            return MoneyField(widget=money_widget_only_uah)
        return super().formfield_for_dbfield(db_field, **kwargs)

    # для отображения только активных товаров
    # def get_search_results(self, request, queryset, search_term):
    #     print('GET_SEARCH_RESULTS')
    #     queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term, )
    #     print('search_term -', search_term)
    #     if 'model_name' in request.GET.keys():
    #         print('MODEL_NAME - ', request.GET['model_name'])
    #         if request.GET['model_name'] == 'productinorder':
    #             queryset = queryset.filter(is_active=True, mark_to_delete=False)
    #     return queryset, may_have_duplicates


class ProductInSupplierOrder(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    # adminsortable2 требует fields именно списком
    fields = ('product', 'purchase_price', 'quantity', 'client_order', 'supplier_order_position')
    model = ProductInOrder
    extra = 2
    autocomplete_fields = ('product', 'client_order')
    sortable_field_name = 'supplier_order_position'
    verbose_name = 'Товар в заказе'
    verbose_name_plural = 'Товары в заказе'


class ByOneclickAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['person'].queryset = Person.objects.filter(phones__phone=self.instance.phone)

    def clean(self):
        if 'status' in self.changed_data:
            new_user_comment = OneClickUserSectionComment(
                order=self.instance, comment_type=1,
                description=BY_ONECLICK_STATUSES_CLIENT_DISPLAY[self.cleaned_data["status"]])
            new_user_comment.save()
            self.instance.is_active = False if self.cleaned_data['status'] in [4, 5, 7] else True
        self.save()


@admin.register(ByOneclick)
class ByOneclickAdmin(admin.ModelAdmin):
    form = ByOneclickAdminForm

    fields = (
        ('product', 'price',),
        ('phone', 'is_active'),
        ('created', 'updated'),
        ('person', 'this_number_contacts'),
        ('status', 'extend_status'),
        ('session_key', 'this_session_oneclicks'),
        'user_ip_info'
    )
    list_display = ('id', 'created', 'phone', 'is_active', 'status', 'product', 'this_number_contacts')
    list_display_links = ('created', 'phone')
    readonly_fields = ('phone', 'created', 'updated', 'this_number_contacts', 'price', 'is_active', 'session_key',
                       'this_session_oneclicks', 'user_ip_info')
    inlines = (ByOneclickCommentAdminInline, OneClickUserSectionCommentInline)

    class Media:
        js = ('admin/textarea-autoheight.js',)
        css = {
            "all": ('admin/order-admin-changeform.css',)
        }


@admin.register(ClientOrder)
class ClientOrderAdmin(nested_admin.NestedModelAdmin, admin.ModelAdmin):
    form = ClientOrderAdminForm
    fieldsets = (
        (
            'Основное',
            {'fields': (
                ('id', 'created', 'updated', 'is_active', 'mark_to_delete', ),
                ('status', 'extend_status'), ('source', 'payment_type'),
            )},
        ),
        (
            'Контактная информация',
            {'fields': (
                ('person', 'incoming_phone',),
            )}
        ),
        (
            'Опт',
            {'fields': (
                ('dropper', 'group_price_type',),
            )}
        ),
        (
            'Доставка',
            {'fields': (
                ('address',), ('contact_person', 'delivery_phone')
            )}
        ),
        (
            'Итого по заказу',
            {'fields': (
                ('total_quantity', 'total_amount', 'total_purchase_amount','total_margin'),
            )}
        ),
    )
    readonly_fields = ('id', 'created', 'updated', 'total_quantity', 'total_amount', 'total_purchase_amount',
                       'total_margin')
    list_display = ('id', 'is_active', 'mark_to_delete', 'status', 'payment_type', 'source', '__str__',
                    'contact_person', 'dropper')
    list_display_links = ('__str__',)
    list_editable = ('status', 'is_active', 'mark_to_delete')
    autocomplete_fields = (
        # 'person',
                           # 'incoming_phone'
                           )
    search_fields = ('person__full_name',)
    inlines = (ProductInClientOrder,)

    class Media:
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
            # "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/js/select2.min.js",
            #   'select2.min.js',
            'notyf.min.js',
            'js_functions_for_admin.js', 'order/client_order_admin_form.js',
            'admin/phone_field_select2_customization.js', 'admin/person_field_select2_customization.js')
        css = {'all': ('admin/price_field.css', 'admin/admin-changeform.css', 'select2.min.css', 'notyf.min.css',
                       'order/order-admin-changeform.css')}

    # для отображения только активных товаров
    def get_search_results(self, request, queryset, search_term):
        print('GET_SEARCH_RESULTS')
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term, )
        print('search_term -', search_term)
        if 'model_name' in request.GET.keys():
            print('MODEL_NAME - ', request.GET['model_name'])
            if request.GET['model_name'] == 'productinorder':
                queryset = queryset.filter(is_active=True, mark_to_delete=False)
        return queryset, may_have_duplicates

    def get_form(self, request, obj=None, **kwargs):
        self._request_method = request.method
        self._curent_phone_ = obj.incoming_phone if obj else None
        self._curent_person_ = obj.person if obj else None
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if hasattr(self, '_request_method'):
            phone = self._curent_phone_ if hasattr(self, '_curent_phone_') else None
            person = self._curent_person_ if hasattr(self, '_curent_person_') else None
            if db_field.name == "incoming_phone" and self._request_method == 'GET':
                kwargs["queryset"] = Phone.objects.filter(id=phone.id) if phone else Phone.objects.none()
            if db_field.name == "person" and self._request_method == 'GET':
                kwargs["queryset"] = Person.objects.filter(id=person.id) if person else Person.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    baton_form_includes = [
        ('order/admin_order_ajax_urls.html', 'id', 'top',),
        ('admin/include_select2.html', 'id', 'top',),
        ('order/person_phones.html', 'person', 'bottom',),
        ('order/founded_persons.html', 'incoming_phone', 'bottom',),
    ]


@admin.register(SupplierOrder)
class SupplierOrderAdmin(nested_admin.NestedModelAdmin, admin.ModelAdmin):
    fields = (
        ('id', 'is_active', 'mark_to_delete', 'status',),
        ('person', 'price_type'), 'comment'
    )
    readonly_fields = ('id', 'created', 'updated')
    list_display = ('id', 'is_active', 'mark_to_delete', 'status', '__str__')
    list_display_links = ('__str__',)
    list_editable = ('status', 'is_active', 'mark_to_delete')
    search_fields = ('person__last_name',)
    inlines = (ProductInSupplierOrder,)

    class Media:
        js = ('admin/textarea-autoheight.js',)
        css = {
            "all": ('admin/order-admin-changeform.css',)
        }

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'person':
            kwargs["queryset"] = Person.objects.filter(is_supplier=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_search_results(self, request, queryset, search_term):
        print('GET_SEARCH_RESULTS')
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term, )
        if 'model_name' in request.GET.keys():
            if request.GET['model_name'] == 'productinorder':
                queryset = queryset.filter(is_active=True, mark_to_delete=False)
        return queryset, may_have_duplicates


@admin.register(Realization)
class RealizationAdmin(admin.ModelAdmin):
    fields = (
        ('id', 'is_active', 'mark_to_delete', 'status',),
    )
    readonly_fields = ('id', 'created', 'updated')
    list_display = ('id', 'is_active', 'mark_to_delete', 'status', '__str__')
    list_display_links = ('__str__',)
    list_editable = ('status', 'is_active', 'mark_to_delete')
