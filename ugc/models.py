from collections import OrderedDict

from django import forms
from django.contrib import messages
from django.core.exceptions import (
    ValidationError, PermissionDenied
)
from django.db import models
from django.shortcuts import redirect
from django.template.defaultfilters import slugify
from django.template.response import TemplateResponse
from django.utils import translation
from django.utils.translation import ugettext as _

from importlib import import_module

from rubion.helpers import bases, distinct_no_order

from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.core.fields import RichTextField
from wagtail.core.models import Orderable, Page, PageRevision

from website.decorators import only_content
from website.models import (
    TranslatedPage, ChildMixin, OptionalIntroductionMixin,
    SidebarContentMixin
)
from wagtail.admin.edit_handlers import (
    FieldPanel, StreamFieldPanel
)

REGISTERED_UGC_CLASSES = {}

def register_ugc(name, cls):
    REGISTERED_UGC_CLASSES [ name ] = cls

def get_ugc_classes():
    return REGISTERED_UGC_CLASSES

class UserGeneratedContent2( RoutablePageMixin ):
    '''
    This is a general model for user generated content
    '''

    VIEW = 'v'
    EDIT = 'e'
    DELETE = 'd'

    exclude = [
        'path', 'depth', 'numchild','content_type',
        'go_live_at', 'expire_at', 'slug', 
        'seo_title', 'search_description',
        'show_in_menus', 'first_published_at'
    ]
    class Meta:
        abstract  = True


    @route(r'^$')
    def view( self, request ):
        if hasattr(self, 'user_passes_test'):
            test_passed = self.user_passes_test( request.user, self.VIEW )
        else:
            test_passed = True

        if test_passed:
            context = self.get_context( request )
            context['page'] = self
            return TemplateResponse(
                request,
                self.view_template,
                context
            )
        else:
            raise PermissionDenied

        
    @route(r'^edit/$')
    def edit( self, request ):
        try:
            test_passed = self.user_passes_test( request.user, self.EDIT )
        except AttributeError:
            test_passed = True

        if not test_passed:
            raise PermissionDenied

        create_page  = (
            # @TODO (?) Might be possible without touching the database...
            UGCCreatePage2.objects.sibling_of(self, inclusive = False)
            .first().specific
        )
        form_model = create_page.get_modelform()
        template  = create_page.template
        if request.method == 'POST':
            form = form_model( request.POST, instance = self )
            if form.is_valid():
                instance = form.save( commit = False )
                instance.save()
                try:
                    form.post_edit_hook(request, instance)
                except AttributeError:
                    pass
                messages.success( request, _('Your changes have been saved.'))
                return self.serve_success( request, edit = True )
            else:
                messages.error( request, _('An error occured.') )
        else:
            form = form_model(instance = self)
            
        
        return TemplateResponse(
            request,
            template,
            {
                'page': self,
                'form' : form
            }
        )
            
            
            
    @route(r'^delete/$', name="delete")
    def delete_view( self, request ):
        pass


    def save_revision_and_publish( self, user = None ):
        revision = self.save_revision(user = user)
        revision.publish()
        return revision


class UserGeneratedPage2 ( UserGeneratedContent2, ChildMixin, TranslatedPage ):
    exclude = [ 
        'path', 'slug', 'depth', 'numchild', 'seo_title',
        'show_in_menus', 'search_description', 'go_live_at',
        'expire_at', 'content_type', 'internal_rubion_comment'
    ]

    internal_rubion_comment = RichTextField(
        blank = True,
        help_text = _('A RUBION-internal comment')
    )
    

    def serve_success ( self, request, edit = False ):

        return redirect(self.url)

    class Meta:
         abstract = True


class UGCMainContainer2 ( TranslatedPage ):
    class Meta:
        abstract = True

    

@only_content
class UGCCreatePage2( TranslatedPage, SidebarContentMixin ):
    is_creatable = False
    template = 'ugc/ugc_create_page.html'

    def get_modelform( self ):
        parent = self.get_parent().specific
        try :
            p, m = parent.for_model.get_model_form( self )
        except AttributeError:
            try :
                p, m = parent.for_model.model_form.rsplit('.', 1)
            except AttributeError:
                m = "{}{}".format(parent.for_model.__name__, 'ModelForm')
                try :
                    p = parent.for_model.model_form_path
                except AttributeError: 
                    try:
                        p, rest = parent.for_model.__module__.rsplit('.models', 1)
                    except ValueError:
                        p, rest = parent.for_model.__module__.rsplit('.', 1)
                    p += '.forms'
        mod = import_module(p)
        cls = getattr(mod, m)
        
        return cls


    def serve ( self, request ):
        Model = self.get_parent().specific.for_model
        try:
            allowed = Model.user_passes_create_test( request, self )
        except AttributeError:
            allowed = True
            
        if not allowed:
            raise PermissionDenied


        if request.method == 'POST':
            form = self.get_modelform()(request.POST)
            if form.is_valid():
                instance = form.save(commit = False)
                if hasattr(form, 'pre_create_hook'):
                    form.pre_create_hook( request )

                self.get_parent().specific.add_child( instance = instance )
                messages.success( request, _('Your input has been saved.'))
                
                if request.user.is_authenticated:
                    instance.save_revision(user = request.user)
                else:
                    instance.save_revision()
                if hasattr(form, 'post_create_hook'):
                    form.post_create_hook( request, instance )

                return instance.serve_success( request )
            else:
                print (form.errors)
                messages.error( request, _('An error occured.'))
        else:
            form = self.get_modelform()()
            
        context = self.get_context( request )
        context['form'] = form
        return TemplateResponse(
            request,
            self.get_template( request ),
            context
        )

    @property
    def sidebar_text( self ):
        try:
            return self.get_parent().specific.sidebar_text
        except AttributeError:
            return None

    content_panels = [
        FieldPanel('title'),
        FieldPanel('title_de'),
        StreamFieldPanel('sidebar_content_de'),
        StreamFieldPanel('sidebar_content_en'),
    ]
    

class UGCContainer2 ( OptionalIntroductionMixin, TranslatedPage ):
    create_title = 'Create'
    create_title_de = 'Erstelle'
    create_slug =  'create'
    is_creatbale = False
    template = 'ugc/ugc_container.html'

    class Meta:
        abstract = True


    def get_visible_children( self ):

        if translation.get_language() == 'de':
            title_field = 'title_de'
        else:
            title_field = 'title'
        
        pages = self.for_model.objects.live().child_of(self).specific()

        return pages.order_by(title_field)

    def after_create_hook( self, request ):
        if len( UGCCreatePage2.objects.child_of( self ) ) > 0:
            return
        try:
            clsname = self.for_model._meta.verbose_name
        except:
            clsname = self.for_model.__name__

        title = self.create_title
        title_de = self.create_title_de
#        title = "{} {}".format(self.create_title, clsname)
        

        create_page = UGCCreatePage2()
        create_page.title = title
        create_page.title_de = title_de
        create_page.slug = self.create_slug
        self.add_child( instance = create_page )

    def clean( self ):
        if not self.slug:
            self.slug = self._get_autogenerated_slug( slugify( self.title ) )
        


    
