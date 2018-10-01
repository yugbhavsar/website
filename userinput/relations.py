from django.db import models
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, MultiFieldPanel, FieldRowPanel,
    PageChooserPanel
)
from wagtail.wagtailcore.models import Orderable

class AbstractRelatedWorkgroup( Orderable ):
    page = models.ForeignKey(
        'userinput.WorkGroup', on_delete=models.CASCADE, 
        related_name = '+', verbose_name=_('workgroup')
    )
    panels = [
        FieldPanel( 'page' )
    ]
    
    class Meta:
        abstract = True

class AbstractRelatedProject( Orderable ):
    page = models.ForeignKey(
        'userinput.Project', on_delete=models.CASCADE, 
        related_name = '+', verbose_name=_('Project')
    )
    panels = [
        FieldPanel( 'page' )
    ]
    
    class Meta:
        abstract = True

class AbstractRelatedRUBIONUser( Orderable ):
    page = models.ForeignKey(
        'userinput.RUBIONUser', on_delete=models.CASCADE, 
        related_name = '+', verbose_name=_('RUBION User')
    )
    panels = [
        FieldPanel( 'page' )
    ]
    
    class Meta:
        abstract = True
