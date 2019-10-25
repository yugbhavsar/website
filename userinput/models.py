from .admin_edit_forms import RUBIONUserAdminEditForm
import datetime 

from dateutil.relativedelta import relativedelta

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from instruments.mixins import (
    AbstractRelatedMethods, AbstractRelatedInstrument
)

from modelcluster.fields import ParentalKey, ParentalManyToManyField


from rubauth.models import Identification
#from .rubionuser import RUBIONUser
from ugc.models import (
    UserGeneratedPage2, UGCContainer2, UGCCreatePage2,
    UGCMainContainer2
)

from wagtail.contrib.routable_page.models import route
from wagtail.admin.edit_handlers import (
    FieldPanel, StreamFieldPanel, MultiFieldPanel,
    FieldRowPanel, InlinePanel, TabbedInterface, 
    ObjectList, PageChooserPanel 
)
from wagtail.core.models import Orderable, Page, PageRevision
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.models import register_snippet

from website.decorators import only_content, default_panels
from website.models import ( 
    TranslatedPage, TranslatedField,
    IntroductionMixin, AbstractContainerPage
)
from website.widgets import StyledDOIWidget



#
# ----------------------------------------------------------------------
#
# Models
#
# ----------------------------------------------------------------------


#__all__ = [WorkGroup, RUBIONUser, Project ]
class WorkGroup ( UserGeneratedPage2 ):
    subpage_types = [
        'userinput.MemberContainer',
        'userinput.ProjectContainer',

    ]
    parent_page_types = [ 'userinput.WorkGroupContainer' ]
    child_template = 'userinput/workgroup_child.html'
    view_template =  'userinput/workgroup_view.html'

    class Meta:
        verbose_name = _('workgroup')
        verbose_name_plural = _('workgroups')
        

    department_de = models.CharField(
        max_length = 64,
        blank = True,
        null = True,
        verbose_name = _('department (de)')
    )
    department_en = models.CharField(
        max_length = 64,
        blank = True,
        null = True,
        verbose_name = _('department (en)')
    )

    institute_en = models.CharField(
        max_length = 64,
        verbose_name = _('institute (en)')
    )
    institute_de = models.CharField(
        max_length = 64,
        verbose_name = _('institute (de)')
    )

    university_de = models.CharField(
        max_length = 64,
        verbose_name = _('university (de)')
    )
    university_en = models.CharField(
        max_length = 64,
        verbose_name = _('university (en)')
    )
        
    department = TranslatedField('department')
    institute = TranslatedField('institute')
    university = TranslatedField('university')

    homepage = models.CharField(
        max_length = 128,
        blank = True, null = True,
        verbose_name = _( 'internet address' ),
        help_text = _('Please include http:// or https:// and www, if required.')
    )

    content_panels = [
        MultiFieldPanel([
            FieldPanel('title_de'),
            FieldPanel('institute_de'),
            FieldPanel('department_de'),
            FieldPanel('university_de'),
        ], heading =_ ('German Information')),
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('institute_en'),
            FieldPanel('department_en'),
            FieldPanel('university_en'),
        ], heading =_ ('English Information')),
        MultiFieldPanel([
            FieldPanel('homepage'),
        ], heading =_ ('Additional Information')),
    ]
    comment_panel = [
        FieldPanel('internal_rubion_comment')
    ]

    edit_handler = TabbedInterface([
        ObjectList( content_panels, _('Information')),
        ObjectList( comment_panel, _('Internal comments')),
    ])

    @property
    def under_revision( self ):
        return self.has_unpublished_changes

    @property
    def is_active( self ):
        return self.get_projects().filter(expire_at__gte = datetime.datetime.now()).exists()

    def add_member_container( self ):
        # Generates a container for the workgroup members

        if len( MemberContainer.objects.child_of( self ) ) == 0:
            title = "Members"
            title_de = "Mitglieder"
            mc = MemberContainer()
            mc.title = title
            mc.title_de = title_de
            mc.slug = "members"
            self.add_child( instance = mc )

    def add_project_container( self ):
        # Generate a container for Projects
        
        if len( ProjectContainer.objects.child_of( self ) ) == 0:
            title = "Projects"
            title_de = "Projekte"
            pc = ProjectContainer()
            pc.title = title
            pc.title_de = title_de
            pc.slug = "project"
            self.add_child( instance = pc )

    def after_create_hook( self, request ):

        # Auto-generate child containers        
        self.add_member_container()
        self.add_project_container()

        # Adding a workgroup requires revision by RUBION
        
#        self.unpublish()
#        self.save_revision()

    def serve_success( self, request, edit = False ):
        if edit:
        # if edited, the workgroup is available
            return redirect( self.url )
        else:
        # Created, workgroup awaits verification. Show add user page to add work group leader
            ident = Identification()
            ident.page = self
            ident.create_user = True
            ident.login_user = True
            ident.mail_text = 'Workgroup.create.identify'
            ident.save()
            pk = ident.id
            return redirect( reverse('rubauth.identify', kwargs = {'pk' : pk}) )
 

    def create_project_page( self ):
        pc = ProjectContainer.objects.child_of(self).first()
        return UGCCreatePage2.objects.child_of(pc).first()

    def create_member_page( self ):
        mc = MemberContainer.objects.child_of(self).first()
        return UGCCreatePage2.objects.child_of(mc).first()

    def get_head( self ):
        return RUBIONUser.objects.live().descendant_of(self).filter(is_leader=True).first()
    
    # for displaying in the admin overview:
    get_head.short_description = _('Group leader')


    def get_members( self ):
        return RUBIONUser.objects.live().descendant_of(self).filter(expire_at__isnull = True)

    def get_projects( self ):
        return Project.objects.live().descendant_of(self)

    def get_methods( self ):
        
        projects = self.get_projects()
        methods = []
        for project in projects:
            pr_methods = project.get_methods()
            for method in pr_methods:
                if method not in methods:
                    methods.append(method) 

        return methods

    def create_group_leader ( self, user ):
        mc = MemberContainer.objects.child_of(self).first()
        group_leader = RUBIONUser()
        group_leader.is_leader = True
        group_leader.linked_user = user
        group_leader.owner = user
        group_leader.is_rub = user.username.find('@') == -1
        group_leader.may_create_projects = True

        if not group_leader.is_rub:
            group_leader.title = user.username
            group_leader.title_de = user.username
            group_leader.slug = slugify(user.username)

            # Avoid cleaning on save...
            group_leader.dont_clean = True
        else:
            group_leader.title = '{}, {}'.format(user.last_name, user.first_name)
            group_leader.title_de = '{}, {}'.format(user.last_name, user.first_name)
            group_leader.slug = slugify('{}, {}'.format(user.last_name, user.first_name))
            group_leader.first_name_db = user.first_name
            group_leader.last_name_db = user.last_name

        mc.add_child(group_leader)

        group_leader.save_revision(
            submitted_for_moderation = True,
            user = user
        )

        return group_leader

    def validate( self, request, user = None, username = None):
        if RUBIONUser.exists( user ):
            return TemplateResponse(
                request,
                'userinput/errors/user_has_workgroup.html',
                {
                    'user' : user
                }
            )
        else:
            self.save()
            r_user = self.create_group_leader( user )
            self.owner = r_user.linked_user
            self.save_revision(submitted_for_moderation = True, user = r_user.linked_user)
            
            return redirect (r_user.full_url + r_user.reverse_subpage('edit'))

    def user_passes_test( self, user, what ):
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        r_user = RUBIONUser.objects.get( linked_user = user )
        user_in_wg = r_user.get_workgroup() == self

        # Every RUBION-User may see the workgroups
        if what == self.VIEW:
            if self.under_revision:
                # Instead of returning False, which would result in a `403 Forbidden`
                # response, I raise a `404 Not found` here. A 403 would indicate that the group 
                # has applied to work in RUBION, which should be treated confidential.
                #
                # Of course, someone would have to guess the name of the group to construct 
                # the URL. But anyway...
                if  not user_in_wg:
                    raise Http404()

            return user.is_authenticated

        if what == self.EDIT:
            r_user = RUBIONUser.objects.get( linked_user = user )
            return r_user == self.get_head()
        
        return False

    def get_context(self, request):
        context = super(WorkGroup, self).get_context(request)
        context['user_may_edit'] = self.user_passes_test(request.user, self.EDIT)
        context['user_is_workgroup_member'] = False
        if request.user.is_authenticated:
            try:
                r_user = RUBIONUser.objects.get(linked_user = request.user)
            except:
                r_user = None
            if r_user:
                is_workgroup_member = ( r_user.get_workgroup() == self ) 
                context['user_is_workgroup_member'] = is_workgroup_member
                if is_workgroup_member:
                    context['user_may_add_projects'] = r_user.may('project')
                    context['user_may_add_members'] = r_user.may('member')
        return context


    def clean( self ):
        if not self.slug:
            self.slug = self._get_autogenerated_slug( slugify( self.title ) )

    def inactivate( self, user = None ):
        # inactivate this group.
        now = datetime.datetime.now()
        self.expire_at = now
        if user:
            self.save_revision_and_publish(user=user)
        else:
            self.save_revision_and_publish()

        for member in self.get_members():
            member.inactivate(user = user)

        for project in self.get_projects():
            if project.expire_at > now:
                project._close(user = user)
        
            

    def __str__( self ):
        if self.department:
            return '{}, {}, {}, {}'.format( self.title_trans, self.institute, self.department, self.university )
        else:
            return '{}, {}, {}'.format( self.title_trans, self.institute, self.university )

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
    
    # Form used in admin
    
    base_form_class = RUBIONUserAdminEditForm

    # Some additional information for the front-end

    front_end_verbose_name = _('workgroup member')
    front_end_verbose_name_plural = _('workgroup members')

    
    
    class Meta:
        verbose_name = _('RUBION User')
        verbose_name_plural = _('RUBION Users')

        permissions = (
            ('edit','Can edit RUBION User Information'),
        )

    parent_page_types = [ 'userinput.MemberContainer' ]
    subpage_types = []

    # The view template is used by UGC. this is the template that
    # is shown if this page object is delivered
    view_template = 'userinput/rubionuser_view.html'

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
    # --- Fields

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

    MALE = 'm'
    FEMALE = 'f'

    SEXES = (
        (MALE, _('male')),
        (FEMALE, _('female')),
    )

    sex = models.CharField(
        max_length = 1,
        choices = SEXES,
        blank = True,
        null = True,
        verbose_name = _('What is your gender?'),
        help_text = _('We ask this question to correctly address you in emails and letters send to you.')
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
    
    # Safety-instructions are not yet implemented

#    last_safety_instructions = models.DateField(
#        null = True,
#        blank = True
#    )
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

    # The dont_clean-flag is used since I have some problems 
    # to ensure a populated title tag. 
    
    def __init__ ( self, *args, **kwargs):
        self.dont_clean = False
        super(RUBIONUser, self).__init__( *args, **kwargs)
    
    # --- Shorthands

    # name, first_name are taken from underlying website user
    # if it exists

    @property
    def name( self ):
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

    # --- Permissions

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

    # --- Views
            
    @route(r'^edit/$')
    def edit( self, request ):
        from .views import RUBIONUserEditView
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
        if website_user:
            website_user.is_active = False
            website_user.save()
            
    # Admin content panels.
    # @TODO might require some clean-up
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

        
    


class Project ( UserGeneratedPage2 ):
    
    # --- Settings 

    parent_page_types = [ 'userinput.ProjectContainer' ]
    subpage_types = []

    # --- Templates
    view_template = 'userinput/project_view.html'

    
    # --- Fields
    summary_en = models.TextField(
        max_length = 1024,
        blank = False,
        null = False,
        verbose_name = _('project summary (en)'),
        help_text = _('Public summary of the project (in english).')
    )
    summary_de = models.TextField(
        max_length = 1024,
        blank = False,
        null = False,
        verbose_name = _('project summary (de)'),
        help_text = _('Public summary of the project (in german).')
    )

    is_confidential = models.BooleanField(
        default = False,
        verbose_name = _('hide project'),
        help_text = _('Is this project confidential? If you check this, it will not be visible to the public.')
    )

    uses_gmos = models.BooleanField(
        default = False,
        verbose_name = _('genetically modified organisms'),
        help_text = _('Does the project include working with genetically modified organisms?')
    )
    
    gmo_info = models.CharField(
        max_length = 1024,
        verbose_name = _('Information on GMOs'),
        help_text = _('Provide information about the GMOs you plan to use (safety level, cell type, ...)'),
        blank = True
    )

    uses_chemicals = models.BooleanField(
        default = False,
        verbose_name = _('Uses chemical compounds'),
        help_text = _('Does the project include working with chemical compounds'),
    )

    chemicals_info = models.CharField(
        max_length = 1024,
        verbose_name = _('Information on chemicals'),
        help_text = _('Provide information about the chemicals you plan to use (compound, amount, ...)'),
        blank = True
    )

    uses_hazardous_substances = models.BooleanField(
        default = False,
        verbose_name = _('Uses hazardous compounds'),
        help_text = _('Does the project include working with hazardous compounds'),

    )

    hazardous_info = models.CharField(
        max_length = 1024,
        verbose_name = _('Information on hazardous compunds'),
        help_text = _('Provide information about the hazardous compunds you plan to use (compound, amount, ...)'),
        blank = True
    )

    biological_agents = models.BooleanField(
        default = False,
        verbose_name = _('Ordinance on biological agents'),
        help_text = _('Does the project include work which underlies the Ordinance on Biological Agents')
    )
    
    bio_info = models.CharField(
        max_length = 1024,
        verbose_name = _('Information on biological agents'),
        help_text = _('Provide information about the biological agents you plan to use (agent, amount, ...)'),
        blank = True
    )
    

    funding_asked = models.BooleanField(
        default = False,
        verbose_name=_('has the user been asked to add funding?'),
        help_text =_('This is an auto-filled field. Do not change')
    )
    publications_asked = models.BooleanField(
        default = False,
        verbose_name=_('has the user been asked to add publications?'),
        help_text =_('This is an auto-filled field. Do not change')
    )
    theses_asked = models.BooleanField(
        default = False,
        verbose_name=_('has the user been asked to add theses?'),
        help_text =_('This is an auto-filled field. Do not change')
    )
    is_research = models.BooleanField(
        default = True,
        verbose_name=_('research'),
    )
    is_teaching = models.BooleanField(
        default = False,
        verbose_name=_('teaching'),
    )

    
    cnt_prolongations = models.IntegerField(
        default = 0,
        verbose_name = _('Prolongation counter'),
        help_text = ('How often the project has been prolongued without changes.' )
    )

    max_prolongations = models.IntegerField(
        default = 2,
        verbose_name = _('Maximum number of prolongations'),
        help_text = ('How often the project can be prolongued without changes.' )
    )
    
    @property 
    def can_prolong( self ):
        return self.cnt_prolongations < self.max_prolongations

    @property
    def under_revision( self ):
        return self.has_unpublished_changes

    # --- TranslatedFields

    summary = TranslatedField('summary')

    # --- AdminInterface

    summary_panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('is_research'),
                FieldPanel('is_teaching'),
            ])
        ], heading="Project type"),
        MultiFieldPanel([
            FieldPanel('title_de'),
            FieldPanel('summary_de'),
        ], heading = _('summary in german')),
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('summary_en'),
        ], heading = _('summary in english'))
    ]

    nuclide_panel = [
        InlinePanel('related_nuclides', label = _('Used Nuclides'))
    ]

    methods_panel = [
        InlinePanel('related_methods', label = _('methods'))
    ]

    related_items_panels = [
        InlinePanel('related_fundings', label = _('funding')),
        InlinePanel('related_publications', label = _('publications')),
        InlinePanel('related_theses', label = _('theses')),
    ]
    settings_panel = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('go_live_at'),
                FieldPanel('expire_at'),
            ]),
            FieldRowPanel([
                FieldPanel('cnt_prolongations'),
                FieldPanel('max_prolongations'),
            ]),
#            FieldPanel('is_confidential')
        ], heading =_( 'Expiration' )),
    ]
    comment_panel = [
        FieldPanel('internal_rubion_comment')
    ]

    edit_handler = TabbedInterface([
        ObjectList( methods_panel, _('Resources') ),
        ObjectList( nuclide_panel, _('Nuclides') ),
        ObjectList( related_items_panels, _('related items')), 
        ObjectList( summary_panels, _('description') ),
        ObjectList( settings_panel, _('Settings') ),
        ObjectList( comment_panel, _('Internal comment'))
    ])



    # METHODS

    # --- restrict views
    def user_passes_test( self, user, what, test_for_lock = True ):
        if test_for_lock:
            if what == self.EDIT and self.locked:
               return False

        if user.is_superuser:
            return True

        try:
            r_user = RUBIONUser.objects.get( linked_user = user )        
            is_workgroup_member = r_user.get_workgroup() == self.get_workgroup()
        except:
            is_workgroup_member = False

        # Everyone may see the project unless it is_confidential or under_revision
        if what == self.VIEW:
            if self.is_confidential or self.under_revision:
                # restrict to members of this group and RUBION-staff
                if user.is_staff or is_workgroup_member:
                    return True
                else:
                    # raise a 404 instead of a 403 to avoid indicating the project exists
                    raise Http404()
            else:
                return True

        if what == self.EDIT:
            # We might not have an r_user instance in case of anonymous users
            # In that case, is_workgroup_member is False.
            if is_workgroup_member:
                return r_user.may('project')
            else:
                return False

    @staticmethod
    def user_passes_create_test( request, asking_page ):
        if request.user.is_superuser:
            return True
        if request.user.is_anonymous:
            return False

        # allowed if user is workgroup member and my create projects        

        r_user = RUBIONUser.objects.get( linked_user = request.user )        
        designated_wg = asking_page.get_parent().get_parent().specific
        is_workgroup_member = ( designated_wg == r_user.get_workgroup() )

        return is_workgroup_member and r_user.may('project')

    
    # --- Automatically adding data
    def clean ( self ):
        if not self.slug:
            self.slug = self._get_autogenerated_slug( slugify ( self.title ) )
    
    # --- Additional views
    
    def add_relation( self, request, Model, RelationModel, tpl, **kwargs):
        ''' 
        This method adds a relation_model between the project and a snippet. 
        If kwargs['has_been_asked_field'] is present, it updates the field to True 
        if it is False, ensuring that every relation has been asked at least once.
        '''
        try:
            has_been_asked_field = kwargs.pop('has_been_asked_field')
        except:
            has_been_asked_field = None

        try:
            proceed_with = kwargs.pop('proceed_with')
        except:
            proceed_with = None

        try:
            instance = kwargs.pop('instance')
            rel = RelationModel.objects.get(snippet_id = instance.id)
            if rel.project_page_id != self.id:
                raise PermissionDenied()
        except KeyError:
            instance = None
        has_been_asked = True
        if has_been_asked_field and getattr(self, has_been_asked_field) == False:
            has_been_asked = False
            setattr(self, has_been_asked_field, True)

        ModelForm = modelform_factory( Model, exclude = ['is_duplicate'], **kwargs )

        # An inline function for proceeding.
        def proceed():
            if proceed_with:
                try:
                    was_asked = getattr(self, proceed_with['field'])
                except AttributeError:
                    was_asked = True
                if not was_asked:
                    return redirect( self.full_url + self.reverse_subpage( proceed_with['target'] ) )
            return redirect( self.full_url )

            
        if request.method == 'POST':
            if request.POST['next'] == 'cancel':
                return proceed()
            if instance:
                form = ModelForm( request.POST, instance = instance )
            else:
                form = ModelForm(request.POST)
            if form.is_valid():
                inst = form.save()
                if not instance:
                    relation = RelationModel()
                    relation.project_page_id = self.id
                    relation.snippet_id = inst.id
                    relation.save()
                    
                    if not self.under_revision:
                        self.expire_at = datetime.datetime.now() + relativedelta(years=1)
                        self.cnt_prolongations = 0
                        self.save_revision_and_publish( user = request.user )
                    
                try:
                    msg_type = Model.verbose_name
                except AttributeError:
                    msg_type = 'data'
                if instance:
                    messages.success( request, 'The {} has been updated.'. format(msg_type) )
                else:
                    messages.success( request, 'The {} has been added to the project.'. format(msg_type) )
                nxt = request.POST.get('next')
                if nxt in ['add_publication', 'add_funding', 'add_thesis']:
                    return redirect (self.full_url + self.reverse_subpage( nxt ))
                else:
                    return proceed()
                    
            else:
                messages.error( request, _('An error occured.') )
        else:
            if instance:
                form = ModelForm( instance = instance )
            else:
                form = ModelForm()
        context = {}
        context['form'] = form
        context['page'] = self
        context['has_been_asked'] = has_been_asked 
        return TemplateResponse(
            request,
            tpl,
            context
        )
        



    @route(r'^edit_publication/(\d+)/$', name="edit_publication")
    @route(r'^add_publication/$')
    def add_publication( self, request, pk=None ):
        if self.user_passes_test(request.user, self.EDIT):
            kwargs = {}
            if pk:
                instance = get_object_or_404( PublicationSnippet, pk = pk)
                kwargs['instance'] = instance
            return self.add_relation( 
                request, 
                PublicationSnippet, 
                Project2PublicationRelation,
                'userinput/project_add_publications.html',
                widgets = {'doi' : StyledDOIWidget},
                has_been_asked_field = 'publications_asked',
                proceed_with = {
                    'field' : 'theses_asked',
                    'target': 'add_thesis'
                },
                **kwargs
            )
        else:
            raise PermissionDenied

    @route(r'^edit_funding/(\d+)/$', name="edit_funding")
    @route(r'^add_funding/$')
    def add_funding( self, request, pk = None ):
        if self.user_passes_test(request.user, self.EDIT):
            kwargs = {}
            if pk:
                instance = get_object_or_404( FundingSnippet, pk = pk)
                kwargs['instance'] = instance
            return self.add_relation( 
                request, 
                FundingSnippet, 
                Project2FundingRelation,
                'userinput/project_add_funding.html',
                has_been_asked_field = 'funding_asked',
                proceed_with = {
                    'field' : 'publications_asked',
                    'target': 'add_publication'
                },
                **kwargs
            )
        else:
            raise PermissionDenied

    @route(r'^edit_thesis/(\d+)/$', name="edit_thesis")
    @route(r'^add_thesis/$')
    def add_thesis( self, request, pk = None ):
        if self.user_passes_test(request.user, self.EDIT):
            kwargs = {}
            if pk:
                instance = get_object_or_404( ThesisSnippet, pk = pk)
                kwargs['instance'] = instance
            return self.add_relation( 
                request, 
                ThesisSnippet, 
                Project2ThesisRelation,
                'userinput/project_add_thesis.html',
                has_been_asked_field = 'theses_asked',
                **kwargs
            )
        else:
            raise PermissionDenied

    @route(r'^delete_theses/(\d+)/$', name="delete_thesis")
    def delete_thesis( self, request, pk ):
        if self.user_passes_test(request.user, self.EDIT):
            instance = get_object_or_404( ThesisSnippet, pk = pk )
            return self.delete_relation( 
                request,
                ThesisSnippet, 
                Project2ThesisRelation,
                instance,
                object_title = "{} ({}): {}".format(instance.author, instance.year, instance.title),
                object_type = _('thesis')
            )
        else:
            raise PermissionDenied

    @route(r'^delete_publication/(\d+)/$', name="delete_publication")
    def delete_publication( self, request, pk ):
        if self.user_passes_test(request.user, self.EDIT):
            instance = get_object_or_404( PublicationSnippet, pk = pk )
            return self.delete_relation( 
                request,
                PublicationSnippet, 
                Project2PublicationRelation,
                instance,
                object_title = "{}: {}. {} {}".format(instance.authors, instance.title, instance.journal, instance.year),
                object_type = _('publication')
            )
        else:
            raise PermissionDenied

    @route(r'^delete_funding/(\d+)/$', name="delete_funding")
    def delete_funding( self, request, pk ):
        if self.user_passes_test(request.user, self.EDIT):
            instance = get_object_or_404( FundingSnippet, pk = pk )
            return self.delete_relation( 
                request,
                FundingSnippet, 
                Project2FundingRelation,
                instance,
                object_title = "{}: {}".format(instance.agency, instance.title),
                object_type = _('funding')
            )
        else:
            raise PermissionDenied

    def delete_relation(self, request, SnippetModel, RelationModel, instance, **kwargs):
        rel = RelationModel.objects.get(snippet_id = instance.id)
        if rel.project_page_id != self.id:
            raise PermissionDenied()
        
        if request.method == 'GET':
            context = kwargs
            context['project_title'] = self.title_trans
            return TemplateResponse(
                request,
                'userinput/project_delete_relation.html',
                context
            )
        if request.method == 'POST':
            if request.POST['next'] == 'confirm':
                rel = get_object_or_404( RelationModel, snippet_id = instance.id )
                messages.success( request, "The {} »{}« was deleted.".format(kwargs['object_type'], kwargs['object_title']) )
                rel.delete()
                instance.delete()

            return redirect( self.full_url )

    @route(r'^prolong/$', name="prolong")
    def prolong( self, request ):
        if self.user_passes_test( request.user, self.EDIT):
            if request.method == 'GET':
                return TemplateResponse(
                    request,
                    'userinput/prolong_project.html',
                    { 'page' : self }
                )
            elif request.method == 'POST':
                if request.POST['next'] == 'prolong':
                    if self.can_prolong:
                        self.expire_at = datetime.datetime.now() + relativedelta (years = 1)
                        self.cnt_prolongations += 1
                        self.save_revision_and_publish( user = request.user )
                        messages.info( request, _('The project was extended by one year.' ) )
                    else:
                        messages.error( request, _('The project cannot be extended anymore. Please contact the RUBION team.' ) )
                else:
                    messages.info( request, _( 'Operation was canceled.' ) )
                return redirect(self.full_url)
        raise PermissionDenied

    @route(r'^close/$', name="close")
    def close( self, request ):
        if self.user_passes_test( request.user, self.EDIT):            
            if request.method == 'GET':
                return TemplateResponse(
                    request,
                    'userinput/close_project.html',
                    { 'page' : self }
                )
            elif request.method == 'POST':
                if request.POST['next'] == 'close':
                    self._close(user = request.user)
                    messages.info( request, _('The project was closed.' ) )
                    return redirect(self.get_parent().full_url)
                else:
                    messages.info( request, _( 'Operation was canceled.' ) )
                return redirect(self.full_url)
        raise PermissionDenied


    def _close(self, user = None ):
        self.expire_at = datetime.datetime.now() + relativedelta (seconds = -1)
        self.locked = True
        if user:
            self.save_revision_and_publish( user = user )
        else:
            self.save_revision_and_publish()

        
    # --- Successful creation of new project

    def serve_success ( self, request, edit = False ):
        if edit:
            return redirect( self.full_url )
        else:
            return redirect( self.full_url + self.reverse_subpage('add_funding') )


    # --- render a project in the list of projects

    def render_as_child ( self ):
        return render_to_string(
            'userinput/project_child.html',
            { 
                'page' : self,
                
            }
        )

    # --- get workgroup for project
    def get_workgroup( self ):
        return self.get_parent().get_parent().specific

    # --- get info about workgroup
    def get_workgroup_info( self ):
        wg = self.get_workgroup()
        return "{}, {}, {}".format(
            wg.title_trans,
            wg.institute,
            wg.university
        )
            
    def get_methods( self ):
            
        methods = []

        for p2m in Project2MethodRelation.objects.filter(project_page = self):
            if p2m not in methods:
                methods.append(p2m.page) 

        return methods


    def get_context(self, request):

        context = super(Project, self).get_context( request )
        context['user_may_change_project'] = self.user_passes_test( request.user, self.EDIT, test_for_lock = False )
        UserModel = get_user_model()
        
        if self.expire_at:
            if (datetime.datetime.now() + relativedelta(months=1)) > self.expire_at:
                context['will_expire_soon'] = True                

        # @TODO the owner_id is not set on pages? It seems to be available 
        # through the revisions
        #context['owner'] = UserModel.objects.get(pk = self.owner_id)
        return context



@only_content    
class MemberContainer ( UGCContainer2 ):
    subpage_types = [ UGCCreatePage2, 'userinput.RUBIONUser' ]
    parent_page_types = [ WorkGroup ]
    for_model = RUBIONUser
    content_panels = [
        FieldPanel( 'title' ),
        FieldPanel( 'title_de' ),
        StreamFieldPanel( 'introduction_en' ),
        StreamFieldPanel( 'introduction_de' ),
    ]

    def get_visible_children( self ):
        return RUBIONUser.objects.child_of(self).order_by('title')

@only_content
class ProjectContainer ( UGCContainer2 ):
    create_title = "Apply for Project"
    create_title_de = "Projekt beantragen"
    is_creatable = False
    subpage_types = [ UGCCreatePage2, Project ]
    parent_page_types = [ WorkGroup ]
    for_model = Project

    sidebar_text = _('''
<h3>Information</h3>
<p>The information about your project will be publicly available on our website</p>
<p>If your project should be treated confidential, please check "Hide Project"</p>
<p>Select all methods you think you will use in this project.</p>
<p>Use the last field to explain your project to us in more detail.</p>
    ''')
    
    content_panels = [
        FieldPanel( 'title' ),
        FieldPanel( 'title_de' ),
        StreamFieldPanel( 'introduction_en' ),
        StreamFieldPanel( 'introduction_de' ),
    ]
    def get_visible_children( self ):
        return Project.objects.child_of(self)

@only_content
class WorkGroupContainer ( UGCContainer2 ):
    is_creatable = False
    create_title = "Apply for Workgroup registration"
    create_title_de = "Aufnahme der Arbeitsgruppe beantragen"
    template = 'userinput/list_of_workgroups_page.html'
    subpage_types = [ WorkGroup, UGCCreatePage2 ]
    parent_page_types = [ 'website.StartPage' ]
    for_model = WorkGroup

    content_panels = [
        FieldPanel( 'title' ),
        FieldPanel( 'title_de' ),
        StreamFieldPanel( 'introduction_en' ),
        StreamFieldPanel( 'introduction_de' ),
    ]

    def get_visible_children( self ):
        if translation.get_language() == 'de':
            order = 'title_de'
        else:
            order = 'title'
        return WorkGroup.objects.filter(has_unpublished_changes = False).order_by(order)

    def get_context( self, request ):
        context = super(WorkGroupContainer, self).get_context(request)
        context['workgroups'] = self.get_visible_children()
        return context

# ----------------------------------------------------------------------
#
# AbstractRelations
#
# ----------------------------------------------------------------------

class AbstractNuclideRelation( Orderable ):
   snippet = models.ForeignKey(
       'userinput.Nuclide',
       related_name = 'related_nuclides',
       verbose_name = _('Isotope'),
       on_delete = models.CASCADE
   )
   
   panels = [ 
       SnippetChooserPanel('snippet')
   ]

   class Meta:
       abstract = True

class AbstractThesisRelation( Orderable ):
    snippet = models.ForeignKey(
        'userinput.ThesisSnippet',
        related_name = 'related_theses',
        on_delete = models.CASCADE
    )
    panels = [
        SnippetChooserPanel('snippet')
    ]
    class Meta:
        abstract = True

class AbstractPublicationRelation( Orderable ):
    snippet = models.ForeignKey(
        'userinput.PublicationSnippet',
        related_name = 'related_publications',
        on_delete = models.CASCADE
        
    )
    panels = [
        SnippetChooserPanel('snippet')
    ]
    class Meta:
        abstract = True

class AbstractFundingRelation( Orderable ):
    snippet = models.ForeignKey(
        'userinput.FundingSnippet',
        related_name = 'related_fundings',
        on_delete = models.CASCADE
    )
    panels = [
        SnippetChooserPanel('snippet')
    ]
    class Meta:
        abstract = True


# ----------------------------------------------------------------------
#
# Relations 
## ----------------------------------------------------------------------

class Project2MethodRelation( AbstractRelatedMethods ):
    project_page = ParentalKey( Project, related_name = 'related_methods')

    panels = [
        PageChooserPanel('page', 'instruments.MethodPage'),
    ]

class Project2FundingRelation( AbstractFundingRelation ):
    project_page = ParentalKey( Project, related_name = 'related_fundings')
    panels = AbstractFundingRelation.panels

class Project2PublicationRelation( AbstractPublicationRelation ):
    project_page = ParentalKey( Project, related_name = 'related_publications')
    panels = AbstractPublicationRelation.panels

class Project2ThesisRelation( AbstractThesisRelation ):
    project_page = ParentalKey( Project, related_name = 'related_theses')
    panels = AbstractThesisRelation.panels

class Project2NuclideRelation( AbstractNuclideRelation ):
   project_page = ParentalKey( Project, related_name = 'related_nuclides')
   max_order = models.CharField (
       max_length = 8,
       blank = True,
       null = True,
       verbose_name = _('max amount per order (in MBq)')
   )
   amount_per_experiment = models.CharField (
       blank = True,
       null = True,
       max_length = 8,
       verbose_name = _('estimated amount per experiment (in MBq)')
   )
   room = models.CharField(
       max_length = 8,
       null = True,
       blank = True,
       verbose_name = _('room')
   )

   panels = AbstractNuclideRelation.panels + [ 
       FieldPanel('max_order'), 
       FieldPanel('amount_per_experiment'),
       FieldPanel('room'),

   ]

class UserMayBookInstrumentRelation( AbstractRelatedInstrument ):
    user = ParentalKey( RUBIONUser, related_name = 'may_book' )
    panels = [ PageChooserPanel('page', ['instruments.InstrumentPage']) ]


# ----------------------------------------------------------------------
#
# Snippets 
#
# ----------------------------------------------------------------------

@register_snippet
class FundingSnippet( models.Model ):
    class Meta:
        verbose_name = _('Project funding')
        verbose_name_plural = _('Project fundings')
        
    agency = models.CharField(
        max_length = 64,
        blank = False,
        null = False,
        verbose_name = _('funding agency')
    )
    project_number = models.CharField(
        max_length = 64,
        blank = False,
        null = False,
        verbose_name = _('project ID')
    )
    title_en = models.CharField(
        max_length = 256,
        blank = False,
        null = False,
        verbose_name = _('project title (english)'),
    )
    title_de = models.CharField(
        max_length = 256,
        blank = True,
        null = True,
        verbose_name = _('project title (german)'),
    )
    title = TranslatedField('title')
    project_url = models.CharField(
        max_length = 128,
        blank = True,
        null = True,
        verbose_name = _('project url'),
    )
    def __str__(self):
        return self.title_en
        
@register_snippet
class PublicationSnippet ( models.Model ):
    class Meta:
        verbose_name = _('Publication in a scientific journal')
        verbose_name_plural = _('Publications in scientific journals')
    doi = models.CharField(
        max_length = 32,
        blank = True,
        null = True
    )
    authors = models.CharField(
        max_length = 256,
        blank = False,
        null = False,
        verbose_name = _('authors'),
        help_text = _('comma separated list of authors')
    )
    title = models.CharField(
        max_length = 256,
        blank = False,
        null = False,
        verbose_name = _('title'),
        help_text = _('title of the publication')
    )
    journal = models.CharField(
        max_length = 128,
        blank = False,
        null = False,
        verbose_name = _('journal')
    )
    volume = models.CharField(
        max_length = 16,
        blank = False,
        null = False,
        verbose_name = _('volume')
    )
    year = models.IntegerField(
        blank = False,
        null = False,
        verbose_name = _('year')
    )
    pages = models.CharField(
        blank = True,
        null = True,
        max_length = 32,
        verbose_name = _('pages')
    )
    is_duplicate = models.BooleanField(
        default = False
    )



    def __str__(self):
        return self.title


@register_snippet
class ThesisSnippet( models.Model ):
    HAB = 'h'
    PHD = 'p'
    MS  = 'm'
    BS  = 'b'

    THESES_TYPES = [
        (HAB, _('Habilitation')),
        (PHD, _('PhD thesis')),
        (MS,  _('Master\'s thesis')),
        (BS,  _('Bachelor\'s thesis'))
    ]

    thesis_type = models.CharField(
        max_length = 1,
        blank = False,
        null = False,
        choices = THESES_TYPES,
        verbose_name = _('theses type (Bachelor, Master or PhD)')
    )
    title = models.CharField(
        max_length = 256,
        blank = False,
        null = False,
        verbose_name = _('title'),
        help_text = _('title of the thesis')
    )
    author = models.CharField(
        max_length = 128,
        blank = False,
        null = False,
        verbose_name = _('author')
    )
    year = models.IntegerField(
        blank = False,
        null = False,
        verbose_name = _('year')
    )
    url = models.CharField(
        max_length = 256,
        blank = True,
        null = True,
        verbose_name = _('internet address')
        
    )

    def __str__(self):
        return self.title



@default_panels
class ListOfProjectsPage ( AbstractContainerPage ):
    subpage_types = []
    template = 'userinput/list_of_projects_page.html'

    is_creatable = False

    def get_visible_children( self, active = True ):
        if translation.get_language() == 'de':
            title_field = 'title_de'
        else:
            title_field = 'title'
        pages = (Project.objects.live().
                 filter(is_confidential = False).
                 filter(has_unpublished_changes = False).
                 filter(locked = (not active) ) 
        )
                

        return pages.order_by(title_field)

    def get_context( self, request ):
        context = super(ListOfProjectsPage, self).get_context(request)
        if request.GET.get('status', None) == 'closed':
            context['projects'] = self.get_visible_children( active = False )
            context['show_active'] = False
        else:
            context['projects'] = self.get_visible_children()
            context['show_active'] = True
        return context
            

@register_snippet
class UserComment ( models.Model ):
    page = models.ForeignKey( Page, on_delete = models.CASCADE )
    text = models.TextField() 
    created_at = models.DateTimeField(
        auto_now_add = True
    )
    is_creatable = False
    
    
@register_snippet
class Nuclide ( models.Model ):
    element = models.CharField(
        max_length = 3,
        verbose_name = _('Element')
    )

    mass = models.IntegerField(
        null = True,
        blank = True,
        verbose_name = _('Isotope mass')
    )

    def __str__(self):
        return "{}-{}".format(self.element, self.mass)


