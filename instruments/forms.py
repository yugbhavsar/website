from .helpers import INSTRUMENTBYPROJECTBOOKING_TEXTS as I_BY_P_TEXTS

from django import forms
from django.utils.translation import ugettext as _

from userinput.mixins import StyledForm

class AbstractFormWithProjects( StyledForm ):
    class Meta:
        abstract = True

    def __init__( self, *args, **kwargs):
        self.projects = kwargs.pop('projects')
        super(AbstractFormWithProjects, self).__init__(*args, **kwargs)
        project_choices = ((p.id, p.title) for p in self.projects)
        self.fields['projects'].choices = project_choices

    projects = forms.ChoiceField(
        required = True,
        choices = (),
        label = _('Select a project')
    )


class ApplicationForm( AbstractFormWithProjects ):
    '''
This form should be a model form, 
however, this requires import the respective model,
which in turn leads to circular imports.

Since it is a quite simple form, I do it manually.

The projects of the current user should be passed to the form init method.
'''

    description = forms.CharField(
        required = True,
        widget = forms.Textarea,
        label = I_BY_P_TEXTS['description']['verbose_name'],
        help_text = I_BY_P_TEXTS['description']['help_text'],
    )


class CalendarForm( AbstractFormWithProjects ):
    start = forms.DateTimeField(
        required = True,
        label=_('Begin'),
        help_text=_('Start of the measurement, format YYYY-MM-DD HH:MM')
    )
    end = forms.DateTimeField(
        required = True,
        label=_('End'),
        help_text=_('End of the measurement, format YYYY-MM-DD HH:MM')
    )

    description = forms.CharField(
        required = False,
        widget = forms.Textarea,
        label = I_BY_P_TEXTS['description']['verbose_name'],
        help_text = _('Add additional information about the project for the RUBION staff.')
    )
    
