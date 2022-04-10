from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from mptt.admin import DraggableMPTTAdmin

from main_page.models import StaticPage, Menu

import nested_admin


@admin.register(Menu)
class MenuAdmin(DraggableMPTTAdmin):
    fields = ('title', 'type_of_item', 'parent', 'description')

    def get_fields(self, request, obj=None):
        if obj is not None:
            match obj.type_of_item:
                case 1:
                    return self.fields + ('category',)
                case 2:
                    return self.fields + ('page',)
                case 3:
                    return self.fields + ('url',)
        else:
            return self.fields


@admin.register(StaticPage)
class StaticPageAdmin(SummernoteModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    summernote_fields = ('text', )
