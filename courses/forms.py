from .models import (
    StudentAttendee, SskStudentAttendee, SharedData, SskRubMemberAttendee,
    SskExternalAttendee, SskHospitalAttendee
)

from .widgets import WaitlistCheckboxWidget
from collections import OrderedDict

import datetime
from dateutil.relativedelta import relativedelta
from django import forms
from django.utils.translation import ugettext as _



from userinput.mixins import StyledForm, StyledModelForm

from website.widgets import (
    StyledCheckbox, StyledDateSelect, TermsAndConditionsWidget
)
class WaitlistForm ( StyledForm ):
    display_text = _('Waiting list for earlier course')
    waitlist = forms.BooleanField(required = False, label=_('Put me on the wait list'), widget = WaitlistCheckboxWidget)

    def __init__( self, *args, **kwargs ):
        self.provided_values = kwargs.pop('provided_values', {})
        self.course = kwargs.pop('course')
        super(WaitlistForm, self).__init__(*args, **kwargs)
        self.fields['waitlist'].widget.course = self.course

    
    def clean( self ):
        self.provided_values = {'waitlist' : self.cleaned_data['waitlist']}

class RUBIDForm ( StyledForm ):

    display_text = _('Identify')

    rub_id = forms.CharField(
        label = _('RUB ID'),
        help_text = _('Enter your RUB-ID. That is the same ID you use to read your e-mails or to login into the Moodle system.')
    )
    pwd = forms.CharField(
        widget = forms.widgets.PasswordInput,
        label = _('RUB password'),        
        help_text = _('Enter your password for the RUB-ID.')
    )

    def __init__( self, *args, **kwargs ):
        super(RUBIDForm, self).__init__(*args, **kwargs)
        self.provided_values = {}
    
    def clean ( self ):
        from .models import StudentAttendee
        att = StudentAttendee()
        if att.auto_fill( self.cleaned_data.get('rub_id'), self.cleaned_data.get('pwd') ):
            self.provided_values = {
                'last_name'    : att.last_name,
                'first_name'   : att.first_name,
                'email'        : att.email,
                'student_id'   : att.student_id,
            }
            self.is_validated = True
        else:
            self.add_error('pwd', forms.ValidationError( _('ID and password do not match.'), code='Invalid RUB credentials') )


class StudentForm ( StyledModelForm ):
    display_text = _('Personal information')
    class Meta:
        model = StudentAttendee
        fields = ['academic_title', 'last_name', 'first_name', 'email', 'student_id', 'student_course']

    def __init__( self, *args, **kwargs ):
        try:
            self.provided_values = kwargs.pop( 'provided_values' )
        except KeyError:
            self.provided_values = None
        super(StudentForm, self).__init__(*args, **kwargs)
        if self.provided_values:
            print(self.provided_values)
            print(self.fields)
            for key in self.provided_values.keys():
#                self.fields[key].widget.value = self.provided_values[key]
                try:
                    self.fields[key].widget.attrs['readonly'] = True
                    self.fields[key].widget.attrs['class'] = 'readonly'
                    self.fields[key].initial = self.provided_values[key]

                    
                except KeyError:
                    pass

class SskRubMemberDataForm( StudentForm ):
    class Meta:
        model = SskRubMemberAttendee
        fields = [
            'academic_title', 'last_name', 'first_name', 'email', 
            'institute', 'room', 'faculty', 'department'
        ]

class SskStudentForm( StudentForm ):
    class Meta:
        model = SskStudentAttendee
        fields = ['academic_title', 'last_name', 'first_name', 'email', 'student_id', 'student_course']

class SskExternalDataForm( StudentForm ):
    class Meta:
        model = SskExternalAttendee
        fields = [
            'academic_title', 'last_name', 'first_name', 'email', 
    #        'institute', 'room', 'faculty', 'department'
        ]
class SskHospitalDataForm (SskExternalDataForm):
    class Meta:
        model = SskHospitalAttendee
        fields = [
            'academic_title', 'last_name', 'first_name', 'email', 
    #        'institute', 'room', 'faculty', 'department'
        ]

        
class AbstractCertificateForm( StyledModelForm ):
    display_text = _('Information for the certificate')
    class Meta:
        abstract = True
        fields = [
            'date_of_birth', 'place_of_birth', 'country_of_birth',
            'town_zip', 'town', 
        ]

        widgets = {
            'date_of_birth' : StyledDateSelect
        }
    
    def __init__(self, *args, **kwargs):
        try:
            kwargs.pop('provided_values')
        except:
            pass
        super(AbstractCertificateForm, self).__init__(*args, **kwargs)

def get_past_years():
    today = datetime.date.today()
    years = []
    for delta in range(17,100):
        d = today - relativedelta(years = delta) 
        years.append(d.year)

    yield years

        
class SskStudentCertificateForm( AbstractCertificateForm ):
    class Meta:
        model = SskStudentAttendee
        fields = [
            'date_of_birth', 'place_of_birth', 'country_of_birth',
            'town_zip', 'town', 'country'
        ]
        widgets = {
            'date_of_birth' : StyledDateSelect(
                years = range(datetime.date.today().year-18, datetime.date.today().year-100, -1)
            )
        }

class SskRubMemberAttendeeCertificateForm( AbstractCertificateForm ):
    class Meta:
        model = SskRubMemberAttendee
        fields = [
            'date_of_birth', 'place_of_birth', 'country_of_birth',
            'town_zip', 'town', 'country'
        ]
        widgets = {
            'date_of_birth' : StyledDateSelect(
                years = range(datetime.date.today().year-18, datetime.date.today().year-100, -1)
            )
        }


    
class SskExternalAttendeeCertificateForm( AbstractCertificateForm ):
    class Meta:
        model = SskExternalAttendee
        fields = [
            'date_of_birth', 'place_of_birth', 'country_of_birth',
            'town_zip', 'town', 'country'
        ]
        widgets = {
            'date_of_birth' : StyledDateSelect(
                years = range(datetime.date.today().year-18, datetime.date.today().year-100, -1)
            )
        }



class SskHospitalAttendeeCertificateForm( SskExternalAttendeeCertificateForm ):
    class Meta:
        model = SskHospitalAttendee
        fields = [
            'date_of_birth', 'place_of_birth', 'country_of_birth',
            'town_zip', 'town', 'country'
        ]
        widgets = {
            'date_of_birth' : StyledDateSelect(
                years = range(datetime.date.today().year-18, datetime.date.today().year-100, -1)
            )
        }
        
class SskExternalAttendeInvoiceForm( StyledModelForm ):
    display_text = _('Billing information')
    class Meta:
        model = SskExternalAttendee
        fields = [
            'invoice_company', 'invoice_additional_line_1',
            'invoice_additional_line_2', 'invoice_additional_line_3',
            'invoice_street', 'invoice_street_number', 'invoice_town_zip', 
            'invoice_town', 'invoice_country'
        ]

class SskHospitalAttendeeInvoiceForm( SskExternalAttendeInvoiceForm ):
    class Meta:
        model = SskHospitalAttendee
        fields = [
            'invoice_company', 'invoice_additional_line_1',
            'invoice_additional_line_2', 'invoice_additional_line_3',
            'invoice_street', 'invoice_street_number', 'invoice_town_zip', 
            'invoice_town', 'invoice_country'
        ]



class AbstractSskTermsAndConditionsForm( StyledModelForm ):
    display_text = _('Terms and Conditions')
    class Meta:
        abstract = True
    agree = forms.BooleanField(
        widget = TermsAndConditionsWidget('courses'),
#        widget = StyledCheckbox,
        label = _('I agree to the terms and conditions.')
    )

    def __init__(self, *args, **kwargs):
        try:
            kwargs.pop('provided_values')
        except:
            pass
        super(AbstractSskTermsAndConditionsForm, self).__init__(*args, **kwargs)

    def clean( self ):
        if not ( self.cleaned_data.get('agree', None) ):
            self.add_error('agree', _('You have to agree to the terms and conditions.'))



class SskExternalAttendeeTermsAndConditionsForm( AbstractSskTermsAndConditionsForm ):
    class Meta:
        model = SskExternalAttendee
        fields = []

class SskStudentTermsAndConditionsForm( AbstractSskTermsAndConditionsForm ):
    class Meta:
        model = SskStudentAttendee
        fields = []

class SskHospitalAttendeeTermsAndConditionsForm( AbstractSskTermsAndConditionsForm ):
    class Meta:
        model = SskHospitalAttendee
        fields = []

class SskRubMemberTermsAndConditionsForm( AbstractSskTermsAndConditionsForm ):
    class Meta:
        model = SskRubMemberAttendee
        fields = []



class DataUploadForm( StyledModelForm ):
    class Meta:
        model = SharedData
        fields = [
            'uploaded_by','description'
        ]
    
    uploaded_file = forms.FileField(
        label = _('File to upload')
    )

    fieldsets = OrderedDict([
        ('upload a file', ['uploaded_file','description','uploaded_by']),
    ])
    fieldset_trans = {
        'upload a file': _('upload a file')
    }
