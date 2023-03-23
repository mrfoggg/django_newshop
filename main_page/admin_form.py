from django import forms
from django.forms.widgets import TextInput
from django_svg_image_form_field import SvgAndImageFormField

from main_page.models import Banner, Menu


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
        widgets = {
            'title': TextInput(attrs={'size': 60}),
        }


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = '__all__'
        widgets = {
            'title': TextInput(attrs={'size': 90}),
        }
