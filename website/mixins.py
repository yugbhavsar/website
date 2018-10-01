from wagtail.contrib.modeladmin.options import (
    ModelAdmin
)
from wagtail.wagtailcore import hooks



class ForcedModelAdminForPageModels ( ModelAdmin ):
    def __init__( self, *args, **kwargs ):
        super( ForcedModelAdminForPageModels, self).__init__(*args, **kwargs)
        self.is_pagemodel = False
