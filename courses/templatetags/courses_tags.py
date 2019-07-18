import datetime
import importlib

from courses.wagtail_hooks import SskStudentAttendeeMA
from courses.models import CourseAttendee


from dateutil.relativedelta import relativedelta
def minus_one_week():
    return datetime.date.today() - relativedelta(weeks = 1)


from django import template



register = template.Library()

@register.inclusion_tag(
    'tags/next_dates.html'
)
def render_next_dates( page ):
    children = page.get_upcoming_courses()
    return {
        'page' : page,
        'children' : children
    }

@register.simple_tag()
def get_n_attendees( at, course ):
    return get_attendees_by_type(at, course).count()

@register.simple_tag()
def get_n_attendees_waitlist( at, course ):
    return get_waitlist_by_type(at, course).filter(is_validated = True).count()

@register.simple_tag()
def get_n_waitlist( course ):
    return CourseAttendee.objects.filter(
        waitlist_course = course,
        is_validated = True
    ).count()

@register.simple_tag()
def get_n_confirmed_attendees( at, course, payed = None ):
    qs = get_attendees_by_type(at, course).filter(is_validated = True)
    if payed is None:
        return qs.count()
    if payed is True:
        if at.price and hasattr(at, 'amount'):
            try:
                a = qs.filter(amount__isnull = True).count()
            except FieldError:
                a = 0
            try:
                b = qs.filter(amount = 0).count()
            except FieldError:
                b = 0
            try:
                c = qs.filter(amount__gt = 0, payed = True).count()
            except FieldError:
                c = 0
            return a+b+c
        else:
            return qs.count()
    if payed is False:
        if at.price and hasattr(at, 'amount'):
            return qs.filter(amount__gt = 0, payed = False).count()
        else:
            return 0


@register.simple_tag()
def get_n_recent_unconfirmed_attendees_waitlist(at, course ):
    return (
        get_waitlist_by_type(at, course).filter(
            is_validated = False,
            add2course_mail_sent = True,
            add2course_mail_sent_at__gte = minus_one_week()
        ).count()
    )
    # TODO!


@register.simple_tag()
def get_n_recent_unconfirmed_attendees( at, course ):
    return (
        get_attendees_by_type(at, course).
        filter(
            is_validated = False,
            validation_mail_sent = True,
            validation_mail_sent_at__gte = minus_one_week()
        ).count()
    )

@register.simple_tag()
def get_n_total_recent_unconfirmed( course ):
    return (
        CourseAttendee.objects.
        filter(
            related_course = course,
            is_validated = False,
            validation_mail_sent = True,
            validation_mail_sent_at__gte = minus_one_week()
        ).count()
    )

@register.simple_tag()
def get_n_total_confirmed( course, payed = None ):
    n = 0
    for at in course.get_attendee_types().all():
        n = n + get_n_confirmed_attendees( at, course, payed )
    return n


@register.simple_tag()
def get_n_expired_unconfirmed_attendees( at, course ):
    return (
        get_attendees_by_type(at, course).
        filter(
            is_validated = False,
            validation_mail_sent = True,
            validation_mail_sent_at__lt = minus_one_week()
        ).count()
    )
@register.simple_tag()
def get_n_expired_unconfirmed( course ):
    return (
        CourseAttendee.objects.
        filter(
            related_course = course,
            is_validated = False,
            validation_mail_sent = True,
            validation_mail_sent_at__lt = minus_one_week()
        ).count()
    )

@register.simple_tag()
def get_attendees_by_type( at, course ):
    Kls = at.get_attendee_class()
    return Kls.objects.filter( related_course = course )

def get_waitlist_by_type( at, course ):
    Kls = at.get_attendee_class()
    return Kls.objects.filter( waitlist_course = course )

@register.simple_tag()
def get_value(obj, field):
    return getattr(obj,field)

@register.inclusion_tag(
    'tags/courses/specific_attendee_list.html',
    takes_context = True
)
def specific_attendee_list( context, at, instance ):
    additional_fields = []
    additional_fields_title = []
    if hasattr(at.get_attendee_class(), 'additional_admin_fields'):
        for f in at.get_attendee_class().additional_admin_fields:
            additional_fields.append(f[0])
            additional_fields_title.append(f[1])
            

    context.update({
        'has_attendees' : get_n_attendees(at, instance) > 0,
        'attendees' : get_attendees_by_type(at, instance),
        'has_waitlist' : at.waitlist,
        'waitlist' : get_waitlist_by_type( at, instance),
        'additional_fields' : additional_fields,
        'additional_fields_title' : additional_fields_title,
    })
    return context

@register.inclusion_tag(
    'tags/courses/attendee_in_list.html',
    takes_context = True
)
def attendee_in_list( context, course, Attendee ):
    return {
        'available' : course.get_free_slots(Attendee.get_attendee_class()) > 0,
        'waitlist' : course.has_waitlist_for(Attendee.get_attendee_class()),
        'type' : Attendee,
        'page' : course,
        'request' : context['request']
    }

@register.inclusion_tag(
    'tags/courses/attendee_buttons.html',
    takes_context = True
)
def attendee_buttons( context, attendee ):
    module = importlib.import_module('courses.wagtail_hooks')
    MA = getattr(module, "{}MA".format(attendee.__class__.__name__))
    
    ma = MA()
    BH = ma.get_button_helper_class()
    bh = BH(context['view'] , context['request'], modeladmin = ma )
    if attendee.related_course == context['instance'] :
        btns = bh.get_buttons_for_obj(
            attendee, 
            classnames_add=['button-small button-secondary'],
            exclude = ['delete_from_waitlist', 'add_to_course']
        )
    else:
        if attendee.add2course_mail_sent:
            exclude = ['delete', 'add_to_course']
        else:
            exclude = ['delete']
        btns = bh.get_buttons_for_obj(
            attendee, 
            classnames_add=['button-small button-secondary'],
            exclude = exclude
        )

    context.update({'buttons' : btns })   
    return context

