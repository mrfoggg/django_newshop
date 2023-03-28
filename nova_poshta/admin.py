from django.contrib import admin

from nova_poshta.forms import SettlementForm, CityForm
from nova_poshta.models import City, Settlement, Warehouse, Street


class WarehouseForSettlementInline(admin.TabularInline):
    model = Warehouse
    extra = 0
    fields = ('number', 'type_warehouse', 'description_ru', 'warehouse_status', 'deny_to_select', 'place_max_weight',
              'total_max_weight', 'map_link')
    # 'total_max_weight')
    readonly_fields = ('map_link',)
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False


class StreetForCityInline(admin.TabularInline):
    model = Street
    extra = 0
    # fields = ('number', 'type_warehouse', 'description_ru', 'warehouse_status', 'deny_to_select', 'place_max_weight',
    #           'total_max_weight', 'map_link')
    # readonly_fields = ('map_link',)
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    fields = [x.name for x in Settlement._meta.fields]
    list_display = ('description_ru', 'description_ua', 'type', 'area', 'region', 'warehouse')
    list_display_links = ('description_ru', 'description_ua')
    list_filter = ('area__description_ru', 'warehouse')
    baton_cl_includes = [
        ('nova_poshta/button_update_settlements.html', 'top',),
    ]
    search_fields = ('description_ru', 'description_ua', 'index_1')
    inlines = (WarehouseForSettlementInline,)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        if obj is not None:
            return self.fields + ['map_link']
        return self.fields


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    # fields = (
    #     'type', 'description_ru', 'description_ua', 'area', 'city_id', 'is_branch', 'prevent_entry_new_streets_user'
    # )
    list_display = ('description_ru', 'description_ua', 'type', 'area',)
    list_display_links = ('description_ru', 'description_ua')
    list_filter = ('area__description_ru',)
    baton_cl_includes = [
        ('nova_poshta/button_update_cities.html', 'top',),
    ]
    search_fields = ('description_ru', 'description_ua',)
    inlines = (WarehouseForSettlementInline, StreetForCityInline)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    fields = [x.name for x in Warehouse._meta.fields]
    baton_cl_includes = [
        ('nova_poshta/admin_update_warehouses.html', 'top',),
    ]

    autocomplete_fields = ('settlement',)
    list_filter = ('type_warehouse',)
    list_display = ('stl_descr_ru', 'settlement', 'city', '__str__',)
    search_fields = ('description_ua', 'settlement__description_ua', 'settlement__description_ru')
    ordering = ('settlement', 'number')
    list_display_links = ('__str__',)

    def changelist_view(self, request, extra_context=None):
        # extra_context = extra_context or {}
        extra_context = {'settlement_form': SettlementForm}
        return super().changelist_view(
            request, extra_context=extra_context,
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        if obj is not None:
            return self.fields + ['map_link']
        return self.fields

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'select2.min.js',)

        css = {
            "all": ("select2.min.css",)}


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    baton_cl_includes = [
        ('nova_poshta/admin_update_streets.html', 'top',),
    ]

    autocomplete_fields = ('city',)
    list_display = ('city', '__str__',)
    search_fields = ('description_ua', 'city__description_ua', 'city__description_ru')
    ordering = ('city', 'description_ua')
    list_display_links = ('__str__',)

    def changelist_view(self, request, extra_context=None):
        extra_context = {'city_form': CityForm}
        return super().changelist_view(
            request, extra_context=extra_context,
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    class Media:
        js = ('https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              'select2.min.js',)

        css = {
            "all": ("select2.min.css",)}
