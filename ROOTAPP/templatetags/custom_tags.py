from django import template
import phonenumbers

register = template.Library()


@register.filter
def phone_national(value):
    """Removes all values of arg from the given string"""
    phone = phonenumbers.format_number(value, phonenumbers.PhoneNumberFormat.NATIONAL)
    return f"({phone[0:3]}) {phone[4:7]} {phone[8:10]} {phone[10:]}"


@register.filter
def get_attr_str_value(product, attribute):
    return product.get_attr_string_val(attribute)


@register.simple_tag
def values_by_condition(condition, value_1, value_2=''):
    return value_1 if condition else value_2
