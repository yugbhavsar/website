"""Decorators often used for page models"""
from wagtail.admin.edit_handlers import (
    FieldPanel, StreamFieldPanel, MultiFieldPanel,
    PageChooserPanel, InlinePanel, FieldRowPanel
)
from wagtail.admin.edit_handlers import (
    TabbedInterface, ObjectList
)
from django.utils.translation import ugettext as _
from wagtail.core.models import Page
from wagtail.search import index

def default_panels( cls ):
    panels = [
        ( 'content_panels_en', 'english content' ),
        ( 'content_panels_de', 'german content' ),
        ( 'search_fields', None ),
        ( 'additional_info_panels', 'additional information'),
        ( 'settings_panels', 'settings' )
    ]
    olists = []
    for panel in panels:
        pan = []
        for p in cls.__bases__:
            if hasattr( p, panel[0] ) and getattr( p, panel[0] ) is not None:
                for cls_p in getattr( p, panel[0] ):
                    if cls_p not in pan:
                        pan += [cls_p]
        if hasattr(cls, panel[0]) and getattr( cls, panel[0] ) is not None:
            cls_panels = getattr( cls, panel[0])
            for cls_p in cls_panels:
                if cls_p not in pan:
                    pan += [cls_p]



                
        if len( pan ) > 0:
            setattr( cls, panel[0], pan )
            if panel[1] is not None:
                olists += [  
                    ObjectList( getattr( cls, panel[0] ), heading = _( panel[1] ) ) 
                ]

    cls.edit_handler = TabbedInterface( olists )
    return cls

def default_interface( cls ):
    cls.edit_handler = TabbedInterface([
        ObjectList( cls.content_panels_en, heading = _( 'english content' )),
        ObjectList( cls.content_panels_de, heading = _( 'german content' )),
        ObjectList( cls.additional_info_panels, heading = _( 'additional information' )),
        ObjectList( cls.settings_panels, heading = _( 'settings' )),

    ])


def simple_panels( cls ):
    cls.edit_handler = TabbedInterface([
        ObjectList( cls.content_panels_en, heading = _( 'english content' )),
        ObjectList( cls.content_panels_de, heading = _( 'german content' )),
        ObjectList( cls.settings_panels, heading = _( 'settings' )),
    ])
    return cls

def only_content( cls ):
    cls.edit_handler = TabbedInterface([
        ObjectList( cls.content_panels, heading = _( 'Content' )),
    ])
    return cls
def has_related( related ):
    def deco ( cls ):
        cls.related = related
        return cls
    return deco
