from django.conf.urls import url
from rubauth.views import create
app_name = 'rubauth'


urlpatterns = [
    url(r'^add/$', create, name='add'),
]
