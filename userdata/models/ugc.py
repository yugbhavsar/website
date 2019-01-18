from django.core.exceptions import (
    ValidationError,
)
from importlib import import_module
from django.db import models
from django.shortcuts import redirect
from django import forms
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from website.models import TranslatedPage
from wagtail.admin.forms import WagtailAdminPageForm
from rubion.helpers import bases, distinct_no_order, get_unique_value
from django.template.defaultfilters import slugify
from collections import OrderedDict
from django.utils.translation import ugettext as _
from website.decorators import only_content
from wagtail.admin.edit_handlers import (
    FieldPanel
)
from django.template.response import TemplateResponse

#from userdata.views import ugc_create

REGISTERED_UGC_CLASSES = {}

def register_ugc(name, cls):
    REGISTERED_UGC_CLASSES [ name ] = cls

def get_ugc_classes():
    return REGISTERED_UGC_CLASSES

class UserGeneratedContent( RoutablePageMixin ):
    '''
    This is a general model for user generated content
    '''

    exclude = [
        'go_live_at', 'expire_at', 'slug', 
        'seo_title', 'search_description',
        'show_in_menus'
    ]
    class Meta:
        abstract  = True


    @route(r'^$')
    def view( self, request ):
        pass
        
    @route(r'^edit/(\w+)$')
    def edit( self, request, pid ):
        pass
            
    @route(r'^delete/(\w+)$')
    def delete( self, request, pid ):
        pass



class UserGeneratedPage ( UserGeneratedContent, TranslatedPage ):
    exclude = [ 
        'path', 'slug', 'depth', 'numchild', 'seo_title',
        'show_in_menus', 'search_description', 'go_live_at',
        'expire_at', 'content_type'
    ]
    class Meta:
         abstract = True


class UGCMainContainer ( TranslatedPage ):
    class Meta:
        abstract = True

# class UGCContainerMeta ( type(TranslatedPage) ):
#     def __new__(mcs, name, bases, attrs):
#         try:
#             abst = attrs['Meta'].abstract
#         except:
#             abst = False
#         if not abst:
#             cls = None
#             if 'subpage_types' in attrs.keys():
#                 raise ValidationError('UGCContainer may not have subpage_types defined')
        
#             if not 'for_model' in attrs.keys():
#                 raise ValidationError('UGCContainer must define a for_model property')
#             else:
#                 if isinstance(attrs['for_model'], str):
#                     p, m = attrs['for_model'].rsplit('.', 1)
#                     print ('p: {}, m: {}'.format(p,m))
#                     mod = import_module(p)
#                     cls = getattr(mod, m)
#                 else:
#                     cls = attrs['for_model']

#             if not issubclass(cls, UserGeneratedPage):
#                 raise ValidationError('The model in the for_model-property must be derived from UserGeneratedPage')
#             attrs.update({'subpage_types' : [ cls ]})
#         return super(UGCContainerMeta, mcs).__new__(mcs, name, bases, attrs)
    


class UGCCreatePage( TranslatedPage ):
    is_creatable = False
    template = 'userdata/ugc/ugc_create_page.html'

    def get_modelform( self ):
        parent = self.get_parent().specific
        try :
            p, m = parent.subpage_types[0].model_form.rsplit('.', 1)
        except AttributeError:
            m = "{}{}".format(parent.subpage_types[0].__name__, 'ModelForm')
            try :
                p = parent.subpage_types[0].model_form_path
            except AttributeError: 
                try:
                    p, rest = parent.subpage_types[0].__module__.rsplit('.models', 1)
                except ValueError:
                    p, rest = parent.subpage_types[0].__module__.rsplit('.', 1)
                p += '.forms'
        mod = import_module(p)
        cls = getattr(mod, m)
        
        return cls

    def serve_success( self, request ):
        return redirect(self.get_parent().url)

    def serve ( self, request ):
        if request.method == 'POST':
            form = self.get_modelform()(request.POST)
            if form.is_valid():
                instance = form.save(commit = False)
                self.get_parent().add_child( instance = instance )
                return self.serve_success( request )
        else:
            form = self.get_modelform()()
            
        context = self.get_context( request )
        context['form'] = form
        return TemplateResponse(
            request,
            self.get_template( request ),
            context
        )
        
            

class UGCContainer ( TranslatedPage ):
    create_title = 'Create'
    create_title_de = 'Erstelle'
    create_slug =  'create'

    is_creatable = False

    class Meta:
        abstract = True

    def after_create_hook( self, request ):
        if len( UGCCreatePage.objects.child_of( self ) ) > 0:
            return
        try:
            clsname = self.subpage_types[0]._meta.verbose_name
        except:
            clsname = self.subpage_types[0].__name__

        title = "{} {}".format(self.create_title, clsname)
        title_de = "{} {}".format(self.create_title_de, clsname)
        create_page = UGCCreatePage()
        create_page.title = title
        create_page.title_de = title_de
        create_page.slug = self.create_slug
        self.add_child( instance = create_page )

    def clean( self ):
        self.slug = get_unique_value( type( self ), slugify( self.title ) )
        
        
# class TestModel( UserGeneratedPage ): 

#     class Meta:
#         verbose_name = _('a test model')
    

# @only_content
# class TestModelContainer ( UGCContainer ):
#     for_model = 'userdata.models.ugc.TestModel'
#     content_panels = [
#         FieldPanel( 'title' ),
#         FieldPanel( 'title_de' )
#     ]
    



@only_content
class UserGeneratedContentContainer( UGCMainContainer ):
    content_panels = [
        FieldPanel( 'title' ),
        FieldPanel( 'title_de' ),
    ]


    is_creatable = False
