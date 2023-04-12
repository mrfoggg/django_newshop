from djmoney.forms import MoneyWidget
from django import forms

money_widget_only_uah = MoneyWidget(
    amount_widget=forms.TextInput(attrs={'size': 7, 'class': 'form-class'}),
    currency_widget=forms.Select(attrs={}, choices=[('UAH', 'UAH ₴')]),
)