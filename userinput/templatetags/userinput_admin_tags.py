from django import template
from userinput.models import RUBIONUser
register = template.Library()

@register.simple_tag(  ) 
def get_previous_revision( page ): 
    curr = page.revisions.order_by('-created_at').first()
    prev = curr.get_previous()
    return prev.as_page_object()

@register.filter(name='radiation_safety_data_complete')
def radiation_safety_data_complete( user ):
    return user.date_of_birth and user.place_of_birth 

@register.simple_tag(takes_context = True)
def official_dosemeter( context ):
    user = context['user']
    print("user: {}".format(user.__dict__))
    return user.dosemeter == user.OFFICIAL_DOSEMETER

@register.simple_tag()
def dosemeter_short( dosemeter ):
    try:
        return RUBIONUser.DOSEMETER_SHORT_NAMES[dosemeter]
    except KeyError:
        return RUBIONUser.DOSEMETER_SHORT_NAMES[dosemeter[0]]

@register.filter(name = "first_item")
def first_item( l ):
    return l[0]

@register.filter(name = "may_change_dosemeter")
def may_change_dosemeter( user, ruser ):
    return ruser.permissions_for_user(user).can_edit()
