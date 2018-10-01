from django.conf.urls import url
from rubauth.views import create
urlpatterns = [
    url(r'^add/$', create, name='add'),
]
