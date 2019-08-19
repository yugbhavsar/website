from django.utils.translation import ugettext as _

from notifications.models import AbstractRUBIONNotification
from notifications.register import register_notification

class SafetyInstractionExpiredMailNotification( AbstractRUBIONNotification ):
    identifier = 'staff.safety_instruction_expired_warning_to_user'
    description= _('A warning about expired or soon expiring safety instructions was sent to users')

    mail = {
        'subject_de' : 'Ein Nutzer wurde über ablaufende Sicherheitsunterweisungen informiert',
        'subject_en' : 'A user has been informed about expiring safety instructions',
        'text_de' : '''{% load i18n %}{% language 'de' %}Hallo {{staff.get_first_name}}!

Der Nutzer 
  {{user.full_name}} 

aus der Arbeitsgruppe
  {{user.get_workgroup}}

wurde darüber informiert, dass 

{% if not_yet %}
- folgende Sicherheitsunterweisungen noch nicht erfolgt sind:       
{% for ny in not_yet %}
 -- {{ ny }}
{% endfor %}
{% endif %}

{% if expired %}
- folgende Sicherheitsunterweisungen abgelaufen sind:
{% for e in expired %}
 -- {{ e }}
{% endfor %}
{% endif %}

{% if soon %}
- folgende Sicherheitsunterweisungen bald ablaufen:
{% for s in soon %}
 -- {{ s }}
{% endfor %}
{% endif %}

Viele Grüße vom virtuellen Kollegen!
{% endlanguage %}
        ''',
        'text_en': '''Dear {{staff.get_first_name}}!

'''
    }


    def __init__( self, r_user, not_yet_given, expired, soon, *args, **kwargs ):
        super(SafetyInstractionExpiredMailNotification, self).__init__(*args, **kwargs)

        self.not_yet = not_yet_given
        self.expired = expired
        self.soon = soon
        self.page = r_user
        self.workgroup = r_user.get_workgroup()
        self.projects = self.workgroup.get_projects()
        self.methods = self.workgroup.get_methods()
        self.instruments = []
        for m in self.methods:
            for i2r in m.related.all():
                if i2r.page not in self.instruments:
                    self.instruments.append(i2r.page)

    def get_context( self, context ):
        context['user'] = self.page
        context['not_yet'] = self.not_yet
        context['expired'] = self.expired
        context['soon'] = self.soon
        return context
    
        

register_notification(SafetyInstractionExpiredMailNotification)
