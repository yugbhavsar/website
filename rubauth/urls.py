from django.conf.urls import url
from .views import identify, confirm

urlpatterns = [
    url(r'identify/(?P<pk>[0-9]+)/$', identify, name='rubauth.identify'),
    url(r'confirm/(?P<uuid>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[‌​0-9a-f]{12})/$', confirm, name='rubauth.confirm'),
]
