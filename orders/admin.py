import nested_admin
from django import forms
from django.contrib import admin
from django.db import models
from ROOTAPP.models import Person, PersonPhone
from .admin_form import ClientOrderAdminForm

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
    fields = ('product', 'full_current_price_info', 'sale_price', 'quantity', 'sale_total', 'margin', 'margin_total',
              'margin_percent', 'profitability',
              'supplier_order',
              'purchase_price', 'client_order_position', 'purchase_total')
    readonly_fields = (
        'full_current_price_info', 'sale_total', 'purchase_total', 'margin', 'margin_total', 'margin_percent',
        'profitability'
    )
    model = ProductInOrder
    extra = 0
    autocomplete_fields = ('product', 'supplier_order')
    sortable_field_name = 'client_order_position'
    verbose_name = 'Товар в заказе'
    verbose_name_plural = 'Товары в заказе'

    def formfield_for_dbfield(self, db_field, **kwargs):
        # This method will turn all TextFields into giant TextFields
        if db_field.name == 'quantity':
            return forms.CharField(widget=forms.widgets.TextInput(attrs={'size': 4, }))
        return super().formfield_for_dbfield(db_field, **kwargs)


class ProductInSupplierOrder(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    # adminsortable2 требует fields именно списком
    fields = ('product', 'purchase_price', 'quantity', 'client_order', 'supplier_order_position')
    model = ProductInOrder
    extra = 0
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
            "all": ('admin/textarea-autoheight.css',)
        }


@admin.register(ClientOrder)
class ClientOrderAdmin(nested_admin.NestedModelAdmin, admin.ModelAdmin):
    form = ClientOrderAdminForm
    fields = (
        ('id', 'is_active', 'mark_to_delete', 'status', 'extend_status'),
        ('source', 'payment_type', 'created', 'updated'),
        'person', 'address'
    )
    readonly_fields = ('id', 'created', 'updated')
    list_display = ('id', 'is_active', 'mark_to_delete', 'status', 'payment_type', 'source', '__str__')
    list_display_links = ('__str__',)
    list_editable = ('status', 'is_active', 'mark_to_delete')
    autocomplete_fields = ('person',)
    search_fields = ('person__last_name',)
    inlines = (ProductInClientOrder,)

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'select2.min.js', 'notyf.min.js',
              'root_app/person_address_admin_form.js')
        css = {'all': ('admin/price_field.css',)}

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term, )
        if 'model_name' in request.GET.keys():
            print('MODEL_NAME - ', request.GET['model_name'])
            if request.GET['model_name'] == 'productinorder':
                queryset = queryset.filter(is_active=True, mark_to_delete=False)
        return queryset, may_have_duplicates


@admin.register(SupplierOrder)
class SupplierOrderAdmin(nested_admin.NestedModelAdmin, admin.ModelAdmin):
    fields = (
        ('id', 'is_active', 'mark_to_delete', 'status',),
        'person', 'comment'
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
            "all": ('admin/textarea-autoheight.css',)
        }

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'person':
            kwargs["queryset"] = Person.objects.filter(is_supplier=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_search_results(self, request, queryset, search_term):
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
