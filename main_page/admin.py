from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from mptt.admin import DraggableMPTTAdmin
from main_page.models import StaticPage, Menu, Banner, PopularCategory, PopularProduct, NewProduct


@admin.register(Menu)
class MenuAdmin(DraggableMPTTAdmin):
    fields = ('title', 'type_of_item', 'parent', 'description', 'get_link')
    readonly_fields = ('get_link',)

    def get_fields(self, request, obj=None):
        if obj is not None:
            match obj.type_of_item:
                case 1:
                    return self.fields + ('category',)
                case 2:
                    return self.fields + ('page',)
                case 3:
                    return self.fields + ('link',)
                case 4:
                    return self.fields
        else:
            return self.fields


@admin.register(StaticPage)
class StaticPageAdmin(SummernoteModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    summernote_fields = ('text',)


@admin.register(Banner)
class BannerAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'date_from', 'date_to', 'position')
    list_editable = ('date_from', 'date_to', 'position')


@admin.register(PopularCategory)
class PopularCategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('category', 'date_from', 'date_to', 'position')
    list_editable = ('date_from', 'date_to', 'position')


@admin.register(PopularProduct)
class PopularProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('product', 'date_from', 'date_to', 'position')
    list_editable = ('date_from', 'date_to', 'position')


@admin.register(NewProduct)
class NewProductAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('product', 'date_from', 'date_to', 'position')
    list_editable = ('date_from', 'date_to', 'position')
