from .admin_panels import (
    WorkgroupsForModerationPanel, ProjectsForModerationPanel,
    InstrumentBookingsForModerationPanel, MethodsBookingsForModerationPanel
)

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import ugettext as _

from notifications.admin_panels import NotificationPanel 

from userinput.admin_panels import UserKeyApplicationPanel

from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import (
    modeladmin_register, ModelAdminGroup)
from wagtail.core import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem, Menu as AdminMenu

from website.models import Menu



homepage_menu = AdminMenu(register_hook_name ='register_homepage_menu_item')



@hooks.register('register_homepage_menu_item')
def register_webpages_menu_item():
  return MenuItem(_('Web pages'), reverse('wagtailadmin_explore_root'), classnames='icon icon-folder-inverse', order=100)
@hooks.register('register_homepage_menu_item')
def register_docs_menu_item():
  return MenuItem(_('Documents'), reverse('wagtaildocs:index'), classnames='icon icon-doc-full-inverse', order=101)
@hooks.register('register_homepage_menu_item')
def register_imgs_menu_item():
  return MenuItem(_('Images'), reverse('wagtailimages:index'), classnames='icon icon-image', order=102)


@hooks.register('register_admin_menu_item')
def homepage_menu_item():
  return SubmenuMenuItem( _('Homepage'), homepage_menu, classnames = "icon icon-fa-globe", order = 99)

@hooks.register('construct_main_menu')
def reconstruct_admin_menu( request, menu_items ):

    exclude = []

    if not request.user.has_perm('RubionAdminPermissionSnippet.snippet_menu'):
        exclude.append('snippet')
        exclude.append('schnipsel')
    if not request.user.has_perm('rubionadmin.full_explorer'):
        exclude.append('explorer')
    #if not request.user.has_perm('rubionadmin.images_menu'):
    exclude.append('images')
    exclude.append('bilder')
    #if not request.user.has_perm('rubionadmin.document_menu'):
    exclude.append('documents')
    exclude.append('dokumente')
    #if not request.user.has_perm('rubionadmin.staff_menu'):
    #exclude.append('staff')
    #exclude.append('Mitarbeiter')
    #if not request.user.has_perm('rubionadmin.instruments_menu'):
    #    exclude.append('instruments')
    #    exclude.append('geräte')
    #if not request.user.has_perm('rubionadmin.methods_menu'):
    #    exclude.append('methods')
    #    exclude.append('methoden')
    #if not request.user.has_perm('rubionadmin.courses_menu'):
    #    exclude.append('courses')
    #    exclude.append('kurse')

    menu_items[:] = [item for item in menu_items if item.name not in exclude ]
        
    


@hooks.register('construct_explorer_page_queryset')
def hide_menu_container( parent_page, pages, request ):
    """
    This functions hides the MenuContainers used to define the menu from 
    the list of contents in the Overview on the admin page. It does, however, 
    not change the Explorer menu items.
    """

    # goal is to omit every page that is of content_type MenuContainer 
    # from the list

    if not request.user.has_perm('website.MenuContainer_add'):

        # Get id of corresponding ContentType 
        # (model is in django.contrib.contenttypes.models)...
        id = ContentType.objects.get_for_model( Menu ).id
        # ... and exclude it
        pages = pages.exclude( content_type_id = id )
        
    return pages


@hooks.register('construct_homepage_panels', order=10000)
def construct_homepage_panels( request, panels ):

    # These panels should be hidden
    hide = [ 'SiteSummaryPanel' ]#, 'PagesForModerationPanel' ]
    if not request.user.has_perm('rubionadmin.db_pages_for_moderation'):
        hide.append('PagesForModerationPanel')
    # Remove the panels fron the `panels` list
    # For the default settings, only "Your last edits" will 
    # remain. For admins, there will be a notification if
    # wagtail updates are available.
    panels[:] = [panel for panel in panels if not panel.__class__.__name__ in hide]
    if request.user.has_perm('rubionadmin.db_workgroup_requests'):
        panels.append( WorkgroupsForModerationPanel( request ) )
    if request.user.has_perm('rubionadmin.db_project_requests'):
        panels.append( ProjectsForModerationPanel( request ) )
    if request.user.has_perm('rubionadmin.db_instrument_requests'):
        panels.append( InstrumentBookingsForModerationPanel( request ) )
    if request.user.has_perm('rubionadmin.db_method_requests'):
        panels.append( MethodsBookingsForModerationPanel( request ) )
    if request.user.has_perm('rubionadmin.db_key_applications'):
        panels.append( UserKeyApplicationPanel( request ) )
    panels.append( NotificationPanel ( request ) )
    

class ExportMenuItem(MenuItem):
  def is_shown(self, request):
    return request.user.has_perm('rubionadmin.export_menu')

@hooks.register('register_admin_menu_item')
def export_menu_entry():
  return ExportMenuItem(
    'Export to Excel',
    reverse('rubionadmin:full_xls_list'),
    classnames='icon icon-fa-table',
    order=10000
  )
    
