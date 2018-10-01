from django import forms
from django.utils.translation import ugettext as _


from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.wagtailcore.blocks import (
    CharBlock, RichTextBlock, FieldBlock, 
    StructBlock, StreamBlock, ListBlock, 
    ChoiceBlock, PageChooserBlock, RawHTMLBlock
)
from wagtail.wagtaildocs.blocks import DocumentChooserBlock
from wagtail.wagtailimages.blocks import ImageChooserBlock




class ImageFormatChoiceBlock(FieldBlock):
    field = forms.ChoiceField(choices=(
        ('left', _('Wrap left') ), ('right', _('Wrap right')), 
        ('center', _('Centered') ),
    ))

class DefinitionListItem( StructBlock ):
    dt = CharBlock(
        label = "Definition"
    )
    dd = RichTextBlock(
        label = "Content",
    )

    class Meta:
        template = "website/blocks/definition_list_item.html"
        label = "Definition list item"
#class DefinitionListBlock(ListBlock):

class ImageWidthBlock( ChoiceBlock ):
    choices = [
        (100, '100 %'),
        (75, '75 %'),
        (50, '50 %'),
        (33, '33 %'),
    ]
    
    

class ImageBlock(StructBlock):

    image = ImageChooserBlock()
    caption = RichTextBlock()
#        editor="simple"
    
    alignment = ImageFormatChoiceBlock()
    width = ImageWidthBlock()


    class Meta:
        template = "website/blocks/image_block.html"

class LinkedPageBlock( StructBlock ):
    title = CharBlock( label = _( 'title' ) )
    link = PageChooserBlock( label = _( 'internal link' ) )


class SidebarBlock( StructBlock ):
    h3 = CharBlock(
        icon = "title", 
        classname = "title", 
        label = _('heading'),
        template = "website/blocks/h3.html"
    )
    paragraph = RichTextBlock(
        icon = "pilcrow", 
#        editor = "simple", 
        label=_( 'text' )
    )
    image = ListBlock(
        ImageBlock( 
            label= _('image'), 
            icon= 'image',
        ),
        verbose_name = _('Bild'),
        default = []
    )
    # image = ImageBlock( 
    #     label= _('image'), 
    #     icon= 'image',
    #     required = False
    # )
    paragraph2 = RichTextBlock(
        icon="pilcrow", 
#        editor="simple", 
        label=_( 'text' ),
        required = False
    )
    link = LinkedPageBlock(
        label = _( 'internal link' ),
        icon = 'doc-full-inverse'
    )

class SidebarStreamBlock( StreamBlock ):
    item = SidebarBlock(
        icon = 'doc-full-inverse',
        label = _( 'sidebar content' )
    )
class IntroductionStreamBlock( StreamBlock ):
    paragraph = RichTextBlock(
        icon = "pilcrow", 
#        editor = "simple", 
        label=_( 'text' )
    )

class MathMLBlock ( RawHTMLBlock ):
    class Meta:
        template = "website/blocks/math_ml_block.html"

class LocalVideoBlock ( StructBlock ):
    video = DocumentChooserBlock(label = _('Video file'))
    caption = RichTextBlock(label = _('Caption'))
    class Meta:
        template = "website/blocks/local_video_block.html"
        label = _("Local video")

class BodyStreamBlock(StreamBlock):
    h3 = CharBlock(
        icon="title", 
        classname="title", 
        label = "h3",
        template="website/blocks/h3.html"
    )
    h4 = CharBlock(
        icon="title", 
        classname="title",
        label="h4",
        template="website/blocks/h4.html"
    )

    paragraph = RichTextBlock(icon="pilcrow", features=['bold','italic','ol','ul','link','document-link'])
    table = TableBlock()
    dl = ListBlock(
        DefinitionListItem,
        label = 'Definition list',
        icon = "list-ul",
        template = "website/blocks/dl.html"
    )
    aligned_image = ImageBlock(label="Aligned image", icon="image")
    document = DocumentChooserBlock(icon="doc-full-inverse")
    video = LocalVideoBlock( icon = "fa-video-camera" )
    math = MathMLBlock( icon = "fa-calculator" )

