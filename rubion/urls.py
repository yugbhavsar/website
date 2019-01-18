from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

from search import views as search_views
from wagtail.admin import urls as wagtailadmin_urls
from rubionadmin import urls as rubionadmin_urls
from courses import admin_urls as courses_urls
from courses import urls as courses_user_urls
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
#from userdata import validation_urls, ugc_urls
from userinput import urls as userinput_urls
from rubauth import urls as rubauth_urls
from rubauth.views import logout
urlpatterns = [
    url(r'^django-admin/', admin.site.urls),
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^rubionadmin/', include(rubionadmin_urls)),
    url(r'^coursesadmin/', include(courses_urls, namespace='coursesadmin')),
    url(r'^manage-courses/', include(courses_user_urls, namespace='manage-courses')),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^logout/$', logout, name='logout')
]

urlpatterns += i18n_patterns(
    # These URLs will have /<language_code>/ appended to the beginning

    url(r'^search/$', search_views.search, name='search'),
#    url(r'^validate/', include(validation_urls)),
#    url(r'^ugc/', include(ugc_urls)),
    url(r'^auth/', include(rubauth_urls)),
    url(r'^home/', include(userinput_urls)),
    url(r'', include(wagtail_urls)),
)

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
