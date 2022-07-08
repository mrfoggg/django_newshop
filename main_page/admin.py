from adminsortable2.admin import SortableAdminMixin
from django import forms
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from mptt.admin import DraggableMPTTAdmin
from main_page.models import StaticPage, Menu, Banner, PopularCategory, PopularProduct, NewProduct
from django_svg_image_form_field import SvgAndImageFormField
from django_summernote.utils import get_attachment_model

admin.site.unregister(get_attachment_model())


class MenuAdminForm(forms.ModelForm):
    def clean(self):
        super(MenuAdminForm, self).clean()

        if self.cleaned_data['type_of_item'] == 1 and 'category' in self.cleaned_data.keys():
            if self.cleaned_data['category'] is None:
                raise forms.ValidationError('Выберите категорию на которую ссылается пункт меню')

        if self.cleaned_data['type_of_item'] == 2 and 'page' in self.cleaned_data.keys():
            if self.cleaned_data['page'] is None:
                raise forms.ValidationError('Выберите текстовую старницу на которую ссылается пункт меню')

        if self.cleaned_data['type_of_item'] == 3 and 'link' in self.cleaned_data.keys():
            if self.cleaned_data['link'] is None:
                raise forms.ValidationError('Укажите ссылку на которую указывает пункт меню')

    class Meta:
        model = Menu
        exclude = []
        field_classes = {
            'image': SvgAndImageFormField,
        }


@admin.register(Menu)
class MenuAdmin(DraggableMPTTAdmin):
    fields = ('title', 'type_of_item', 'parent', 'description', 'get_link', 'image')
    readonly_fields = ('get_link',)
    form = MenuAdminForm

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
