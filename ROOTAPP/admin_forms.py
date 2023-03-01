from django import forms
from django.core.exceptions import ValidationError


class PersonPhonesAdminFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                if form.cleaned_data['phone'] == self.instance.main_phone:
                    raise ValidationError('Нельзя отвязать номер указаный как номер для входа')

                if form.cleaned_data['phone'] == self.instance.delivery_phone:
                    raise ValidationError('Нельзя отвязать номер указаный как номер для доставки')