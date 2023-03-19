from django import forms
from django.forms.models import modelform_factory

from ROOTAPP.models import Person, PersonAddress
from nova_poshta.forms import warehouse_widget, settlement_widget, area_widget


class PersonForm(forms.ModelForm):
    # main_phone = forms.CharField(label="Номер телефону")
    first_name = forms.CharField(label='Прізвище')
    last_name = forms.CharField(label="Ім'я")
    middle_name = forms.CharField(label="По-батькові")
    email = forms.EmailField(label="Електронна пошта")

    class Meta:
        model = Person
        fields = ('first_name', 'last_name', 'middle_name', 'main_phone', 'email')
        help_texts = {
            'first_name': "Обов'язкове", 'last_name': "Обов'язкове поле", 'middle_name': "Обов'язкове поле",
            'email': "Обов'язкове поле"
        }


PersonEmailForm = modelform_factory(
    Person,
    fields=('email',)
)


class PersonalInfoForm(forms.ModelForm):
    last_name = forms.CharField(label='Прізвище', widget=forms.TextInput(attrs={'placeholder': "Обов'язкове поле", }))
    first_name = forms.CharField(label="Ім'я", widget=forms.TextInput(attrs={'placeholder': "Обов'язкове поле", }))
    middle_name = forms.CharField(label="По-батькові", required=False)

    def clean(self):
        self.cleaned_data = super(PersonalInfoForm, self).clean()
        self.cleaned_data['first_name'] = self.cleaned_data['first_name'].title()
        self.cleaned_data['last_name'] = self.cleaned_data['last_name'].title()
        self.cleaned_data['middle_name'] = self.cleaned_data['middle_name'].title()
        # self.instance.first_name = 'My'
        return self.cleaned_data

    class Meta:
        model = Person
        fields = ('last_name', 'first_name', 'middle_name',)


class FullAddressForm(forms.ModelForm):
    class Meta:
        model = PersonAddress
        exclude = []
        widgets = {
            'area': area_widget, 'settlement': settlement_widget,
            'warehouse': warehouse_widget
        }