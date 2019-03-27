from django import template
from django.template.defaultfilters import date
from django.utils import translation

register = template.Library()

@register.filter('datelang')
def date_in_language( val, arg = None ):
    if not arg:
        return date(val)
    lang, fmt= arg.split('|', 2)
    with translation.override(lang):
        dt = date(val, fmt)
    return dt
    
