from django import forms

from website.models import TermsAndConditionsPages

from wagtail.wagtailcore.models import Site


class StyledCheckbox(forms.widgets.CheckboxInput):
    template_name = 'website/forms/widgets/checkbox.html'

class StyledRadioSelect(forms.widgets.RadioSelect):
    template_name = 'website/forms/widgets/radioselect.html'
    option_template_name = 'website/forms/widgets/radio_option.html'

class StyledCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    '''This widget now is very messy since it handles, hard-coded, 
    the `required_nuclides` used for ProjectForms.'''

    template_name = 'website/forms/widgets/checkbox_select.html'
    option_template_name = 'website/forms/widgets/checkbox_option.html'

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)

        try:
            context['requires_nuclides'] = self.requires_nuclides
        except AttributeError:
            pass
        return context

    def create_option(self, *args, **kwargs):
        options = super().create_option(*args, **kwargs)
        try:
            if options['value'] in self.requires_nuclides:
                options['attrs']['data-requires_nuclides'] = '1'
        except AttributeError:
            pass

        return options

class StyledDOIWidget( forms.widgets.TextInput ):
    template_name = 'website/forms/widgets/doi_input.html'

class DependentTextarea( forms.widgets.Textarea ) :
    template_name = 'website/forms/widgets/dependent_textarea.html'

    def __init__(self, depends_on, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.depends_on = depends_on

    def get_context(self, *args, **kwargs):
        context = super(DependentTextarea, self).get_context(*args, **kwargs)
        context['depends_on'] = self.depends_on

        return context

class InlineFieldFourFields( forms.widgets.HiddenInput ):
    template_name = 'website/forms/widgets/inline_field_four_fields.html'
    
    def __init__(self, headings, depending_field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headings = headings
        self.depending_field = depending_field
    
    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['head1'] = self.headings[0]
        context['head2'] = self.headings[1]
        context['head3'] = self.headings[2]
        context['head4'] = self.headings[3]
        context['depending_field'] = self.depending_field

        return context

class StyledDateSelect( forms.widgets.SelectDateWidget ):
    template_name = 'website/forms/widgets/multiwidget_with_p.html'

class TermsAndConditionsWidget( StyledCheckbox ):
    template_name = 'website/forms/widgets/terms_and_conditions.html'

    def __init__(self, tandc, *args, **kwargs ):
        super(TermsAndConditionsWidget, self).__init__(*args, **kwargs)

        self.tandc = tandc

    def get_context(self, *args, **kwargs):
        context = super(TermsAndConditionsWidget, self).get_context(*args, **kwargs)
        site = Site.objects.get(is_default_site = True)
        tandcsetting = TermsAndConditionsPages.for_site(site)
        try:
            context['tandcpage'] = getattr(tandcsetting, self.tandc)
        except AttributeError:
            pass

        print(context)
        return context
            
