from .attendees import CourseAttendee

from django.db import models

import uuid 

from wagtail.snippets.models import register_snippet

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
