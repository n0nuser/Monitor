from django import template
from json import loads

register = template.Library()


@register.filter()
def field_name_to_label(value):
    return value.replace("_", " ").capitalize()


@register.filter()
def typeof(value):
    return str(type(value))


@register.filter()
def todict(value):
    try:
        return loads(value.replace("'", '"'))
    except Exception:
        return value
