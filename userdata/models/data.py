# from django.db import models
# from django import forms
# from wagtail.contrib.forms.models import AbstractFormField, AbstractForm
# from wagtail.core.models import Orderable, Page, PageViewRestriction
# from modelcluster.fields import ParentalKey
# from django.utils import translation
# from wagtail.snippets.models import register_snippet
# from wagtail.admin.edit_handlers import (
#     FieldPanel, FieldRowPanel, MultiFieldPanel, InlinePanel,
#     StreamFieldPanel
# )
# from django.utils.translation import ugettext as _
# from modelcluster.models import ClusterableModel
# from wagtail.snippets.edit_handlers import SnippetChooserPanel
# from collections import OrderedDict
# from userdata.blocks import DataStreamBlock
# from wagtail.core.fields import StreamField
# from django.utils.text import slugify
# from django.shortcuts import render
# from website.models import TranslatedField, TranslatedPage
# import uuid



# class AbstractTranslatedFormField( AbstractFormField ):
#     ''' A form field with translations on label and help_text '''
#     help_text_de = models.CharField(
#         max_length = 255,
#         null = True, blank = True
#     )

#     label_de = models.CharField(
#         max_length = 255
#     )
    
    
#     unique_id = models.CharField(
#         max_length = 32,
#         verbose_name = _( 'unique identifier' ),
#         help_text = _( 'A unique identifier used for accessing the field in PDF generation or emails.' ),
#         null = True, blank = True
#     ) 
#     panels = [
#         MultiFieldPanel([
#             FieldRowPanel([
#                 FieldPanel('label'),
#                 FieldPanel('label_de'),
#             ])
#         ], heading = _('label')),
#         MultiFieldPanel([
#             FieldPanel('help_text'),
#             FieldPanel('help_text_de'),
#         ], heading=_( 'help texts' )),
#         MultiFieldPanel([
#             FieldRowPanel([
#                 FieldPanel('required'),
#                 FieldPanel('unique_id'),
#             ]),
#             FieldPanel('field_type', classname="formbuilder-type"),
#             FieldPanel('choices', classname="formbuilder-choices"),
#             FieldPanel('default_value', classname="formbuilder-default"),
#         ], heading = _( 'settings' ) ),
#     ]
#     class Meta:
#         abstract = True

# @register_snippet
# class DataSetSnippet( ClusterableModel ):
#     """ A general model to combine some FormFields into a data set """
#     title_en = models.CharField (
#         max_length = 128,
#         verbose_name = _('title [EN]'),
#         help_text = _('english id of the data set (should be unique)')    
#     )
#     title_de = models.CharField (
#         max_length = 128,
#         verbose_name = _('title [DE]'),
#         help_text = _('german id of the data set (should be unique)')    
#     )
    
#     title = TranslatedField('title')
    
#     visibility = models.CharField(
#         max_length = 32,
#         choices = [
#             ('PUBLIC', _('public') ),
#             ('RUBION', _('internal')),
#         ],
#         default = 'PUBLIC',
#     )

#     panels = [
#         MultiFieldPanel([
#             FieldRowPanel([
#                 FieldPanel('title_en'),
#                 FieldPanel('title_de'),
#             ]), 
#         ], heading = _('identifier')),
#         InlinePanel('form_fields', label = _( 'required data' ))
#     ]

#     def get_form_fields( self,  ):
#         return [
#             field for field in self.form_fields.all()
#         ]
            

#     def __str__( self ):
#         if translation.get_language() == 'de':
#             return self.title_de
#         else:
#             return self.title_en

# class FormField( AbstractTranslatedFormField ):
#      dataset = ParentalKey('DataSetSnippet', related_name='form_fields')    
    
# class AbstractDatasetCollection( ClusterableModel ):
#     class Meta:
#         abstract = True

#     data_set_name = 'data_sets'

#     title_en = models.CharField(
#         max_length = 128,
#         verbose_name = _( 'Collection title [en]' ),
#     )
#     title_de = models.CharField(
#         max_length = 128,
#         verbose_name = _( 'Collection title [de]' ),
#     )
#     title = TranslatedField('title')
#     title_trans = TranslatedField('title')

#     requires_name = models.BooleanField(
#         default = True,
#         verbose_name = _( 'name required?' ),
#         help_text = _( 'Are first name and last name required?' )
#     )

#     requires_email = models.BooleanField(
#         default = True,
#         verbose_name = _( 'email required?' ),
#         help_text = _( 'Is an email address required?' )
#     )
    
#     has_rubID = models.BooleanField(
#         default = True, 
#         verbose_name = _( 'RUB ID required?' ),
#     )

#     panels = [
#         MultiFieldPanel([
#             FieldRowPanel([
#                 FieldPanel( 'requires_name' ),
#                 FieldPanel( 'requires_email' ),
#                 FieldPanel( 'has_rubID' ),
#             ])
#         ], heading=_('settings')),
#     ]

#     def __str__( self ):
#         return self.title


#     def get_form_fields( self ):
#         fields = []
#         for data_set in getattr( self, self.data_sets_name).all():
#             fields += data_set.data_set.get_form_fields()
#         return fields


# @register_snippet
# class DataSetCollectionSnippet( AbstractDatasetCollection ):

#     panels = [
#         MultiFieldPanel([
#             FieldRowPanel([
#                 FieldPanel( 'title_en' ),
#                 FieldPanel( 'title_de' ),
#             ])
#         ], heading=_('title')),
#     ] + AbstractDatasetCollection.panels + [
#         InlinePanel( 'data_sets', label = _( 'data sets') ),         
#     ]
        

#     class Meta:
#         verbose_name = _(' Collection of data sets' )
#         verbose_name_plural = _(' Collections of data sets' )

# class DataSet2DataSetCollectionRelation( Orderable ):
#     collection = ParentalKey(
#         'DataSetCollectionSnippet', related_name = 'data_sets'
#     )
    
#     data_set = models.ForeignKey(
#         DataSetSnippet,
#     )

#     panels = [ SnippetChooserPanel( 'data_set' ) ]


# class AbstractDataItemPage( TranslatedPage ):

#     class Verification:
#         NONE   = 'none'
#         EMAIL  = 'email'
#         RUBION = 'rubion'
#         LOGIN  = 'login' 

#         METHODS = [
#             ( NONE   , _( 'none' )  ), 
#             ( EMAIL  , _( 'via E-Mail') ),
#             ( RUBION , _( 'via Staff member' ) ),
#             ( LOGIN  , _( 'via Login' ) ),
#         ]

        
#     class Meta:
#         abstract = True

#     content = StreamField(DataStreamBlock)
#     verification_method = models.CharField(
#         max_length = 16,
#         choices = Verification.METHODS,
#         default = Verification.NONE
#     )
#     verification_key =  models.CharField(
#         max_length = 256,
#         null = True, blank = True
#     )

# class DataItem ( AbstractDataItemPage ):
#     class Meta:
#         verbose_name = _( 'Data set' )        
#         verbose_name_plural = _( 'Data sets' )
        
#     content_panels = [
#         MultiFieldPanel([
#             FieldRowPanel([
#                 FieldPanel('verification_method'),
#                 FieldPanel('verification_key'),
#             ])], heading = _('verification') ),
#         StreamFieldPanel('content')
#     ]

# class DataDefinitionMixin ( models.Model ):
#     class Meta:
#         abstract = True

#     class Availability:
#         AVAILABLE = 'available'
#         WAITLIST  = 'waitlist'
#         FULL      = 'full'

#         STATUS = [
#             (AVAILABLE, _('available')),
#             (WAITLIST, _('waiting list')),
#             (FULL,_('fully booked'))
#         ]

#     price = models.IntegerField(
#         default = 0,
#         verbose_name = _('Fee'),
#     )
#     status = models.CharField(
#         max_length = 16,
#         choices = Availability.STATUS,
#         default = Availability.AVAILABLE
#     )
#     data_set = models.ForeignKey(
#         'userdata.DataSetCollectionSnippet',
#         verbose_name = _('required data'),
#         on_delete=models.PROTECT,
#         null = True, blank = True
#     )

# class AbstractDataDefinition( Orderable, DataDefinitionMixin ):
#     class Meta:
#         abstract = True


#     title_en = models.CharField(
#         max_length = 64,
#         verbose_name = _('name of this data set (en)')
#     )
#     title_de = models.CharField(
#         max_length = 64,
#         verbose_name = _('name of this data set (de)')
#     )
#     title = TranslatedField('title')
#     title_trans = TranslatedField('title')

# class DataCollection( AbstractForm, DataDefinitionMixin ):
#     template = 'userdata/datacollections/datacollection_form.html'
#     landing_page_template = 'userdata/datacollections/datacollection_landing.html'
#     verification_landing_page_template = 'userdata/datacollections/datacollection_verification_landing.html'

#     settings_panels = Page.settings_panels + [ 
#         MultiFieldPanel([
#             # @TODO: Hide this from Panel for Production, better: use disabled field
#             FieldPanel('price'),
#             FieldPanel('status'),
#             # @TODO: Hide this from Panel for Production, better: use disabled field
#             FieldPanel('data_set') 
#         ], heading = _( 'Data definition' ))
#     ]

#     def get_verification_landing_page_template( self, request, *args, **kwargs ):
#         return self.verification_landing_page_template

#     def get_form_fields( self ):
#         return self.data_set.get_form_fields()

#     def serve( self, request, *args, **kwargs ):

#         if request.method == 'POST':
#             form = self.get_form(request.POST, page=self, user=request.user)

#             if form.is_valid():
#                 # Return a flag whether a verification 
#                 # email was send
#                 verified = self.process_form_submission( form )

#                 if verified:
#                     return render(
#                         request,
#                         self.get_landing_page_template(request),
#                         self.get_context(request)
#                     )
#                 else:
#                     return render(
#                         request,
#                         self.get_verification_landing_page_template(request),
#                         self.get_context(request)
#                     )
#         else:
#             form = self.get_form(page=self, user=request.user)

#         context = self.get_context(request)
#         context['form'] = form
#         return render(
#             request,
#             self.get_template(request),
#             context
#         )


#     def process_form_submission( self, form ):

#         data = DataItem()
#         is_verified = False
#         if form.user.is_authenticated():
#             data.verification_method = AbstractDataItemPage.Verification.LOGIN
#             is_verified = True
#         else:
#             data.verification_method = AbstractDataItemPage.Verification.NONE
#             data.verification_key = str( uuid.uuid4() )

#         data.slug = str( uuid.uuid4() )
#         data.title = str( uuid.uuid4() )
#         content = []
            
#         for label, value in form.fields.items():
#             content.append(
#                 ('item', {
#                     'key'  : label,
#                     'label': value.label,  
#                     'value': form.data[label] 
#                 })
#             )
#         data.content = content
#         self.add_child( instance = data )

#         return is_verified
        

# class AbstractDataContainerPage( TranslatedPage ):
#     class Meta:
#         abstract = True



        

# class AbstractDataReceiverPage( TranslatedPage ):
#     """ 
#     A DataReceiver is a Page model that accepts Form data
#     and stores it as child pages. 
    
#     The Data fields that should be stored are taken from an 
#     InlinePanel named `data_definitions`. This should be  
#     created by a ParentalKey from an `AbstractDataDefinition` 
#     implementation.
#     """

#     class Meta:
#         abstract = True

#     def get_data_group_titles( self ):
#         # maybe not required
#         '''
#         Returns the titles of the `data_definitions` fields. 
#         Since it is multilingual, result will be a list of dicts:
#         [
#              { 
#                  'de' : 'Titel',
#                  'en' : 'Title',
#              }
#         ]
#         '''
#         defs = self.data_definitions.all()
#         titles = []
#         for definition in defs:
#             titles += [{ 
#                 'de' : definition.title_de,
#                 'en' : definition.title_en,
#             }]

#         return titles

#     def save( self, *args, **kwargs ):
#         # After the page is saved, generate the children if necessary
#         result = super( AbstractDataReceiverPage, self ).save(*args, **kwargs)
#         self.create_children()
#         return result
      
#     def create_children( self ):
#         '''
#         Generates the children with appropriate titles and slugs
#         if they are not yet present. This assumes that 
#         slugify(title_en+title_de) is unique, otherwise it will store 
#         everything in the same path.
#         '''
#         defs = self.data_definitions.all()
        
#         for definition in defs:
#             self.create_if_not_exists( definition )

#     def create_if_not_exists( self, definition ):
#         slug = slugify( definition.title_en )
#         if self.get_children().filter( slug = slug ).count() == 0:
#             # Entry does not exist, create it
#             folder = DataCollection()
#             folder.set_url_path( self )
#             folder.slug = slug
#             folder.title = definition.title_en
#             folder.title_de = definition.title_de
#             folder.price = definition.price
#             folder.data_set = definition.data_set
#             self.add_child( instance = folder )
#             folder.save_revision().publish()
            
#             # Restrict view to the Editor class
#             pvr = PageViewRestriction()
#             pvr.restriction_type = PageViewRestriction.NONE
#             pvr.page = folder
#             pvr.save()
#             pvr.restriction_type = PageViewRestriction.GROUPS

#             # @TODO do not hardcode the Group here, but make a new permission
#             pvr.groups = [ 2 ]
#             pvr.save()

    




# class TestDataReceiverPage( AbstractDataReceiverPage ):
#     content_panels = Page.content_panels + [
#         InlinePanel('data_definitions', label = _('data definitions'))
#     ]
#     class Meta:
#         verbose_name = "Testdaten_Receiver"

# class TestData( AbstractDataDefinition ):
#     page = ParentalKey(TestDataReceiverPage, related_name='data_definitions')    


