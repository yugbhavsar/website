from wagtail.wagtailcore import hooks
from django.utils.html import format_html_join, format_html
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static

@hooks.register('insert_editor_js')
def editor_js():
    
    js_files = [
        'js/admin/auto_populate_slug_en.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )

    return js_includes


@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/admin/admin-changes.css'))
