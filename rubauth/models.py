from .auth import fetch_user_info
from .forms import LoginForm

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, get_user_model
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.template import Template, Context
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext as _

import uuid 

from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, PageRevision
from wagtail.snippets.models import register_snippet

from website.decorators import default_panels
from website.models import (
    TranslatedPage, IntroductionMixin, EMailText
)

from website.utils import send_mail


@default_panels
class LoginPage( RoutablePageMixin, IntroductionMixin, TranslatedPage ):
    template = 'rubauth/login.html'

    is_creatable = False

    sidebar_content = RichTextField(
        verbose_name = _('sidebar content'),
        blank = True, null = True
    )

    @route(r'^$', name='view')
    def handle_form( self, request ):
        if request.method == 'GET':
            form = LoginForm()
            return TemplateResponse(
                request,
                self.template,
                {
                    'page' : self,
                    'form' : form,
                    'user' : request.user
                }
            )
        
        # Called with data
 
        form = LoginForm(request.POST)
        if form.is_valid():
            auth_login(request, form.get_user() ) 
            return HttpResponseRedirect(resolve_url('userhome'))
        else:
            messages.error( request, _('Incorrect login data.'))
            return HttpResponseRedirect( self.url )
    
@register_snippet        
class Identification (models.Model):
    email = models.CharField(
        max_length = 256
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        blank = True,
        null = True
    )
    uid = models.CharField(
        max_length = 128,
        blank = True,
        null = True
    )

    created_at = models.DateTimeField(
        auto_now_add = True
    )

    has_been_shown = models.BooleanField(
        default = False 
    )

    redirect_to = models.CharField(
        max_length = 128,
        null = True,
        blank = True
    )

    mail_text = models.CharField(
        max_length = 256,
        blank = True,
        null = True
    )
    
    page = models.ForeignKey(
        Page,
        on_delete = models.CASCADE,
    )

    create_user = models.BooleanField(
        default = False
    )
    login_user = models.BooleanField(
        default = False
    )
    

    def __str__(self):
        return str(self.page)


    def deactivate( self ):
        self.uuid = None
        self.save()

    def create_rub_user( self, username ):
        Usermodel = get_user_model()
        userinfo = fetch_user_info( username ) 
        user = Usermodel()
        user.username = username
        user.email = userinfo[ 'email' ].replace('ruhr-uni-bochum', 'rub')
        user.first_name = userinfo[ 'first_name' ] 
        user.last_name = userinfo[ 'last_name' ]
        user.set_unusable_password()
        user.save()
        return user
    
    def create_external_user( self, username ):
        Usermodel = get_user_model()
        user = Usermodel()
        user.username = username
        user.email = username
        user.set_unusable_password()
        user.save()
        return user

    def send_mail( self, email, request, context = {} ):
        self.email = email
        self.save()
        context['uuidlink'] = request.build_absolute_uri(
            reverse('rubauth.confirm', kwargs = {'uuid': self.uuid})
        ) 
        mail = EMailText.objects.get(identifier = self.mail_text)
        mail.send(email, context)



    def is_identified( self, username, request, rub_user = False ):
#        if not settings.DEBUG:
        self.deactivate()
        self.has_been_shown=True
        self.save()
        # Check if user exists:

        Usermodel = get_user_model()
        user = None
        try:
            user = Usermodel.objects.get(username = username)
        except:
            pass

        if self.uid:
            rub_user = True
            username = self.uid
            
        if rub_user:
            backend = 'rubauth.auth.LDAPBackend'
        else:
            backend = 'django.contrib.auth.backends.ModelBackend'

        if not user and self.create_user:
            if rub_user:
                user = self.create_rub_user( username )
            else:
                user = self.create_external_user( username )

        if user and self.login_user:
            auth_login( request, user, backend = backend )

        response = None
        try:
            response = self.page.specific.validate( 
                request, user = user, username = username 
            )
        except AttributeError:
            pass

        if not response:
            if self.redirect_to:
                response = HttpResponseRedirect(self.redirect_to)
            else:
                response = HttpResponseRedirect('/')
        
        return response
    
