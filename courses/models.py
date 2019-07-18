'''
This set of models implements the courses organized by and held in RUBION. 

Furthermore, it contains models for different attendees. The latter is a bit complex 
since a lot of different attendees exist.

Attendees are *not* implemented as Pages since they only show up in the admin.
'''

from .attendees import register_attendee, get_attendee_class, ATTENDEE_TYPES

from .pdfhandling import RUBIONCourseInvoice
from .widgets  import AttendeeSelectWidget

import datetime

from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.db import models
from django.forms import modelform_factory, ModelForm, FileField
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify, format_lazy 
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l

import importlib
import json

from modelcluster.fields import ParentalKey

import random 

from rubauth.auth import LDAPBackend, fetch_user_info


from ugc.models import UserGeneratedPage2
from userdata.mixins import AbstractContactPerson

import uuid 


# This is required for a constant containing academic titles. 
# Might be better to put this somewhere else
from userinput.models import RUBIONUser


from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.contrib.settings.models import BaseSetting, register_setting

from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel, MultiFieldPanel, InlinePanel,
    TabbedInterface, ObjectList, StreamFieldPanel
)
from wagtail.core.fields import RichTextField
from wagtail.core.models import Orderable, PageViewRestriction
from wagtail.documents.models import get_document_model
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.snippets.models import register_snippet


from website.models import (
    TranslatedPage, MandatoryIntroductionMixin,
    BodyMixin, OptionalIntroductionMixin,
    EMailText, ChildMixin, ImportantPages
)


# This should for sure go somewhere else

class PHJsonEncoder( json.JSONEncoder ):
    def default( self, obj ):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super(PHJsonEncoder, self).default(obj)


class CourseInformationPage( TranslatedPage, MandatoryIntroductionMixin, BodyMixin, ChildMixin ):
    '''
    A general model for a course.
    '''
    
    subpage_types = [ 'courses.Course' ]
    parent_page_types = ['courses.ListOfCoursesPage']
    class Meta:
        verbose_name = _('Definition of a course')

    # ID in the courses register
    course_id = models.CharField(
        max_length = 64,
        blank = True
    )

    register_via_website = models.BooleanField(
        default = False
    )
    
    share_data_via_website = models.BooleanField(
        default = False
    )

    max_attendees = models.IntegerField(
        blank = True,
        null = True,
        default = None
    )

    information_list = models.BooleanField(
        default = False,
        help_text= _('Is there a list that stores people intereted in this course if no course date is available?')
    )

    content_panels_de = [
        FieldPanel('title_de'),
        StreamFieldPanel('introduction_de'),
        StreamFieldPanel('body_de'),
    ]
    content_panels_en = [
        FieldPanel('title'),
        StreamFieldPanel('introduction_en'),
        StreamFieldPanel('body_en'),
    ]
    additional_information_panel = [
        FieldPanel('course_id'),
        InlinePanel('contact_persons', label = _( 'Contact persons' ) )
    ]
    settings_panel = [
        FieldPanel('information_list'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('register_via_website'),
                FieldPanel('share_data_via_website'),
            ]),
        ], heading = _('Registration options')),
        FieldPanel('max_attendees'),
        InlinePanel('attendee_types', label = _('allowed attendees')) 
    ]
    
    edit_handler = TabbedInterface([
        ObjectList(content_panels_de, heading = _('Content (de)')),
        ObjectList(content_panels_en, heading = _('Content (en)')),
        ObjectList(additional_information_panel, heading = _('Additional information')),
        ObjectList(settings_panel, heading = _('Settings')),
    ])

    def get_upcoming_courses( self ):
        children = Course.objects.live().child_of(self).filter( start__gt = datetime.date.today() )
        return children
   
        

    def get_admin_display_title( self ):
        return self.title_trans
class CourseContactPerson( AbstractContactPerson ):
    page = ParentalKey( CourseInformationPage, related_name ='contact_persons')

    
class Course( RoutablePageMixin, TranslatedPage, BodyMixin  ):
    class Meta:
        verbose_name = _('Course date')

    parent_page_types = [ CourseInformationPage ]

    start = models.DateField(
        verbose_name = _('start date')
    )
    end = models.DateField(
        blank = True,
        null = True,
        verbose_name = _('end date'),
        help_text = _('leave empty for a one-day course')
    )

    overrule_parent = models.BooleanField(
        default = False,
        verbose_name = _('Overrule standard settings')
    )
    register_via_website = models.BooleanField(
        default = False,
        verbose_name = _('Registration via website')
    )
    
    share_data_via_website = models.BooleanField(
        default = False,
        verbose_name = _('Share data via website')
    )

    max_attendees = models.IntegerField(
        blank = True,
        null = True,
        default = None,
        verbose_name = _('Max attendees')
    )

    fill_automatically = models.BooleanField(
        default = False,
        help_text = _('Fill with attendees from waitlist automatically?')
    )

    content_panels = [
        FieldRowPanel([
            FieldPanel('start'),
            FieldPanel('end')
        ]),
        StreamFieldPanel('body_en'),
        StreamFieldPanel('body_de'),
    ]

    settings_panels = [
        FieldPanel('overrule_parent'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('register_via_website'),
                FieldPanel('share_data_via_website'),
            ]),
        ], heading = _('Registration options')),
        FieldPanel('max_attendees'),
        InlinePanel('attendee_types', label = _('allowed attendees')) 
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading = _('Date and info') ),
        ObjectList(settings_panels, heading = _('Overrule parent settings') ),
    ])


    def clean( self ):
        self.title = '{}–{}'.format(self.start, self.end)
        self.title_de = self.title
        if not self.slug:
            self.slug = self._get_autogenerated_slug( slugify( self.title ) ) 

    def _get_me_or_parent( self ):
        if self.overrule_parent:
            return self
        else:
            return self.get_parent().specific

    @property
    def is_bookable( self ):
        return self._get_me_or_parent().register_via_website 

    def started_in_past( self ):
        return self.start <= datetime.date.today()

    def get_attendee_types( self ):
        return self._get_me_or_parent().attendee_types
    def get_max_attendees( self ):
        return self._get_me_or_parent().max_attendees

    @property
    def has_data_sharing( self ):
        return self._get_me_or_parent().share_data_via_website

    def get_price( self, attendee ):
        
        for at_rel in self.get_attendee_types().all():
            if at_rel.get_attendee_class() == attendee:
                return at_rel.price
        return 0
    
    def has_waitlist_for( self, attendee):
        return self.get_attendee_types().filter(attendee = attendee.identifier, waitlist = True).count() > 0
    

    @property
    def registered_attendees_stats( self ):
        '''
        Returns an overview of the the registered attendees
        '''
        attendees = {}
        
        for atype in self.get_attendee_types().all():
            Klass = atype.get_attendee_class()
            try:
                disp = Klass.display_name_plural
            except AttributeError:
                disp = Klass.display_name

            # The total number of attendees for one attendee-type 
            # is the sum of
            #
            # a) those who are validated

            qs = Klass.objects.filter(related_course = self)
            num = qs.filter(is_validated = True).count()

            # b) those who are not yet validated, but the 
            # mail asking for validation has been sent within the last week

            minus_one_week = datetime.date.today() - relativedelta(weeks=1)

            num = num + qs.filter(
                is_validated = False,
                validation_mail_sent = True,
                validation_mail_sent_at__gte = minus_one_week).count()

            # c) People from the waitlist that have been asked to
            # attend this course, but have not yet answered and the
            # mail was sent within the last week

            num = num + Klass.objects.filter(
                waitlist_course = self,
                add2course_mail_sent = True,
                add2course_mail_sent_at__gte = minus_one_week
            ).count()


            # This is just in case that two or more attendee types have the 
            # same display name. Should not happen! It might be better
            # to solve this by something like:
            # { 'unique' : ('display', num) }
            #
            # (see method get_free_slots below)
            c = 0
            while disp in attendees:
                c += 1
                disp = "{}_{}".format(disp, c)


            attendees[disp] = num
        return attendees

    def get_free_slots( self, Attendee ):
        stats = self.registered_attendees_stats

        # we need idx to be a unique index. 
        try:
            idx = Attendee.display_name_plural
        except AttributeError:
            idx = Attendee.display_name
            
        try:
            n_attendees = stats[idx]
        except KeyError:
            # if idx is not in stats, this Attendee type is not allowed 
            # for this course. Thus, free slots is 0
            return 0
         
        # get max_attendees for this attendee-type, if exists
            
        limit_type = (
            self.get_attendee_types()
            .get(attendee = Attendee.identifier).max_attendees
        )
        if limit_type is not None:
            attendee_free = limit_type - n_attendees
            if attendee_free < 0:
                # might happen during testing or if someone adds an attendee 
                # manually
                attendee_free = 0
        else:
            attendee_free = None

        limit_total = self.get_max_attendees()
        

        # compute total number of attendees
        total_attendees = 0
        for k,v in stats.items():
            total_attendees = total_attendees + v
        
        total_free = limit_total - total_attendees
        if total_free < 0:
            # see above...
            total_free = 0

        # Very import to test for None, since 0 is interpreted as False...
        if attendee_free is not None:
            return min(total_free, attendee_free)
        else:
            return total_free


    def get_n_attendees( self ):
        c = 0
        for k,v in self.registered_attendees_stats.items():
            c = c + v

        return c
            
    @property
    def is_fully_booked( self ):
        return self.get_n_attendees() >= self.get_max_attendees()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # test whether there are any free slots in this course

        n_attendees = 0
        
        for k,v in self.registered_attendees_stats.items():
            n_attendees = n_attendees + v
            
        if self.get_max_attendees():
            if self.get_max_attendees() <= n_attendees:
                context['fully_booked'] = True
            else:
                context['fully_booked'] = False
        # test if we have a waitlist for any allowed attendee type
        # and no slots left for the type...
        free_courses = {}
        for a2c_rel in self.get_attendee_types().all().filter(waitlist = True):
            if self.get_free_slots(a2c_rel.get_attendee_class()) == 0:

                # Do we have another course, not fully booked, for that attendee type?

                upcoming_courses = self.get_parent().specific.get_upcoming_courses().exclude(id = self.id)
                for uc in upcoming_courses:
                    if uc.specific.get_free_slots(a2c_rel.get_attendee_class()) > 0:
                        if not a2c_rel.get_attendee_class().display_name_plural in free_courses.keys():
                            free_courses[a2c_rel.get_attendee_class().display_name_plural] = []
                        free_courses[a2c_rel.get_attendee_class().display_name_plural].append(uc)

        if free_courses:
            context['show_waitlist_info'] = True
            context['free_courses'] = free_courses

        return context


    @route(r'^register/(\w+)/$', name = "register")
    @route(r'^register/(\w+)/(\d+)/$', name = "register")
    def register_for_course( self, request, attendee, form_count = 0 ):
        # implements a multi-step form for registration.
        # The forms are provided by `forms` list of the corresponding attendee class.

        # get the form count
        form_count = int(form_count)

        # if a form has been filled is stored in request.session.form<number>
        # Avoid that a form is shown before the previous has been filled:
        if form_count > 0:
            if not request.session.get('form{}_filled'.format(form_count - 1)):
                return redirect( self.url + self.reverse_subpage('register', args=[attendee, form_count-1]))
           
        
        # get the attende by the "register_attendee" mechanism and raise a 404 if not known
        Attendee = get_attendee_class ( attendee )

        if not Attendee:
            raise Http404

            

        # IF THE COURSE IS IN THE PAST, RAISE A 404
        
        if self.start <= datetime.date.today():
            raise Http404


        # @TODO: Test if attendee is allowed for this course

        
        # collect all form classes...
        forms = []
        for f in Attendee.forms:
            module_name, class_name = f.rsplit(".", 1)
            module = importlib.import_module(module_name)
            FormKlass = getattr(module, class_name)
            forms.append(FormKlass)

        # Check if there are earlier courses that have a waitlist for this Attendee class

        waitlist_available = False
        previous_courses = self.get_parent().specific.get_upcoming_courses().filter(start__lt = self.start).order_by('-start')
        for pc in previous_courses.all():
            if pc.get_free_slots(Attendee) == 0  and pc.get_attendee_types().filter(waitlist=True, attendee = Attendee.identifier).count() > 0:
                waitlist_available = True
                waitlist_course = pc
                break

        


        # and if there is one, add the respective form class in the second last position
        # but only, if this regsitration is for the course, and not for the waitlist of this course
        has_waitlist = self.has_waitlist_for(Attendee) 
        free_slots = self.get_free_slots(Attendee)
        uses_waitlist = has_waitlist and free_slots < 1
        if uses_waitlist:
            waitlist_available = False
        if waitlist_available:
            from .forms import WaitlistForm
            last_form = forms[-1]
            forms[-1] = WaitlistForm
            forms.append(last_form)

        # ... and get the current one
        try:
            CurrentFormKlass = forms[form_count]
        except KeyError:
            raise Http404


        kwargs = {}
        
        # there might be some values passed from the previous form 
        provided_values = request.session.get('provided_values{}'.format(form_count - 1), None)

        if provided_values:
            kwargs['provided_values'] = provided_values


        print ('Form count is: {}'.format(form_count))
        if waitlist_available and form_count == len(forms)-2:
            kwargs['course'] = pc
        
        # now the usual stuff
        if request.method == 'GET':
            
            # @TODO. 
            # This code might be executed if someone clicks on the "step indicator"
            # try to fill it with the already collected data...
            if request.session.get('form{}_filled'.format(form_count), None):
                data_json = request.session.get('cleaned_data', None)
                if data_json:
                    data = json.loads( data_json )
                else:
                    data = {}
                kwargs['initial'] = data
            else:
                if provided_values:
                    kwargs['initial'] = provided_values
                    
            form = CurrentFormKlass(**kwargs)


        if request.method == 'POST':
            form = CurrentFormKlass(request.POST, **kwargs)

            if form.is_valid():          
                if hasattr(form, 'is_validated'):
                    cleaned_data={'is_validated' : True}
                else:
                    cleaned_data={}

                # Get the json for the data from the session
                data_json = request.session.get('cleaned_data', None)
                if data_json:
                    cleaned_data.update(json.loads( data_json ))

                if issubclass(CurrentFormKlass, ModelForm) or (waitlist_available and form_count == len(forms)-2):
                    for key, value in form.cleaned_data.items():
                        cleaned_data[key] = value
                 
                    
                else:
                    try:
                        request.session['provided_values{}'.format(form_count)] = form.provided_values
                    except AttributeError:
                        request.session['provided_values{}'.format(form_count)] = {}


                request.session['form{}_filled'.format(form_count)] = True
                request.session['cleaned_data'] = json.dumps(cleaned_data, cls=PHJsonEncoder)
                request.session.modified = True

                if form_count < len(forms) - 1:
                    messages.info( request, format_lazy(
                        'Your data for step {} has been saved. Please proceed with step {}.',
                        form_count+1, form_count+2))
                    return redirect(self.url + self.reverse_subpage('register', args=[attendee, form_count+1]))
                else:
                    instance = form.save( commit = False )
                    for key, value in cleaned_data.items():
                        if key == 'waitlist' and waitlist_available:
                            setattr( instance, 'waitlist_course', pc )
                        else:
                            setattr( instance, key, value )

                    # Attendees that have to pay have the amount of the fee and the 
                    # amount already payed in the database. We need to provide values here...
                    if hasattr(instance, 'amount'):
                        instance.amount = self.get_price(Attendee)
                    if hasattr(instance, 'payed'):
                        instance.payed = False

                    instance.related_course = self
                    if self.get_free_slots( Attendee ) > 0:
                        instance.save()
                        if not instance.is_validated:
                            return redirect(self.url + self.reverse_subpage('validation_mail', args=[instance.courseattendee_ptr_id] ))
                        else:
                            return redirect(self.url + self.reverse_subpage('success', args=[instance.courseattendee_ptr_id] ))
                    elif has_waitlist:
                        instance.waitlist_course = self
                        instance.related_course = None
                        instance.save()
                        messages.info(request, _('You were put on the waiting list.'))
                        if not instance.is_validated:
                            return redirect(self.url + self.reverse_subpage('validation_mail', args=[instance.courseattendee_ptr_id] ))
                        else:
                            return redirect(self.url + self.reverse_subpage('success', args=[instance.courseattendee_ptr_id] ))         
                    else:
                        messages.error(request, _('The course is fully booked. You have not been registered.'))
                        messages.info(request, _('We have not stored your data.'))
                        try:
                            del request.session['cleaned_data']
                        except KeyError:
                            pass
                        return redirect(self.url)
                    
        price = self.get_price(Attendee)
        show_price_hint = price > 0 and form_count == len(forms) - 1


        return TemplateResponse(
            request,
            'courses/register.html',
            {
                'attendee'     : attendee,
                'attendee_name': Attendee.display_name,
                'forms'        : forms,
                'current_form' : form_count,
                'form'         : form, 
                'page'         : self,
                'price'        : price,
                'show_price_hint' : show_price_hint,
                'free_slots' : free_slots,
                'has_waitlist': has_waitlist
            }
        )

    @route(r'^success/(\d+)/$', name = "success")
    def success( self, request, attendee_id ):
        
        attendee = get_object_or_404(CourseAttendee, id = attendee_id )
        if attendee.confirmation_mail_sent:
            raise Http404

        mailtext = EMailText.objects.get(identifier = 'courses.registration.confirmation')
        mailtext.send(
            attendee.email,
            {
                'attendee' : attendee,
                'course' : self
            }
        )
        self.send_invoice(attendee)
        try:
            del request.session['cleaned_data']
        except KeyError:
            pass
        return TemplateResponse(
            request,
            'courses/success.html',
            {
                'page'         : self
            }
        )

    @route(r'^validation_required/(\d+)/$', name="validation_mail")
    def validation_mail(self, request, attendee_id ):
        attendee = get_object_or_404(CourseAttendee, id = attendee_id )

        validation = CourseParticipationValidation()
        validation.attendee = attendee
        validation.save()

        now = datetime.datetime.now()

        attendee.validation_mail_sent = True
        attendee.validation_mail_sent_at = now
        attendee.save()

        valid_until = now + relativedelta(weeks=+1)
        
        if valid_until.date() >= self.start:
            valid_until = self.start + relativedelta(days=-2)
        
        mailtext = EMailText.objects.get(identifier = 'courses.registration.validation')
        mailtext.send(
            attendee.email,
            {
                'attendee' : attendee,
                'course' : self,
                'validation_url' : request.build_absolute_uri(
                    reverse('manage-courses:validate_course_registration', kwargs={'uuid' : validation.uuid})
                ),
                'validation' : validation,
                'valid_until' : valid_until
            }
        )
        try:
            del request.session['cleaned_data']
        except KeyError:
            pass
        return TemplateResponse(
            request,
            'courses/validation_mail.html',
            {
                'page'         : self,
                'valid_until' : valid_until,
                'attendee' : attendee
            }
        )

    def send_invoice(self, attendee):

        # get the specific course attendee object
        for Kls in ATTENDEE_TYPES:
            try: 
                s_att = Kls.objects.get( courseattendee_ptr_id = attendee.id )
                break
            except Kls.DoesNotExist:
                pass

        attendee = s_att
        try:   
            if attendee.amount == 0:
                return
        except AttributeError:
            return

        parent = self.get_parent().specific
        staff_mails = [staff.person.email for staff in parent.contact_persons.all()]        
        
        pdffile = RUBIONCourseInvoice(
            attendee,
            parent.contact_persons.first().person,
        )
        pdffilename = pdffile.write2file()

        mailtext = EMailText.objects.get(identifier = 'courses.staff.invoice_copy')
        mailtext.send(
            staff_mails,
            {
                'course' : self,
                'attendee' : attendee,
                'invoice_was_sent' : False
            },
            attachements = [ pdffilename ],
            lang = 'de'
        )

        # Should mails be sent automatically or manually?
        # I guess we said manually, at least in the beginning.
        
        #MAILTEXT = EMailText.objects.get(identifier = 'courses.attendee.invoice' ) 
        #mailtext.send(
        #    attendee.email,
        #    {
        #        'attendee': attendee,
        #        'course' : self
        #    }
        #)

    def get_data_sharing_page( self ):
        if DataSharingPage.objects.child_of(self).exists():
            return DataSharingPage.objects.child_of(self).first()
        else:
            return None

    def save( self, *args, **kwargs ):
        super(Course, self).save(*args, **kwargs)

        if self.has_data_sharing:
            if not self.get_data_sharing_page():
                dsp = DataSharingPage()
                dsp.clean()
                self.add_child(dsp)
                characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_*?!$&"
                pvr = PageViewRestriction(
                    page = dsp,
                    restriction_type = PageViewRestriction.PASSWORD,
                    password = "".join(random.choice(characters) for __ in range(10))
                )
                pvr.save()

        
class CourseAttendee ( models.Model ):
    '''
    This model contains the "minimum" of data
    that is needed for an attendee.

    This is the same information that we collect for 
    RUBION users. Might be better to put this in an abstract
    "Person" class...

    This class is not(!) abstract.
    '''

    # we need a name and an email-address
        
    last_name = models.CharField(
        max_length = 128,
        verbose_name = _l('last name')
    )

    first_name = models.CharField(
        max_length = 128,
        verbose_name = _l('first name')
    )

    email = models.CharField(
        max_length = 128,
        verbose_name = _l('e-mail address')
    )

   
    # Since we are in germany, academic titles are important!
    # We have defined them already...

    academic_title = models.CharField(
        max_length = 1,
        choices = RUBIONUser.ACADEMIC_TITLES,
        blank = True,
        null = True
    )

    # this is the courses the attendee wants to attend. 
    # Don't make it too complicated: We have a simple one2one-relation
    # here.
    related_course = models.ForeignKey(
        Course,
        blank = True,
        null = True,
        related_name = 'attendees',
        on_delete = models.PROTECT
        
    )

    # It might, however, happen, that people are additionally on a wait list
    waitlist_course = models.ForeignKey( 
        Course,
        blank = True,
        null = True,
        related_name = 'waitlist',
        on_delete = models.PROTECT
    )

    # This stores whether any verification
    # has been performed by the attendee.
    is_validated = models.BooleanField(
        default = False,
        help_text = _('Is the attendee validated?')
    )
    
    internal_rubion_comment = RichTextField(
        blank = True
    )

    created_at = models.DateTimeField(
        auto_now_add = True
    )

    add2course_mail_sent = models.BooleanField(
        default = False,
        help_text = _('E-Mail for adding this attendee to the course from the wait list sent?'),
        verbose_name = _('Mail sent?')
    )

    add2course_mail_sent_at = models.DateTimeField(
        blank = True,
        null = True,
        help_text=_('When was the mail sent?')
    )

    validation_mail_sent = models.BooleanField(
        default = False,
    )

    validation_mail_sent_at = models.DateTimeField(
        blank = True,
        null = True,
        help_text=_('When was the validation mail sent?')
    )

    confirmation_mail_sent = models.BooleanField(
        default = False,
    )
    confirmation_mail_sent_at = models.DateTimeField(
        blank = True,
        null = True,
        help_text=_('When was the confirmation mail sent?')
    )
    
    
    # A method that validates the object and saves it.
    #
    # Saving can be omitted by passing False to the 
    # respective parameter
    
    def validate( self, save = True ):
        self.is_validated = True        
        if save:
            self.save()
            
    # A property that retrieves the full name of the attendee,
    # including academic title

    @property
    def full_name( self ):
        title_format = ""
        if self.academic_title in [ 
                RUBIONUser.PHD, 
                RUBIONUser.MD, 
                RUBIONUser.PROF 
        ]:
            title_format = "{} ".format( self.get_academic_title_display() )

        return title_format+"{} {}".format(self.first_name, self.last_name)

    def __str__( self ):
        try:
            return "{} ({} am {})".format(
                self.full_name,
                self.related_course.get_parent(),
                self.related_course.start)
        except AttributeError:
            return "{}".format(self.full_name)
class AbstractRUBAttendee ( CourseAttendee ):
    '''
    A RUB member can identify by RUB-ID and RUB-password. Data can be 
    auto-filled by this.
    
    This class is abstract.
    '''

    class Meta:
        abstract = True

    def _auto_fill( self, rub_id ):
        '''
        This method is meant to be private.
        We can retireve information from the RUB database
        without the password of the user. However, the corresponding
        information should not be released to the public. Thus, use this
        only after authentification.
        '''
        information = fetch_user_info ( rub_id )
        self.last_name = information['last_name']
        self.first_name = information['first_name']
        self.email = information['email']
        return information


    def auto_fill( self, rub_id, rub_pwd ):
        '''
        Method should be fed with id and pwd of a RUB member.

        returns whether authentification worked.
        '''
        if LDAPBackend.ldap_authenticate( rub_id, rub_pwd ):
            self.validate( save = False )
            self._auto_fill( rub_id )
            return True

        return False


class AbstractStudentAttendee( AbstractRUBAttendee ):
    '''
    For students, we need some additional information. I assume
    that all students are from the RUB.

    This class is abstract.
    '''

    class Meta:
        abstract = True

    def _auto_fill ( self, rub_id ):
        information = super(AbstractStudentAttendee, self)._auto_fill( rub_id )
        self.student_id = information['student_id']

    student_id = models.BigIntegerField()

    student_course = models.CharField(
        max_length = 128
    )

    
# The above classes are sufficient to define a Attendee for, f.e, 
# the english radiation safety course.

class StudentAttendee( AbstractStudentAttendee ):
    # All definitions are made.
    # Just some information for selecting this attendee

    identifier = 'student'
    display_name = _l('Student')
    display_name_plural = _l('Students')
    forms = ['courses.forms.RUBIDForm', 'courses.forms.StudentForm']

    class Meta:
        verbose_name = _l('student, no additional information')

register_attendee( StudentAttendee )

class AbstractCertificateInformationMixin( models.Model ):
    '''
    We need some information for the certificate
    '''

    class Meta:
        abstract = True
    

    date_of_birth = models.DateField(
        verbose_name = _l('date of birth')
    )

    place_of_birth = models.CharField(
        max_length = 128,
        verbose_name = _l('Place (town) of birth')
    )

    country_of_birth = models.CharField(
        max_length = 128,
        verbose_name = _l('Country of birth (if not Germany)'),
        blank = True,
    )

    street = models.CharField(
        max_length = 128,
        verbose_name = _l('street')
    )

    street_number = models.CharField(
        max_length = 16,
        verbose_name = _l('street number')
    )

    town_zip = models.CharField(
        max_length = 16,
        verbose_name = _l('ZIP code')
    )
        
    town = models.CharField(
        max_length = 128,
        verbose_name = _l('town')
    )
    
    country = models.CharField(
        max_length = 128,
        verbose_name= _l( 'Country (if not Germany)' ),
        blank = True
    )
    
    
    
class InvoiceMixin( models.Model ):
    class Meta:
        abstract = True

    amount = models.DecimalField(
        max_digits = 7,
        decimal_places = 2
    )

    amount_payed =  models.DecimalField(
        max_digits = 7,
        decimal_places = 2,
        default = 0
    )
    
    payed = models.BooleanField()
    
    invoice_company = models.CharField(
        max_length = 128,
        verbose_name = _l( 'company or university' )
    )
    
    invoice_additional_line_1 = models.CharField(
        max_length = 128,
        verbose_name = _l( 'department, room  or similar' ),
        blank = True
    )
    
    invoice_additional_line_2 = models.CharField(
        max_length = 128,
        verbose_name = _l( 'department, room  or similar' ),
        blank = True
    )
    
    invoice_additional_line_3 = models.CharField(
        max_length = 128,
        verbose_name = _l( 'department, room or similar' ),
        blank = True
    )
    
    invoice_street = models.CharField(
        max_length = 128,
        verbose_name = _l('street')
    )
    invoice_street_number = models.CharField(
        max_length = 128,
        verbose_name = _l('street number')
    )
    
    invoice_town_zip = models.CharField(
        max_length = 16,
        verbose_name = _l('ZIP code')
    )
    
    invoice_town = models.CharField(
        max_length = 128,
        verbose_name = _l('town')
    )
    
    invoice_country = models.CharField(
        max_length = 128,
        verbose_name= _l( 'Country (if not Germany)' ),
        blank = True, 
    )
    

class SskStudentAttendee ( 
        AbstractStudentAttendee, AbstractCertificateInformationMixin
):
    class Meta:
        verbose_name = _l( 'student for course with official certificate' )

    identifier = 'sskstudent'
    display_name =_l('Student')
    display_name_plural =_l('Students')
    forms = [
        'courses.forms.RUBIDForm', 
        'courses.forms.SskStudentForm', 
        'courses.forms.SskStudentCertificateForm', 
        'courses.forms.SskStudentTermsAndConditionsForm'
    ]
    
    additional_admin_fields = (
        ('student_course', _('student course')),
    )

register_attendee ( SskStudentAttendee )

class SskExternalAttendee ( 
        CourseAttendee, AbstractCertificateInformationMixin, InvoiceMixin 
):
    class Meta:
        verbose_name = _l('External participant for course with official certificate')

    identifier = 'sskexternal'
    display_name =_l('External')
    display_name_plural =_l('Externals')
    additional_admin_fields = (
        ('invoice_company', _('company')),
        ('payed', _('has payed')),
        
    )
    forms = [
        'courses.forms.SskExternalDataForm',
        'courses.forms.SskExternalAttendeeCertificateForm',
        'courses.forms.SskExternalAttendeInvoiceForm',
        'courses.forms.SskExternalAttendeeTermsAndConditionsForm'
    ]
    

register_attendee( SskExternalAttendee )

class SskHospitalAttendee ( 
        CourseAttendee, AbstractCertificateInformationMixin, InvoiceMixin 
):
    class Meta:
        verbose_name = _l('External participant from RUB hospital for course with official certificate')

    identifier = 'sskhospital'
    display_name =_l('RUB hospital employee')
    display_name_plural =_l('RUB hospital employees')
    forms = [
        'courses.forms.SskHospitalDataForm',
        'courses.forms.SskHospitalAttendeeCertificateForm',
        'courses.forms.SskHospitalAttendeeInvoiceForm',
        'courses.forms.SskHospitalAttendeeTermsAndConditionsForm'
    ]

register_attendee( SskHospitalAttendee )

class SskRubMemberAttendee( 
        AbstractRUBAttendee, AbstractCertificateInformationMixin
):

    identifier = 'sskrubmember'
    display_name =_l('RUB employee')
    display_name_plural =_l('RUB employees')
    forms = ['courses.forms.RUBIDForm', 'courses.forms.SskRubMemberDataForm' ,'courses.forms.SskRubMemberAttendeeCertificateForm','courses.forms.SskRubMemberTermsAndConditionsForm' ]

    class Meta:
        verbose_name = _l('RUB staff for course with official certificate')

    faculty = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Faculty')
    )

    department = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Department')
    )

    institute = models.CharField(
        max_length = 128,
        verbose_name = _l('Institute or Workgroup')
    )

    room = models.CharField(
        max_length = 16,
        verbose_name = _l('Building and room')
    )

register_attendee( SskRubMemberAttendee )

class AbstractAttendeeRelation( Orderable ):
    class Meta: 
        abstract = True

    attendee = models.CharField(
        max_length = 16,
        verbose_name=_('attendee type')
    )

    waitlist = models.BooleanField(
        default = False,
        verbose_name=_('waitlist')
    )

    price = models.DecimalField(
        max_digits = 7,
        decimal_places = 2,
        default = 0,
        blank = True,
        null = True,
        verbose_name=_('price')
    )

    max_attendees = models.IntegerField(
        blank = True,
        null = True,
        verbose_name = _('max attendees')
    )

    panels = [
        FieldPanel('attendee', widget = AttendeeSelectWidget() ) ,
        FieldPanel('price'),
        FieldRowPanel([
            FieldPanel('max_attendees'),
            FieldPanel('waitlist'),
        ])
    ]

    def get_attendee_class ( self ):
        if not self.attendee:
            return None
        return get_attendee_class( self.attendee ) 


class CourseDefinition2AttendeeRelation( AbstractAttendeeRelation ):
    course = ParentalKey( CourseInformationPage, related_name = 'attendee_types' )

class Course2AttendeeRelation( AbstractAttendeeRelation ):
    course = ParentalKey( Course, related_name = 'attendee_types' )

        

# The last model simply contains the list of courses

class ListOfCoursesPage ( TranslatedPage, OptionalIntroductionMixin ):
    class Meta:
        verbose_name = _('Listing of the courses in RUBION')

    template = 'website/container.html'
    subpage_types = [CourseInformationPage]
    parent_page_type = ['website.StartPage']


    content_panel_de = [
        FieldPanel('title_de'),
        StreamFieldPanel('introduction_de')
    ]

    content_panel_en = [
        FieldPanel('title'),
        StreamFieldPanel('introduction_en')
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panel_de, heading = _('Content (de)') ),
        ObjectList(content_panel_en, heading = _('Content (en)') ),
    ])

    def get_visible_children( self ):
        return self.get_children().live()


class DataSharingPage ( TranslatedPage ):
    parent_page_type = ['courses.Course']
    
    def clean( self ):
        if not self.title:
            self.title = 'Data sharing'
            self.title_de = 'Datenaustausch'

        if not self.slug:
            # we make it a bit harder to guess the URL of a data sharing page
            # However, this is not true security!

            self.slug = self._get_autogenerated_slug('data')


    def get_context( self, request ):
        context = super(DataSharingPage, self).get_context(request)
        from .forms import DataUploadForm
        form = DataUploadForm()

        context['form'] = form

        return context
        

    def serve( self, request, *args, **kwargs ):
        if request.method == 'POST':
            from .forms import DataUploadForm
            form = DataUploadForm(request.POST, request.FILES)
            if form.is_valid():
                self.process_submission(form, request)
                return super(DataSharingPage, self).serve(request)
            else:
                context = self.get_context(request)
                context['form'] = form
                return TemplateResponse(
                    request,
                    self.get_template(request, *args, **kwargs),
                    context
                )
        else:
            return super(DataSharingPage, self).serve(request)


    def process_submission(self, form, request):
        cleaned_data = form.cleaned_data

        document_data = cleaned_data['uploaded_file']
        if document_data:
            DocumentModel = get_document_model()

            doc = DocumentModel(
                file = document_data,
                title = document_data.name,
                collection = ImportantPages.for_site(request.site).collection_for_user_upload
            )
            doc.save()

            instance = form.save(commit = False)
            instance.uploaded_on = datetime.datetime.now()
            instance.sharing_page = self
            instance.file_link = doc

            instance.save()


    content_panels = [
        InlinePanel('shared_data')
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading = _('Data')),
    ])

class SharedData ( Orderable ):
    file_link = models.ForeignKey(
        get_document_model(),
        on_delete = models.CASCADE 
    )
    uploaded_on = models.DateTimeField()
    uploaded_by = models.CharField( 
        max_length = 128,
        verbose_name = _('your name')
    )
    description = models.TextField(
        verbose_name = _('description of the file content')
    )
    
    sharing_page = ParentalKey( DataSharingPage, related_name = 'shared_data' )

    panels = [
        DocumentChooserPanel('file_link'),
        FieldPanel('uploaded_on'),
        FieldPanel('uploaded_by'),
        FieldPanel('description'),
    ]

@register_snippet
class CourseParticipationValidation( models.Model ):
    attendee = models.ForeignKey(
        CourseAttendee,
        on_delete = models.CASCADE,
        editable = False
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        null = True,
        blank = True,
        editable = False
    )
    created_at = models.DateTimeField(
        auto_now_add = True
    )

    def validate( self ):
        self.attendee.validate()
        self.uuid = None
        self.save()
        
    def __str__( self ):
        return "{}: {} ({})".format(self.uuid, self.attendee.full_name, self.created_at)

@register_setting
class CourseSettings(BaseSetting):
    vat = models.DecimalField(
        max_digits = 4,
        decimal_places = 2,
        default = 19,
        verbose_name = _('VAT rate')
    )

    invoice_counter = models.IntegerField(
        default = 0,
    )
    invoice_counter_year = models.IntegerField(
        default = 2018
    )

    panels = [
        FieldPanel('vat')
    ]
