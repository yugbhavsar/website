from wagtail.admin.rich_text import HalloRichTextArea
from django.forms import Media, widgets
from django.contrib.staticfiles.templatetags.staticfiles import static
from wagtail.admin.edit_handlers import RichTextFieldPanel
from wagtail.utils.widgets import WidgetWithScript
import json

class CustomizableHalloRichTextArea( HalloRichTextArea ):
    def __init__ (self, options = None):
        super(CustomizableHalloRichTextArea, self).__init__()
        self.plugins = options;


    def render_js_init(self, id_, name, value):
        if self.plugins is None:
            return "makeCustomizedHalloRichTextEditable({0});".format(json.dumps(id_))
        else:
            return "makeCustomizedHalloRichTextEditable({0},{1});".format(
                json.dumps(id_), json.dumps(self.plugins))
    @property 
    def media( self ):
        return Media(js=[
            static('wagtailadmin/js/vendor/hallo.js'),
            static('rubion/js/hallo-customizable.js'),
            static('wagtailadmin/js/hallo-plugins/hallo-wagtaillink.js'),
            static('wagtailadmin/js/hallo-plugins/hallo-hr.js'),
            static('wagtailadmin/js/hallo-plugins/hallo-requireparagraphs.js'),
        ])
