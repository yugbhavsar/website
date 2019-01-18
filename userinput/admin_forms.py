from .models import WorkGroup

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l

from wagtail.core.models import Page

class WorkgroupChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        wg = WorkGroup.objects.ancestor_of(obj).first()
        try:
            return "{} ({})".format(wg.get_admin_display_title(), wg.get_head().get_admin_display_title())
        except AttributeError:
            return "{}".format(wg.get_admin_display_title())



class WorkgroupChooserForm(forms.Form):
    parent_page = WorkgroupChoiceField(
        label=_l('Workgroup'),
        required=True,
        empty_label=None,
        queryset=Page.objects.none(),
        widget=forms.RadioSelect(),
    )

    def __init__(self, valid_parents_qs, *args, **kwargs):
        self.valid_parents_qs = valid_parents_qs
        super(WorkgroupChooserForm, self).__init__(*args, **kwargs)
        self.fields['parent_page'].queryset = self.valid_parents_qs

class InactivateUserForm( forms.Form ):
    WG_CHOICES = (
        ('inactivate_group', _('inactivate group')),
        ('new_head', _('select new group leader')) 
    )
    
    def __init__(self, ruser, *args, **kwargs ):
        super(InactivateUserForm, self).__init__(*args, **kwargs)

        if ruser.is_leader:
            self.fields['inactivate_group'] = forms.ChoiceField(
                choices=self.WG_CHOICES,
                widget = forms.RadioSelect(),
                label = _('Decision on the group')
            )

            wg = ruser.get_workgroup()
            choices = ((None,'--------------------------'),)
            for member in wg.get_members():
                if member != ruser:
                    choices = choices + ((member.id, member.full_name),) 

            self.fields['new_head'] = forms.ChoiceField(
                choices = choices,
                label = _('Select new group leader'),
                required = False
            )

    def clean( self ):
        cleaned_data = super().clean()
        self.decision = cleaned_data.get("inactivate_group")
        self.new_head = cleaned_data.get("new_head")
        
        if self.decision == 'new_head':
            if not self.new_head:
                self.add_error('new_head', _('Please select a new group leader.'))



        

