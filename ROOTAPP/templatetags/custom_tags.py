from django import template
import phonenumbers

register = template.Library()


@register.filter
def phone_national(value):
    """Removes all values of arg from the given string"""
    phone = phonenumbers.format_number(value, phonenumbers.PhoneNumberFormat.NATIONAL)
    return f"({phone[0:3]}) {phone[4:7]} {phone[8:10]} {phone[10:]}"
