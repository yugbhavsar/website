from django.utils.translation import ugettext as _

from notifications.models import (
    AbstractRUBIONNotification, CreateNotificationHelper 
)
from notifications.register import register_notification

from userdata.models import SafetyInstructionsSnippet
from wagtail.snippets.models import register_snippet


class RUBIONUserAddedNotification( AbstractRUBIONNotification ):
    identifier = 'rubionuser.add'
    description = _('A RUBION user was added')
    template = 'notifications/rubionuser_added.html'
    check_create = True
    mail = {
        'subject_de' : 'Ein neuer RUBION-Nutzer wurde hinzugefügt.',
        'subject_en' : 'A new RUBION user was added.',
        'text_de' : '''Hallo {{staff.get_first_name}}!

Der Nutzer bzw. die Nutzerin:
  {{ r_user.full_name }}

wurde der Arbeitsgruppe
  {{ r_user.get_workgroup }}

hinzugefügt.


Viele Grüße,

der automatische Benachrichtigungsservice des RUBION.
''',
        'text_en' : '''Dear {{staff.get_first_name}}!

A new user,

  {{ r_user.full_name }}

has been added to the workgroup
  {{ r_user.get_workgroup }}.

Kind regards from

RUBION\'s automatic notification service.
'''
    }

    def __init__( self, r_user, *args, **kwargs ):
        super(RUBIONUserAddedNotification, self).__init__(*args, **kwargs)
        self.page = r_user
        self.workgroup = r_user.get_workgroup()
        self.projects = self.workgroup.get_projects()
        self.methods = self.workgroup.get_methods()
        self.instruments = []

        self.staff_entries = []

        for m in self.methods:
            for i2r in m.related.all():
                if i2r.page not in self.instruments:
                    self.instruments.append(i2r.page)
        

    def get_context(self, context):
        context['r_user'] = self.page
        return context

    def create_panel_entry(self, user):
        entry = super(RUBIONUserAddedNotification, self).create_panel_entry(user)
        entry.page = self.page
        entry.save()

    @staticmethod
    def get_context_static():
        return {
            'safety_instructions' : SafetyInstructionsSnippet.objects.all()
        }


class RUBIONUserChangedNotification( RUBIONUserAddedNotification ):
    identifier = 'rubionuser.changed'
    description = _('Data of a RUBION user was changed')
    template = 'notifications/rubionuser_changed.html'
    check_create = False
    mail = {
        'subject_de': 'Die Daten eines Nutzers haben sich geändert.',
        'subject_en': 'Data of a user have changed.',
        'text_de': '''Hallo {{staff.get_first_name}}!

Der Nutzer 
  {{ r_user.full_name }}

hat seine Daten geändert. 

Viele Grüße,

der automatische Benachrichtigungsservice des RUBION.''',    
        'text_en': '''Dear {{staff.get_first_name}}!
        
A new user,

  {{ r_user.full_name }}

has changed his data.

Kind regards from

RUBION\'s automatic notification service.'''
    }

    def __init__(self, r_user, *args, **kwargs):
        # sets self.page = r_user
        super(RUBIONUserChangedNotification, self).__init__(r_user, *args, **kwargs)
        
        revisions = self.page.revisions.order_by('-created_at')
        current_rev = revisions.first()
        previous_rev = current_rev.get_previous()
        self.previous_r_user = previous_rev.as_page_object().specific

        # The usage of page.get_edit_handler().get_comparison(), as used in wagtail's view, is not documented
        # so I use a poor-man's comparison here

        fields = ['name_db', 'first_name_db', 'academic_title', 'labcoat_size', 'overshoe_size', 'entrance']
        
        current_user = current_rev.as_page_object().specific

        changed = []
        for f in fields:
            if getattr(current_user, f) != getattr(self.previous_r_user, f):
                try:
                    old_val = getattr(self.previous_r_user, 'get_{}_display'.format(f))()
                    new_val = getattr(self.page, 'get_{}_display'.format(f))()
                except AttributeError:
                    old_val = getattr(self.previous_r_user, f)
                    new_val = getattr(self.page, f)
                changed.append({
                    'fieldname' : f,
                    'old_value' : old_val,
                    'new_value' : new_val
                })

        self.changed = changed
        self.has_changed = bool(self.changed)
    
    def get_context(self, context):
        context = super(RUBIONUserChangedNotification, self).get_context(context)
        context['changed'] = self.changed
        context['previous'] = self.previous_r_user
        return context
    
    def notify(self):
        if self.has_changed:
            return super(RUBIONUserChangedNotification, self).notify()
        else:
            return False
    
class ProjectApprovedNotification( AbstractRUBIONNotification ):
    identifier = 'project.approved'
    description = _('A new project was approved')
    template = 'notifications/project_approved.html'
    mail = {
        'subject_de' : 'Ein neues Projekt wurde im RUBION gestartet.',
        'subject_en' : 'A new project has been started at RUBION.',
        'text_de' : '''Hallo {{staff.get_first_name}}!

Die Arbeitsgruppe
  {{ project.get_workgroup }}

hat ein neues Projekt am RUBION gestartet. Der Titel des Projekts lautet
  {{ project }}


Viele Grüße,

der automatische Benachrichtigungsservice des RUBION.
''',
        'text_en' : '''Dear {{staff.get_first_name}}!

A new project, entitled 
  {{ project }}

has been started at RUBION by the workgroup
  {{ project.get_workgroup }}.

Kind regards from

RUBION\'s automatic notification service.
'''
    }

    def __init__( self, project, *args, **kwargs ):
        super(ProjectApprovedNotification, self).__init__(*args, **kwargs)

        self.page = project
        self.workgroup = project.get_workgroup()
        self.methods = self.workgroup.get_methods()
        self.instruments = []

        for m in self.methods:
            for i2r in m.related.all():
                if i2r.page not in self.instruments:
                    self.instruments.append(i2r.page)
        

    
    def match_projects( self, projects ):
        '''
        It does not make sense to match a new project vs. the existing ones
        '''
        return True

    def get_context(self, context):
        context['project'] = self.page
        return context


    @staticmethod
    def get_context_static():
        return {}

class WorkgroupApprovedNotification( AbstractRUBIONNotification ):
    identifier = 'project.approved'
    description = _('A new project was approved')
    template = 'notifications/project_approved.html'
    mail = {
        'subject_de' : 'Ein neue Arbeitsgruppe beginnt am RUBION.',
        'subject_en' : 'A new workgroup starts working at RUBION.',
        'text_de' : '''Hallo {{staff.get_first_name}}!

Die Arbeitsgruppe
  {{ workgroup }}

beginnt am RUBION.

Viele Grüße,

der automatische Benachrichtigungsservice des RUBION.
''',
        'text_en' : '''Dear {{staff.get_first_name}}!

The workgroup will start working at RUBION
        {{ workgroup }}

Kind regards from

RUBION\'s automatic notification service.
'''
    }

    def __init__( self, wg, *args, **kwargs ):
        super(WorkgroupApprovedNotification, self).__init__(*args, **kwargs)

        self.page = wg
        self.methods = wg.get_methods()
        self.instruments = []

        for m in self.methods:
            for i2r in m.related.all():
                if i2r.page not in self.instruments:
                    self.instruments.append(i2r.page)
        

    
    def match_projects( self, projects ):
        '''
        It does not make sense to match a new wg vs. the existing projects
        '''
        return True

    def match_workgroups( self, projects ):
        '''
        It does not make sense to match a new wg vs. existing wgs
        '''
        return True


    def get_context( self, context ):
        context['workgroup'] = self.page


    @staticmethod
    def get_context_static():
        return {}


class ProjectExpiredMailNotification( AbstractRUBIONNotification ):

    identifier = 'project.warning_was_sent'
    description = _('A warning concerning an expiring project was sent')
#    template = 'notifications/project_approved.html'
    mail = {
        'subject_de' : 'Eine Warnung über ein ablaufendes Projekt wurde versendet.',
        'subject_en' : 'A warning concerning an expiring project was sent.',
        'text_de' : '''Hallo {{staff.get_first_name}}!

Das Projekt
  {{ project }}

der AG
  {{ workgroup }}

läuft (bzw. lief) am 
  {{project.expire_at}}

aus. Die folgenden Nutzer wurden darüber benachrichtigt:

  {% for user in to %}
- {{user.full_name}} ({{user.email}})  
  {% endfor %}

Viele Grüße,

der automatische Benachrichtigungsservice des RUBION.
''',
        'text_en' : '''Dear {{staff.get_first_name}}!

The project
  {{ project }}

from the group
  {{ workgroup }}

has expired (or is going to expire) at
  {{project.expire_at}}

The following users have been notified:

  {% for user in to %}
- {{user.full_name}} ({{user.email}})  
  {% endfor %}

Cheers,

the RUBION's automatic notification service.
'''
    }
    def __init__(self, project, to, *args, **kwargs):
        super(ProjectExpiredMailNotification, self).__init__(*args, **kwargs)
        print("Notification on project: {}".format(project))
        self.page = project
        self.projects = project
        self.workgroup = project.get_workgroup()
        self.methods = self.workgroup.get_methods()
        self.instruments = []
        self.to = to

        for m in self.methods:
            for i2r in m.related.all():
                if i2r.page not in self.instruments:
                    self.instruments.append(i2r.page)


#        print("Notification matches? {}".format(self.matches()))

        
    def get_context(self, context):
        context['project'] = self.projects
        context['to'] = self.to
        context['workgroup'] = self.workgroup
        return context
    
register_notification( RUBIONUserAddedNotification )
register_notification( RUBIONUserChangedNotification )
register_notification( ProjectApprovedNotification )
register_notification( WorkgroupApprovedNotification )
register_notification( ProjectExpiredMailNotification )
