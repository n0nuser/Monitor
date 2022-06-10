from django import template
from json import loads

register = template.Library()


@register.filter()
def field_name_to_label(value):
    value = value.replace("_", " ")
    return value.capitalize()


@register.filter()
def typeof(value):
    return str(type(value))


@register.filter()
def todict(value):
    try:
        value = value.replace("\'", "\"")
        return loads(value)
    except Exception:
        return value
