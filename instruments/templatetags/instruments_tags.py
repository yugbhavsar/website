import datetime
import holidays

from dateutil.rrule import HOURLY, rrule

from django import template

from instruments.models import InstrumentPage, MethodPage, InstrumentByProjectBooking
from instruments.models import Method2InstrumentRelation as M2I

from rubion.utils import iso_to_gregorian

from userinput.models import RUBIONUser

register = template.Library()

@register.inclusion_tag(
    'tags/related_methods.html',
)
def related_methods( page ):
    methods = M2I.objects.filter( page = page )    
    return {
        'methods' : methods
    }

@register.inclusion_tag(
    'tags/booking_buttons.html',
    takes_context = True
)
def render_booking_buttons( context, page ):

    if context.request.user.is_anonymous:
        # anon users cannot book
        return {}

    if isinstance(page, InstrumentPage):
        # When page is an InstrumentPage, one can only book 
        # this instrument
        instruments = [ page ]
        is_instrument_page = True
    else:
        # page is a MethodPage, fetch the related instruments

        m2is = page.related.all()
        instruments = [m2i.page for m2i in m2is]
        is_instrument_page = False


    try:
        r_user = RUBIONUser.objects.get( linked_user = context.request.user )
    except RUBIONUser.DoesNotExist:
        r_user = None
    # Get all instruments connected to methods in Projects of the user's
    # workgroup. Slightly complicated task...

    # First, get all methods
    group_instruments = []
    if r_user:
        group_methods = r_user.get_workgroup().get_methods()

        if not is_instrument_page and page not in group_methods:
            return {}


        
        for method in group_methods:
            m2is = method.related.all()
            for m2i in m2is: 
                if m2i.page not in group_instruments:
                    group_instruments.append(m2i.page)

    direct = []
    apply_button = False

    if r_user:
        for instrument in instruments:
            if instrument.can_be_booked_by( r_user ):
                direct.append( instrument )
            elif instrument.is_bookable:
                apply_button = True
        
    context['is_instrument_page']= is_instrument_page
    context['instruments'] = group_instruments
    context['direct'] =  direct
    context['apply_button'] = apply_button
    return context

    
@register.inclusion_tag( 
    'tags/cal/week.html',
    takes_context = True 
)
def cal_week( context, year, week ):
#    context['page'] = page
    context['year'] = year
    context['week'] = week
    context['days'] = range(1,6)
    return context

@register.inclusion_tag( 
    'tags/cal/day.html',
    takes_context = True 
)
def cal_day( context, year, week, day ):
    context['day'] = day
    currdate = iso_to_gregorian(year, week, day)
    context['currdate'] = currdate
    context['is_past'] = currdate < datetime.date.today() 
    context['is_holiday'] = currdate in holidays.DE(prov = 'NW')


    first = datetime.datetime(
        currdate.year, currdate.month, 
        currdate.day, hour = 8, 
    )
    last = datetime.datetime(
        currdate.year, currdate.month, 
        currdate.day, hour = 17, 
    )
    unavailable = []
    hours = rrule(HOURLY, dtstart = first, until = last)
    for h in hours:
        if h in context['bookings']:
            unavailable.append(h.hour)
    context['unavailable'] = unavailable
    context['hours'] = range(8,18)
    return context
