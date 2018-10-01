from django import forms
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.widgets import AdminDateTimeInput

class RejectionForm ( forms.Form ):
    reasons_de = forms.CharField(
        widget = forms.Textarea,
        required = False
    )

    reasons_en = forms.CharField(
        widget = forms.Textarea,
        required = False
    )


    def __init__( self, *args, **kwargs ):
        self.send_en = False
        self.send_de = False

        super(RejectionForm, self).__init__(*args, **kwargs)

    def has_text( self, field ):
        text = self.cleaned_data.get(field, '').strip()
        return text != ''

    def clean_reasons_de ( self ):
        self.send_de = self.has_text('reasons_de')
        return self.cleaned_data['reasons_de']

    def clean_reasons_en ( self ):
        self.send_en = self.has_text('reasons_en')
        return self.cleaned_data['reasons_en']

    def clean( self ):
        if not( self.send_en or self.send_de):
            self.add_error('__all__', forms.ValidationError(
                'Please provide reasons at least in one language.',
                code='Data required'
            ))
        

class InstrumentBookingForm ( forms.Form ):
    start = forms.DateTimeField(
        required = True,
        label = _('Start date and time' ),
        help_text=_('use format yyyy-mm-dd hh:mm'),
        widget = AdminDateTimeInput
    )
    end = forms.DateTimeField(
        required = True,
        label = _('End date and time' ),
        help_text=_('use format yyyy-mm-dd hh:mm'),
        widget = AdminDateTimeInput
    )

    method_booking_id = forms.CharField(
        required = False,
        widget = forms.widgets.HiddenInput
    )
        

    def __init__ (self, *args, **kwargs):
        try:
            self.method_booking_id = kwargs.pop('method_booking_id')
        except:
            self.method_booking_id = None

        super( InstrumentBookingForm, self ).__init__( *args, **kwargs )

        if self.method_booking_id:
            self.fields['method_booking_id'].value = self.method_booking_id


class MethodBookingForm( forms.Form ):

    instrument = forms.ChoiceField(
        label = _( 'Select instrument' ),
        choices = (),
        widget = forms.widgets.RadioSelect,
        required = True
    )

    def clean_instrument( self ):
        ids = [ str(i.id) for i in self.instruments ]
        if self.cleaned_data['instrument'] not in ids:
            self.add_error(
                'instrument', 
                forms.ValidationError(
                    _('Please select a suitable instrument'),
                    code = 'Wrong or missing input data'
                )
            )

        return self.cleaned_data['instrument']
                           

    def __init__( self, *args, **kwargs):
        self.instruments = kwargs.pop('instruments')
        self.instrument_choices = ((i.id, i.title) for i in self.instruments)

        super( MethodBookingForm, self ).__init__(*args, **kwargs)
        
        self.fields['instrument'].choices = self.instrument_choices

