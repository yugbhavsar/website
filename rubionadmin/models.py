from django.db import models
from django.utils.translation import ugettext as _

from wagtail.snippets.models import register_snippet
# Create your models here.


@register_snippet
class RubionAdminPermissionSnippet( models.Model):
    '''
    This class is an ugly workaround for the wagtail permission system.

    I want to decide on the groups-level which entries are listed in the 
    admin menu to make things more simple. However, wagtail seems not to 
    support this on page-derived models. So we need a single instance of
    this snippet to enable the permissions. 

    This is ugly.
    '''

    class Meta:
        permissions = (
            #
            # Permissions used to control elements of the 
            # admin menu
            ('full_explorer', _('Sees full explorer menu')),
            ('snippet_menu', _('Sees snippet menu')),
            ('document_menu', _('Sees document menu')),
            ('images_menu', _('Sees images menu')),
            ('settings_menu', _('Sees settings menu')),
            ('staff_menu', _('Sees staff menu')),
            ('instruments_menu', _('Sees instruments menu')),
            ('methods_menu', _('Sees methods menu')),
            ('courses_menu', _('Sees courses menu')),
            ('webpages_menu', _('Sees a webpages menu')),
            ('export_menu', _('Sees the export menu')),
            #
            # Additional permissions used for some admin views
            ('update_safety_instructions', _('May update safety instruction')),
            #
            # Dashboard customization
            ('db_workgroup_requests', _('Workgroup requests shown on dashboard')),
            ('db_project_requests', _('Project requests shown on dashboard')),
            ('db_instrument_requests', _('Instrument requests shown on dashboard')),
            ('db_methods_requests', _('Method requests shown on dashboard')),
            ('db_pages_for_moderation', _('Pages awaiting moderation shown on dashboard')),
            ('db_key_applications', _('Key applications shown on dashboard')),
        )

