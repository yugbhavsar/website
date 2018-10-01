from django import template
register = template.Library()

@register.filter
def keyvalue(form, key):    
    return form[key]

