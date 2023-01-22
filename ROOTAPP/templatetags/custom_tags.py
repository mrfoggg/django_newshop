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


@register.filter
def strip_phone(phone):
    return phone[4:]


@register.filter
def bool_when_in(val, ls):
    return val in ls


@register.simple_tag
def val_if_eq(inp_val_1, inp_val_2, val):
    return val if inp_val_1 == inp_val_2 else ''


@register.simple_tag
def values_by_condition(condition, value_1, value_2=''):
    return value_1 if condition else value_2


@register.simple_tag
def hide_when_in(val, ls):
    return 'display: none;' if val in ls else ''


@register.simple_tag
def hide_when_not_in(val, ls):
    return '' if val in ls else 'display: none;'


@register.simple_tag
def val_when_in(val, ls, val_1, val_2=''):
    return val_1 if val in ls else val_2

# @register.filter
# def true_if_in(val, ls):
#     return True if val in ls else False
