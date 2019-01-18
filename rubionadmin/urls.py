from __future__ import absolute_import, unicode_literals

from .views import (
    approve_moderation, reject_moderation, reject_moderation_form, 
    instrument_cal, method_cal, method_done,
    user_keys_reject, user_keys_accept, full_xls_list,
    user_set_dosemeter, user_send_data_to_cro, user_cro_knows_data
)


from django.conf.urls import url

from notifications.views import notification_seen, news_templates
from userinput.views import (
    user_safety_instruction_add, user_safety_instruction_del, 
    set_safety_instruction_date
)
app_name = 'rubionadmin'
urlpatterns = [
    #
    # Moderation of workgroups and projects
    #
    url(r'^moderation/(\d+)/approve/$', approve_moderation, name='approve_moderation'),
    url(r'^moderation/(\d+)/reject/$', reject_moderation, name='reject_moderation'),
    url(r'^moderation/reject/modal/(\d+)/$', reject_moderation_form, name='reject_moderation_form'),
    url(r'^moderation/reject/modal/$', reject_moderation_form, name='reject_moderation_form'),
    #
    # Bookings of instruments and methods
    #
    url(r'^booking/instrument/modal/(\d+)/$', instrument_cal, name='instrument_cal_form'),
    url(r'^booking/instrument/modal/(\d+)/(\d+)/$', instrument_cal, name='instrument_cal_form'),
    url(r'^booking/instrument/modal/(\d+)/(\d+)/(\d+)/$', instrument_cal, name='instrument_cal_form'),
    url(r'^booking/instrument/modal/$', instrument_cal, name='instrument_cal_form'),
    url(r'^booking/methods/modal/(\d+)/$', method_cal,  name = 'method_cal_form'),
    url(r'^booking/methods/modal/$', method_cal,  name = 'method_cal_form'),
    url(r'^booking/methods/done/(\d+)/$', method_done, name = 'method_done'),
    #
    # applications for keys
    #
    url(r'^rubionuser/(\d+)/key/reject$', user_keys_reject, name='user_keys_reject'),
    url(r'^rubionuser/(\d+)/key/accept$', user_keys_accept, name='user_keys_accept'),
    url(r'^rubionuser/(\d+)/add_safety_instruction/(\d+)/$', user_safety_instruction_add, name='user_safety_instruction_add'),
    url(r'^rubionuser/(\d+)/remove_safety_instruction/(\d+)/$', user_safety_instruction_del, name='user_safety_instruction_del'),
    url(r'^rubionuser/(\d+)/set_safety_instruction_date/(\d+)/$', set_safety_instruction_date, name='set_safety_instruction_date'),
    url(r'^rubionuser/(\d+)/set_safety_instruction_date/(\d+)/(\w+)/$', set_safety_instruction_date, name='set_safety_instruction_date'),
    url(r'^rubionuser/(\d+)/set_dosemeter/(\d+)/$', user_set_dosemeter, name="user_set_dosemeter"), 
    url(r'^rubionuser/(\d+)/submit_data_to_cro/$', user_send_data_to_cro, name="user_send_data_to_cro"),
    url(r'^rubionuser/(\d+)/user_cro_knows_data/$', user_cro_knows_data, name="user_cro_knows_data"),
    #
    # Notifications
    #
    url(r'^notification/(\d+)/seen/$', notification_seen, name="notification_seen"),
    #
    # News templates
    #
    url(r'^news/templates/(\w+)/$', news_templates, name='news_templates'),
    #
    # exports
    #
    url(r'^exp/xls/userdata/$', full_xls_list, name="full_xls_list")
]
