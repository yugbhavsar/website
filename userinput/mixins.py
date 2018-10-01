from django import forms

class StyledModelForm( forms.ModelForm ):
    required_css_class = 'required'
    error_css_class = 'error'

    fieldset_trans = {}

    def get_legend_trans( self, legend ):
        try:
            return self.fieldset_trans[legend]
        except KeyError:
            return legend

    class Meta:
        abstract = True

class StyledForm( forms.Form ):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        abstract = True
