import nested_admin
from django.contrib import admin

# Register your models here.
from catalog.models import ProductPrice
from finance.models import PriceChangelist


class ProductPriceProductInline(nested_admin.NestedTabularInline):
    fields = ('price_changelist', 'price')
    # autocomplete_fields = ('product',)
    # readonly_fields = ('price',)
    model = ProductPrice
    extra = 0
    # ordering = ('position',)


class ProductPricePriceChangelistInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = ProductPrice
    extra = 3
    sortable_field_name = 'position'
    ordering = ('position',)
    autocomplete_fields = ('product',)


@admin.register(PriceChangelist)
class PriceChangelistAdmin(nested_admin.NestedModelAdmin, ):
    fields = ('confirmed_date', 'confirmed')
    inlines = (ProductPricePriceChangelistInline,)

# admin.site.register(ProductPrice)
