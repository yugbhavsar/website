from .forms import EmergencyPowerNotificationForm, AirConditionNotificationForm, AlarmNotificationForm
from .models import StaffNotification


from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse

import json

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow


def notification_seen( request, notification_id ):
    notification = get_object_or_404(StaffNotification, pk = notification_id)
    if request.user != notification.staff.user:
        raise PermissionDenied()
        
    notification.has_been_seen = True
    notification.save()
    return redirect('wagtailadmin_home')



def news_templates( request, tpl_name ):

    # --------------------------------------------
    def get_notification_tpl_form( tpl_name ):
        if tpl_name == 'emergency_power_test':
            return EmergencyPowerNotificationForm
        if tpl_name == 'air_condition_test':
            return AirConditionNotificationForm
        if tpl_name == 'alarm_test':
            return AlarmNotificationForm
        return None
    # --------------------------------------------

    Form = get_notification_tpl_form( tpl_name )

    if Form is None:
        raise Http404
    
    if request.method == 'GET':
        form = Form()
    if request.method == 'POST':
        form = Form(request.POST)
        if form.is_valid():
            return render_modal_workflow(
                request,
                None,
                'news/tpls/{}.json'.format(tpl_name),
                {'data' : form.cleaned_data}
            )
    
    
    return render_modal_workflow(
        request,
        'news/tpls/tpl_form.html',
        'news/tpls/tpl_form.js',
        {
            'form' : form,
            'post_url' : reverse('rubionadmin:news_templates', args = [tpl_name])
        }
    )

