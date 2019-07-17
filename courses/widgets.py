from .attendees import get_attendee_choices

from website.widgets import StyledCheckbox

from django.forms.widgets import Select



class AttendeeSelectWidget( Select ):
    def __init__( self, *args, **kwargs ):
        super(AttendeeSelectWidget, self).__init__( *args, **kwargs )

        self.choices = get_attendee_choices()


class WaitlistCheckboxWidget( StyledCheckbox ):
    template_name = 'courses/forms/widgets/waitlist_checkbox.html'

    
    def __init__( self, *args, **kwargs ):
        self.course = None
        super(WaitlistCheckboxWidget, self).__init__( *args, **kwargs)

    def get_context( self, name, value, attrs ):
        context = super(WaitlistCheckboxWidget, self).get_context(name, value, attrs)
        context['widget']['course'] = self.course
        return context
