from wagtail.wagtailcore import hooks
from .views import create
from wagtail.wagtailadmin.menu import MenuItem
from django.core.urlresolvers import reverse
from wagtail.wagtailusers.wagtail_hooks import add_user_perm
from django.conf.urls import url, include
from django.utils.translation import ugettext as _
import rubauth.admin_urls 
@hooks.register('register_admin_urls')
def register_admin_urls():
    
    return [
        url(r'^rubauth/', include(
            rubauth.admin_urls, app_name= 'rubauth', namespace = 'rubauth' ) ),
    ]


