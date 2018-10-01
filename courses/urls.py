from __future__ import absolute_import, unicode_literals

from .admin_views import AddToCourseView 
from .views import (
    agree_add2course, reject_add2course, validate_course_registration
)

from django.conf.urls import url

urlpatterns = [
    url(r'^w2c/agree/(?P<uuid>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[‌​0-9a-f]{12})/$', agree_add2course, name ='agree_add2course'),
    url(r'^w2c/refuse/(?P<uuid>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[‌​0-9a-f]{12})/$', reject_add2course, name ='reject_add2course'),
    url(r'^validate/(?P<uuid>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[‌​0-9a-f]{12})/$', validate_course_registration, name ='validate_course_registration'),

]

