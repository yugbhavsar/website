from .forms import ApplicationForm, CalendarForm

import datetime 
from dateutil.rrule import rrule, HOURLY

from django.contrib import messages
from django.db import models
from django.http import Http404
from django.shortcuts import redirect
from django.utils.module_loading import import_string
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from rubion.utils import iso_to_gregorian

from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin, route
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.models import Orderable
from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel

from website.models import TranslatedField


def get_bookings_for( obj, cal_start, cal_end ):
    Klass = obj.import_and_get_booking_model()
    filters = {
        obj.booking_model_fieldname : obj
    }
    
    # Make it simple. Start should be larger than cal_start
    # and end smaller than cal_end. We do not support bookings spanning
    # more than one day. Note: Recurrent bookings not yet implemented.
    # @TODO: implement recurring bookings (not only here, but in general)
    
    bookings = ( 
        Klass.objects.filter( **filters )
        .filter( start__lt = cal_end )
        .filter( end__gt = cal_start )
    )
    
    booked = []
    
    for booking in bookings:
        s_date = datetime.datetime(
            booking.start.year, booking.start.month, 
            booking.start.day, hour=booking.start.hour,
            tzinfo = booking.start.tzinfo
        )
        rr = rrule(HOURLY, dtstart = s_date, until = booking.end)
        booked += list(rr)
    return booked


class AbstractBookable( RoutablePageMixin, models.Model ):
    '''
    This abstract class can be used as a mixin to enable
    bookings. The derived class should implement an `is_bookable'
    property that indicates whether a specific instance of this 
    class is a bookable object. 
    '''

    class Meta:
        abstract = True

    is_bookable = models.BooleanField(
        default = False,
        verbose_name = _('Can this be booked')
    )

    is_managed_elsewhere = False
    #models.BooleanField(
    #    default = True,
    #    verbose_name = _('Managed elsewhere?'),
    #    help_text = _('Are bookings stored and managed in an external software')
    #)
    

    def can_be_booked_by( self, user ):
        if not self.is_bookable:
            return False
            
        return user.can_book( self )

    def import_and_get_booking_model( self ):
        return import_string( self.booking_model )

    def get_r_user( self, request ):
        # this is ugly...
        try:
            r_user = RUBIONUser.objects.get( linked_user = request.user )
        except:
            from userinput.models import RUBIONUser
            r_user = RUBIONUser.objects.get( linked_user = request.user )
        return r_user

    # Sub-pages. `Apply' for an instrument usage:

    @route(r'^apply/$', name='apply')
    def apply_view(self, request):
        if not self.is_bookable:
            raise Http404('Instrument cannot be booked.')

        r_user = self.get_r_user( request )
        projects = r_user.get_workgroup().get_projects()


        # don't know if `get' is a good name for an internal method, thus 
        # I use this one
        def apply_view__get( form = None ):
            if form is None:
                form = ApplicationForm(projects = projects)
            tpl = 'website/general_form.html'

            return TemplateResponse(
                request, tpl,
                {
                    'page' : self,
                    'title' : _('Apply for measurement'),
                    'form' : form,
                    'submit' : _('Submit application')
                }
            )

        def apply_view__post():
            form = ApplicationForm( request.POST, projects = projects )

            if form.is_valid():
                self.save_booking( form.cleaned_data['projects'], form.cleaned_data['description'], request.user )
                messages.info(request, _( 'Your request for measurement has been send.'))
                return redirect( self.url )
            else:
                return apply_view__get( form )


        if request.method == 'GET':
            return apply_view__get()
        if request.method == 'POST':
            return apply_view__post()

            
    # book-views with calendar-like date-selection

    @route(r'^book/$', name='book')
    @route(r'^book/(\d+)/(\d+)/$', name='book_with_date')
    def book_view(self, request, year = None, week = None):
        if not self.is_bookable or self.is_managed_elsewhere:
            raise Http404('Instrument cannot be booked.')

        r_user = self.get_r_user( request )
        if not r_user.can_book( self ):
            return redirect( self.url + self.reverse_subpage('apply') )

        now = datetime.datetime.now()

        if year is None:
            year = now.year
        else:
            year = int(year)
        if week is None:
            week = now.isocalendar()[1]
        else:
            week = int(week)


        projects = r_user.get_workgroup().get_projects()

        cal_start = iso_to_gregorian(year, week-1, 7)
        cal_end = iso_to_gregorian(year, week+2, 6)

        booked = get_bookings_for( self, cal_start, cal_end )
            
        def book_view__get( form = None ):
            # internal function for get-requests or
            # if a form-submission contained errors

            tpl = 'instruments/calendar_form.html'
            is_posted = True

            if form is None:
                form = CalendarForm(projects = projects)
                is_posted = False

            return TemplateResponse(
                request, tpl,
                {
                    'page'     : self,
                    'title'    : _('Apply for measurement'),
                    'form'     : form,
                    'submit'   : _('Book instrument'),
                    'year'     : year,
                    'currweek' : week,
                    'prevweek' : week - 2,
                    'nextweek' : week + 2,
                    'weeks'    : range(week, week+2),
                    'bookings' : booked,
                    'is_posted': is_posted
                }
            )

        def book_view__post():
            # internal function for POST-requests
            form = CalendarForm(request.POST, projects = projects)

            if form.is_valid():
                self.save_booking( 
                    form.cleaned_data['projects'],
                    form.cleaned_data['description'],
                    request.user,
                    start = form.cleaned_data['start'],
                    end = form.cleaned_data['end']
                )
                return redirect( self.url )

            else:
                return book_view__get( form )

        if request.method == 'GET':
            return book_view__get()
        if request.method == 'POST':
            return book_view__post()

    def save_booking( self, project, description, user, start = None, end = None ):
        # Generates and saves the booking model instance

        Klass = self.import_and_get_booking_model()
        from userinput.models import Project

        # @TODO: A user might manipulate the project-id sent by
        # the form. One should check whether the current project
        # belongs to the same workgroup as the user.
        project = Project.objects.get( id = project )
        instance = Klass()
        
        # Since this mixin might extend different classes, the 
        # ForeignKey to this model might have a different name.
        # It must be provided in `booking_model_fieldname'.
        setattr( instance, self.booking_model_fieldname, self )             

        instance.project = project
        instance.description = description
        instance.booked_by = user

        if start is not None:
            instance.start = start
        if end is not None:
            instance.end = end

        instance.save()

        return instance
                
        


class AbstractRelatedInstrument( Orderable ):
    page = models.ForeignKey(
        'instruments.InstrumentPage', on_delete=models.CASCADE, 
        related_name = '+', verbose_name=_('instrument')
    )
    panels = [
        FieldPanel( 'page' )
    ]
    
    class Meta:
        abstract = True

class AbstractRelatedMethods( Orderable ):
    page = models.ForeignKey(
        'instruments.MethodPage', on_delete=models.CASCADE, 
        related_name = '+', verbose_name=_('methods')
    )
    panels = [
        FieldPanel( 'page' )
    ]
    
    class Meta:
        abstract = True


class AbstractRelatedDocument( Orderable ):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, 
        related_name = '+', verbose_name=_('document')
    )
    title_en = models.CharField(
        max_length = 64
    )
    title_de = models.CharField(
        max_length = 64
    )
    TranslatedField('title')
    panels = [
        DocumentChooserPanel( 'document' )
    ]
    
    class Meta:
        abstract = True
