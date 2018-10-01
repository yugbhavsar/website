
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l



from wagtail.wagtailcore.models import Page

class CourseDescriptionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.specific.get_admin_display_title()




class CourseDescriptionChooserForm(forms.Form):
    parent_page = CourseDescriptionChoiceField(
        label=_l('Course'),
        required=True,
        empty_label=None,
        queryset=Page.objects.none(),
        widget=forms.RadioSelect(),
    )

    def __init__(self, valid_parents_qs, *args, **kwargs):
        self.valid_parents_qs = valid_parents_qs
        super(CourseDescriptionChooserForm, self).__init__(*args, **kwargs)
        self.fields['parent_page'].queryset = self.valid_parents_qs
