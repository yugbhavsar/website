"""
The models in the package implement a way to deal with user data.
It goes well behind additional data for user accounts, but implements 
this, too.
"""
from django import forms
from django.conf import settings
from django.db import models
from django.http import Http404
from django.utils import translation
from django.utils.translation import ugettext_lazy as _, get_language
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from modelcluster.fields import ParentalKey, ParentalManyToManyField

from rubion.helpers import get_unique_value

from userinput.models import RUBIONUser

from wagtail.admin.edit_handlers import (
    FieldPanel, StreamFieldPanel, MultiFieldPanel,
    FieldRowPanel, InlinePanel, TabbedInterface, 
    ObjectList
)

from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable, ClusterableModel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.models import register_snippet

from website.decorators import simple_panels, only_content
from website.models import AbstractContainerPage, TranslatedPage, ChildMixin, TranslatedField
#from website.edit_handlers import InlinePanelForForeignKey
#

@simple_panels
class UserContainer ( AbstractContainerPage, ChildMixin ):
    '''
    Users can be split into different types, such 
    as staff, directors or users.
    
    Since a `UserContainer` can be a child of `UserContainer`, 
    it derives from both `AbstractContainerPage` and `AbstractChildPage`. 
    '''


    # This model does not need a body
    body = None
    
    # allowed in
    parent_page_types = [
#        'website.StartPage', 
        'userdata.UserContainer',
    ]

    # allows
    subpage_types = [
        'userdata.UserContainer',
        'userdata.StaffUser',
#        'userdata.WebsiteUser'
    ]

    # possibility to hide users from the parent list
    
    show_in_list = models.BooleanField(
        default = True,
        verbose_name = _( 'show in lists?' ),
        help_text = _( 'if this is not checked, this group and its members are not shown in the parent list' )
    )

    content_panels_de = [
        FieldPanel( 'title_de' ),
        StreamFieldPanel( 'introduction_de' ),
    ]
    content_panels_en = [
        FieldPanel( 'title' ),
        StreamFieldPanel( 'introduction_en' ),
    ]

    settings_panels = [
        FieldPanel('show_in_list'),
        FieldPanel( 'slug' )
    ]

    # Templates
    child_template = 'userdata/user_container_in_list.html'
    template = 'userdata/userdata_container.html'

    def render_as_child( self ):
        """This method can be overriden to pass additional context to the `child_template`."""
        return render_to_string(
            self.child_template,
            {
                'page': self,
            }
        )
    
    def get_visible_children( self ):
        children = StaffUser.objects.live().child_of(self)
        if len ( children ) > 0:
            sort_fields = ['first_name', 'last_name']
        else:
            children = UserContainer.objects.live().child_of(self)
            sort_fields = []
            
        for f in sort_fields:
            children = children.order_by(f)

        return children

    class Meta:
        verbose_name = _('group of persons')

@only_content
class StaffUser ( TranslatedPage ):
    '''
    This class implements a RUBION staff member.
    '''

    
    parent_page_types = [ 'userdata.UserContainer' ]

    # A staff member is usually connected to a Wagtauil user, but 
    # some (Director, Vice director) are not
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank = True,
        null = True,
        on_delete = models.SET_NULL
    )

    # To be consistent with the definition in RUBIONUser I
    # introduce the field `linked_user`
    #
    # Bad design... :-(
    @property
    def linked_user( self ):
        return self.user

    # Academic grade
    grade = models.CharField(
        max_length = 20, verbose_name = _( 'academic title' ),
        null = True, blank = True,
    )

    # We need a name if no user is connected
    first_name = models.CharField(
        max_length = 100, verbose_name = _( 'first name' ),
        null = True, blank = True,
    )
    last_name = models.CharField(
        max_length = 100, verbose_name = _( 'name' ),
        null = True, blank = True,
    )

    # ...and an e-mail-address, if not connected to a user
    email = models.EmailField(
        null = True, blank = True,
        help_text = _( 'only required if no user is connected.' ),
    )

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
        verbose_name = _('Gender'),
    )


    # # Some more stuff...
    # role_en = models.CharField(
    #     max_length = 255, verbose_name = _( 'role' ),
    #     help_text = _( 'comma-separated roles of the staff member. (en)' )
    # )
    # # Some more stuff...
    # role_de = models.CharField(
    #     max_length = 255, verbose_name = _( 'role' ),
    #     help_text = _( 'comma-separated roles of the staff member. (de)' )
    # )

    institute_en = models.CharField(
        max_length = 128,
        default = 'RUBION',
        verbose_name = _('Department or company (default RUBION), in english')
    )
    institute_de = models.CharField(
        max_length = 128,
        default = 'RUBION',
        verbose_name = _('Department or company (default RUBION), in german')
    )
    institute = TranslatedField('institute')
    room = models.CharField(
        max_length = 20, verbose_name = _( 'room' ),
    )
    phone = models.CharField( max_length = 64, verbose_name = _( 'phone' ),  )
    fax = models.IntegerField( 
        null = True, blank = True, 
        verbose_name = _( 'fax' ) )

    link = models.URLField(
        max_length = 200, verbose_name = _( 'homepage' ),
        blank = True, null = True
    )

    picture = models.ForeignKey(
        'wagtailimages.Image',
        null = True, blank = True,
        on_delete = models.SET_NULL,
        related_name = '+'
    )

    orcid = models.CharField(
        max_length = 19,
        null = True, blank = True,
        verbose_name = _( 'Orcid-ID' )
    )

    researchgate = models.CharField(
        max_length = 64,
        null = True, blank = True,
        verbose_name = _( 'research gate profile link' ),
        help_text = _( 'the XXX-part of the URL: <https://www.researchgate.net/profile/XXX>' )
    )

    gnd = models.CharField(
        max_length = 16,
        null=True, blank = True,
        verbose_name = _( 'GND id'),
        help_text = _('used to link to RUB\'s research bibliography') 
    )

    key_number = models.CharField(
        max_length = 64,
        blank = True,
        default = '',
        verbose_name = _('Key number')
    )

    needs_safety_instructions =  ParentalManyToManyField(
        'userdata.SafetyInstructionsSnippet',
        verbose_name = _('user needs safety instruction'),
        help_text=_('Which safety instructions are required for the user?'),
        blank = True
    )

    comment = RichTextField(
        blank = True,
        verbose_name = _('Comment')
    )
    
    content_panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel( 'last_name' ),
                FieldPanel( 'first_name' ),
                FieldPanel( 'grade'),
            ]),
            FieldRowPanel([
                FieldPanel('institute_de'),
                FieldPanel('institute_en'),
            ])
        ], heading= _('Personal information')),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel( 'user' ),
                FieldPanel( 'email' ),
                FieldPanel('sex'),

            ]),
            ImageChooserPanel ( 'picture' ),
        ], heading = _( 'additional information')),
        InlinePanel('roles', label = _('Staff roles')),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel( 'room' ),
                FieldPanel( 'phone' ),
            ]),
            FieldRowPanel([
                FieldPanel( 'fax' ),
                FieldPanel( 'key_number' )
            ])
        ], heading = _('contact details') ),

        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('orcid'),
                FieldPanel('researchgate'),
                FieldPanel('gnd')
            ]),
            FieldPanel( 'link' ),
        ], heading = _('links') ),

    ]

    si_panel = [
        MultiFieldPanel([
            FieldPanel('needs_safety_instructions', widget=forms.CheckboxSelectMultiple),
            
        ], heading = _('Required safety instructions')),
        MultiFieldPanel([
             InlinePanel(
                 'staff_user_si',
                 panels=[
                     FieldRowPanel([
                         FieldPanel('instruction'),
                         FieldPanel('date')
                     ], classname='label-above')
                 ]
             )
        ], heading=_('Safety Instruction Dates') )
    ]
    
    comment_panel = [
        FieldPanel( 'comment' )
    ]




    
    @property 
    def mail ( self ):
        return self.get_email()

    def get_email( self ):
        if self.user:
            return self.user.email
        else:
            return self.email
    def get_first_name( self ):
        if self.user:
            return self.user.first_name
        else:
            return self.first_name
    def get_last_name( self ):
        if self.user:
            return self.user.last_name
        else:
            return self.last_name

    def full_name( self, language = None, include_first = False ):
        if language is None:
            language = translation.get_language()
            
        ns = "{}"
            
        if include_first:
            ns = ns + ' {}'
            return ns.format(self.get_first_name(), self.get_last_name())
        else:
            return ns.format(self.get_last_name())

        
    
    def clean(self):
        super( StaffUser, self ).clean()
        self.title = "%s, %s" % ( self.last_name, self.first_name )
        self.title_de = "%s, %s" % ( self.last_name, self.first_name )
        self.slug = "%s-%s" % ( self.last_name, self.first_name )

    def has_connections(self):
        return self.orcid is not None or self.researchgate is not None or self.gnd is not None
    
    child_template = 'userdata/staff_user_in_list.html'
    template = 'userdata/staff_user.html'

    def render_as_child( self ):
        roles = []
        for r in self.roles.all():
            if r.show_in_list:
                roles.append(str(r.role))
        if roles:
            roles_str = ', '.join(roles)
        else:
            roles_str = None
        return render_to_string(
            self.child_template,
            { 
                'self' : self, 
                'roles' : roles_str
            }
        )

    def serve( self ):
        raise Http404('The page does not exist')


    

    class Meta:
        verbose_name = _('staff member')
        verbose_name_plural = _('staff members')


# Does not work inside the class for some reason...
        
StaffUser.edit_handler = TabbedInterface([
    ObjectList( StaffUser.content_panels, _('Data')),
    ObjectList( StaffUser.comment_panel, _('Comments')),
    ObjectList( StaffUser.si_panel, _('Safety instructions')),
])
        
### Tasks for Staff Members

@register_snippet
class StaffRoles( ClusterableModel ):
    class Meta:
        verbose_name = _('staff role')
        verbose_name_plural = _('staff roles')

    role_de = models.CharField(
        max_length = 128,
    )
    role_en = models.CharField(
        max_length = 128,
    )

    role = TranslatedField('role')

    def __str__( self ):
        return self.role

class StaffUser2RoleRelation( Orderable ):
     roles = ParentalKey(
         'StaffUser', related_name = 'roles',
         
     )
    
     role = models.ForeignKey(
         StaffRoles,
         on_delete = models.CASCADE
     )
     
     show_in_list = models.BooleanField(
         default = False,
         help_text = _('Show this role in the staff listing?')
     )

     panels = [ SnippetChooserPanel( 'role' ), FieldPanel ('show_in_list') ]

@register_snippet
class SafetyInstructionsSnippet( models.Model ):
    class Meta:
        verbose_name = _('Available safety instruction')
    
    title_en = models.CharField(
        max_length = 256
    )
    title_en_short = models.CharField(
        max_length = 64
    )
    title_de = models.CharField(
        max_length = 256
    )
    title_de_short = models.CharField(
        max_length = 256
    )
    contains_general_safety_info = models.BooleanField(
        default = True,
        verbose_name = _('General safety included'),
        help_text = _('Does this instruction include general safety information?')
    )
    contains_general_safety_info_radionuclides = models.BooleanField(
        default = True,
        verbose_name = _('Radionuclide lab safety included'),
        help_text = _('Does this instruction include general safety information for the isotope laboratory?')
    )
    contains_general_safety_info_accelerators = models.BooleanField(
        default = True,
        verbose_name = _('Accelerator lab safety included'),
        help_text = _('Does this instruction include general safety information for the accelerator labs?')
    )
    contains_p38_safety_info = models.BooleanField(
        default = True,
        verbose_name = _('$38 included'),
        help_text = _('Does this instruction include radiation sfaety according to §38 StrlSchV?')
    )

    contains_laser_safety = models.BooleanField(
        default = False,
        verbose_name = _('Laser safety'),
        help_text = _('Does this instruction include laser radiation safety?')
    )
    contains_crane_license = models.BooleanField(
        default = False,
        verbose_name = _('Crane license update'),
        help_text = _('Does this instruction include crane management?')
    )
    contains_forklift_license = models.BooleanField(
        default = False,
        verbose_name = _('Forklift license update'),
        help_text = _('Does this instruction include forklift license update?')
    )

    contains_hazardous_materials_instrucions = models.BooleanField(
        default = True,
        verbose_name = _('Hazardous materials instructions'),
        help_text = _('Does this instruction include the management of hazardous materials?')
    )

    title = TranslatedField( 'title' )
    title_short = TranslatedField( 'title_en_short', 'title_de_short' )
    panels = [
        FieldPanel( 'title_en' ),
        FieldPanel( 'title_en_short' ),
        FieldPanel( 'title_de' ),
        FieldPanel( 'title_de_short' ),
        FieldPanel( 'contains_general_safety_info'),
        FieldPanel( 'contains_p38_safety_info' ),
        FieldPanel( 'contains_laser_safety' ),
        FieldPanel( 'contains_general_safety_info_radionuclides' ),
        FieldPanel( 'contains_general_safety_info_accelerators' ),
        FieldPanel( 'contains_crane_license' ),
        FieldPanel( 'contains_forklift_license' ),
        FieldPanel( 'contains_hazardous_materials_instrucions' ),        

    ]

    def __str__( self ):
        return self.title_short


@register_snippet
class SafetyInstructionUserRelation( models.Model ):
    class Meta:
        verbose_name = _( 'Safety instruction dates for user' )

    rubion_user = ParentalKey(
        RUBIONUser, related_name='rubion_user_si',
        blank = True, null = True,
        on_delete = models.CASCADE
    )
    rubion_staff = ParentalKey(
        StaffUser, related_name='staff_user_si',
        blank = True, null = True,
        on_delete = models.CASCADE
    )
    date = models.DateField()

    instruction = models.ForeignKey(
        SafetyInstructionsSnippet,
        on_delete = models.CASCADE
    )


    def save( self ):
        if self.rubion_user and self.rubion_user.linked_user:
            try:
                self.rubion_staff = StaffUser.objects.get(user = self.rubion_user.linked_user)
            except (StaffUser.DoesNotExist, StaffUser.MultipleObjectsReturned):
                pass
        elif self.rubion_staff and self.rubion_staff.user:
            try:
                self.rubion_user = RUBIONUser.objects.get(linked_user = self.rubion_staff.user)
            except (RUBIONUser.DoesNotExist, RUBIONUser.MultipleObjectsReturned):
                pass
        return super().save()
        

    def __str__( self ):
        if self.rubion_user:
            usr = self.rubion_user
        else: 
            usr = self.rubion_staff

        if get_language() == 'de':
            return "{} für {} am {}".format(
                self.instruction.title_de_short, 
                usr.full_name(language = 'de', include_first = True), 
                self.date
            )
        else:
            return "{} for {} at {}".format(
                self.instruction.title_en_short, 
                usr.full_name(language = 'en', include_first = True), 
                self.date
            )
