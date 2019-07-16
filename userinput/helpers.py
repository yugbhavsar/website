from django.contrib.admin.utils import quote
from django.utils.translation import ugettext as _
from django.urls import reverse

from notifications.models import CentralRadiationSafetyDataSubmission
from rubionadmin.admin import NoCopyButtonHelper, NoCopyNoDelButtonHelper

from userdata.models import StaffUser

from wagtail.contrib.modeladmin.helpers import PermissionHelper, PagePermissionHelper
from wagtail.core.models import Page

class RUBIONUserButtonHelper(NoCopyButtonHelper):
    badge_button_classnames = []
    inactivate_button_classnames = ['no']
    def badge_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.badge_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('badge', quote(pk)),
            'label': _('Badge'),
            'classname': cn,
            'title': _('Badge')
        }

    def inactivate_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.inactivate_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('inactivate', quote(pk)),
            'label': _('Inactivate'),
            'classname': cn,
            'title': _('Inactivate this user')
        }

    def get_buttons_for_obj(
            self, obj, exclude=None, classnames_add=None,
            classnames_exclude=None
    ):
        if exclude is None:
            exclude = []


        btns = super(RUBIONUserButtonHelper, self).get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)
        if 'badge' not in exclude:
            btns.append(self.badge_button(getattr(obj, self.opts.pk.attname), classnames_add, classnames_exclude))
        if 'inactivate' not in exclude:
            btns.append(self.inactivate_button(getattr(obj, self.opts.pk.attname), classnames_add, classnames_exclude))

        return btns


class RUBIONUserPermissionHelper(PagePermissionHelper):
    def user_can_inspect_obj( self, user, obj ):
        return self.user_can_edit_obj( self, user, obj )

    
class RUBIONUserSafetyRelationButtonHelper(NoCopyButtonHelper):
    def get_buttons_for_obj(            
            self, obj, exclude=None, classnames_add=None,
            classnames_exclude=None
    ):
        if exclude is None:
            exclude = ['delete', 'edit']
        else:
            exclude.append('delete')
            exclude.append('edit')

        btns = super().get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)

        return btns


class RUserDataSubmissionButtonHelper(NoCopyNoDelButtonHelper):
    submit_button_classnames = ['button-secondary button-small']
    def submit_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.submit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': reverse('rubionadmin:user_send_data_to_cro', args=[pk])+'?next='+self.url_helper.get_action_url('index'),
            'label': _('Submit via email'),
            'classname': cn,
            'title': _('Submit via email')
        }
    manual_button_classnames = ['button-secondary button-small']
    def manual_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.manual_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': reverse('rubionadmin:user_cro_knows_data', args=[pk])+'?next='+self.url_helper.get_action_url('index'),
            'label': _('Manual submission'),
            'classname': cn,
            'title': _('Manual submission')
        }

    def get_buttons_for_obj(
            self, obj, exclude=None, classnames_add=None,
            classnames_exclude=None
    ):
        btns = super(RUserDataSubmissionButtonHelper, self).get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)
        btns.append(self.submit_button(getattr(obj, self.opts.pk.attname)))
        btns.append(self.manual_button(getattr(obj, self.opts.pk.attname)))
        return btns


class RUserDataSubmissionPermissionHelper( PermissionHelper ):
    def __init__(self, model, inspect_view_enabled=False):
        # override the Model
        super(RUserDataSubmissionPermissionHelper, self).__init__(model, inspect_view_enabled)
        self.model = CentralRadiationSafetyDataSubmission
        self.opts = CentralRadiationSafetyDataSubmission._meta
        
    def get_valid_parent_pages(self, user):
        return Page.objects.none()
        

def get_staff_obj( r_user ):
    if r_user.linked_user:
        try:
            staff_u = StaffUser.objects.get(user = r_user.linked_user)
            return staff_u
        except StaffUser.DoesNotExist:
            return None

def get_key_if_staff( r_user ):
    staff_u = get_staff_obj( r_user )
    if staff_u:
        return staff_u.key_number
    
    return None
