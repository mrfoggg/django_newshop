import nested_admin
from django.contrib import admin
from djmoney.models.fields import MoneyField

# Register your models here.
from catalog.models import ProductPrice
from finance.admin_forms import money_widget_only_uah
from finance.models import PriceChangelist, PriceTypePersonBuyer, PriceTypePersonSupplier, Stock, \
    SupplierPriceChangelist


class ProductPriceProductInline(nested_admin.NestedTabularInline):
    fields = ('price_changelist', 'price')
    # autocomplete_fields = ('product',)
    # readonly_fields = ('price',)
    model = ProductPrice
    extra = 0
    # ordering = ('position',)


class ProductPricePriceChangelistInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    formfield_overrides = {
        MoneyField: {"widget": money_widget_only_uah},
    }
    model = ProductPrice
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
    fields = (('created', 'updated', 'is_active', 'mark_to_delete'), 'comment')
    readonly_fields = ('created', 'updated')
    inlines = (ProductPricePriceChangelistInline,)

    class Media:
        css = {"all": ('admin/textarea-autoheight.css',)}
        js = ('admin/textarea-autoheight.js',)


@admin.register(SupplierPriceChangelist)
class SupplierPriceChangelistAdmin(admin.ModelAdmin):
    fields = (('created', 'updated', 'is_active', 'mark_to_delete', 'price_type'), 'comment')
    readonly_fields = ('created', 'updated')

    class Media:
        css = {"all": ('admin/textarea-autoheight.css',)}
        js = ('admin/textarea-autoheight.js',)


admin.site.register(PriceTypePersonBuyer)
admin.site.register(PriceTypePersonSupplier)
admin.site.register(Stock)
