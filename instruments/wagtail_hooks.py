from .filters import BookableInstrumentsFilter
from .models import (
    MethodPage, InstrumentPage, InstrumentByProjectBooking,
    MethodsByProjectBooking, InstrumentContainerPage, MethodContainerPage
)

from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l

from rubionadmin.admin import HiddenModelAdmin
from wagtail.contrib.modeladmin.options import (
     ModelAdmin, ModelAdminGroup, modeladmin_register
)


# Hide from explorer

class InstrumentContainerPageMA( HiddenModelAdmin ):
    model = InstrumentContainerPage
    exclude_from_explorer = True

class MethodContainerPageMA( HiddenModelAdmin ):
    model = MethodContainerPage
    exclude_from_explorer = True

modeladmin_register(MethodContainerPageMA)
modeladmin_register(InstrumentContainerPageMA)

class MethodPageModelAdmin ( ModelAdmin ):
    model = MethodPage
    menu_label = _l('Methods')
    menu_icon = ' icon-fa-gears'
    list_display = ('title', 'title_de','responsible_editor')
    search_fields = ('title', 'title_de')
    menu_order = 300
    exclude_from_explorer = True

class InstrumentPageModelAdmin ( ModelAdmin ):
    model = InstrumentPage
    menu_label = _l('Instruments')
    menu_icon = ' icon-fa-gear'
    list_display = ('title','responsible_editor')
    menu_order = 300
    exclude_from_explorer = True


class InstrumentByProjectBookingModelAdmin ( ModelAdmin ):
    model = InstrumentByProjectBooking
    menu_label=_l('Instruments')
    menu_icon=' icon-fa-gear'
    list_display = ( 'instrument','project','start','end' )
    list_filter = (BookableInstrumentsFilter,)

class MethodsByProjectBookingModelAdmin ( ModelAdmin ):
    model = MethodsByProjectBooking
    menu_label=_l('Methods')
    menu_icon=' icon-fa-gears'
    list_display = ( 'method','project','instrument_booking' )
#    list_filter = (BookableInstrumentsFilter,)

class BookingsModelAdminGroup(ModelAdminGroup):
    menu_label = _l('Bookings')
    menu_icon = ' icon-fa-calendar'  
    menu_order = 200  
    items = (InstrumentByProjectBookingModelAdmin, MethodsByProjectBookingModelAdmin)

#modeladmin_register(BookingsModelAdminGroup)

class EquipmentModelAdmin( ModelAdminGroup ):
    menu_label = _l('Equipment')
    menu_icon = ' icon-fa-gears'
    menu_order = 50
    items = ( MethodPageModelAdmin, InstrumentPageModelAdmin )
    

modeladmin_register(EquipmentModelAdmin)



