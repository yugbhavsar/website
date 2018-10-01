from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from .views import current_user

urlpatterns = [
    url(r'', current_user, name='userhome' )
]

