from __future__ import absolute_import, unicode_literals

from .admin_views import (
    AddToCourseView, HasPayedView
)

from django.conf.urls import url
app_name = 'courses'
urlpatterns = [
    url(r'^move2course/(\d+)/(\d+)/$', AddToCourseView.as_view(), name='add2course'),
    url(r'^haspayed/(\d+)/(\d+)/$', HasPayedView.as_view(), name='haspayed'),
]

