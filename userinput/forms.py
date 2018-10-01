from .models import (
    RUBIONUser, Project, WorkGroup, Project2MethodRelation, 
    PublicationSnippet, UserComment, Nuclide, Project2NuclideRelation
)
from .mixins import StyledModelForm

from collections import OrderedDict

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.translation import get_language, ugettext_lazy as _
from django.utils.text import slugify

from instruments.models import MethodPage

import re 
from rubauth.auth import fetch_user_info
from rubauth.forms import RUBUserCreationForm
from rubauth.models import Identification

from ugc.models import UserGeneratedContent2

from website.widgets import (
    StyledCheckbox, StyledRadioSelect, 
    StyledCheckboxSelectMultiple,
    DependentTextarea, InlineFieldFourFields
)

import json

class RelatedMethodsForm ( forms.Form ):
    related_methods = forms.MultipleChoiceField(
        choices = (),
        widget = StyledCheckboxSelectMultiple
    )
    
    def __init__ (self, *args, **kwargs):

        super(RelatedMethodsForm, self).__init__(*args, **kwargs)
        methods = MethodPage.objects.live()
        if get_language() == 'de':
            self.fields['related_methods'].choices = methods.order_by('title_de').values_list('id', 'title_de')
        else:
            self.fields['related_methods'].choices = methods.order_by('title').values_list('id', 'title')

        self.fields['related_methods'].widget.requires_nuclides = []
        for m in methods:
            if m.specific.requires_isotope_information:
                self.fields['related_methods'].widget.requires_nuclides.append(m.id)


    def post_create_hook( self, request, instance ):
        so = 0;
        for method_page_id in self.cleaned_data.get('related_methods'):
            obj = Project2MethodRelation()
            obj.page_id = int(method_page_id)
            obj.sort_order = so;
            obj.project_page_id = instance.id
            obj.save()
            #instance.related_methods.add(obj)
            so += 1
        #if request.user.is_authenticated:
        #    instance.save_revision(user = request.user)
        #else:
        #    instance.save_revision()
        try:
            super().post_create_hook( request, instance )
        except AttributeError:
            pass


    class Meta:
        abstract = True

class RelatedNuclidesForm( forms.Form ):
    related_nuclides = forms.CharField(
        widget = InlineFieldFourFields(
            [_('Element (use Symbol)'),
             _('Isotope'),
             _('Max amount ordered/MBq'),
             _('Max amount used per experiment/MBq')], 
            'requires_nuclides',
        ),
        required = False,
        label = _('Information about nuclides to be used')
        
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_create_hook( self, request, instance ):
        try:
            super().post_create_hook( request, instance )
        except AttributeError:
            pass
        try:
            nuclides = json.loads(self.cleaned_data.get('related_nuclides', None))
        except (TypeError, json.JSONDecodeError) as e:
            nuclides = None
        if nuclides:
            so = 0
            for nucl in nuclides:
                n = Nuclide.objects.filter(mass = nucl[1]).filter(element = nucl[0]).first()
                if not n:
                    n = Nuclide(mass = nucl[1], element = nucl[0])
                    n.save()
                p2n = Project2NuclideRelation(
                    project_page_id = instance.id, 
                    snippet = n,
                    max_order = nucl[2],
                    amount_per_experiment = nucl[3],
                    sort_order = so
                )
                so =so +1;
                p2n.save()

class RelatedPublicationsForm( forms.Form ):
    doi = forms.CharField(
        required = False
    )
    title = forms.CharField(
        required = False,
    )
    authors = forms.CharField(
        required = False,
    )
    journal = forms.CharField(
        required = False,
    )
    year = forms.CharField(
        required = False,
    )
    volume = forms.CharField(
        required = False,
    )
    fieldsets = OrderedDict([
        ('by DOI',['doi']),
        ('by values',['title', 'authors', 'journal', 'volume', 'year']),
    ])
    fieldset_trans = {
        'by DOI': _('by DOI'),
        'by values' : _('by values'),
        'Publications' : _('Publications')
    }
    alternative_fieldsets = OrderedDict([
        ('Publications', [
            'by DOI', 'by values'
        ]),
    ])
#        abstract = True



class RUBIONUserSelfModelForm ( StyledModelForm ):
    class Meta:
        model = RUBIONUser
        exclude = UserGeneratedContent2.exclude + [
            'linked_user', 'title', 'title_de', 
            'is_validated', 'has_agreed', 'dosemeter', 'is_rub',
            'may_add_members', 'may_create_projects', 'needs_key',
            'needs_safety_instructions','owner'
        ]
        widgets = {
            'previous_exposure': StyledCheckbox
        }

    fieldsets = OrderedDict([
        ('Contact information', ['sex', 'preferred_language', 'phone']),
        ('Personal data',['academic_title']),
#        ('Radiation safety data',['date_of_birth','place_of_birth','previous_exposure']),
    ])

    fieldset_trans = {
        'Contact information': _('Contact information'),
        'Personal data': _('Personal data'),
        'Safety information': _('Safety information'),
#        'Terms and conditions': _('Terms and conditions'),
#        'Radiation safety data': _('Radiation safety data'),
    }



    def __init__( self, *args, **kwargs ):
        super(RUBIONUserSelfModelForm, self).__init__(*args, **kwargs)
        try:
            r_user = kwargs['instance']
            print ("RUBION-User agreed: {}".format(r_user.has_agreed))
        except KeyError:
            r_user = None
            print ("No RUBION-User set...")

        if r_user:
            safety_fields = []
            if r_user.needs_labcoat:
                safety_fields.append('labcoat_size')
            if r_user.needs_overshoes:
                safety_fields.append('overshoe_size')
            if r_user.needs_entrance:
                safety_fields.append('entrance')
                self.fields['entrance'].help_text = _('You will find your protective clothing in the security entrance you select here.')
            if r_user.needs_radiation_safety_data:
                safety_fields.append('date_of_birth')
                self.fields['date_of_birth'].help_text = '{}. {}'.format(_('Format: YYYY-MM-DD'), _('Due to the work of your group, you might need an official dosemeter. In this case, the authorities will need your date of birth to identify you. If you are not sure, you can leave this empty and fill it later, if required.'))
                safety_fields.append('place_of_birth')
                self.fields['date_of_birth'].help_text = '{}. {}'.format(_('Add the country, if not Germany'), _('Due to the work of your group, you might need an official dosemeter. In this case, the authorities will need your place of birth to identify you. If you are not sure, you can leave this empty and fill it later, if required.'))
                safety_fields.append('previous_names')
                safety_fields.append('previous_exposure')
                if r_user.dosemeter == RUBIONUser.OFFICIAL_DOSEMETER:
                    self.fields['date_of_birth'].required = True
                    self.fields['date_of_birth'].help_text = '{}. {}'.format(_('Format: YYYY-MM-DD'), _('You need an official dosemeter and your exposure data will be send to the authorities. We need your date of birth to identify you.'))
                    self.fields['place_of_birth'].required = True
                    self.fields['place_of_birth'].help_text = '{}. {}'.format(_('Add the country, if not Germany'), _('You need an official dosemeter and your exposure data will be send to the authorities. We need your place of birth to identify you.'))

            if safety_fields:
                self.fieldsets.update({'Safety information' : safety_fields})
                
            if not r_user.has_agreed:
                self.fields['terms_conditions'] = forms.BooleanField(
                    label = _('I agree to the terms and conditions'),
                    help_text = _('I agree to the following terms and conditions: The personal data provided by you is stored for electronic and personal communication. Safety related data is stored and passed to the respective authorities according to §112 Strahlenschutzverordnung.'),
                    widget = StyledCheckbox(attrs={'checked' : False} ),
                )


                self.fieldsets.update({'Terms and conditions': ['terms_conditions']});
                self.fieldset_trans.update({'Terms and conditions': _('Terms and conditions')})
                
        

class ExternalRUBIONUserSelfModelForm ( StyledModelForm ):
    class Meta:
        model = RUBIONUser
        exclude = UserGeneratedContent2.exclude + RUBIONUser.admin_fields + RUBIONUser.group_head_fields + ['dosemeter']
        widgets = {
            'previous_exposure': StyledCheckbox
        }

    pwd1 = forms.CharField(
        label = _('password'),
        help_text = _('The password for logging into this site'),
        widget = forms.PasswordInput,
        required = False
    )
    pwd2 = forms.CharField(
        label = _('repeat password'),
        help_text = _('Repeat the password for logging into this site'),
        widget = forms.PasswordInput,
        required = False
    )
        
    fieldsets = OrderedDict([
        ('Contact information', ['sex', 'preferred_language', 'phone']),
        ('Personal data',['academic_title','name_db', 'first_name_db']),
#        ('Radiation safety data',['date_of_birth','place_of_birth','previous_exposure']),
        ('Change login data',['pwd1','pwd2']),
    ])
    fieldset_trans = {
        'Contact information': _('Contact information'),
        'Personal data': _('Personal data'),
#        'Radiation safety data': _('Radiation safety data'),
        'Change login data': _('Change login data'),
        'Safety information': _('Safety information'),
    }

    def __init__( self, *args, **kwargs ):

        try:
            instance = kwargs['instance']
        except KeyError:
            instance = None
        super( ExternalRUBIONUserSelfModelForm, self ).__init__( *args, **kwargs )

        self.fields['name_db'].required = True
        self.fields['first_name_db'].required = True
        self.pwd = None

        if instance:
            if not self.fields['first_name_db'].initial:
                self.initial['first_name_db'] = instance.first_name
            if not self.fields['name_db'].initial:
                self.initial['name_db'] = instance.name
        try:
            r_user = kwargs['instance']
        except KeyError:
            r_user = None
        if r_user:
            safety_fields = []
            if r_user.needs_dosemeter:
                safety_fields.append('date_of_birth')
                safety_fields.append('place_of_birth')
                safety_fields.append('previous_exposure')
            if safety_fields:
                self.fieldsets.update({'Safety information' : safety_fields})


    def clean( self ):
        pwd1 = self.cleaned_data.get('pwd1', None)
        pwd2 = self.cleaned_data.get('pwd2', None)
        
        
        if pwd1 and pwd2 and pwd1 == pwd2:
            self.pwd = pwd1
        elif pwd1 or pwd2:
            self.add_error(
                'pwd1', 
                forms.ValidationError(
                    _('The passwords did not match'),
                    code = 'Password repetition mismatch'
                )
            )
            self.add_error(
                'pwd2', 
                forms.ValidationError(
                    _('The passwords did not match'),
                    code = 'Password repetition mismatch'
                )
            )



class ExternalRUBIONUserSelfModelFormPWD ( StyledModelForm ):
    class Meta:
        model = RUBIONUser
        exclude = UserGeneratedContent2.exclude + [
            'linked_user', 'title', 'title_de', 
            'is_validated', 'has_agreed', 'may_create_projects', 
            'may_add_members', 'is_leader', 'is_rub', 'dosemeter',
            
        ]
        widgets = {
            'previous_exposure': StyledCheckbox
        }
  
    pwd1 = forms.CharField(
        label = _('password'),
        help_text = _('The password for logging into this site'),
        widget = forms.PasswordInput
    )
    pwd2 = forms.CharField(
        label = _('repeat password'),
        help_text = _('Repeat the password for logging into this site'),
        widget = forms.PasswordInput
    )

    terms_conditions = forms.BooleanField(
        label = _('I agree to the terms and conditions'),
        help_text = _('I agree to the following terms and conditions: The personal data provided by you is stored for electronic and personal communication. Safety related data is stored and passed to the respective authorities according to §112 Strahlenschutzverordnung.'),
        widget = StyledCheckbox(attrs={'checked' : False} ),
    )

    fieldsets = OrderedDict([
        ('Login data',['pwd1','pwd2']),
        ('Contact information', ['sex', 'preferred_language', 'phone']),
        ('Personal data',['academic_title','name_db', 'first_name_db']),
#        ('Radiation safety data',['date_of_birth','place_of_birth','previous_exposure']),
        ('Terms and conditions',['terms_conditions']),
    ])
    fieldset_trans = {
        'Login data': _('Login data'),
        'Contact information': _('Contact information'),
        'Personal data': _('Personal data'),
#        'Radiation safety data': _('Radiation safety data'),
        'Terms and conditions': _('Terms and conditions'),
        'Safety information': _('Safety information'),
    }

    def __init__( self, *args, **kwargs ):

        try:
            instance = kwargs['instance']
        except KeyError:
            instance = None

        super( ExternalRUBIONUserSelfModelFormPWD, self ).__init__( *args, **kwargs )

        self.pwd = None
        self.fields['name_db'].required = True
        self.fields['first_name_db'].required = True
 
        if instance:
            if not self.fields['first_name_db'].initial:
                self.initial['first_name_db'] = instance.first_name
            if not self.fields['name_db'].initial:
                self.initial['name_db'] = instance.name
        try:
            r_user = kwargs['instance']
        except KeyError:
            r_user = None
        if r_user:
            safety_fields = []
            if r_user.needs_dosemeter:
                safety_fields.append('date_of_birth')
                safety_fields.append('place_of_birth')
                safety_fields.append('previous_names')
                safety_fields.append('previous_exposure')
            if safety_fields:
                self.fieldsets.update({'Safety information' : safety_fields})
        
    def clean( self ):
        pwd1 = self.cleaned_data.get('pwd1', None)
        pwd2 = self.cleaned_data.get('pwd2', None)
            
        if pwd1 and pwd2 and pwd1 == pwd2:
            self.pwd = pwd1
        else:
            self.add_error(
                'pwd1', 
                forms.ValidationError(
                    _('The passwords did not match'),
                    code = 'Password repetition mismatch'
                )
            )
            self.add_error(
                'pwd2', 
                forms.ValidationError(
                    _('The passwords did not match'),
                    code = 'Password repetition mismatch'
                )
            )

    


class RUBIONUserModelForm ( StyledModelForm ):
    class Meta:
        model = RUBIONUser
        exclude = UserGeneratedContent2.exclude + [
            'linked_user', 'title', 'title_de', 
            'is_validated', 'has_agreed', 'dosemeter'
        ]
        widgets = {
            'needs_key' : StyledCheckbox
        }
        
    CHOICES_PERMISSIONS = (
        ('may_create_projects', _('may apply for projects')),
        ('may_add_members', _('may add members to the workgroup')),
    )

    SIDEBAR_TEXT_PARS = [
        _('<strong>For workgroup members that are RUB members:</strong> Please provide the RUB-ID.'),
        _('<strong>For workgroup members that are not members of the RUB:</strong> Please provide name and e-mail address.'),
        _('<strong>Key application:</strong> Do you think the workgroup member needs a key to have permanent access to our laboratories? (Please note: We might reject this application.)'), 
        _('<strong>Permissions:</strong> If you want to allow the the new workgroup member to administer you group and/or your projects, grant the corresponding permissions here.')
    ]
        
    rub_id = forms.CharField(
        required = False,
        label = _( 'RUB login ID' )
    )
    permissions = forms.MultipleChoiceField(
        label = _('Workgroup member permissions'),
        choices = CHOICES_PERMISSIONS,
        widget = StyledCheckboxSelectMultiple,
        required = False
    )
    fieldsets = OrderedDict([
        ('by RUB login ID',['rub_id'],),
        ('by data',['name_db', 'first_name_db','email_db'],),
        ('additional information', ['needs_key']),
        ('permissions', ['permissions'])
    ])
    fieldset_trans = {
        'by RUB login ID':_('by RUB login ID'),
        'by data':_('by data'),
        'additional information':_('additional information'),
        'permissions': _('permissions'),
        'Personal data': _('personal data'),
    }

    alternative_fieldsets = OrderedDict([
        ('Personal data', [
            'by RUB login ID',
            'by data'
        ]),
    ])


    def post_create_hook( self, request, instance  ):

        # If it is a rub-user, populate the fields with values from 
        # the ldap server
        rubid = self.cleaned_data.get('rub_id', None)
        if rubid:        
            info = fetch_user_info(self.cleaned_data.get('rub_id'))
            instance.name_db = info['last_name']
            instance.first_name_db = info['first_name']
            instance.email_db = info['email']
            instance.is_rub = True
        else:
            instance.name_db = self.cleaned_data['name_db']
            instance.first_name_db = self.cleaned_data['first_name_db']
            instance.email_db = self.cleaned_data['email_db']

        perms = self.cleaned_data.get('permissions', None)
        permissions = []
        if 'may_create_projects' in perms:
            instance.may_create_projects = True
        if 'may_add_members' in perms:
            instance.may_add_members = True
        instance.title = "{}, {}".format(instance.name, instance.first_name)
        instance.slug = instance._get_autogenerated_slug(slugify(instance.title))
        instance.dont_clean = True

        if rubid:
            # a RUB user is saved without any name or first name since the database fields do not match. 
            # Thus, let's publish it one to add name and first name...
            instance.save_revision_and_publish(user = request.user)
        instance.save_revision(submitted_for_moderation = True, user = request.user)
        # Send an email to notify the new user
        

        ident = Identification()
        ident.page = instance
        ident.create_user = True
        ident.login_user = True
        ident.activate = True
        ident.mail_text = 'Workgroup.User.create.identify'
        ident.uid  = rubid
        ident.save()
        creator = RUBIONUser.objects.get( linked_user = request.user )
        ident.send_mail( 
            instance.email, 
            request, 
            context = { 
                'creator' : creator, 
                'user' : instance,
                'workgroup' : instance.get_workgroup()
            } 
        )

    def clean (self):
        super(type(self), self).clean()
        if not self.cleaned_data.get('rub_id', False):
            e = False
            if not self.cleaned_data.get('name_db', False):
                self.add_error(
                    'name_db', 
                    forms.ValidationError(
                        _('Please fill this'),
                        code = 'empty'
                    )
                )
                e = True
            if not self.cleaned_data.get('first_name_db', False):
                self.add_error(
                    'first_name_db', 
                    forms.ValidationError(
                        _('Please fill this'),
                        code = 'empty'
                    )
                )
                e = True
            if not self.cleaned_data.get('email_db', False):
                self.add_error(
                    'email_db', 
                    forms.ValidationError(
                        _('Please fill this'),
                        code = 'empty'
                    )
                )
                e = True
            
            else:
                mail = self.cleaned_data.get('email_db', False)
                if re.match(r'^[^@]+@.*rub.de$',mail.lower()) or re.match(r'^[^@]+@.*ruhr-uni-bochum.de$',mail.lower()):
                    self.add_error(
                        'rub_id', 
                        forms.ValidationError(
                            _('You have entered a RUB e-Mail address. Please, provide the RUB-ID instead.'),
                            code = 'empty'
                        )
                    )   

            if e:
                self.add_error(
                    None,
                    forms.ValidationError(
                        _('Please provide either the RUB ID or name, first name and e-mail.'),
                        code = 'incomplete'
                    )
                )
        else:
            try:
                info = fetch_user_info(self.cleaned_data.get('rub_id'))

            except:
                self.add_error(
                    'rub_id',
                    forms.ValidationError(
                        _('Not a correct RUB ID'),
                        code = 'incorrect RUB ID'
                    )
                )
            
                
#        return cleaned_data
    



class ProjectModelForm ( StyledModelForm, RelatedMethodsForm, RelatedNuclidesForm ):
    class Meta:
        model = Project
        exclude = UserGeneratedContent2.exclude + ['max_prolongations','cnt_prolongations']
        widgets = {
            'is_confidential' : StyledCheckbox,
            'uses_gmos' : StyledCheckbox,
            'gmo_info' : DependentTextarea('uses_gmos'),
            'uses_chemicals' : StyledCheckbox,
            'chemicals_info':DependentTextarea('uses_chemicals'),
            'uses_hazardous_substances' : StyledCheckbox,
            'hazardous_info':DependentTextarea('uses_hazardous_substances'),
            'biological_agents' : StyledCheckbox,
            'bio_info' : DependentTextarea('biological_agents'),
        }


        
    note = forms.CharField(
        widget = forms.Textarea,
        label = _('Information for the RUBION team (will not be published):'),
        help_text = _('Please provide any important information. If you have spoken to one of us already, please mention this here.'),
        required = False
    )
 

    fieldsets = OrderedDict([
        ('Information about the project (en)', ['title', 'summary_en']),
        ('Information about the project (de)', ['title_de', 'summary_de']),
        ('additional information', ['is_confidential']),
        ('general safety information',[
            'uses_gmos','gmo_info',
            'uses_chemicals','chemicals_info',
            'uses_hazardous_substances','hazardous_info',
            'biological_agents','bio_info']),
        ('methods', ['related_methods','related_nuclides']),
    ])
    fieldset_trans = {
        'Information about the project (en)' : _('Information about the project (en)'),
        'Information about the project (de)' : _('Information about the project (de)'),
        'additional information' : _('additional information'),
        'methods' : _('methods'),
        'Message to the RUBION team' : _('Message to the RUBION team')
    }

    
    
    def __init__( self, *args, **kwargs):
        super(ProjectModelForm, self).__init__(*args, **kwargs)
        self.fields['title'].label = "{} ({})".format(_('Title of the project'), _("in english"))
        self.fields['title_de'].label = "{} ({})".format(_('Title of the project'), _("in german"))
        self.fields['title'].help_text = None
        
        try: 
            instance = kwargs['instance']
        except KeyError:
            self.fieldsets.update({'Message to the RUBION team': ['note']})
#            for key, val in self.fieldsets.items():
#                print("{}: {}".format(key, val))
            return

        self.fields['related_methods'].initial = []
        for rm in instance.related_methods.all():
            self.fields['related_methods'].initial.append(rm.page_id)
        self.fields['related_methods'].disabled = True
        self.fields['related_methods'].help_text=_('You cannot add or remove a method from a project that has been already approved. If you want to add or remove a method to or from your project, please contact us directly.')

        nucl = []
        for p2nr in instance.related_nuclides.all():
            nucl.append([
                p2nr.snippet.element, p2nr.snippet.mass,
                str(p2nr.max_order), str(p2nr.amount_per_experiment)
            ])

        self.fields['related_nuclides'].initial = json.dumps(nucl)


    def post_create_hook( self, request, instance ):
        super().post_create_hook(request, instance)    
        if self.cleaned_data.get('note', None):
            note = UserComment()
            note.page = instance
            note.text = self.cleaned_data.get('note', '')
            note.save()
        revision = instance.save_revision()
        revision.publish()
        instance.save_revision(submitted_for_moderation = True, user = request.user)
        messages.info( request, _('Your application for the project has been filed. You will receive a decision as soon as possible, usually within two weeks.'))



class WorkGroupModelForm ( StyledModelForm ):
    class Meta:
        model = WorkGroup
        exclude = UserGeneratedContent2.exclude

    def __init__( self, *args, **kwargs):
        super(WorkGroupModelForm, self).__init__(*args, **kwargs)
        self.fields['title_de'].label = "{} ({})".format(_('Workgroup name'), _('in german'))
        self.fields['title_de'].help_text = "{} ({})".format(_('The name of your workgroup'), _('in german'))
        self.fields['title'].label = "{} ({})".format(_('Workgroup name'), _('in english'))
        self.fields['title'].help_text = "{} ({})".format(_('The name of your workgroup'), _('in english'))
        print (self.fields['title'].__dict__)

    fieldsets = OrderedDict([
        ('information in german', ['title_de', 'institute_de', 'department_de', 'university_de']),
        ('information in english', ['title', 'institute_en', 'department_en', 'university_en']),
        ('additional information', ['homepage']),
    ])
    fieldset_trans = {
        'information in german': _('information in german'),
        'information in english': _('information in english'),
        'additional information': _('additional information'),
    }

    def post_create_hook( self, request, instance ):
        messages.info( request, _('Your application for your workgroup has been filed. Please proceed with your identification. You will receive a decision as soon as possible, usually within two weeks.') )      
