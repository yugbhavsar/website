from .models import UGCCreatePage2

from wagtail.contrib.modeladmin.options import modeladmin_register
from wagtail.wagtailcore import hooks

from rubionadmin.admin import HiddenModelAdmin


@hooks.register('after_create_page')
def do_after_page_create(request, page):
    try:
        page.after_create_hook( request )
    except AttributeError:
        pass


class UGCCreatePage2ModelAdmin ( HiddenModelAdmin ):
    exclude_from_explorer = True
    model = UGCCreatePage2

modeladmin_register( UGCCreatePage2ModelAdmin )
