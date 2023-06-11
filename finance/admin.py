import nested_admin
from django.contrib import admin
from djmoney.models.fields import MoneyField
from dynamic_admin_forms.admin import DynamicModelAdminMixin

from ROOTAPP.admin_forms import DocumentForm
from ROOTAPP.models import PriceTypePersonBuyer
# Register your models here.
from catalog.models import ProductPrice, ProductSupplierPrice, ProductSupplierPriceInfo, ProductGroupPrice
from finance.admin_forms import money_widget_only_uah, ProductPriceChangelistInlineAdminForm
from finance.models import PriceChangelist, PriceTypePersonSupplier, Stock, \
    SupplierPriceChangelist, GroupPriceChangelist


class ProductPriceProductInline(nested_admin.NestedTabularInline):
    fields = ('price_changelist', 'price', 'is_active')
    # autocomplete_fields = ('product',)
    readonly_fields = ('is_active',)
    model = ProductPrice
    extra = 0

    # ordering = ('position',)

    @admin.display(description='Проведено')
    def is_active(self, obj):
        return obj.price_changelist.is_active


class ProductPricePriceChangelistInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    form = ProductPriceChangelistInlineAdminForm
    fields = ('product', 'full_current_price_info', 'price', 'margin', 'margin_percent', 'profitability',
              'supplier_price_variants', 'position')
    readonly_fields = ('full_current_price_info', 'margin', 'margin_percent', 'profitability')
    formfield_overrides = {
        MoneyField: {"widget": money_widget_only_uah},
    }
    model = ProductPrice
    extra = 0
    sortable_field_name = 'position'
    ordering = ('position',)
    autocomplete_fields = ('product',)


class ProductSupplierPriceChangelistInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    # formfield_overrides = {
    #     MoneyField: {"widget": money_widget_only_uah},
    # }
    model = ProductSupplierPrice
    extra = 0
    sortable_field_name = 'position'
    ordering = ('position',)
    autocomplete_fields = ('product',)


class ProductGroupPriceChangelistInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    # formfield_overrides = {
    #     MoneyField: {"widget": money_widget_only_uah},
    # }
    model = ProductGroupPrice
    extra = 0
    sortable_field_name = 'position'
    ordering = ('position',)
    autocomplete_fields = ('product',)


class PriceTypePersonBuyerInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = PriceTypePersonBuyer
    extra = 0
    sortable_field_name = 'position'


class PriceTypePersonSupplierInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = PriceTypePersonSupplier
    extra = 0
    sortable_field_name = 'position'


@admin.register(PriceChangelist)
class PriceChangelistAdmin(nested_admin.NestedModelAdmin, ):
    fields = (('created', 'updated', 'applied'), ('is_active', 'mark_to_delete'), 'comment')
    readonly_fields = ('created', 'updated', 'applied', 'is_active', 'mark_to_delete')
    list_display = ('__str__', 'is_active', 'mark_to_delete', 'comment')
    inlines = (ProductPricePriceChangelistInline,)

    change_form_template = 'admin/apply_buttons.html'

    class Media:
        css = {"all": (
            'admin/admin-changeform.css',
            'magnific_popup/magnific-popup.css',
            'jquery.datetimepicker.min.css')}
        js = (
            'notyf.min.js',
            'magnific_popup/jquery.magnific-popup.min.js',
            'jquery.datetimepicker.full.min.js', 'admin/apply_documents.js',
            'js_functions_for_admin.js', 'finance/price_list_admin_form.js',
            'admin/textarea-autoheight.js')

    def response_change(self, request, obj):
        apply_result = apply_documents(self, request, obj)
        if apply_result:
            return apply_result
        return super().response_change(request, obj)

    baton_form_includes = [
        ('finance/admin_pricelist_ajax_urls.html', 'created', 'top',),
    ]


@admin.register(SupplierPriceChangelist)
class SupplierPriceChangelistAdmin(DynamicModelAdminMixin, nested_admin.NestedModelAdmin):
    fields = (('created', 'updated', 'applied'), ('is_active', 'mark_to_delete'), ('person',), ('price_type',), 'comment')
    readonly_fields = ('created', 'updated', 'applied', 'is_active', 'mark_to_delete')
    dynamic_fields = ('price_type',)
    list_display = ('created', '__str__', 'is_active', 'comment')
    inlines = (ProductSupplierPriceChangelistInline,)

    change_form_template = 'admin/apply_buttons.html'

    class Media:
        css = {"all": (
            'admin/admin-changeform.css',
            'magnific_popup/magnific-popup.css',
            'jquery.datetimepicker.min.css')}
        js = (
            'admin/jq.js',
            'magnific_popup/jquery.magnific-popup.min.js',
            'jquery.datetimepicker.full.min.js', 'admin/apply_documents.js',
            'admin/textarea-autoheight.js')

    def response_change(self, request, obj):
        apply_result = apply_documents(self, request, obj)
        if apply_result:
            return apply_result
        return super().response_change(request, obj)

    def get_dynamic_price_type_field(self, data):
        # automatically choose first city that matches first letter of name
        supplier = data.get("person")
        if not supplier:
            queryset = PriceTypePersonSupplier.objects.all()
            value = queryset.first()
        else:
            queryset = PriceTypePersonSupplier.objects.filter(person=supplier)
            # value = queryset.first()
            value = data.get("price_type")
        hidden = not queryset.exists()
        return queryset, value, hidden


@admin.register(GroupPriceChangelist)
class GroupPriceChangelistAdmin(DynamicModelAdminMixin, nested_admin.NestedModelAdmin):
    form = DocumentForm
    fields = (('created', 'updated', 'applied'), ('is_active', 'mark_to_delete'), ('person',), ('price_type',), 'comment')

    readonly_fields = ('created', 'updated', 'applied', 'is_active', 'mark_to_delete')
    dynamic_fields = ('price_type',)
    list_display = ('created', '__str__', 'is_active', 'comment')

    inlines = (ProductGroupPriceChangelistInline,)

    change_form_template = 'admin/apply_buttons.html'

    class Media:
        css = {"all": (
            'admin/admin-changeform.css',
            'magnific_popup/magnific-popup.css',
            'jquery.datetimepicker.min.css')}
        js = (
            'admin/jq.js',
            'magnific_popup/jquery.magnific-popup.min.js',
            'jquery.datetimepicker.full.min.js', 'admin/apply_documents.js',
            'admin/textarea-autoheight.js')

    def response_change(self, request, obj):
        apply_result = apply_documents(self, request, obj)
        if apply_result:
            return apply_result
        return super().response_change(request, obj)

    def get_dynamic_price_type_field(self, data):
        # automatically choose first city that matches first letter of name
        buyer = data.get("person")
        if not buyer:
            queryset = PriceTypePersonBuyer.objects.all()
            value = queryset.first()
        else:
            queryset = PriceTypePersonBuyer.objects.filter(person=buyer)
            # value = queryset.first()
            value = data.get("price_type")
        hidden = not queryset.exists()
        return queryset, value, hidden


admin.site.register(PriceTypePersonBuyer)
admin.site.register(PriceTypePersonSupplier)
admin.site.register(Stock)
# admin.site.register(Arrival)
