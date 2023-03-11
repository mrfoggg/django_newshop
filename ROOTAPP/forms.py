from django import forms
from django.forms import modelform_factory
from django.forms.models import inlineformset_factory
from django_select2.forms import ModelSelect2Widget

from ROOTAPP.models import Settlement, SettlementArea, Person, Phone, PersonPhone, Warehouse, PersonAddress
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


# class FullAddressForm(forms.ModelForm):
#     area = forms.ModelChoiceField(
#         queryset=SettlementArea.objects.all(),
#         label="Область",
#         widget=ModelSelect2Widget(
#             model=SettlementArea,
#             search_fields=['description_ua__icontains', 'description_ru__icontains'],
#             attrs={'data-placeholder': 'назва області'}
#         )
#     )
#
#     settlement = forms.ModelChoiceField(
#         queryset=Settlement.objects.all(),
#         label="Населений пункт",
#         widget=ModelSelect2Widget(
#             model=Settlement,
#             search_fields=('description_ua__icontains', 'description_ru__icontains'),
#             dependent_fields={'area': 'area'},
#             max_results=50,
#             attrs={'data-placeholder': 'назва населеного пункту'}
#         )
#     )
#
#     warehouse = forms.ModelChoiceField(
#         queryset=Warehouse.objects.all(),
#         label="Отделение",
#         widget=ModelSelect2Widget(
#             model=Warehouse,
#             search_fields=('description_ua__icontains', 'description_ru__icontains'),
#             dependent_fields={'settlement': 'settlement'},
#             max_results=50,
#             attrs={'data-placeholder': 'отделение'}
#         )
#     )

area_widget = ModelSelect2Widget(
    model=SettlementArea,
    search_fields=['description_ua__icontains', 'description_ru__icontains'],
    attrs={'data-placeholder': 'назва області', 'style': 'width: 80%;',
           'data-minimum-input-length': '0'}
)

settlement_widget = ModelSelect2Widget(
    model=Settlement,
    search_fields=('description_ua__icontains', 'description_ru__icontains'),
    dependent_fields={'area': 'area'},
    max_results=50,
    attrs={'data-placeholder': 'назва населеного пункту', 'style': 'width: 80%;'}
)

warehouse_widget = ModelSelect2Widget(
    model=Warehouse,
    search_fields=('description_ua__icontains', 'description_ru__icontains'),
    dependent_fields={'settlement': 'settlement'},
    max_results=50,
    # minimum_results_for_search=1,
    attrs={'data-placeholder': 'отделение', 'style': 'width: 80%;',
           'data-minimum-input-length': '0'}
)


class FullAddressForm(forms.ModelForm):
    class Meta:
        model = PersonAddress
        exclude = []
        widgets = {
            'area': area_widget, 'settlement': settlement_widget,
            'warehouse': warehouse_widget
        }


# class SettlementSelectWidget(ModelSelect2Widget):
#     model = Settlement
#     search_fields = [
#         'description_ua__icontains',
#         'description_ru__icontains',
#     ]
#     max_results = 50


PersonEmailForm = modelform_factory(
    Person,
    fields=('email',)
)


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

# PersonInlineFormset = inlineformset_factory(Person, PersonPhone, fields=('phone', 'is_nova_poshta'))
