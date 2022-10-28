from django import forms
from django.contrib import admin

# Register your models here.
from ROOTAPP.models import Person
from .models import ByOneclick, ByOneclickComment


class ByOneclickCommentAdminInline(admin.TabularInline):
    model = ByOneclickComment
    extra = 1


class ByOneclickAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact'].queryset = Person.objects.filter(personphone__phone=self.instance.phone)


@admin.register(ByOneclick)
class ByOneclickAdmin(admin.ModelAdmin):
    form = ByOneclickAdminForm

    fields = (
        ('product', 'price',),
        ('phone',),
        ('created', 'updated'),
        ('contact', 'this_number_contacts'),
        ('status', 'extend_status'),
    )
    list_display = ('id', 'created', 'phone', 'is_active', 'status', 'product', 'this_number_contacts')
    list_editable = ('is_active', 'status')
    list_display_links = ('created', 'phone')
    readonly_fields = ('phone', 'created', 'updated', 'this_number_contacts', 'price')
    inlines = (ByOneclickCommentAdminInline, )

# admin.site.register(ByOneclick)
