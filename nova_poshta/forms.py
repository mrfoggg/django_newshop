from allauth.account.forms import ResetPasswordForm
from django import forms
from django_select2.forms import ModelSelect2Widget

from nova_poshta.models import Settlement, SettlementArea, Warehouse


# from django_select2 import forms as s2forms


# class MyCustomResetPasswordForm(ResetPasswordForm):
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


class SettlementForm(forms.Form):
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


# class SettlementSelectWidget(ModelSelect2Widget):
#     model = Settlement
#     search_fields = [
#         'description_ua__icontains',
#         'description_ru__icontains',
#     ]
#     max_results = 50

# PersonInlineFormset = inlineformset_factory(Person, PersonPhone, fields=('phone', 'is_nova_poshta'))
