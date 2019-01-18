from django import forms
from wagtail.admin.widgets import AdminDateInput, AdminTimeInput

class EmergencyPowerNotificationForm( forms.Form ):
    date = forms.DateField( widget = AdminDateInput() )
    start = forms.TimeField(widget = AdminTimeInput())
    end =  forms.TimeField(widget = AdminTimeInput())

class AirConditionNotificationForm( forms.Form ):
    date = forms.DateField( widget = AdminDateInput() )
    start = forms.TimeField(widget = AdminTimeInput())
    end =  forms.TimeField(widget = AdminTimeInput())

class AlarmNotificationForm( forms.Form ):
    date = forms.DateField( widget = AdminDateInput() )
    start = forms.TimeField(widget = AdminTimeInput())
    end =  forms.TimeField(widget = AdminTimeInput())
