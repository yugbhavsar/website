from .course import Course

import datetime

from django.db import models
from django.utils.translation import ugettext as _

from modelcluster.fields import ParentalKey

from userdata.mixins import AbstractContactPerson

from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel, MultiFieldPanel, InlinePanel,
    TabbedInterface, ObjectList, StreamFieldPanel
)

from website.models import (
    TranslatedPage, MandatoryIntroductionMixin,
    BodyMixin, ChildMixin, OptionalIntroductionMixin
)

class CourseInformationPage(
        TranslatedPage, MandatoryIntroductionMixin,
        BodyMixin, ChildMixin ):
    '''
    A general model for a course.

    '''

    #--------------------------------------------------
    #
    # Settings
    #
    #--------------------------------------------------

    subpage_types = [ 'courses.Course' ]
    parent_page_types = ['courses.ListOfCoursesPage']
    class Meta:
        verbose_name = _('Definition of a course')

    #--------------------------------------------------
    #
    # model definition
    #
    #--------------------------------------------------
        
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

    #--------------------------------------------------
    #
    # edit handlers
    #
    #--------------------------------------------------
    
    edit_handler = TabbedInterface([
        ObjectList(content_panels_de, heading = _('Content (de)')),
        ObjectList(content_panels_en, heading = _('Content (en)')),
        ObjectList(additional_information_panel, heading = _('Additional information')),
        ObjectList(settings_panel, heading = _('Settings')),
    ])

    #--------------------------------------------------
    #
    # METHODS
    #
    #--------------------------------------------------

    def get_upcoming_courses( self ):
        '''returns the upcoming courses of this type'''
        
        children = Course.objects.live().child_of(self).filter(
            start__gt = datetime.date.today()
        )
        return children
    
    def get_admin_display_title( self ):
        '''returns the translated page title to be shown in admin'''
        return self.title_trans


    
class CourseContactPerson( AbstractContactPerson ):
    '''Contact person(s) for the course'''
    page = ParentalKey( CourseInformationPage, related_name ='contact_persons')


    
class ListOfCoursesPage ( TranslatedPage, OptionalIntroductionMixin ):
    '''Page containing the different course information pages'''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    class Meta:
        verbose_name = _('Listing of the courses in RUBION')

    template = 'website/container.html'
    subpage_types = [CourseInformationPage]
    parent_page_type = ['website.StartPage']

    #--------------------------------------------------
    #
    # edit handlers
    #
    #--------------------------------------------------
    
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

    #--------------------------------------------------
    #
    # METHODS
    #
    #--------------------------------------------------

    def get_visible_children( self ):
        return self.get_children().live()
