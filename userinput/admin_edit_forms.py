from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.forms import WagtailAdminPageForm

class RUBIONUserAdminEditForm( WagtailAdminPageForm ):

    def __init__ ( self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        staff_u = None
        initial = {}
        if instance and instance.linked_user:
            from userdata.models import StaffUser
            if StaffUser.objects.filter(user = instance.linked_user).exists():
                staff_u = StaffUser.objects.get(user = instance.linked_user)
                initial['key_number'] = staff_u.key_number
                initial['needs_key'] = True
                initial['needs_safety_instructions'] = staff_u.needs_safety_instructions.all()
                    

        if instance and instance.linked_user:
            if not instance.name_db:
                initial['name_db'] = instance.linked_user.last_name
            if not instance.first_name_db:
                initial['first_name_db'] = instance.linked_user.first_name
            if not instance.email_db:
                initial['email_db'] = instance.linked_user.email

        kwargs.update(initial = initial)                   
        super().__init__(*args, **kwargs)


        
        if staff_u:
            self.fields['key_number'].disabled=True
            self.fields['key_number'].help_text = mark_safe(
                _('This user is belongs to the RUBION staff. To edit the key number, <a href="/admin/pages/{}/edit/?next=/admin/pages/{}/edit/">edit the staff entry</a>.'.format(staff_u.pk, instance.pk))
            )
            self.fields['needs_key'].disabled=True
            self.fields['needs_safety_instructions'].disabled = True
            self.fields['needs_safety_instructions'].help_text = mark_safe(
                _('This user is belongs to the RUBION staff. To change the required safety instructions, <a href="/admin/pages/{}/edit/?next=/admin/pages/{}/edit/">edit the staff entry</a>.'.format(staff_u.pk, instance.pk))
            )
