"""
The models in this package implement methods and instruments.
"""

from .mixins import (
    AbstractRelatedInstrument, AbstractRelatedDocument, AbstractBookable
)
from .helpers import INSTRUMENTBYPROJECTBOOKING_TEXTS as I_BY_P_TEXTS
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext as _


from modelcluster.fields import ParentalKey

from userdata.mixins import (
    AbstractContactPerson, ResponsibleEditorMixin
)

from userinput.models import Project, RUBIONUser

from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, MultiFieldPanel, FieldRowPanel,
    StreamFieldPanel, InlinePanel
)
from wagtail.wagtailcore.models import Orderable, ClusterableModel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsnippets.models import register_snippet

from website.models import (
    AbstractContainerPage, AbstractChildPage, TranslatedField
)
from website.decorators import default_panels, only_content, has_related

# Instruments first:

@only_content
class InstrumentContainerPage( AbstractContainerPage ):
    # Annoyingly, the template from the abstract class gets overridden 
    # by wagtails Page mechanism. 
    template = AbstractContainerPage.template

    parent_page_types = [
        'website.StartPage'
    ]
    subpage_types = [
        'instruments.InstrumentPage'
    ]

    is_creatable = False

    content_panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel( 'title' ),
                FieldPanel( 'title_de' ),
                FieldPanel( 'slug' ),
            ], ),
        ], heading = _('title')),
        StreamFieldPanel( 'introduction_en' ),
        StreamFieldPanel( 'introduction_de' ),
    ]

    class Meta:
        verbose_name = _( 'list of instruments' )


@default_panels
class AbstractPageWithHeaderimage( AbstractChildPage, ResponsibleEditorMixin ):
    class Meta:
        abstract = True

    # instruments don't have additional sidebar content
    sidebar_content = None

    # instruments can have their own title image

    title_image = models.ForeignKey(
        'wagtailimages.Image',
        null = True, blank = True,
        on_delete=models.PROTECT,
        verbose_name = _( 'title image' ),
        help_text = _( 'this image is shown on top of the page and in listings. Title image size is 713px×300px.' ),
    )

    additional_info_panels = [
#        ImageChooserPanel( 'title_image' ),
        InlinePanel( 'contact_persons', label = _( 'contact person' ) ) 
    ]
    settings_panels = ResponsibleEditorMixin.settings_panels + [
        FieldPanel( 'slug' )
    ]

@register_snippet
class RadiationHandlingPermit( models.Model ):
    name = models.CharField(
        max_length = 128,
        verbose_name = _('Name of the permit')
    )

    def __str__ ( self ):
        return self.name


@default_panels
class InstrumentPage( AbstractBookable, AbstractPageWithHeaderimage ):

    template = 'instruments/instrument_page.html'
    booking_model = 'instruments.models.InstrumentByProjectBooking'
    booking_model_fieldname = 'instrument'

    short_name_de = models.CharField(
        max_length = 32,
        null = True,
        blank = True,
        verbose_name = _('Short name (de)'),
        help_text = _('used in buttons')
    )
    short_name_en = models.CharField(
        max_length = 32,
        null = True,
        blank = True,
        verbose_name = _('Short name (en)'),
        help_text = _('used in buttons')
    )

    short_name = TranslatedField('short_name')

    requires_labcoat = models.BooleanField(
        default = False,
        help_text = _('Does using this method require wearing a coat?'),
        verbose_name = _('Coat?')
    )
    requires_overshoes = models.BooleanField(
        default = False,
        help_text = _('Does using this method require wearing overshoes?'),
        verbose_name = _('Overshoes?')
    )
    requires_entrance = models.BooleanField(
        default = False,
        help_text = _('Does using this method require using the security entrance?'),
        verbose_name = _('Security entrance?')
    )

    requires_dosemeter = models.BooleanField(
        default = False,
        help_text = _('Does using this method require a personal (not a eelctronic) dose meter?'),
        verbose_name = _('dose meter')
    )

    requires_isotope_information = models.BooleanField(
        default = False,
        help_text = _('Does using this instrument requires information about isotopes?'),
        verbose_name = _('Isotope information')
    )

    permit = models.ForeignKey(
        RadiationHandlingPermit,
        related_name = '+',
        null = True,
        verbose_name = _('related radiation handling permit'),
        on_delete = models.SET_NULL,
        blank = True
    )
    additional_info_panels = [
    
        FieldPanel('short_name_de'),
        FieldPanel('short_name_en'),
        FieldPanel('is_bookable'),
        MultiFieldPanel([
            FieldPanel('permit'),
            FieldPanel('requires_labcoat'),
            FieldPanel('requires_overshoes'),
            FieldPanel('requires_entrance'),
            FieldPanel('requires_dosemeter'),
            FieldPanel('requires_isotope_information'),
        ], heading = _('safety settings')),
        InlinePanel('related_documents', label=_('usage guides and similar'))
    ]

    parent_page_types = [ 
        'instruments.InstrumentContainerPage' 
    ]
    subpage_types = [
        'website.StandardPage'
    ]


    def get_short_name( self ):
        if not self.short_name or self.short_name == '':
            return self.title_trans
        else:
            return self.short_name


class Document2InstrumentRelation( AbstractRelatedDocument ):
    page = ParentalKey( InstrumentPage, related_name = 'related_documents')
    

class InstrumentContactPerson( AbstractContactPerson ):
    page = ParentalKey( InstrumentPage, related_name ='contact_persons')


# Methods
@only_content
class MethodContainerPage ( AbstractContainerPage ):
    # Annoyingly, the template from the abstract class gets overridden 
    # by wagtails Page mechanism. 
    template = AbstractContainerPage.template

    parent_page_types = [
        'website.StartPage'
    ]
    subpage_types = [
        'instruments.MethodPage'
    ]

    is_creatable = False

    content_panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel( 'title' ),
                FieldPanel( 'title_de' ),
                FieldPanel( 'slug' ),
            ], ),
        ], heading = _('title')),
        StreamFieldPanel( 'introduction_en' ),
        StreamFieldPanel( 'introduction_de' ),
    ]

    class Meta:
        verbose_name = _( 'list of methods' )

@default_panels
class MethodPage ( AbstractBookable, AbstractPageWithHeaderimage ):

    booking_model = 'instruments.models.MethodsByProjectBooking'
    booking_model_fieldname = 'method'

    # Annoyingly, the template from the abstract class gets overridden 
    # by wagtails Page mechanism. 
    template = 'instruments/methods_page.html'

    parent_page_types = [ 
        'instruments.MethodContainerPage' 
    ]
    subpage_types = [
        'website.StandardPage'
    ]
    title_image = models.ForeignKey(
        'wagtailimages.Image',
        null = True, blank = True,
        on_delete = models.PROTECT,
        verbose_name = _( 'title image' ),
        help_text = _( 'this image is shown on top of the page and in listings. Title image size is 713px×300px.' ),
    )

    additional_info_panels = [
        ImageChooserPanel( 'title_image' ),
        InlinePanel( 'related', label=_ ('related instrument'))
    ]
    settings_panels = ResponsibleEditorMixin.settings_panels



    # Introducing this property overrides the is_bookable field from the AbstractBookable mixin
    @property
    def is_bookable( self ):
        # In general, a method is bookable if it contains instruments that are bookable 
        # However, if a user can book all bookable instruments, we do
        # not need an apply button. But this should be dealt with in the template tag

        i2ms = Method2InstrumentRelation.objects.filter( method = self )
        bookable = [ i2m.page.specific.is_bookable for i2m in i2ms ]
        return any(bookable)

    def get_instruments( self ):
        i2ms = Method2InstrumentRelation.objects.filter( method = self )
        return [ i2m.page.specific for i2m in i2ms ]

        
    @property
    def requires_isotope_information( self ):
        i2ms = Method2InstrumentRelation.objects.filter( method = self )
        req = [ i2m.page.specific.requires_isotope_information for i2m in i2ms ]
        return any(req)
        
class MethodContactPerson( AbstractContactPerson ):
    method = ParentalKey( MethodPage, related_name = 'contact_persons')
    
class Method2InstrumentRelation( AbstractRelatedInstrument ):
    method = ParentalKey( MethodPage, related_name = 'related')


class AbstractSimpleBooking( models.Model ):
    start = models.DateTimeField(
        blank = True,
        null = True
    )
    end = models.DateTimeField(
        blank = True,
        null = True
    )

    booked_by = models.ForeignKey(
        get_user_model(),
        on_delete = models.CASCADE
    )

    class Meta:
        abstract = True

class AbstractBookingByProject( AbstractSimpleBooking ):
    project = models.ForeignKey (
        Project,
        on_delete = models.CASCADE
    )

    description = models.CharField(
        max_length = 2048,
        verbose_name = I_BY_P_TEXTS['description']['verbose_name'],
        blank = True,
        null = True,
        help_text = I_BY_P_TEXTS['description']['help_text'],
    )
    class Meta:
        abstract = True

class InstrumentByProjectBooking ( AbstractBookingByProject ):
    instrument = models.ForeignKey (
        InstrumentPage,
        on_delete = models.CASCADE
    )
class MethodsByProjectBooking ( AbstractBookingByProject ):
    method = models.ForeignKey (
        MethodPage,
        on_delete = models.CASCADE
    )
    instrument_booking = models.ForeignKey(
        InstrumentByProjectBooking,
        on_delete = models.CASCADE,
        null = True,
        blank = True
    )

