"""Some handy mixins related to users"""
from django.db import models
from wagtail.admin.edit_handlers import FieldPanel
from django.utils.translation import ugettext as _
from wagtail.core.models import Orderable
from wagtail.contrib.forms.models import AbstractForm
from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string

class ResponsibleEditorMixin( models.Model ):
    '''
    This class implements a mixin for a responsible staff member.
    '''
    responsible_editor = models.ForeignKey(
        'userdata.StaffUser', verbose_name = _( 'responsible editor' ),
        on_delete = models.PROTECT, null = True, blank = True
    )

    settings_panels = [
        FieldPanel( 'responsible_editor' )
    ]

    class Meta:
        abstract = True

class AbstractContactPerson( Orderable ):
    person = models.ForeignKey(
        'userdata.StaffUser', on_delete=models.CASCADE, 
        related_name = '+', verbose_name=_('staff member')
    )
    panels = [
        FieldPanel( 'person' )
    ]
    
    class Meta:
        abstract = True

class InlinePanelWithDefaultsMixin( object ):
    ''' A class that provides defaults for InlinePanels. Must be used within classes derived from page or similar '''
    
    # default fields shoud be a dict  in the form
    #   {'this_page_field': 'parent_page_field'}
    # where 'parent_page_field' defines the field name of the 
    # InlinePanel of the Parent where the defaults are found and
    # 'this_page_field' is the name of the InlinePanle that receives 
    # the values as default

    default_fields = [ ]
    relation_name = 'page'

    def get_defaults( self, field ):
        parent = self.get_parent()
        try:
            field_name = self.default_fields[ field ]
        except KeyError:
            return None

        obj = getattr(parent, field_name)

        



class AbstractUserDataForm ( AbstractForm ):
    class Meta:
        abstract = True


    # The property name of the field holding the information to be collected
    field_information = None

    choices_template = None



    def get_information_fields( self ):
        return getattr(self, self.field_information).all()

    def get_selected_information_field( self, id ):
        return getattr(self, self.field_information).filter( id = id )

    def check_for_choice( self, request ):
        self.choice = request.GET.get('choice', None)
        info_fields = self.get_information_fields()
        if info_fields.count() == 1:
            self.choice = info_fields.first().id
        if self.choice is None:
            return True
        else:
            return False

    def serve( self, request ):
        if self.check_for_choice( request ):
            return self.serve_choices( request )
        else:
            if request.method == 'GET':
                return self.serve_form( request )


    def serve_form( self, request ):
        return super(AbstractUserDataForm, self).serve( request )
            

    def serve_choices( self, request ):
        choices = self.get_information_fields()
        return render(
            request,
            self.choices_template,
            { 
                 'page' : self,
                 'choices' : choices
             },
             content_type = 'text/html; charset=utf-8'
         )

    def get_context( self, request ):
        context = super( AbstractUserDataForm, self ).get_context( request )
        context['choice'] = self.choice
        return context

    def get_data_fields(self):
        """
        Returns a list of tuples with (field_name, field_label).
        """
        
        data_fields = [
            ('selected_choice', _('Selected choice')),
            ('submit_time', _('Submission date')),
        ]
        
        data_fields += super( AbstractUserDataForm, self).get_data_fields()
        return data_fields
            
    def get_form_fields( self ):
        info = self.get_selected_information_field ( self.choice ).first()
        form_fields = info.data.get_form_fields()

        fields = []
        for key, val in form_fields.items():
            fields += val
        return fields



    

class EMailAuth ( models.Model ):
    class Meta:
        abstract = True

    mail_template = 'userdata/validation/default_mail.txt'
    validation_template = 'userdata/validation/success.html' 

    def get_validation_template( self, *args, **kwargs):
        return self.validation_template

    def validate ( self ):
        self.is_validated = True

    def send_confirmation_mail( self, to, subject, context, 
                                template = None):
        if template is None:
            template = self.mail_template
        
        return send_mail(
            subject, 
            render_to_string( template, context ),
            'foo@bar.com',
            to
        )
