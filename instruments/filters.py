from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from instruments.models import InstrumentPage

class BookableInstrumentsFilter( admin.SimpleListFilter ):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Instrument')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'instrument'

    def lookups( self, request, model_admin ):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        bookables = InstrumentPage.objects.filter(is_bookable = True).live()
        instruments = ( 
            (instrument.id, instrument.title_trans) for instrument in bookables
        )
        return instruments

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value():
            instrument = InstrumentPage.objects.get(id = self.value())
            return queryset.filter(instrument = instrument)
        return queryset
