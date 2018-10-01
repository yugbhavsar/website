"""
This module implements the container->child mechanism as well as models for 
standard pages and the starting page. 
"""

from .blocks import ( 
    BodyStreamBlock, IntroductionStreamBlock, 
    SidebarStreamBlock
)
from .standardtexts import HELP_TEXTS, VERBOSE_NAMES
from .decorators import default_panels, only_content, default_interface
from .utils import wrap

from django.conf import settings

from django.core.mail import EmailMessage
from django.db import models
from django.db.models import FieldDoesNotExist
from django.forms.widgets import Textarea
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from django.utils.text import format_lazy

import importlib
import inspect

from modelcluster.fields import ParentalKey

from userdata.mixins import (
    ResponsibleEditorMixin, AbstractContactPerson
)


from wagtail.contrib.settings.models import BaseSetting, register_setting

from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, StreamFieldPanel, MultiFieldPanel,
    PageChooserPanel, InlinePanel, FieldRowPanel,
    TabbedInterface, ObjectList
)
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch import index
from wagtail.wagtailsnippets.models import register_snippet


class TranslatedField(object):
    '''
    This Class returns the translated version of a 
    class attribute, depending on the currently set language.
    
    This is the way described in the wagtail docs (1.10),
    but it requires to define every translated field twice, which
    is not nice.

    However, wagtailtranslation seems to be not under active 
    development, so I believe it's better to use this way. Inheriting
    from abstract classes reduces the problem of writing code twice.

    Example:
    
    class MyPage( TranslatedPage ):
        myfield_en = models.Charfield(...)
        myfield_de = models.Charfield(...)
        myfield = TranslatedField('myfield')

    
    Now, MyPage.myfield will retrieve the contents of either myfield_en or
    myfield_de, depending on the current language settings.
    
    '''

    def __init__(self, field, field_de = None):
        if field_de is None:
            field_en = field+'_en'
            field_de = field+'_de'
        else:
            field_en = field

        self.en_field = field_en
        self.de_field = field_de

    def __get__(self, instance, owner):
        if translation.get_language() == 'de':
            return getattr(instance, self.de_field)
        else:
            return getattr(instance, self.en_field)


class TranslatedPage( Page ):
    '''
    abstract class.
    Implements a Page model with a translated title-field. 

    Overrides the `add_child` method of the Page model to call the childs 
    `after_create_hook` method, if available.

    
    '''
    title_de = models.CharField(
        max_length = 128,
#        null = True, blank = True,
        verbose_name = _('title (de)')
    )
    title_trans = TranslatedField('title','title_de')

    content_panels_de = [
        FieldPanel('title_de')
    ]
    content_panels_en = [
        FieldPanel('title')
    ]
    search_fields = Page.search_fields + [
                index.SearchField( 'title_de' ),
    ]

    def __str__( self ):
        return self.title_trans

    def get_admin_display_title ( self ):
        return self.title_trans

    def add_child( self, instance = None, **kwargs ):
        # Calls the instance's `after_create_hook` method with the current
        # request as argument, if the instance has implemented this method.
        
        request = kwargs.get('request', None)
        
        child = super(TranslatedPage, self).add_child ( instance = instance, **kwargs )
        try:
            instance.after_create_hook( request )
        except AttributeError:
            pass
        return child
            
    class Meta:
        abstract = True

@default_panels
class IntroductionMixin( models.Model ):
    '''
    abstract class.
    Mixin implementing an optional introduction.
    '''

    # @TODO: Remove either this class or `OptionalIntroductionMixin`
    # below. Both provide the same.

    introduction_en = StreamField(
        IntroductionStreamBlock(required = False),
        blank = True, null = True, 
        verbose_name = _( VERBOSE_NAMES['INTRODUCTION']+' (en)' ),
        help_text = _( HELP_TEXTS['INTRODUCTION'] )
    )
    introduction_de = StreamField(
        IntroductionStreamBlock(required = False),
        blank = True, null = True, 
        verbose_name = _( VERBOSE_NAMES['INTRODUCTION']+' (de)' ),
        help_text = _( HELP_TEXTS['INTRODUCTION'] )
    )
    introduction = TranslatedField('introduction')

    content_panels_de = [
        StreamFieldPanel('introduction_de')
    ]
    content_panels_en = [
        StreamFieldPanel('introduction_en')
    ]
    search_fields = [
        index.SearchField( 'introduction_de' ),
        index.SearchField( 'introduction_en' ),
    ]

    class Meta:
        abstract = True

@default_panels
class MandatoryIntroductionMixin( models.Model ):
    '''
    abstract class
    Mixin implementing a mandatory introduction.
    '''

    introduction_en = StreamField(
        IntroductionStreamBlock(required = False),
        blank = False, null = False, 
        verbose_name = _( VERBOSE_NAMES['INTRODUCTION'] ),
        help_text = _( HELP_TEXTS['INTRODUCTION'] )
    )
    introduction_de = StreamField(
        IntroductionStreamBlock(required = False),
        blank = False, null = False, 
        verbose_name = _( VERBOSE_NAMES['INTRODUCTION'] ),
        help_text = _( HELP_TEXTS['INTRODUCTION'] )
    )
    introduction = TranslatedField('introduction')
    content_panels_de = [
        StreamFieldPanel('introduction_de')
    ]
    content_panels_en = [
        StreamFieldPanel('introduction_en')
    ]
    search_fields = [
                index.SearchField( 'introduction_de' ),
                index.SearchField( 'introduction_en' ),
    ]
    class Meta:
        abstract = True

class OptionalIntroductionMixin( models.Model ):
    '''
    abstract class.
    Mixin implementing the same as `IntroductionMixin` above: an optional
    introduction.

    Obviously, one of these two classes is not necessary.
    '''

    # @TODO: Remove either this class or `IntroductionMixin` above.

    introduction_en = StreamField(
        IntroductionStreamBlock(required = False),
        blank = True, null = True, 
        verbose_name = _( VERBOSE_NAMES['INTRODUCTION']+' (en)' ),
        help_text = _( HELP_TEXTS['INTRODUCTION'] +' (english)' )
    )
    introduction_de = StreamField(
        IntroductionStreamBlock(required = False),
        blank = True, null = True, 
        verbose_name = _( VERBOSE_NAMES['INTRODUCTION']+' (de)' ),
        help_text = _( HELP_TEXTS['INTRODUCTION']  +' (german)')
    )
    introduction = TranslatedField('introduction')
    content_panels_de = [
        StreamFieldPanel('introduction_de')
    ]
    content_panels_en = [
        StreamFieldPanel('introduction_en')
    ]
    search_fields = [
                index.SearchField( 'introduction_de' ),
                index.SearchField( 'introduction_en' ),
    ]
    class Meta:
        abstract = True

@default_panels
class BodyMixin( models.Model ):
    '''
    abstract class.
    A mixin adding an optional body field.
    '''
    body_en = StreamField(
        BodyStreamBlock,
        blank = True, null = True,
        verbose_name = _( VERBOSE_NAMES['BODY']+' (en)' ),
        help_text = _( HELP_TEXTS['BODY'] )
    )
    body_de = StreamField(
        BodyStreamBlock,
        blank = True, null = True,
        verbose_name = _( VERBOSE_NAMES['BODY']+' (de)' ),
        help_text = _( HELP_TEXTS['BODY'] )
    )
    body = TranslatedField('body')
    
    content_panels_de = [
        StreamFieldPanel('body_de')
    ]
    content_panels_en = [
        StreamFieldPanel('body_en')
    ]

    class Meta:
        abstract = True

@default_panels
class SidebarContentMixin( models.Model ):
    '''
    abstract class
    Mixin adding optional sidebar content to the model.
    '''
    sidebar_content_en = StreamField(
        SidebarStreamBlock,
        blank = True, null = True,
        verbose_name = _( VERBOSE_NAMES['SIDEBAR']+' [en]' ),
        help_text = _( HELP_TEXTS['SIDEBAR'] )
    )
    sidebar_content_de = StreamField(
        SidebarStreamBlock,
        blank = True, null = True,
        verbose_name = _( VERBOSE_NAMES['SIDEBAR']+' [de]' ),
        help_text = _( HELP_TEXTS['SIDEBAR'] )
    )
    sidebar_content = TranslatedField('sidebar_content')

    content_panels_de = [
        StreamFieldPanel('sidebar_content_de')
    ]
    content_panels_en = [
        StreamFieldPanel('sidebar_content_en')
    ]

    class Meta:
        abstract = True

@default_panels
class StandardMixin( IntroductionMixin, BodyMixin, SidebarContentMixin ):
    """
    abstract class
    A standard page contains the fields
    - introduction
    - body
    - sidebar_content
    - contact persons
    """
    
    # template
    template = 'website/standard_page.html'


    class Meta:
        abstract = True

@default_panels
class AbstractStandardPage( TranslatedPage, StandardMixin ):
    additional_info_panels = [
        InlinePanel('contact_persons', label=_('Contact persons'))
    ]
    class Meta:
        abstract = True


#@default_panels
class AbstractContainerPage ( TranslatedPage, IntroductionMixin ):
    """Container pages render a list of their children."""

    # The default template for container pages. Can be overriden on a 
    # per-model basis
    template = 'website/container.html'
    
    # By default, only children are allowed
    subpage_types = [
        'website.AbstractChildPage'
    ]

    # A first idea of implementing unique pages which (see `can_exist_under`
    # below) is not and will maybe never used.  

    is_unique = False
    is_unique_in_parent = False
    
    
    @classmethod
    def can_exist_under( self, parent ):
        # test for uniqueness not implemented
        if self.is_unique:
            pass
        if self.is_unique_in_parent:
            pass

        return super(AbstractContainerPage, self).can_exist_under( parent )
        

    def get_visible_children( self ):
        ''' Get the visible children of this page. '''
        title_field = 'title'
        
        # I'm not sure whether the following module-testing is really
        # required. It might be easier and much more readable to use 
        #   obj = Page
        # or maybe
        #   obj = TranslatedPage
        # instead.
        this_class = type(self)
        if len( this_class.subpage_types ) == 1:
            kls = this_class.subpage_types[0]
            if inspect.isclass( kls ):
                obj = kls;
            else:
                module, klass = kls.split( '.' )
                m = importlib.import_module( '{}.{}'.format( module, 'models' ) )
                obj = getattr(m, klass)
            if translation.get_language() == 'de':
                title_field = 'title_de'
        else:
            obj = Page

        pages = obj.objects.live().child_of(self)

        return pages.order_by(title_field)

    class Meta:
        abstract = True

class ChildMixin( object ):
    # template used when rendered as a child in a list
    child_template = 'website/child_in_list.html'
    
    def render_as_child( self ):
        """This method can be overriden to pass additional context to the `child_template`."""
        return render_to_string(
            self.child_template,
            {
                'page': self,
            }
        )

@default_panels
class AbstractChildPage( TranslatedPage, MandatoryIntroductionMixin, BodyMixin, 
        SidebarContentMixin, ChildMixin ):
    """Child pages can be listed in the list of a container page."""
    
    # default template

    template = 'website/standard_page.html'
    

    class Meta:
        abstract = True




@default_panels
class StandardPage( AbstractStandardPage, ResponsibleEditorMixin ):
    """Implementation of a standard page"""
    subpage_types = [
        'website.StandardPage',
        'website.StandardPageWithTOC'
    ]
    class Meta:
        verbose_name = _( 'standard content page' )

class StandardPageContact( AbstractContactPerson ):
    page = ParentalKey( StandardPage, related_name ='contact_persons')

@default_panels
class StandardPageWithTOC( 
        TranslatedPage, OptionalIntroductionMixin, BodyMixin 
):
    ''' 
    Implements a page where a Table of contents is automatically
    generated. The TOC entries are taken from the h3-blocks in he body-field.
    '''
    
    subpage_types = [
        'website.StandardPage',
        'website.StandardPageWithTOC'
    ]
    template = 'website/standard_page_with_TOC.html'
    class Meta:
        verbose_name = 'Standard page with automatic table of contents'

    def get_context( self, request ):
        context = super(StandardPageWithTOC, self).get_context( request )
        headings = []
        for block in self.body:
            if block.block_type == 'h3':
                headings.append(block.value)

        context['headings'] = headings
    
        return context
        

class StartPage ( TranslatedPage, BodyMixin, SidebarContentMixin ):
    parent_page_types = [ 'wagtailcore.Page' ]
    """The start page"""
    template = 'website/start_page.html'
    
    # we don't need an introduction here
#    introduction_de = None
#    introduction_en = None
#    introduction = None

    # But we might need a different headline

    headline_en = models.CharField(
        max_length = 64,
        blank = True, null = True,
        verbose_name = _( 'alternative title' ),
        help_text = _( 'if provided, this will be shown on top of the page' ) 
    )
    headline_de = models.CharField(
        max_length = 64,
        blank = True, null = True,
        verbose_name = _( 'alternative title' ),
        help_text = _( 'if provided, this will be shown on top of the page' ) 
    )

    headline = TranslatedField('headline')

    content_panels_de = [
        FieldPanel( 'title_de' ),
        FieldPanel( 'headline_de' ),
        StreamFieldPanel( 'body_de' ),
        StreamFieldPanel( 'sidebar_content_de')
    ]
    content_panels_en = [
        FieldPanel( 'title' ),
        FieldPanel( 'headline_en' ),
        StreamFieldPanel( 'body_en' ),
        StreamFieldPanel( 'sidebar_content_en')
    ]


    settings_panels = Page.settings_panels + [FieldPanel('slug')]
    
    edit_handler =  TabbedInterface([
        ObjectList( content_panels_en, heading = _( 'content (en)' )),
        ObjectList( content_panels_de, heading = _( 'content (de)' )),
        ObjectList( settings_panels, heading = _( 'settings' )),
    ])
    

    class Meta:
        verbose_name = _( 'start page' )

#    def get_context( self, request ):
#        context = super( StartPage, self).get_context( self, request )
#        context['user'] = request.user
#        return context


class Menu( TranslatedPage ):
    """ This model implements a menu indepent from the hierachic structure """

    subpage_types=[ 'website.MenuItem' ]
    parent_page_types = [ 'wagtailcore.Page' ]
    content_panels = [
        MultiFieldPanel([
            FieldPanel( 'title' ),
            FieldPanel( 'title_de' ),
        ], heading = _( 'title' )),
    ]
    settings_panels = [
        FieldPanel( 'slug' )
    ]
    
    edit_handler = TabbedInterface([
        ObjectList( content_panels, heading = _( 'content' )),
        ObjectList( settings_panels, heading = _( 'settings' )),
    ])

    is_creatable = False
        

class MenuItem( TranslatedPage ):
    """ Implements an entry in a Menu """
    subpage_types = ['website.MenuItem']
    parent_page_types = [
        'website.MenuItem',
        'website.Menu'
    ]
    
    linked_page = models.ForeignKey(
        'wagtailcore.Page',
        null = True,
        blank = True,
        on_delete = models.PROTECT,
        related_name = '+',
    )
    content_panels = [
        MultiFieldPanel([
            FieldPanel( 'title' ),
            FieldPanel( 'title_de' ),
        ], heading = _( 'title' )),
        PageChooserPanel('linked_page')
    ]
    settings_panels = [
        FieldPanel( 'slug')
    ]

    edit_handler = TabbedInterface([
        ObjectList( content_panels, heading = _( 'content' )),
        ObjectList( settings_panels, heading = _( 'settings' )),
    ])


@only_content
class PublicationsContainerPage( AbstractContainerPage ):
    """
    This class is special since the publications are 
    imported from the RUB reserach bibliography via javascript.
    However, Bachelor, Master and PhD theses are not listed there, 
    so we will keep track of them.
    """
    # @TODO: implement PhD, master, bachelor thesis
    subpage_types = []

    template = 'website/publications_container.html'

    # This page should be unique

    is_unique = True
    is_creatable = False


    # it has no body
    
    body = None

    content_panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel( 'title' ),
                FieldPanel( 'title_de' ),
                FieldPanel( 'slug' ),
            ], ),
        ], heading = _('title')),
        StreamFieldPanel( 'introduction_en'),
        StreamFieldPanel( 'introduction_de'),
    ]
    
    class Meta:
        verbose_name = _( 'automatically generated list of publications' )
    




@register_snippet
class EMailText ( models.Model ):
    '''
    This models is used to send emails with content which can be defined in
    the admin panel. It uses the template syntax as implemented by wagtail to
    insert specific content.

    Its implementation is rather weird. Every instance of EMailText needs an
    identifier, which can be modified in the admin panels. However, this
    identifier is also hardcoded in the code. this very unstable
    implementation was used before I stumbled upon
    https://docs.djangoproject.com/en/2.1/howto/initial-data/ which might be a
    better way to provide the identifier as well as a default text.

    However, as long as one ensures that all identifiers used somewhere in the
    code are available in the database, it is a quite easy way to send mails.

    First, one needs the current context, as in the HTML-page template
    system. It would be very helpful if it would be possible to provide a way
    to list the available context-dict in the admin panel, but I have not yet
    found a way. But, given the context, the identifier and the mail address,
    sending an E-Mail is as simple as:

       mailtext = EMailText.objects.get(identifier = 'abc')
       mailtext.send( 'mail@test.com', {'context' : 'dict'})
 
    '''
    identifier = models.CharField(
        max_length = 512,
    )
    description_en = models.CharField(
        max_length = 128,
        help_text = _( 'A short description (en) ')
    )
    description_de = models.CharField(
        max_length = 128,
        help_text = _( 'A short description (ger)' )
    )
    text_de = models.TextField(
        help_text = _( 'The mail text that will be parsed by the template machinery. Available variables should be documented in the respective code.' )
    )
    text_en = models.TextField(
        help_text = _( 'The mail text that will be parsed by the template machinery. Available variables should be documented in the respective code.' )
    )
    subject_de = models.CharField(
        max_length = 256,
        help_text = _('Mail subject in german. Will not be parsed.'),
        blank = True,
        null = True
    )
    subject_en = models.CharField(
        max_length = 256,
        help_text = _('Mail subject in english. Will not be parsed.'),
        blank = True,
        null = True
    )
    description = TranslatedField( 'description' )
    text = TranslatedField('text')

    panels = [
        FieldPanel('identifier'),
        FieldPanel('description_en'),
        FieldPanel('description_de'),
        FieldPanel('subject_en'),
        FieldPanel('subject_de'),
        FieldPanel('text_en', widget = Textarea),
        FieldPanel('text_de', widget = Textarea),
    ]
    
    def __str__( self ):
        return self.identifier

    def get_text( self, context, lang ):

        if lang not in ['en','de']:
            raise AttributeError( 'E-Mail text and subject for lang {0} unknown.'.format(lang) )

        subj = getattr( self, 'subject_{}'.format( lang ) )
        tpl_text = getattr( self, 'text_{}'.format( lang ) )

        tpl = Template( tpl_text ) 
        con = Context ( context )

        return [ subj, tpl.render( context = con ) ]
        


    def get_german_text( self, context ):
        return self.get_text( context, 'de')

    def get_english_text( self, context ):
        return self.get_text( context, 'en')


    def send( self, to, context, lang = None, attachements = [], reply_to = None ):
        # This is the major method of this module. 
        
        if lang != 'de':
            subj_en, en = self.get_english_text( context )
            
        if lang != 'en':
            subj_de, de = self.get_german_text( context )

        if not lang: # make multilang-mail
            body = '''[english text below]

{}

----------------------------------------------------------------------

{}'''.format(de, en)

            subj = "{} | {}".format(subj_de, subj_en)
        elif lang =='de':
            body = de
            subj = subj_de
        else:
            body = en
            subj = subj_en

        # Make sure `to` is a list
        if isinstance(to, str):
            to = [ to ]

        wrapped_body = wrap( body )

        email = EmailMessage(
            subj,
            wrapped_body,
            settings.RUBION_MAIL_FROM,
            to
        )
        if reply_to is not None:
            email.replay_to = replay_to
        for attachment in attachements:
            email.attach_file(attachment)

        email.send(fail_silently = False)

        mail = SentMail()
        mail.sender = settings.RUBION_MAIL_FROM
        try:
            mail.to = ', '.join(to)
        except TypeError:
            mail.to = str(to)
        mail.subject = subj
        mail.body = wrapped_body
        mail.save()

        return mail
        


class SentMail ( models.Model ):
    '''
    A model that is used to store every mail that has been send in the
    database.
    '''
    to = models.CharField(
        max_length = 512,
    )
    sender = models.CharField(
        max_length = 256
    )
    subject = models.CharField(
        max_length = 256
    )
    body = models.TextField()
    sent_at = models.DateTimeField(
        auto_now_add = True
    )

    is_creatable = False

    def __str__( self ):
        return _('Sent Mail from') + ' {}'.format(self.sent_at)



@register_setting
class ImportantPages( BaseSetting ):
    registration_page = models.ForeignKey(
        'wagtailcore.Page', 
        null = True, 
        on_delete = models.SET_NULL,
        verbose_name = _('Page containing the registration form'),
        related_name = 'registration_page'
    )
    workgroup_list = models.ForeignKey(
        'wagtailcore.Page', 
        null = True, 
        on_delete = models.SET_NULL,
        verbose_name = _('Page containing the list of workgroups'),
        related_name = 'workgroup_list'
    )
    projects_list = models.ForeignKey(
        'wagtailcore.Page', 
        null = True, 
        on_delete = models.SET_NULL,
        verbose_name = _('Page containing the list of projects'),
        related_name = 'projects_list'
    )

    collection_for_user_upload = models.ForeignKey(
        'wagtailcore.Collection',
        null = True,
        on_delete = models.SET_NULL,
        verbose_name = _('Collection for user uploaded files')
    )

    panels = [
        PageChooserPanel('registration_page'),
        PageChooserPanel('workgroup_list'),
        PageChooserPanel('projects_list'),
        FieldPanel('collection_for_user_upload'),
    ]
    

@register_setting
class ContactSettings( BaseSetting ):
    base_phone_number = models.CharField(
        max_length = 32,
        default = '+4923432',
        verbose_name = _('Phone number for external calls.')
    )

    panels = [
        FieldPanel('base_phone_number'),
    ]


# Beirat


@register_setting
class Beirat( BaseSetting ):
    # Professors

    # natural sciences

    prof_natural_ruser = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'prof_naturalsciences_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    prof_natural_staffuser = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'prof_naturalsciences_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    prof_natural_ruser2 = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'prof_naturalsciences2_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    prof_natural_staffuser2 = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'prof_naturalsciences2_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    # engineering

    prof_engin_ruser = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'prof_engin_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    prof_engin_staffuser = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'prof_engin_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    prof_engin_ruser2 = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'prof_engin2_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    prof_engin_staffuser2 = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'prof_engin2_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )
    
    # medicine

    prof_medicine_ruser = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'prof_medicine_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    prof_medicine_staffuser = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'prof_medicine_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    prof_medicine_ruser2 = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'prof_medicine2_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    prof_medicine_staffuser2 = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'prof_medicine2_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    # scientific staff

    scie_ruser = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'scientificstaff_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    scie_staffuser = models.ForeignKey(
        'userdata.StaffUser',
        related_name = '+',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    scie_ruser2 = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = '+',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    scie_staffuser2 = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'scientificstaff2_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    # technicians

    tech_ruser = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'technician_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    tech_staffuser = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'technician_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    tech_ruser2 = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'technician2_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    tech_staffuser2 = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'technician2_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )


    # STUDENTS

    stud_ruser = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'student_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    stud_staffuser = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'student_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    stud_ruser2 = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'student2_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )

    stud_staffuser2 = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'student2_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff User')
    )

    # others
    # 1

    other1_ru = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'other_persons_1_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )
    other1_su = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'other_persons_1_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff')
    )

    other1_role_de = models.CharField(
        max_length = 128,
        verbose_name = _l('Role of the person (in german)'),
        blank = True,
    )
    other1_role_en = models.CharField(
        max_length = 128,
        verbose_name = _l('Role of the person (in english)'),
        blank = True,
    )

    other1_role = TranslatedField('other1_role')
    
    # 2
    other2_ru = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'other_persons_2_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )
    other2_su = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'other_persons_2_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff')
    )

    other2_role_de = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in german)')
    )
    other2_role_en = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in english)')
    )

    other2_role = TranslatedField('other2_role')

    # 3
    other3_ru = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'other_persons_3_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )
    other3_su = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'other_persons_3_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff')
    )

    other3_role_de = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in german)')
    )
    other3_role_en = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in english)')
    )

    other3_role = TranslatedField('other3_role')

    # 4
    other4_ru = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'other_persons_4_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )
    other4_su = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'other_persons_4_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff')
    )


    other4_role_de = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in german)')
    )
    other4_role_en = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in english)')
    )

    other4_role = TranslatedField('other4_role')

    # 5

    other5_ru = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'other_persons_5_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )
    other5_su = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'other_persons_5_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff')
    )


    other5_role_de = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in german)')
    )
    other5_role_en = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in english)')
    )

    other5_role = TranslatedField('other5_role')


    #6 

    other6_ru = models.ForeignKey(
        'userinput.RUBIONUser',
        related_name = 'other_persons_6_ru',
        blank = True,
        null = True,
        verbose_name = _l('Connected RUBION User')
    )
    other6_su = models.ForeignKey(
        'userdata.StaffUser',
        related_name = 'other_persons_6_su',
        blank = True,
        null = True,
        verbose_name = _l('Connected Staff')
    )

    other6_role_de = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in german)')
    )
    other6_role_en = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Role of the person (in english)')
    )

    other6_role = TranslatedField('other6_role')

    panels =  [
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('prof_natural_ruser'), FieldPanel('prof_natural_staffuser')])
            ],
            heading = format_lazy("{}: {}", _l('Group of Professors'), _l('Natural Sciences')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('prof_natural_ruser2'), FieldPanel('prof_natural_staffuser2')])
            ],
            heading = format_lazy("{}: {} ({})",_l('Group of Professors'), _l('Natural Sciences'), _l('surrogate')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('prof_engin_ruser'), FieldPanel('prof_engin_staffuser')])
            ],
            heading = format_lazy("{}: {}",_l('Group of Professors'), _l('Engineering')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('prof_engin_ruser2'), FieldPanel('prof_engin_staffuser2')])
            ],
            heading = format_lazy("{}: {} ({})",_l('Group of Professors'), _l('Engineering'), _l('surrogate')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('prof_medicine_ruser'), FieldPanel('prof_medicine_staffuser')])
            ],
            heading = format_lazy("{}: {}", _l('Group of Professors'), _l('Medicine')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('prof_medicine_ruser2'), FieldPanel('prof_medicine_staffuser2')])
            ],
            heading = format_lazy("{}: {} ({})", _l('Group of Professors'), _l('Medicine'), _l('surrogate')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('scie_ruser'), FieldPanel('scie_staffuser')])
            ],
            heading = format_lazy("{}", _l('Group of Scientific Staff')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('scie_ruser2'), FieldPanel('scie_staffuser2')])
            ],
            heading = format_lazy("{} ({})", _l('Group of Scientific Staff'), _l('surrogate')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('tech_ruser'), FieldPanel('tech_staffuser')])
            ],
            heading = format_lazy("{}", _l('Group of Technical and Adminstrative Staff')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('tech_ruser2'), FieldPanel('tech_staffuser2')])
            ],
            heading = format_lazy("{} ({})", _l('Group of Technical and Adminstrative Staff'), _l('surrogate')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('stud_ruser'), FieldPanel('stud_staffuser')])
            ],
            heading = format_lazy("{}", _l('Group of Students')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('stud_ruser2'), FieldPanel('stud_staffuser2')])
            ],
            heading = format_lazy("{} ({})", _l('Group of Students'), _l('surrogate')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('other1_ru'), FieldPanel('other1_su')]),
                FieldRowPanel([FieldPanel('other1_role_de'), FieldPanel('other1_role_en')]),
            ],
            heading = format_lazy("{}", _l('Others 1')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('other2_ru'), FieldPanel('other2_su')]),
                FieldRowPanel([FieldPanel('other2_role_de'), FieldPanel('other2_role_en')]),
            ],
            heading = format_lazy("{}", _l('Others 2')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('other3_ru'), FieldPanel('other3_su')]),
                FieldRowPanel([FieldPanel('other3_role_de'), FieldPanel('other3_role_en')]),
            ],
            heading = format_lazy("{}", _l('Others 3')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('other4_ru'), FieldPanel('other4_su')]),
                FieldRowPanel([FieldPanel('other4_role_de'), FieldPanel('other4_role_en')]),
            ],
            heading = format_lazy("{}", _l('Others 4')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('other5_ru'), FieldPanel('other5_su')]),
                FieldRowPanel([FieldPanel('other5_role_de'), FieldPanel('other5_role_en')]),
            ],
            heading = format_lazy("{}", _l('Others 5')),
            classname="collapsible collapsed"
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel('other6_ru'), FieldPanel('other6_su')]),
                FieldRowPanel([FieldPanel('other6_role_de'), FieldPanel('other6_role_en')]),
            ],
            heading = format_lazy("{}", _l('Others 6')),
            classname="collapsible collapsed"
        )
    ]


def is_beirat( user ):
    if not user:
        return False
    beirat = [
        'other6_ru', 'other6_su',  
        'other5_ru', 'other5_su', 
        'other4_ru', 'other4_su', 
        'other3_ru', 'other3_su', 
        'other2_ru', 'other2_su', 
        'other1_ru', 'other1_su', 
        'stud_ruser2', 'stud_staffuser2',
        'stud_ruser', 'stud_staffuser',
        'tech_ruser2', 'tech_staffuser2',
        'tech_ruser', 'tech_staffuser',
        'scie_ruser2', 'scie_staffuser2',
        'scie_ruser', 'scie_staffuser',
        'prof_medicine_ruser', 'prof_medicine_staffuser',
        'prof_medicine_ruser2', 'prof_medicine_staffuser2',
        'prof_engin_ruser', 'prof_engin_staffuser',
        'prof_engin_ruser2', 'prof_engin_staffuser2',
        'prof_natural_ruser2', 'prof_natural_staffuser2',
        'prof_natural_ruser', 'prof_natural_staffuser'
    ]
    
    br = Beirat.objects.first()

    for field in beirat:
        if user == getattr(br, field):
            return True
    return False

@register_setting
class KontaktZentralerStrahlenschutz( BaseSetting ):
    email = models.CharField(
        max_length = 256,
        default = 'strahlenschutz@rub.de',
        verbose_name = _('E-Mail of the central radiation safety officer')
    )

@register_setting
class TermsAndConditionsPages( BaseSetting ):
    courses = models.ForeignKey(
        'wagtailcore.Page', 
        null = True, 
        on_delete = models.SET_NULL,
        verbose_name = _('Page containing the T+C for courses'),
        related_name = '+'
    )    
    
    panels = [
        PageChooserPanel('courses')
    ]
