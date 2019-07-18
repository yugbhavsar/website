import datetime 

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import redirect
from django.template.defaultfilters import slugify
from django.template.response import TemplateResponse
from django.utils import translation
from django.utils.translation import ugettext_lazy as _


from modelcluster.fields import ParentalKey, ParentalManyToManyField

from ugc.models import UserGeneratedPage2
from userinput.admin_edit_forms import RUBIONUserAdminEditForm

from wagtail.admin.edit_handlers import (
    FieldPanel, StreamFieldPanel, MultiFieldPanel,
    FieldRowPanel, InlinePanel, TabbedInterface, 
    ObjectList, PageChooserPanel 
)
from wagtail.contrib.routable_page.models import route
from wagtail.core.models import PageRevision

class RUBIONUser ( UserGeneratedPage2 ):
    '''
    This seems to be the most complex model. It implements a User of RUBION.

    Since users can add themselves to our website (and we have to approve it), 
    it derives from UserGeneratedPage2. However, it has quite a lot of additional
    fields and methods.

    In general, a RUBIONUser can only occur under a Workgroup, it is not possible to 
    have a RUBIONUser without a workgroup. This is fine as long as we do not consider
    RUBION staff, which might or might not be member of a workgroup.
    '''

    #--------------------------------------------------
    #
    # Settings
    #
    #--------------------------------------------------
    
    # Form used in admin
    
    base_form_class = RUBIONUserAdminEditForm

    # Some additional information for the front-end

    front_end_verbose_name = _('workgroup member')
    front_end_verbose_name_plural = _('workgroup members')

    parent_page_types = [ 'userinput.MemberContainer' ]
    subpage_types = []

    # The view template is used by UGC. this is the template that
    # is shown if this page object is delivered
    view_template = 'userinput/rubionuser_view.html'
    
    
    class Meta:
        verbose_name = _('RUBION User')
        verbose_name_plural = _('RUBION Users')

        permissions = (
            ('edit','Can edit RUBION User Information'),
        )


    #--------------------------------------------------
    #
    # Pseudo constants
    #
    #--------------------------------------------------


    # named dosemeters
    
    NOT_YET_DECIDED = '0'
    NO_DOSEMETER = '1'
    OFFICIAL_DOSEMETER = '2'
    ELECTRONIC_DOSEMETER = '3'
    EXTERNAL_DOSEMETER = '4'

    DOSEMETER_CHOICES = (
        (NOT_YET_DECIDED, _('Not yet decided')),
        (NO_DOSEMETER, _('No dosemeter') ),
        (OFFICIAL_DOSEMETER, _('Official dosemeter') ),
        (ELECTRONIC_DOSEMETER, _('Electronic dosemeter') ),
        (EXTERNAL_DOSEMETER, _('External dosemeter' ) ),
    )
    DOSEMETER_SHORT_NAMES = {
        NOT_YET_DECIDED: _('not decided'),
        NO_DOSEMETER: _('not required'),
        OFFICIAL_DOSEMETER: _('official'),
        ELECTRONIC_DOSEMETER: _('electronic'),
        EXTERNAL_DOSEMETER:_('external'),
    }

    MALE = 'm'
    FEMALE = 'f'

    SEXES = (
        (MALE, _('male')),
        (FEMALE, _('female')),
    )

    BSC = 'b'
    MSC = 'm'
    PHD = 'd'
    MD = 'n'
    PROF = 'p'
    NON = ''

    ACADEMIC_TITLES = (
        (NON, _('None')),
        (BSC, _('BSc')),
        (MSC, _('MSc')),
        (PHD, _('PhD')),
        (MD, _('MD')),
        (PROF, _('Prof.')),
    )


    #--------------------------------------------------
    #
    # model field definition
    #
    #--------------------------------------------------
    

    # This is a bit annoying, since it repeats the definitions of the 
    # normal wagtail user fields. These fields might be not necessary,
    # but I introduced them for some reasons (maybe for course users?)
    name_db = models.CharField(
        max_length = 32,
        blank = True, null = True,
        verbose_name = _('name')
    )
    first_name_db = models.CharField(
        max_length = 32,
        blank = True, null = True,
        verbose_name = _('first name')
    )
    email_db = models.CharField(
        max_length = 128,
        blank = True, null = True,
        verbose_name = _('email address')
    )

    # --- Fields for additional personal data
    
    # I don't like the question in the form "What is your gender?"

    sex = models.CharField(
        max_length = 1,
        choices = SEXES,
        blank = True,
        null = True,
        verbose_name = _('What is your gender?'),
        help_text = _('We ask this question to correctly address you in emails and letters send to you.')
    )
    

    academic_title = models.CharField(
        max_length = 1,
        choices = ACADEMIC_TITLES,
        blank = True,
        null = True,
        verbose_name = _('academic title')
    )

    phone = models.CharField(
        max_length = 24,
        verbose_name = _('Phone number'),
        blank = True,
        null = True
    )

    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank = True,
        null = True,
        verbose_name = _( 'linked website user' ),
        on_delete = models.SET_NULL
    )

    preferred_language = models.CharField(
        max_length = 2,
        choices = settings.LANGUAGES,
        null = True,
        blank = True,
        verbose_name = _('Preferred language for communication')
    )


    # --- Fields required by radiation safety

    date_of_birth = models.DateField(
        null = True,
        blank = True,
        verbose_name = _('Date of birth'),
        help_text = _('Format: YYYY-MM-DD')
    )

    place_of_birth = models.CharField(
        max_length = 256,
        null = True,
        blank = True,
        verbose_name = _('Place of birth'),
        help_text = _('Add the country, if not Germany')
    )

    previous_names = models.CharField(
        max_length = 512,
        null = True,
        blank = True,
        verbose_name = _('Previous names.'),
        help_text = _('Please list your previous name (in case of marriage, for example)')
    )

    previous_exposure = models.BooleanField(
        default = False,
        verbose_name=_('Previous exposure'),
        help_text= _('Has there been work-related previous exposure to ionizing radiation?')
    )
    
    # --- Fields for RUBION-internal use

    is_validated = models.BooleanField(
        default = False,
        verbose_name = _('is the user validated')
    )
    has_agreed = models.BooleanField(
        default = False,
        verbose_name = _('has agreed')
    )

    is_rub = models.BooleanField(
        default = False,
        verbose_name = _('is a member of the RUB')
    )
    
    needs_safety_instructions =  ParentalManyToManyField(
        'userdata.SafetyInstructionsSnippet',
        verbose_name = _('user needs safety instruction'),
        help_text=_('Which safety instructions are required for the user?'),
        blank = True
    )

    key_number =  models.CharField(
        max_length = 64,
        blank = True,
        default = '',
        verbose_name = _('Key number')
    )

    labcoat_size = models.CharField(
        max_length = 6,
        blank = True,
        default = '',
        choices = (
            ('S', 'S'),
            ('M', 'M'),
            ('L', 'L'),
            ('XL', 'XL'),
            ('2XL', '2XL'),
            ('3XL', '3XL'),
            ('4XL', '4XL'),
            ('5XL', '5XL'),
        ),
        verbose_name = _('lab coat size'),
        help_text = _('The size of your lab coat.')
    )
    overshoe_size = models.CharField(
        max_length = 6,
        blank = True,
        default = '',
        choices = (
            ('2', 'S-M'),
            ('3', 'L-XL'),
            ('4', 'XXL or above'),
        ),
        verbose_name = _('shoe size'),
        help_text = _('The size your protecting shoes should have.')
    )
    entrance = models.CharField(
        max_length = 6,
        blank = True,
        default = '',
        choices = (
            ('0', 'NB'),
            ('1', 'NC'),
            ('2', 'ND'),
            ('3', 'NI 06'),
        ),
        verbose_name = _('Preferred entrance in the lab.')
    )
    initially_seen = ParentalManyToManyField(
        'userdata.StaffUser',
#        default = False,
        verbose_name = _('User seen by RUBION staff members'),
        blank = True
    )

    
    
    # --- Some simple permissions


    is_leader = models.BooleanField(
        default = False,
        verbose_name = _('leader of the group')
    )

    # Can be set by the group leader

    may_create_projects = models.BooleanField(
        default = False,
        verbose_name = _('may create projects')

    )
    may_add_members = models.BooleanField(
        default = False,
        verbose_name = _('May add members')
    )

    needs_key =  models.BooleanField(
        default = False,
        verbose_name = _('Does this user permanently need a key?')
    )

    dosemeter = models.CharField(
        max_length = 1,
        choices = DOSEMETER_CHOICES,
        default = NOT_YET_DECIDED,
        verbose_name = _('Type of dosemeter')
    )

    #--------------------------------------------------
    #
    # information for form building
    #
    #--------------------------------------------------
    
    admin_fields = [
        'key_number', 'is_group_leader', 'linked_user', 'title', 'title_de', 
        'is_validated', 'has_agreed', 'key_number', 'last_safety_instructions',
        'needs_safety_instructions', 'is_rub', 'dosemeter'
    ]
    group_head_fields = [
        'needs_key', 'may_add_members', 'may_create_projects'
    ]
    personal_fields = [
        'academic_title', 'phone', 'sex'
    ]


    #--------------------------------------------------
    #
    # edit handler definitions
    #
    #--------------------------------------------------
    content_panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('name_db'),
                FieldPanel('first_name_db'),
            ]),
            FieldPanel('email_db'),
            FieldPanel('preferred_language'),
            FieldPanel('academic_title'),
            FieldPanel('sex'),
        ], heading = _( 'personal information' )),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('date_of_birth'),
                FieldPanel('place_of_birth')
            ]),
            FieldRowPanel([
                FieldPanel('previous_names'),
                FieldPanel('previous_exposure')
            ]),
        ], heading=_('Additional personal data for radiation safety')),
    ]
    settings_panel = [
        MultiFieldPanel([
            FieldPanel('linked_user'),
            FieldRowPanel([
                FieldPanel('has_agreed'), 
                FieldPanel('is_validated'), 
            ]),
            FieldRowPanel([
                FieldPanel('is_rub'), 
                FieldPanel('is_leader'), 
            ]),
            
        ], heading = _('internal information')),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('may_create_projects'), 
                FieldPanel('may_add_members'), 
            ])
        ], heading = _( 'user permissions' )),
    ]
    rubion_panel =  [
        MultiFieldPanel([
            FieldPanel('dosemeter'), 
            FieldRowPanel([
                FieldPanel('labcoat_size'),
                FieldPanel('overshoe_size'),
            ]),
            FieldPanel('entrance'),
        ], heading = _('Safety')),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('needs_key', classname="col4"), 
                FieldPanel('key_number', classname="col8"),
            ])
        ], heading = _('Key')),
        MultiFieldPanel([
            InlinePanel('may_book', label=_('User may book')),
        ], heading = 'User permissions'),
    ]

    comment_panel = [
        FieldPanel('internal_rubion_comment')
    ]

    si_panel = [
        FieldPanel('needs_safety_instructions', widget=forms.CheckboxSelectMultiple), 
        InlinePanel(
            'rubion_user_si',
            panels = [
                FieldRowPanel([
                    FieldPanel('instruction'),
                    FieldPanel('date')
                ])
            ]
        )
    ]
    edit_handler = TabbedInterface([
        ObjectList(rubion_panel, heading=_('Settings set by RUBION') ),
        ObjectList(si_panel, heading=_('Safety instructions') ),
        ObjectList(comment_panel, heading=_('internal comments') ),
        ObjectList(settings_panel, heading=_('internal settings') ),
        ObjectList(content_panels, heading=_('User Data') ),

    ])


    #--------------------------------------------------
    #
    # CONSTRUCTOR
    #
    #--------------------------------------------------
    
    def __init__ ( self, *args, **kwargs):
        # The dont_clean-flag is used since I have some problems 
        # to ensure a populated title tag. 

        self.dont_clean = False
        super(RUBIONUser, self).__init__( *args, **kwargs)


        
    #--------------------------------------------------
    #
    # Properties
    #
    #--------------------------------------------------


    @property
    def name( self ):
        # name, first_name are taken from underlying website user
        # if it exists

        if self.name_db:
            return self.name_db
        else:
            if self.linked_user:
                return self.linked_user.last_name
            else:
                return None

    @property
    def last_name( self ):
        return self.name

    @property
    def first_name( self ):
        if self.name_db:
            return self.first_name_db
        else:
            if self.linked_user:
                return self.linked_user.first_name
            else:
                return None

    @property
    def email (self):
        if self.linked_user:
            return self.linked_user.email
        else:
            return self.email_db

    @property 
    def needs_dosemeter( self ):
        return any([inst.requires_dosemeter for inst in self._get_instruments()])

    @property 
    def needs_official_dosemeter( self ):
        return self.dosemeter == self.OFFICIAL_DOSEMETER


    @property 
    def dosemeter_not_set( self ):
        return self.dosemeter == self.NOT_YET_DECIDED



    @property 
    def needs_radiation_safety_data( self ):
        if self.dosemeter == self.OFFICIAL_DOSEMETER:
            return True
        if self.dosemeter == self.NOT_YET_DECIDED:
            return self.needs_dosemeter

        return False
        
    @property 
    def needs_labcoat( self ):
        return any([inst.requires_labcoat for inst in self._get_instruments()])

    @property 
    def needs_overshoes( self ):
        return any([inst.requires_overshoes for inst in self._get_instruments()])

    @property 
    def needs_entrance( self ):
        return any([inst.requires_entrance for inst in self._get_instruments()])



    @property
    def data_has_been_submitted( self ):
        return self.central_radiation_safety_data_submissions.exists()

    #--------------------------------------------------
    #
    # METHODS
    #
    #--------------------------------------------------


    
    # These methods are called from the parent class to see whether a 
    # a certain view (EDIT, etc) is allowed for the current user.

    def user_passes_test( self, user, what ):
        if user.is_anonymous:
            return False
        if user.is_superuser or user.is_staff or self.linked_user == user:
            return True

        try:
            r_user = RUBIONUser.objects.get(linked_user = user)
        except:
            r_user = None
            
        if r_user and r_user.get_workgroup() == self.get_workgroup() and what == self.VIEW:
            return True
        if ( r_user 
             and r_user.get_workgroup() == self.get_workgroup() 
             and r_user.is_leader 
             and what in [ self.EDIT, self.DELETE] 
         ):
            return True
        return False

    # For create views, we do not have an instance yet. Hence, this is a static method

    @staticmethod
    def user_passes_create_test( request, asking_page ):
        # superusers always pass
        if request.user.is_superuser:
            return True

        if request.user.is_anonymous:
            return False

        # Asking page is a UGCCreatePage2, most likely underneath a workgroup
        # get the workgroup

        wg = asking_page.get_parent().get_parent().specific
        
        # If the current user is not member of the work group, return False

        r_user = RUBIONUser.objects.get( linked_user = request.user )
        if r_user.get_workgroup() != wg:
            return False

        # if the user may add members or is leader, return true
        if r_user.may('member'):
            return True

        return False

    # These are shorthand functions for permissions set by the group-leader

    def may( self, what ):
        if what == 'project':
            return self.is_leader or self.may_create_projects
        if what == 'member':
            return self.is_leader or self.may_add_members

    def may_anything( self ):
        r = False
        for what in [ 'project', 'member' ]:
            r = r or self.may(what)
        return r
    
    # Test if a user has the permissions to book an instrument
    def can_book( self, instrument ):
        return (
            UserMayBookInstrumentRelation.objects
            .filter( page = instrument ).filter( user = self )
            .exists()
        )

        

    # render this instance as a child.
    # @TODO either populate this or delete it
    def as_child ( self ):
        return 

    # --- Helper methods
        
    # Clean tries to auto-populate the title. It is slightly weird
    def clean ( self ):
        if self.dont_clean:
            self.dont_clean = False

        else:
            self.title = "{}, {}".format(self.name, self.first_name)
            self.title_de = self.title

            if not self.slug:
                self.slug = self._get_autogenerated_slug( slugify( self.title ) )
    
    # returns the workgroup
    def get_workgroup( self ):
        # This is a very very specific solution. 
        return self.get_parent().get_parent().specific

    # Description for Admin-Views
    get_workgroup.short_description = _('workgroup')


    # Get the full name including academic title etc, depending on the language
    def full_name( self, language = None, include_first = False ):
        if language is None:
            language = translation.get_language()
            
        ns = ""
        if language == 'de':
            if self.sex == self.FEMALE:
                ns = 'Frau '
            elif self.sex == self.MALE:
                ns = 'Herr '
            else:
                ns = 'Frau/Herr '
                
            if self.academic_title == self.PROF:
                ns += 'Prof. Dr. {}'
            elif self.academic_title in [self.PHD, self.MD]:
                ns += 'Dr. {}'
            else:
                ns += '{}'

        else:
            if self.academic_title in [self.PROF, self.PHD, self.MD]:
                ns = "Dr. {}"
            elif self.sex == self.FEMALE:
                ns = "Ms. {}"
            elif self.sex == self.MALE:
                ns = "Mr. {}"
            else:
                ns = "Ms./Mr. {} "
            
        if include_first:
            ns = ns + ' {}'
            return ns.format(self.first_name, self.name)
        else:
            return ns.format(self.name)


    # Simple (static) check whether a user exists
    @staticmethod
    def exists( user ):
        return RUBIONUser.objects.filter(linked_user = user).exists()
        


    # Called by the Identification system. 
    # Should set the is_validated flag. 
    # @TODO this does not work yet. Don't know why.
    #
    # redirects to the edit-view of the instance
    def validate ( self, request, user, username ):
        pr = PageRevision.objects.filter(page = self).order_by('created_at').last()
        pr.approve_moderation()
        me = pr.as_page_object()
        me.linked_user = user
        me.is_validated = True 
        
        rev = me.save_revision_and_publish( user = request.user )
        return redirect (self.full_url + self.reverse_subpage('edit'))
        
    def serve_success ( self, request, edit = False ):
        pr = PageRevision.objects.filter(page = self).order_by('created_at').last()
        me = pr.as_page_object()
        if me.url != self.url:
            return redirect(me.url)
        return redirect(self.url)

    def inactivate ( self, user = None ):
        self.expire_at = datetime.datetime.now()

        if user:
            self.save_revision_and_publish( user = user )
        else:
            self.save_revision_and_publish()

        website_user = self.linked_user
        website_user.is_active = False
        website_user.save()

    #--------------------------------------------------
    #
    # Routing
    #
    #--------------------------------------------------
            
    @route(r'^edit/$')
    def edit( self, request ):
        from userinput.views import RUBIONUserEditView
        return RUBIONUserEditView.as_view()(request, instance = self)

    @route(r'^delete/$', name='delete')
    def delete_view( self, request ):
        try:
            user = RUBIONUser.objects.get(linked_user = request.user)
        except RUBIONUser.DoesNotExist:
            raise PermissionDenied
        if user.get_workgroup() != self.get_workgroup():
            raise PermissionDenied
        if not user.may('member'):
            raise PermissionDenied

        if request.method == 'GET':
            return TemplateResponse(
                request,
                'userinput/workgroup_delete_member.html',
                { 'ruser': self}
            )
        if request.method == 'POST':
            if request.POST['next'] == 'confirm':
                messages.success( request, _( '{} has been removed from your workgroup.'.format(self.title) ) )
                wg = self.get_workgroup()
                try:
                    self.linked_user.delete()
                except AttributeError:
                    pass
                self.inactivate()
                return redirect(wg.full_url)
            else:
                messages.info( request, _( 'Operation was canceled.' ) )
                return redirect(self.get_workgroup().full_url)
        



    #--------------------------------------------------
    #
    # helper methods
    #
    #--------------------------------------------------

    def _get_instruments( self ):
        wg = self.get_workgroup()
        if not wg:
            return []
        methods = wg.get_methods()
        if not methods:
            return []
        instruments = []
        for method in methods:
            for instrument in method.get_instruments():
                if instrument not in instruments:
                    instruments.append(instrument)
        return instruments


        
