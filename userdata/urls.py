from django.conf.urls import url
from .admin_views import add_safety_relation

urls = [
    url(r'^userdata/safetyinstructionuserrelation/add/(\w+)/(\d+)/(\d+)/$', add_safety_relation, name='safetyinstruction_addwithpreselection'),
]
