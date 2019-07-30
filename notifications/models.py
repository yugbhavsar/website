from .register import register_notification


from django.db import models
from django.forms.widgets import Select
from django.utils import translation, timezone
from django.utils.translation import ugettext as _

from instruments.mixins import (
    AbstractRelatedInstrument, AbstractRelatedMethods
)

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel 

from rubion.helpers import any_in

from userdata.models import StaffUser
from userdata.safety_instructions import SAFETYINSTRCUTION_CHOICES

from userinput.relations import (
    AbstractRelatedWorkgroup, AbstractRelatedProject,
    AbstractRelatedRUBIONUser
)


from wagtail.admin.edit_handlers import (
    FieldPanel, MultiFieldPanel, FieldRowPanel,
    PageChooserPanel, InlinePanel, TabbedInterface, ObjectList
)
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Site
from wagtail.images.edit_handlers import (
    ImageChooserPanel
)

from wagtail.snippets.models import register_snippet

from website.models import TranslatedField, EMailText, KontaktZentralerStrahlenschutz

from .widgets import NotificationSelectWidget

@register_snippet
class NewsSnippet( ClusterableModel ):
    """Implements a `News` on the first page of the website."""
    title_de = models.CharField( 
        max_length = 255,
        verbose_name = _('[DE] title'),
        blank = True, null = True
    )
    title_en = models.CharField( 
        max_length = 255,
        verbose_name = _('[EN] title'),
        blank = True, null = True
    )

    title = TranslatedField('title')

    content_de = RichTextField(
        verbose_name = _( '[DE] content' ),
        blank = True, null = True
    )
    content_en = RichTextField(
        verbose_name = _( '[EN] content' ),
        blank = True, null = True,
    )
    content = TranslatedField('content')

    linked_page = models.ForeignKey(
        'wagtailcore.Page', null = True, blank = True,
        on_delete=models.SET_NULL, related_name = '+',
    )
    linked_page_title = models.CharField(
        max_length = 255, blank = True, null = True
    )

    image = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    date_published = models.DateTimeField(
        default = timezone.now,
        verbose_name = _('when to publish'),
        blank = True
    )
    date_unpublish = models.DateTimeField(
        verbose_name = _('when to unpublish'),
        null = True, blank = True
    )
    send_mail_to_all = models.BooleanField(
        default = False,
        verbose_name = _('Send mail to all users?'),
        help_text = _('If this is checked, this news is sent via e-mail to all users of RUBION.')
    )

    mail_was_sent = models.BooleanField(
        default = False,
    )
    
    @property
    def mail_required(self):
        return (self.send_mail_to_all or False)
                
        
    

    panels = [
        MultiFieldPanel([
            FieldPanel( 'title_de' ),
            FieldPanel( 'title_en' ),
        ], heading = _( 'title' )),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('date_published', classname='col6'),
                FieldPanel('date_unpublish', classname='col6'),
            ]),
        ], heading=_('publishing options')),
        MultiFieldPanel([
            FieldPanel( 'content_de' ),
            FieldPanel( 'content_en' ),
        ], heading = _( 'content' )),
        MultiFieldPanel([
            PageChooserPanel( 'linked_page' ),
            FieldPanel( 'linked_page_title' ),
        ], heading = _('linked page (shown as a button)')),
        ImageChooserPanel( 'image' ),
    ]
    email_panels = [
        MultiFieldPanel([
            FieldPanel('send_mail_to_all'),
        ], heading = _('e-mail settings')),
        InlinePanel(
            'method',                
            label = _('Method specification'),
            help_text = _('Notification will be sent to users of this method.')
        ),
        InlinePanel(
            'instrument',                
            label = _('Instrument specification'),
            help_text = _('Notification will be sent to users of this instrument.')
        ),
        InlinePanel(
            'workgroup',                
            label = _('Workgroup specification'),
            help_text = _('Notification will be sent to members of this workgroup.')
        )
    ]

    edit_handler = TabbedInterface([
        ObjectList(panels, heading = _('Content')),
        ObjectList(email_panels,heading = _('E-Mail settings'))
    ])
    def __str__( self ):
        if translation.get_language() == 'de':
            return self.title_de
        else:
            return self.title_en

    class Meta:
        verbose_name = _( 'news' )
        verbose_name_plural = _( 'news' )

class News2WorkgroupRelation( AbstractRelatedWorkgroup ):
    news = ParentalKey( 
        NewsSnippet, 
        related_name = 'workgroup',
        verbose_name = _('Workgroup equals...')
    )
class News2MethodRelation( AbstractRelatedMethods ):
    news = ParentalKey( 
        NewsSnippet, 
        related_name = 'method',
        verbose_name = _('Method equals...')
    )
class News2InstrumentRelation( AbstractRelatedInstrument ):
    news = ParentalKey( 
        NewsSnippet, 
        related_name = 'instrument',
        verbose_name = _('instrument equals...')
    )



class PageNotificationCounter( models.Model ):
    page = models.ForeignKey( Page, on_delete=models.CASCADE )
    count = models.IntegerField( default = 0 )

    def increase(self):
        self.count = self.count + 1
        self.save()


@register_snippet
class StaffNotificationSettings( ClusterableModel ):
    class Meta:
        verbose_name = _('Settings for staff notification')
    # Felder:
    # - Nutzer
    
    user = models.ForeignKey(
        StaffUser,
        verbose_name = _('Connected user'),
        help_text = _('User who recieves the notification'),
        on_delete=models.CASCADE
    )

    # - Event-Kürzel

    event_id = models.CharField(
        max_length = 64,
        verbose_name = ('Event'),
    )

    email = models.BooleanField(
        default = True,
        help_text = _('receive notification by mail?')
    )
    panel = models.BooleanField(
        default = True,
        help_text = _('Show notification on start page?')
    )
    # - Event (add, etc...)
    # - Zusatz 
    panels =  [
        MultiFieldPanel([
            FieldPanel( 'user' ),
            FieldPanel( 'event_id', widget = NotificationSelectWidget ),
        ], heading = _( 'Select event' ))
    ] + [
        MultiFieldPanel([
            InlinePanel(
                'workgroup', 
                label = _('Workgroup specification'),
                help_text = _('Workgroup related to the event. Multiple Workgroups will be connected by OR.')
            ),
            InlinePanel(
                'project', 
                label = _('Project specification'),
                help_text = _('Project related to the event. Multiple projects will be connected by OR.')
            ),
            InlinePanel(
                'rubion_user', 
                label = _('RUBION User specification'),
                help_text = _('RUBION User related to the event. Multiple users will be connected by OR.')
            ),
            InlinePanel(
                'method', 
                label = _('Method specification'),
                help_text = _('Method connected to the event. Multiple methods will be connected by OR.')
            ),
            InlinePanel(
                'instrument', 
                label = _('Instrument specification'),
                help_text = _('Instrument connected to the event. Multiple instruments will be connected by OR.')
            ),
        ], heading = _('Detailed specification'), classname = "collapsible collapsed")
    ] + [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('email'),
                FieldPanel('panel'),
            ])
        ], heading = _('How to notify?'))
    ]

    def _get_relation( self, relation ):
        rel = getattr(self, relation )
        return [ r.page for r in rel.all() ]

    def get_workgroups( self ):
        return self._get_relation('workgroup')

    def get_projects( self ): 
        return self._get_relation('project')

    def get_rubion_users( self ):
        return self._get_relation('rubion_user')

    def get_methods( self ):
        return self._get_relation('method')

    def get_instruments( self ):
        return self._get_relation('instrument')

    def __str__( self ):
        return _("{} for {}").format (self.event_id, self.user)

class Notification2WorkgroupRelation( AbstractRelatedWorkgroup ):
    method = ParentalKey( 
        StaffNotificationSettings, 
        related_name = 'workgroup',
        verbose_name = _('Workgroup equals...')
    )

class Notification2ProjectRelation( AbstractRelatedProject ):
    method = ParentalKey( 
        StaffNotificationSettings, 
        related_name = 'project',
        verbose_name = _('Project equals...')
    )

class Notification2RUBIONUserRelation( AbstractRelatedRUBIONUser ):
    method = ParentalKey( 
        StaffNotificationSettings, 
        related_name = 'rubion_user',
        verbose_name = _('RUBION user equals...')
    )

class Notification2MethodRelation( AbstractRelatedMethods ):
    method = ParentalKey( 
        StaffNotificationSettings, 
        related_name = 'method',
        verbose_name = _('Method equals...')
    )

class Notification2InstrumentRelation( AbstractRelatedInstrument ):
    method = ParentalKey( 
        StaffNotificationSettings, 
        related_name = 'instrument',
        verbose_name = _('Instrument equals...')
    )


# This is a little helper model that stores whether a 
# Create-notification has already been send.
# Works with models inherited from Page
class CreateNotificationHelper( models.Model ):
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE
    )
    sent = models.BooleanField()

    @staticmethod
    def has_been_sent( page ):
        return CreateNotificationHelper.objects.filter(page = page).filter(sent = True).exists()

    @staticmethod
    def is_sent( page ):
        cnh = CreateNotificationHelper()
        cnh.page = page
        cnh.sent = True
        cnh.save()

# This stores a notification until the Staff member has seen it
@register_snippet
class StaffNotification( models.Model ):
    # Show to which Staff member
    # Had to set the related_name property to get rid of a clash which I did
    # not understand
    staff = models.ForeignKey(
        StaffUser,
        related_name = 'staff',
        on_delete=models.CASCADE
    )
    
    # We could use this flag instead of deleting the entry
    has_been_seen = models.BooleanField ( default = False )

    # notification id
    notification = models.CharField(max_length = 64)

    # page 
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE
    )
    
        
    def __str__(self):
        return "{} for {}".format(str(self.notification), str(self.staff))

# The abstract implementation of a notification.
class AbstractRUBIONNotification ( object ):

    identifier = None
    description = None

    check_create = False

    def __init__( self, *args, **kwargs ):
        self.mail_addresses = []
        self.staff_entries = []

    def notify( self ):
        if self.check_create:
            if CreateNotificationHelper.has_been_sent( self.page ):
                return False
        for setting in self.get_settings_list():
            if self.matches(setting):
                if setting.email:
                    self.prepare_send( setting.user )
                if setting.panel:
                    self.create_panel_entry( setting.user )
                self.staff_entries.append( setting.user )
        self.send()
        if self.check_create:
            CreateNotificationHelper.is_sent( self.page )
        return True

    def match_workgroups( self, groups ):
        return not groups or self.workgroup in groups

    def match_projects( self, projects ):
        if not projects:
            return True
        return any_in( self.projects, projects )

    def match_methods( self, methods ):
        if not methods:
            return True
        return any_in( self.methods, methods ) 
        
    def match_instruments( self, instruments ):
        if not instruments:
            return True
        return any_in( self.instruments, instruments ) 

    def matches( self, setting ):
        return (
            self.match_workgroups ( setting.get_workgroups()  ) and
            self.match_projects   ( setting.get_projects()    ) and
            self.match_methods    ( setting.get_methods()     ) and
            self.match_instruments( setting.get_instruments() ) 
        )

    def prepare_send( self, to ):
        self.mail_addresses.append(to)
    

    def send( self ):
        try:
            mail = EMailText.objects.get(identifier = self.identifier)
        except EMailText.DoesNotExist:
            mail = EMailText(
                subject_de = self.mail['subject_de'],
                subject_en = self.mail['subject_en'],
                text_de = self.mail['text_de'],
                text_en = self.mail['text_en'],
            )
        de = []
        en = []
        both = []

        for user in self.mail_addresses:
            context = self.get_context({ 'staff' : user})
            if hasattr(user, 'preferred_language'):
                if user.preferred_language == 'de':
                    mail.send( user.mail, context, 'de' )
                if user.preferred_language == 'en':
                    mail.send( user.mail, context, 'en' )
                if not user.preferred_language:
                    mail.send( user.mail, context )
            else:
                mail.send( user.mail, context )

    def get_context( self, context ):
        return context

    def get_settings_list( self ):
        return StaffNotificationSettings.objects.filter(event_id = self.identifier)

    def create_panel_entry( self, user ):
        panel_entry = StaffNotification()
        panel_entry.staff = user
        panel_entry.notification = self.identifier
        return panel_entry
    
    @staticmethod
    def get_context ():
        return {}


@register_snippet
class CentralRadiationSafetyDataSubmission( models.Model ):

    def __str__(self):
        if self.email:
            if self.ruser:
                return "{}, {} via email".format(str(self.ruser), self.date)
            if self.staff:
                return "{}, {} via email".format(str(self.staff), self.date)
        else:
            if self.ruser:
                return "{}, {} manually".format(str(self.ruser), self.date)
            if self.staff:
                return "{}, {} manually".format(str(self.staff), self.date)
        return "Unkown"
    ruser = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'central_radiation_safety_data_submissions',
        verbose_name = _('Connected RUBION user'),
        blank = True,
        null = True,
        on_delete=models.CASCADE
    )
    staff = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'central_radiation_safety_data_submissions',
        verbose_name = _('Connected staff'),
        blank = True,
        null = True,
        on_delete=models.CASCADE
    )

    date = models.DateTimeField(
        default = timezone.now,
        verbose_name = _('date of the submission')
    )
    email = models.ForeignKey(
        'website.SentMail',
        verbose_name = _('The sent mail'),
        related_name = '+',
        blank = True,
        null = True,
        on_delete=models.CASCADE
    )

    def send_and_save( self, revision = False ):
        # sends a mail to the central radiation protection guy
        # with the corresponding data.
        # If revision is true, sends a data changed notification
        identifier = 'centralradiationsafety.newuser'
        if revision:
            identifier = 'centralradiationsafety.userchanged'
        try:
            mail = EMailText.objects.get( identifier = identifier )
        except EMailText.DoesNotExist:
            pass

        context = self.get_context( revision )
        # slightly annoying...
        site = Site.objects.get(is_default_site = True)
        address = KontaktZentralerStrahlenschutz.for_site(site).email
        self.email =  mail.send( address, context, 'de' )
        self.save()
    
    def get_context( self, revision = False ):
        if self.ruser:
            if self.ruser.previous_exposure:
                prev_exp = 'ja'
            else:
                prev_exp = 'nein'
            wg = self.ruser.get_workgroup()
            head = wg.get_head()
            
            user = {
                'last_name' : self.ruser.name,
                'first_name' : self.ruser.first_name,
                'email' : self.ruser.email,
                'phone' : self.ruser.phone,
                'date_of_birth' : self.ruser.date_of_birth,
                'place_of_birth' : self.ruser.place_of_birth,
                'previous_names' : self.ruser.previous_names,
                'previous_exposure' : prev_exp,
                'workgroup' : wg.title_de,
                'workgroup_head' : "{}, {}".format(head.name, head.first_name),
                'permits' : self.get_permits()
            }
            context = {
                'user' : user,
                'nuclides' : ", ".join(self.get_nuclides_for_workgroup(wg))
            }
            return context


    def get_nuclides_for_workgroup( self, workgroup ):
        projects = workgroup.get_projects()
        nuclides = set()
        for project in projects:
            for project2nuclide_rel in project.related_nuclides.all():
                nuclides.add(str(project2nuclide_rel.snippet))

        return list(nuclides)


    def get_permits( self ):
        permits = set()
        if self.ruser:
            for instrument in self.ruser._get_instruments():
                if instrument.permit:
                    permits.add(str(instrument.permit))
        
        return ", ".join(list(permits))

        
        
@register_snippet    
class ProjectExpiredNotifications( models.Model ):
    project = models.ForeignKey('userinput.Project', on_delete=models.CASCADE)
    mail = models.ForeignKey('website.SentMail', on_delete=models.CASCADE)

@register_snippet    
class SafetyInstructionExpiredNotifications( models.Model ):
    r_user = models.ForeignKey('userinput.RUBIONUser', on_delete=models.CASCADE, null = True)
    s_user = models.ForeignKey('userdata.StaffUser', on_delete=models.CASCADE, null = True)
    instruction = models.CharField(choices = SAFETYINSTRCUTION_CHOICES, max_length = 128, null = True)
    mail = models.ForeignKey('website.SentMail', on_delete=models.CASCADE)



