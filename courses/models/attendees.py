'''
Defines the different attendee types for the courses
'''
from .course import Course

from courses.attendees import register_attendee

from django.db import models
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l

from rubauth.auth import LDAPBackend, fetch_user_info

from userinput.models import RUBIONUser

from wagtail.core.fields import RichTextField



class CourseAttendee ( models.Model ):
    '''
    This model contains the "minimum" of data
    that is needed for an attendee.

    This is the same information that we collect for 
    RUBION users. Might be better to put this in an abstract
    "Person" class...

    This class is not(!) abstract.
    '''

    #--------------------------------------------------
    #
    # model definition
    #
    #--------------------------------------------------
    
    # we need a name and an email-address
        
    last_name = models.CharField(
        max_length = 128,
        verbose_name = _l('last name')
    )

    first_name = models.CharField(
        max_length = 128,
        verbose_name = _l('first name')
    )

    email = models.CharField(
        max_length = 128,
        verbose_name = _l('e-mail address')
    )

   
    # Since we are in germany, academic titles are important!
    # We have defined them already...

    academic_title = models.CharField(
        max_length = 1,
        choices = RUBIONUser.ACADEMIC_TITLES,
        blank = True,
        null = True
    )

    # this is the courses the attendee wants to attend. 
    # Don't make it too complicated: We have a simple one2one-relation
    # here.
    related_course = models.ForeignKey(
        Course,
        blank = True,
        null = True,
        related_name = 'attendees',
        on_delete = models.PROTECT
        
    )

    # It might, however, happen, that people are additionally on a wait list
    waitlist_course = models.ForeignKey( 
        Course,
        blank = True,
        null = True,
        related_name = 'waitlist',
        on_delete = models.PROTECT
    )

    # This stores whether any verification
    # has been performed by the attendee.
    is_validated = models.BooleanField(
        default = False,
        help_text = _('Is the attendee validated?')
    )
    
    internal_rubion_comment = RichTextField(
        blank = True
    )

    created_at = models.DateTimeField(
        auto_now_add = True
    )

    add2course_mail_sent = models.BooleanField(
        default = False,
        help_text = _('E-Mail for adding this attendee to the course from the wait list sent?'),
        verbose_name = _('Mail sent?')
    )

    add2course_mail_sent_at = models.DateTimeField(
        blank = True,
        null = True,
        help_text=_('When was the mail sent?')
    )

    validation_mail_sent = models.BooleanField(
        default = False,
    )

    validation_mail_sent_at = models.DateTimeField(
        blank = True,
        null = True,
        help_text=_('When was the validation mail sent?')
    )

    confirmation_mail_sent = models.BooleanField(
        default = False,
    )
    confirmation_mail_sent_at = models.DateTimeField(
        blank = True,
        null = True,
        help_text=_('When was the confirmation mail sent?')
    )

    #--------------------------------------------------
    #
    # properties
    #
    #--------------------------------------------------

    
    @property
    def full_name( self ):
        '''
        A property that retrieves the full name of the attendee,
        including academic title
        '''

        title_format = ""
        if self.academic_title in [ 
                RUBIONUser.PHD, 
                RUBIONUser.MD, 
                RUBIONUser.PROF 
        ]:
            title_format = "{} ".format( self.get_academic_title_display() )

        return title_format+"{} {}".format(self.first_name, self.last_name)

    #--------------------------------------------------
    #
    # METHODS
    #
    #--------------------------------------------------
    
    
    def validate( self, save = True ):
        '''
        A method that validates the object and saves it.
        
        Saving can be omitted by passing False to the 
        respective parameter
        '''
    
        self.is_validated = True        
        if save:
            self.save()
            


    def __str__( self ):
        try:
            return "{} ({} am {})".format(
                self.full_name,
                self.related_course.get_parent(),
                self.related_course.start)
        except AttributeError:
            return "{}".format(self.full_name)


class AbstractRUBAttendee ( CourseAttendee ):
    '''
    A RUB member can identify by RUB-ID and RUB-password. Data can be 
    auto-filled by this.
    
    This class is abstract.
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    class Meta:
        abstract = True

    #--------------------------------------------------
    #
    # METHODS
    #
    #--------------------------------------------------

    def auto_fill( self, rub_id, rub_pwd ):
        '''
        Method should be fed with id and pwd of a RUB member.

        returns whether authentification worked.
        '''
        if LDAPBackend.ldap_authenticate( rub_id, rub_pwd ):
            self.validate( save = False )
            self._auto_fill( rub_id )
            return True

        return False

        
    def _auto_fill( self, rub_id ):
        '''
        This method is meant to be private.
        We can retrieve information from the RUB database
        without the password of the user. However, the corresponding
        information should not be released to the public. Thus, use this
        only after authentification.
        '''
        information = fetch_user_info ( rub_id )
        self.last_name = information['last_name']
        self.first_name = information['first_name']
        self.email = information['email']
        return information



class AbstractStudentAttendee( AbstractRUBAttendee ):
    '''
    For students, we need some additional information. I assume
    that all students are from the RUB.

    This class is abstract.
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    class Meta:
        abstract = True

    #--------------------------------------------------
    #
    # model definition
    #
    #--------------------------------------------------

    student_id = models.BigIntegerField()

    student_course = models.CharField(
        max_length = 128
    )

    #--------------------------------------------------
    #
    # METHODS
    #
    #--------------------------------------------------
    
    def _auto_fill ( self, rub_id ):
        information = super(AbstractStudentAttendee, self)._auto_fill( rub_id )
        self.student_id = information['student_id']



# The above classes are sufficient to define a Attendee for, f.e, 
# the english radiation safety course.

class StudentAttendee( AbstractStudentAttendee ):
    '''
    This class implements a student from the RUB attending a course
    that does not need any additional information.
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    # Just some information for selecting this attendee
    
    identifier = 'student'
    display_name = _l('Student')
    display_name_plural = _l('Students')
    forms = ['courses.forms.RUBIDForm', 'courses.forms.StudentForm']

    class Meta:
        verbose_name = _l('student, no additional information')




class AbstractCertificateInformationMixin( models.Model ):
    '''
    Fore the german SSK, we need some information for the certificate
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    class Meta:
        abstract = True

    #--------------------------------------------------
    #
    # model definition
    #
    #--------------------------------------------------

    date_of_birth = models.DateField(
        verbose_name = _l('date of birth')
    )

    place_of_birth = models.CharField(
        max_length = 128,
        verbose_name = _l('Place (town) of birth')
    )

    country_of_birth = models.CharField(
        max_length = 128,
        verbose_name = _l('Country of birth (if not Germany)'),
        blank = True,
    )

    street = models.CharField(
        max_length = 128,
        verbose_name = _l('street')
    )

    street_number = models.CharField(
        max_length = 16,
        verbose_name = _l('street number')
    )

    town_zip = models.CharField(
        max_length = 16,
        verbose_name = _l('ZIP code')
    )
        
    town = models.CharField(
        max_length = 128,
        verbose_name = _l('town')
    )
    
    country = models.CharField(
        max_length = 128,
        verbose_name= _l( 'Country (if not Germany)' ),
        blank = True
    )
    
class InvoiceMixin( models.Model ):
    '''
    If a fee has to be payed for participation, we need information
    for the invoice
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    class Meta:
        abstract = True

    #--------------------------------------------------
    #
    # model definition
    #
    #--------------------------------------------------
        
    amount = models.DecimalField(
        max_digits = 7,
        decimal_places = 2
    )

    amount_payed =  models.DecimalField(
        max_digits = 7,
        decimal_places = 2,
        default = 0
    )
    
    payed = models.BooleanField()
    
    invoice_company = models.CharField(
        max_length = 128,
        verbose_name = _l( 'company or university' )
    )
    
    invoice_additional_line_1 = models.CharField(
        max_length = 128,
        verbose_name = _l( 'department, room  or similar' ),
        blank = True
    )
    
    invoice_additional_line_2 = models.CharField(
        max_length = 128,
        verbose_name = _l( 'department, room  or similar' ),
        blank = True
    )
    
    invoice_additional_line_3 = models.CharField(
        max_length = 128,
        verbose_name = _l( 'department, room or similar' ),
        blank = True
    )
    
    invoice_street = models.CharField(
        max_length = 128,
        verbose_name = _l('street')
    )
    invoice_street_number = models.CharField(
        max_length = 128,
        verbose_name = _l('street number')
    )
    
    invoice_town_zip = models.CharField(
        max_length = 16,
        verbose_name = _l('ZIP code')
    )
    
    invoice_town = models.CharField(
        max_length = 128,
        verbose_name = _l('town')
    )
    
    invoice_country = models.CharField(
        max_length = 128,
        verbose_name= _l( 'Country (if not Germany)' ),
        blank = True, 
    )


# Attendee types for the german SSK

class SskStudentAttendee ( 
        AbstractStudentAttendee, AbstractCertificateInformationMixin
):
    '''
    Implements students attending the german SSK
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    class Meta:
        verbose_name = _l( 'student for course with official certificate' )

    identifier = 'sskstudent'
    display_name =_l('Student')
    display_name_plural =_l('Students')
    forms = [
        'courses.forms.RUBIDForm', 
        'courses.forms.SskStudentForm', 
        'courses.forms.SskStudentCertificateForm', 
        'courses.forms.SskStudentTermsAndConditionsForm'
    ]
    
    additional_admin_fields = (
        ('student_course', _('student course')),
    )


class SskExternalAttendee ( 
        CourseAttendee, AbstractCertificateInformationMixin, InvoiceMixin 
):
    '''
    implements external participants for the german SSK
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    class Meta:
        verbose_name = _l('External participant for course with official certificate')

    identifier = 'sskexternal'
    display_name =_l('External')
    display_name_plural =_l('Externals')
    additional_admin_fields = (
        ('invoice_company', _('company')),
        ('payed', _('has payed')),
        
    )
    forms = [
        'courses.forms.SskExternalDataForm',
        'courses.forms.SskExternalAttendeeCertificateForm',
        'courses.forms.SskExternalAttendeInvoiceForm',
        'courses.forms.SskExternalAttendeeTermsAndConditionsForm'
    ]
    




class SskHospitalAttendee ( 
        CourseAttendee, AbstractCertificateInformationMixin, InvoiceMixin 
):
    '''
    implements RUB hospital staff attending the german SSK
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    class Meta:
        verbose_name = _l('External participant from RUB hospital for course with official certificate')

    identifier = 'sskhospital'
    display_name =_l('RUB hospital employee')
    display_name_plural =_l('RUB hospital employees')
    forms = [
        'courses.forms.SskHospitalDataForm',
        'courses.forms.SskHospitalAttendeeCertificateForm',
        'courses.forms.SskHospitalAttendeeInvoiceForm',
        'courses.forms.SskHospitalAttendeeTermsAndConditionsForm'
    ]


class SskRubMemberAttendee( 
        AbstractRUBAttendee, AbstractCertificateInformationMixin
):
    '''
    implements a RUB member attending the german SSK
    '''

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    identifier = 'sskrubmember'
    display_name =_l('RUB employee')
    display_name_plural =_l('RUB employees')
    forms = [
        'courses.forms.RUBIDForm',
        'courses.forms.SskRubMemberDataForm' ,
        'courses.forms.SskRubMemberAttendeeCertificateForm',
        'courses.forms.SskRubMemberTermsAndConditionsForm'
    ]

    class Meta:
        verbose_name = _l('RUB staff for course with official certificate')


    #--------------------------------------------------
    #
    # model definition
    #
    #--------------------------------------------------
    
    faculty = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Faculty')
    )

    department = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _l('Department')
    )

    institute = models.CharField(
        max_length = 128,
        verbose_name = _l('Institute or Workgroup')
    )

    room = models.CharField(
        max_length = 16,
        verbose_name = _l('Building and room')
    )


    

# register the attendees
register_attendee( StudentAttendee )

register_attendee( SskStudentAttendee )
register_attendee( SskExternalAttendee )
register_attendee( SskHospitalAttendee )
register_attendee( SskRubMemberAttendee )
