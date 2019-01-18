from .admin_forms import CourseDescriptionChooserForm
from .models import (
    Course, CourseAttendee, StudentAttendee,
    SskStudentAttendee, SskExternalAttendee,
    SskHospitalAttendee, SskRubMemberAttendee,
    CourseParticipationValidation
)

from website.models import EMailText

from django.http import HttpResponseNotAllowed#, JsonResponse, HttpResponse    
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views import View


from wagtail.contrib.modeladmin.views import ChooseParentView, InspectView
from wagtail.admin import messages

class AddCourseChooseCourseInfoView( ChooseParentView ):
    def get_context_data( self, *args, **kwargs ):
        context = super(AddCourseChooseCourseInfoView, self).get_context_data(*args, **kwargs)
        context['parent_name'] = _('Course')
        context['introduction'] = _('Create a date for which course?')
        return context

    def get_form(self, request):
        parents = self.permission_helper.get_valid_parent_pages(request.user)
        return CourseDescriptionChooserForm(parents, request.POST or None)

class CourseDateInspectView( InspectView ):
    class Media:
        css = {
            'all': ('admin/courses/course-inspect.css',)
        }
        
    def get( self, request, *args, **kwargs ):
        if self.instance.is_fully_booked:
            messages.warning(request, _('This course is fully booked.'))
        return super().get(request, *args, **kwargs)

    def get_page_title(self):
        return self.instance.get_parent().specific.get_admin_display_title()

    def get_context_data(self, *args, **kwargs):
        context = super(InspectView, self).get_context_data(**kwargs)
        context.update(kwargs)
        return context


class AttendeeCourseView( View ):
    def dispatch(self, request, *args, **kwargs):
        attendee_id = args[0]
        course_id = args[1]

        self.course = Course.objects.get(id = course_id)
        self.attendee = CourseAttendee.objects.get(id = attendee_id)

        if request.GET.get('next', None):
            self.next = request.GET['next']
        else:
            self.next = reverse('wagtailadmin_home')
        

        return super(AttendeeCourseView, self).dispatch(request, *args, **kwargs) 

class AddToCourseView( AttendeeCourseView ):
    def get( self, request, *args, **kwargs ):
        #self.attendee.related_course = self.course
        #self.attendee.waitlist_course = None
        self.attendee.is_validated = False
        self.attendee.add2course_mail_sent = True
        self.attendee.add2course_mail_sent_at = timezone.now()
        self.attendee.save()

        validation = CourseParticipationValidation(
            attendee = self.attendee
        )
        validation.save()
        mail = EMailText.objects.get(identifier = 'courses.user_added_to_course')
        mail.send(
            self.attendee.email, 
            { 
                "attendee" : self.attendee,
                "course"   : self.course,
                "agree_url" : self.request.build_absolute_uri(
                    reverse('manage-courses:agree_add2course', kwargs={'uuid':validation.uuid})
                ),
                "reject_url" : self.request.build_absolute_uri(
                    reverse('manage-courses:reject_add2course', kwargs={'uuid':validation.uuid})
                )
            }
        )
        
        messages.success(
            request, 
            _('A confirmation e-mail has been sent to %s.' %  self.attendee.full_name)
        )

        return redirect(self.next)
 
class HasPayedView( AttendeeCourseView ):
    def get( self, request, *args, **kwargs ):

        All_atts = [
            StudentAttendee, SskStudentAttendee, SskExternalAttendee,
            SskHospitalAttendee, SskRubMemberAttendee
        ]
        attendee = None
        for Att in All_atts:
            qs = Att.objects.filter(courseattendee_ptr = self.attendee.id)
            if qs.exists():
                attendee = qs.first()
                break
            

        if attendee and hasattr(attendee, 'payed'):
            attendee.payed = True
            attendee.save()
            messages.success(request, _('The status of %s has been changed.' % attendee.full_name ))
        else:
            return HttpResponseNotAllowed

        return redirect(self.next)


