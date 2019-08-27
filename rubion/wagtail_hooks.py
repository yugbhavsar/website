##
# wagtail hooks for rubion app

from wagtail.core import hooks
from django.utils.html import format_html_join, format_html
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static

@hooks.register('insert_editor_js')
##
# inserts `js/admin/auto_populate_slug_en.js` into the javascripts of the admin area
# This function will be called by wagtail and is meant to be used by other code
def editor_js():
    
    js_files = [
        'js/admin/auto_populate_slug_en.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )

    return js_includes


@hooks.register('insert_global_admin_css')
##
# inserts `css/admin/admin-changes.css` to the css section of the admin area
# This function will be called by wagtail and is meant to be used by other code

def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/admin/admin-changes.css'))
