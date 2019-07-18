from .project import Project
from .rubionuser import RUBIONUser

from django.db import models
from django.utils.translation import ugettext_lazy as _

from instruments.mixins import (
    AbstractRelatedMethods, AbstractRelatedInstrument
)

from modelcluster.fields import ParentalKey



from wagtail.admin.edit_handlers import (
    FieldPanel, StreamFieldPanel, MultiFieldPanel,
    FieldRowPanel, InlinePanel, TabbedInterface, 
    ObjectList, PageChooserPanel 
)
from wagtail.core.models import Orderable, Page, PageRevision
from wagtail.snippets.edit_handlers import SnippetChooserPanel

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

