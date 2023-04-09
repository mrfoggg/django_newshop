from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from django_summernote.utils import get_attachment_model
from mptt.admin import DraggableMPTTAdmin

from main_page.admin_form import BannerForm, MenuAdminForm
from main_page.models import (Banner, Menu, NewProduct, PopularCategory,
                              PopularProduct, Schedule, SitePhone, StaticPage)

admin.site.unregister(get_attachment_model())


@admin.register(SitePhone)
class PhoneAdmin(SortableAdminMixin, admin.ModelAdmin):
    fields = ('phone', 'get_chat_links')
    readonly_fields = ('get_chat_links',)
    list_display = ('phone', 'get_chat_links',)
    list_display_links = ('phone',)


@admin.register(Schedule)
class ScheduleAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('day', 'time_from', 'time_to',)
    list_display_links = ('day',)
    list_editable = ('time_from', 'time_to',)

    baton_cl_includes = [
        ('main-page/admin_schedule_include_top.html', 'top',),
    ]
    baton_form_includes = [
        ('main-page/admin_schedule_include_top.html', 'day', 'bottom',),
    ]


@admin.register(Menu)
class MenuAdmin(DraggableMPTTAdmin):
    fields = ('title', 'type_of_item',)
    readonly_fields = ('get_link',)
    # list_display = ('tree_actions', 'indented_title',)
    form = MenuAdminForm

    def get_fields(self, request, obj=None):
        if obj is not None:
            match obj.type_of_item:
                case 1:
                    return self.fields + ('category', 'parent', 'image', 'get_link')
                case 2:
                    return self.fields + ('page', 'parent', 'image', 'get_link')
                case 3:
                    return self.fields + ('link', 'parent', 'image', 'get_link')
                case 4:
                    return self.fields + ('parent', 'image')
        else:
            return self.fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs["queryset"] = Menu.objects.exclude(id=request.resolver_match.kwargs['object_id'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(StaticPage)
class StaticPageAdmin(SummernoteModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    summernote_fields = ('text',)


@admin.register(Banner)
class BannerAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = BannerForm
    list_display = ('title', 'date_from', 'date_to',)
    list_editable = ('date_from', 'date_to',)


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
