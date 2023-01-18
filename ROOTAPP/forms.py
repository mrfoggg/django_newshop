from django import forms
from django.forms import modelform_factory
from django_select2.forms import ModelSelect2Widget

from ROOTAPP.models import Settlement, SettlementArea, Person
from django_select2 import forms as s2forms

from allauth.account.forms import ResetPasswordForm


# class MyCustomResetPasswordFor(ResetPasswordForm):
#     email = forms.EmailField(
#         label="e-mail адреса",
#         required=True,
#         initial='asd@df.ua',
#         widget=forms.TextInput(
#             attrs={
#                 "type": "email",
#                 "placeholder": "e-mail адр",
#                 "autocomplete": "email",
#             }
#         ),
#     )



class AddressForm(forms.Form):
    area = forms.ModelChoiceField(
        queryset=SettlementArea.objects.all(),
        label="Область",
        widget=ModelSelect2Widget(
            model=SettlementArea,
            search_fields=['description_ua__icontains', 'description_ru__icontains'],
            attrs={'data-placeholder': 'назва області'}
        )
    )

    settlement = forms.ModelChoiceField(
        queryset=Settlement.objects.all(),
        label="Населений пункт",
        widget=ModelSelect2Widget(
            model=Settlement,
            search_fields=('description_ua__icontains', 'description_ru__icontains'),
            dependent_fields={'area': 'area'},
            max_results=50,
            attrs={'data-placeholder': 'назва населеного пункту'}
        )
    )


PersonEmailForm = modelform_factory(
        Person,
        fields=('email',)
    )


class PersonForm(forms.ModelForm):
    contact_phone = forms.CharField(label="Номер телефону")
    first_name = forms.CharField(label='Прізвище')
    last_name = forms.CharField(label="Ім'я")
    middle_name = forms.CharField(label="По-батькові")
    email = forms.EmailField(label="Електронна пошта")
    class Meta:
        model = Person
        fields = ('first_name', 'last_name', 'middle_name', 'contact_phone', 'email')
        help_texts = {
            'first_name': "Обов'язкове", 'last_name': "Обов'язкове поле", 'middle_name': "Обов'язкове поле",
            'email': "Обов'язкове поле"
        }
