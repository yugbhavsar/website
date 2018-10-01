from wagtail.wagtailcore.blocks import StructBlock, ListBlock, StreamBlock, CharBlock
from django.utils.translation import ugettext as _


class AbstractDataBlock( StructBlock ):
    key = CharBlock( required = True )
    label = CharBlock( required = True )
    value = CharBlock( required = True )

class DataCharBlock( AbstractDataBlock ):
    pass

class DataEMailBlock( AbstractDataBlock ):
    pass

class DataTextBlock( AbstractDataBlock ):
    pass

class DataIntegerBlock( AbstractDataBlock ):
    pass


class DataStreamBlock( StreamBlock ):
    chars = DataCharBlock(
        icon = 'doc-full-inverse',
        label = _( 'short text' )
    )
    text = DataTextBlock(
        icon = 'paragraph',
        label = _( 'long text' )
    )
    email = DataEMailBlock(
        icon = 'fa-email',
        label = _('E-Mail')
    )
