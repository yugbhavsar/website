from django.forms.widgets import Select
from .attendees import get_attendee_choices

class AttendeeSelectWidget( Select ):
    def __init__( self, *args, **kwargs ):
        super(AttendeeSelectWidget, self).__init__( *args, **kwargs )

        self.choices = get_attendee_choices()
