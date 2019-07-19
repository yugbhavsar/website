from .course import Course

from django.db import models
from django.utils.translation import ugettext as _

from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel, MultiFieldPanel, InlinePanel,
    TabbedInterface, ObjectList, StreamFieldPanel
)

from website.models import (
    TranslatedPage, MandatoryIntroductionMixin,
    BodyMixin, ChildMixin
)

class CourseInformationPage( TranslatedPage, MandatoryIntroductionMixin, BodyMixin, ChildMixin ):
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
   
class CourseContactPerson( AbstractContactPerson ):
    page = ParentalKey( CourseInformationPage, related_name ='contact_persons')
