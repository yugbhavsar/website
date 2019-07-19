from .containers import CourseInformationPage
from .course import Course

from courses.attendees import get_attendee_class
from courses.widgets  import AttendeeSelectWidget

from django.db import models
from django.utils.translation import ugettext as _

from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel, MultiFieldPanel, InlinePanel,
    TabbedInterface, ObjectList, StreamFieldPanel
)
from wagtail.core.models import Orderable

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

