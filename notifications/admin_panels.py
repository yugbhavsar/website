from django.template.loader import render_to_string

from .models import StaffNotification
from .register import RUBION_NOTIFICATIONS

from userdata.models import StaffUser


class NotificationPanel ( object ):
    template = 'notifications/notification_panels.html'
    order = 100

    def __init__ ( self, request ):
        self.request = request
        try:
            self.staff_user = StaffUser.objects.get(user = request.user)
        except StaffUser.DoesNotExist:
            self.staff_user = None
        self.notifications = StaffNotification.objects.filter(staff = self.staff_user).filter(has_been_seen = False)
        self.indexed_notifications = {}
        for n in self.notifications:
            if n.notification not in self.indexed_notifications:
                self.indexed_notifications[n.notification] = [n]
            else:
                self.indexed_notifications[n.notification].append(n)

    def get_notification_class( self, id ):
        for n in RUBION_NOTIFICATIONS:
            if n.identifier == id:
                return n

        return None

    def render ( self ):
        collector = []
        for key in self.indexed_notifications.keys():
            Kls = self.get_notification_class( key )
            if Kls:
                context = Kls.get_context_static()
                context['objects'] = self.indexed_notifications[key]
                collector.append(
                    render_to_string( Kls.template, context, self.request )
                )
        return render_to_string(
            self.template,
            {
                'notifications' : '\n'.join(collector)
            },
            self.request
        )
        
        
