from django.db import models
from wagtail.wagtailforms.models import AbstractForm
from django.utils.translation import ugettext as _
import uuid
from django.template.defaultfilters import slugify

KNOWN_COURSES = (
    ('BIOCHEMISTRY', _('Master of Biochemistry')),
    ('PHYSICS', _('Master of Physics')),
    ('CHEMISTRY', _('Master of Chemistry')),
    ('iSTEM', _('Master of stem cell biology')),
    ('BIOLOGY', _('Master of Biology')),
    ('OTHER', _('other (please specify)')),
)

class DefaultParticipantMixin ( models.Model ) :
    class Meta:
        abstract = True

    MR = 'mr'
    MS = 'ms'
    DR = 'dr'
    PROF = 'pr'

    
    SALUTATIONS = (
        (MR,    _( 'Mr.' ) ),
        (MS,    _( 'Ms.' ) ),
        (DR,    _( 'Dr.' ) ),
        (PROF,  _( 'Prof. Dr.' ))
    )
        

    name = models.CharField(
        max_length = 64,
        blank = True,
        null = False,
        verbose_name = _('Your name')
    )
    first_name = models.CharField(
        max_length = 64,
        blank = True,
        null = False,
        verbose_name = _('Your first name (including initials)')
    )
    salutation = models.CharField(
        choices = SALUTATIONS, 
        blank = False,
        max_length = 2,
        verbose_name = _('salutation')
    )
    email = models.CharField(
        blank = True,
        null = False,
        max_length = 64,
        verbose_name = _('email')
    )
    secondary_email = models.CharField(
        max_length = 64,
        blank = True,
        verbose_name = _('secondary email')
    )

    def get_course( self ):
        pass

    def clean( self ):
        self.title = "{}, {}".format( self.name, self.first_name )

class SSKCourseMixin ( DefaultParticipantMixin ) :
    class Meta:
        abstract = True



    date_of_birth = models.DateField(
        blank = False,
        verbose_name = _( 'date of birth' )
        
    )
    place_of_birth = models.CharField(
        max_length = 64,
        blank = False,
        verbose_name = _( 'place of birth' )
    )
    country_of_birth = models.CharField(
        max_length = 64,
        blank = False,
        verbose_name = _( 'country of birth' ),
        default = _( 'Germany' ),
    )

    # street = models.CharField(
    #     max_length = 64,
    #     blank = False,
    #     verbose_name = _('street'),
    # )
    # street_number = models.CharField(
    #     max_length = 10,
    #     default = "",
    #     blank = False,
    #     verbose_name = _('number'),
    # )
    # city = models.CharField(
    #     max_length = 64,
    #     blank = False,
    #     verbose_name = _('City'),
    # )
    # zip_code = models.CharField(
    #     max_length = 16,
    #     blank = False,
    #     verbose_name = _('ZIP code'),
    # )

    is_validated = models.BooleanField(
        default = False,
        verbose_name = _('Registration has been validated?')
    )
    EXCLUDED_FIELDS = ['is_validated']
    
    def validate( self ):
        course = self.get_parent().specific.get_course().specific
        if course.is_full_for( self.ptype ):
            pass
            # TODO
        else:
            # In the unlikely case of two people with the same name, we will 
            # get a clash of the slug-fields. Let's temporarily choose a random one
#            self.slug = self.slug+uuid.uuid4()
            self.move( course._get_participants_container(), 'first-child' )
#            self.slug = slugify("{}-{}".format(self.name, self.first_name))
#            self.save()


class StudentMixin ( models.Model ):
    class Meta:
        abstract = True

    student_id = models.CharField(
        max_length = 16,
#        required = False,
        blank = True,
        verbose_name = _('Student ID')
    )
    class Meta:
        abstract = True

class StudentCourseMixin( models.Model ):
    class Meta:
        abstract = True

    student_course = models.CharField(
        max_length = 64,
        blank = True,
        choices = KNOWN_COURSES,
        verbose_name = _('Student course')
    )

    student_course_other = models.CharField(
        max_length = 64,
        blank = True,
        choices = KNOWN_COURSES,
        verbose_name = _('Student course')
    )

    student_examination_office = models.CharField(
        max_length = 64,
        blank = True,
        verbose_name = _('Responsible Examination Office')
    )
    student_examination_office_building = models.CharField(
        max_length = 4,
        blank = True,
        verbose_name = _('Responsible Examination Office Building')
    )

    student_examination_office_building = models.CharField(
        max_length = 8,
        blank = True,
        verbose_name = _('Responsible Examination Office Floor and Room (Use "/" to separate)')
    )
     
        

class BillingAddressMixin( models.Model ):
    class Meta:
        abstract = True

    billing_address_company = models.CharField(
        max_length = 128,
        blank = False,
        verbose_name = _('Company'),
    )
    billing_address_department = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _('Department'),
    )

    billing_address_street = models.CharField(
        max_length = 128,
        blank = False,
        verbose_name = _('Street'),
    )

    billing_address_additional = models.CharField(
        max_length = 128,
        blank = True,
        verbose_name = _('Additional'),
    )

    billing_address_zip = models.CharField(
        max_length = 16,
        blank = False,
        verbose_name = _('ZIP'),
    )
    billing_address_city = models.CharField(
        max_length = 128,
        blank = False,
        verbose_name = _('City'),
    )
    billing_address_country = models.CharField(
        max_length = 128,
        blank = True,
        default = _( 'Germany' ),
        verbose_name = _('Country'),
    )
    
