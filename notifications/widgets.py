from django.forms.widgets import Select

from .register import get_notification_choices

class NotificationSelectWidget( Select ):
    def __init__( self, *args, **kwargs):
        super(NotificationSelectWidget, self).__init__( *args, **kwargs )
        self.choices = get_notification_choices()


    
