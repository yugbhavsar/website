from .admin_forms import CourseDescriptionChooserForm
from .models import (
    Course, CourseAttendee, StudentAttendee,
    SskStudentAttendee, SskExternalAttendee,
    SskHospitalAttendee, SskRubMemberAttendee,
    CourseParticipationValidation
)



from django.conf import settings
from django.http import HttpResponseNotAllowed, HttpResponse    
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import activate, ugettext as _
from django.views import View
from django.views.static import serve
import os
import uuid
import subprocess
import tempfile

from wagtail.contrib.modeladmin.views import ChooseParentView, InspectView
from wagtail.admin import messages

from website.models import EMailText

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



class ScriptView( InspectView ):
    def get( self, request ):
        next_section = None
        job = str(uuid.uuid4())
        fn = '{vardir}/{uuid}.tex'.format(
            vardir = settings.COURSE_LATEX_TEXFILE_DIR,
            uuid = job
        )
        with open(fn, 'w') as ltxfile:
            ltxfile.write('\\input{{{header}}}\n'.format(header = settings.COURSE_SCRIPT_HEADER))
            ltxfile.write('\\title{{{title}}}\n'.format(title=escape_latex(str(self.instance.script_title))))
            ltxfile.write('\subtitle{{{title}}}\n'.format(title=escape_latex(str(self.instance.script_subtitle1))))
            ltxfile.write('\moresubtitle{{{title}}}\n'.format(title=escape_latex(str(self.instance.script_subtitle2))))
            if self.instance.script_date == 'n':
                # no date
                dt = ''
            if self.instance.script_date == 'e':
                lang = 'en'
                dtf = 'E d^^{S}, Y'
            if self.instance.script_date == 'd':
                #german date
                lang = 'de'
                dtf = 'd. E Y'

            if self.instance.script_date in ['e','d']:
                activate(lang)
                dt = date_format(self.instance.start, format=dtf).replace('^^','\\textsuperscript')
                if self.instance.end:
                    dt = dt + '--{}'.format(date_format(self.instance.end, format=dtf).replace('^^','\\textsuperscript'))
                
            ltxfile.write('\\date{{{dt}}}\n'.format(dt = dt))
            ltxfile.write('\\begin{document}\n')
            ltxfile.write('\\thispagestyle{empty}\n')
            ltxfile.write('\\maketitle\n')
            ltxfile.write('\\tableofcontents\n')
            for i in self.instance.script:
                if i.block.name == 'chapter':
                    ltxfile.write('\\chapter{{{chapname}}}\n'.format(chapname=escape_latex(str(i))))
                if i.block.name == 'section':
                    next_section = escape_latex(str(i))
                if i.block.name=='file':
                    filename = '{mediaroot}/{fn}'.format(
                        fn = str(i.value.file),
                        mediaroot = settings.MEDIA_ROOT
                    )
                
                    if next_section is None:
                        ltxfile.write('\\InsertPDF{{{fname}}}'.format(fname=filename))
                    else:
                        ltxfile.write('\\InsertPDF[{section}]{{{fname}}}'.format(
                            section = next_section,
                            fname = filename)
                        )

                        next_section = None
                    ltxfile.write('\n')
            ltxfile.write('\\end{document}')
        jobname = '-jobname={pdffiledir}/{jobname}'.format(
            pdffiledir = settings.COURSE_LATEX_PDFFILE_DIR,
            jobname = job
        )
        result = subprocess.run(['lualatex', jobname, fn ])
        if result.returncode == 0:
            subprocess.run(['lualatex', jobname, fn])

            if settings.DEBUG:
                return serve(request, '{job}.pdf'.format(job=job), settings.COURSE_LATEX_PDFFILE_DIR)
            else:
                response = HttpResponse()
                response['X-Sendfile'] = '{d}{fn}.pdf'.format(
                    d = settings.COURSE_LATEX_PDFFILE_URI,
                    fn = job
                )
                response['Content-Length'] = os.stat('{d}/{fn}.pdf'.format(
                    d = settings.COURSE_LATEX_PDFFILE_DIR,
                    fn = job
                )).st_size
                response['Content-Type'] = 'application/pdf'
        else:
            return HttpResponse('Error generating the script file', status = 500)

##
# tiny helper function to avoid bad input
# people could use latex commands to read or overwrite /etc/password or similar.
# this (hopefully) avoids it
# @param s The string to escape
# @return the escaped string 
def escape_latex(s): 
    return  (
        s
        .replace('\\','\\textbackslash ')
        .replace('#','\\#')
        .replace('^','\\textasciicircum ')
        .replace('$','\\$')
        .replace('%','\\%')
        .replace('&','\\&')
        .replace('_','\\_')
        .replace('{','\\{')
        .replace('}','\\}')
        .replace('~','\\textasciitilde ')
    )
    
