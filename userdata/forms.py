from django.forms.models import ModelForm
from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.admin import widgets
from wagtail.utils.widgets import WidgetWithScript

from userinput.models import RUBIONUser
from .models import SafetyInstructionsSnippet, StaffUser


# from .models.ugc import TestModel, UserGeneratedPage

# class TestModelModelForm( ModelForm ):
#     class Meta:
#         model = TestModel
#         exclude = UserGeneratedPage.exclude


class MultiSelectFromCombo ( forms.widgets.CheckboxSelectMultiple ):
#    allow_multiple_selected = True
#    input_type = 'hidden'
    template_name = 'forms/widgets/multiselect.html'
    option_template_name = 'forms/widgets/multiselect_option.html'
#    add_id_index = False
#    checked_attribute = {'checked': True}
#    option_inherits_attrs = True

    
    def __init__( self, attrs = None ):
        if attrs is None:
            attrs = {'class' : ' multiselectfromcombo'}
        elif 'class' in attrs:
            attrs['class'] = attrs['class'] + ' multiselectfromcombo'
        else:
            attrs['class'] = 'multiselectfromcombo'
        
        
        super().__init__(attrs)


    class Media:
        css = {
            'all': ('css/forms/widgets/multiselectfromcombo.css',)
        }
        
        js = [ 'css/forms/widgets/multiselectfromcombo.js' ]


class ManySafetyInstructionsForm( forms.Form ):
    si = forms.ChoiceField(
        label = _('Instruction'),
        choices = []
    )
    date = forms.DateField(
        label = _('Date'),
        widget= widgets.AdminDateInput
    )
    users = forms.MultipleChoiceField(
        choices = [],
        label = _('RUBION users'),
        widget = MultiSelectFromCombo()
            
    )

    staff = forms.MultipleChoiceField(
        choices = [],
        label = _('RUBION staff'),
        widget = MultiSelectFromCombo()
            
    )

    def __init__ ( self, *args, **kwargs ):
        super().__init__(*args, **kwargs)

        rstaff = StaffUser.objects.all()

        userids = [ staff.user for staff in rstaff if staff.user is not None ]
        rusers = RUBIONUser.objects.exclude(linked_user__in = userids)
  
        self.fields['si'].choices =  ( ( si.id, si.title ) for si in SafetyInstructionsSnippet.objects.all() )

        self.fields['users'].choices = ( (user.id, '{}, {}'.format(user.name, user.first_name) ) for user in rusers )
        self.fields['staff'].choices = ( (user.id, '{}, {}'.format(user.last_name, user.first_name) ) for user in rstaff )
