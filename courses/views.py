from .models import CourseParticipationValidation

from django.shortcuts import render, get_object_or_404, redirect

def agree_add2course( request, uuid ):
    validation = get_object_or_404(CourseParticipationValidation, uuid = uuid)
    old_course = validation.attendee.related_course
    course = validation.attendee.waitlist_course
    validation.attendee.waitlist_course = None
    validation.attendee.related_course = course
    validation.attendee.save()
    validation.uuid = None
    validation.save()    
    return render (
        request,
        'courses/added2course.html',
        {
            'course' : course,
            'old_course': old_course,
            'page' : course
        }
    )

def reject_add2course( request, uuid ):
    validation = get_object_or_404(CourseParticipationValidation, uuid = uuid)
    wl_course = validation.attendee.waitlist_course
    validation.attendee.waitlist_course = None
    validation.attendee.save()
    validation.uuid = None
    validation.save()    

    if wl_course.fill_automatically:
        # Send mail to the next person on waitlist...
        AttKls = validation.attendee.__class__
        waitlist = AttKls.objects.filter(
            waitlist_course = wl_course,
            add2course_mail_sent = False
        ).order_by('created_at')
        

    return render (
        request,
        'courses/added2course_reject.html',
        {
            'page' : wl_course,
            'wl_course' : wl_course,
            'course': validation.attendee.related_course
        }
    )


def validate_course_registration ( request, uuid ):
    validation = get_object_or_404(CourseParticipationValidation, uuid = uuid)
    attendee = validation.attendee

    attendee.is_validated = True

    course = attendee.related_course

    attendee.save()
    
    validation.uuid = None
    validation.save()
    return redirect(course.url + course.reverse_subpage('success', args=[attendee.id] ))
    
    
def register_course_success( request, attendee ):
    pass
