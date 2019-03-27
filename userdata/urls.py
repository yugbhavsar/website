from django.conf.urls import url
from .admin_views import add_safety_relation, add_many_safety_relations

app_name = 'userdata'

urlpatterns = [
    url(r'^userdata/safetyinstructionuserrelation/add/(\w+)/(\d+)/(\d+)/$', add_safety_relation, name='safetyinstruction_addwithpreselection'),
    url(r'^userdata/safetyinstructionuserrelation/addmany/$', add_many_safety_relations, name='safetyinstruction_admany')
]
