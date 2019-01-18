from .filters import IsotopeFilter, GroupFilter, ProjectActiveFilter, SafetyRelationDateFilter
from .models.users import StaffUser, UserContainer, SafetyInstructionUserRelation, SafetyInstructionsSnippet
from .model_admin import SafetyModelAdmin
from .admin_views import Project2NuclideIndexView
#from .urls import urls

from django.conf.urls import url

from django.template.loader import render_to_string
from django.urls import include
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l


from rubionadmin.admin import NoCopyButtonHelper, HiddenModelAdmin

from userinput.models import Project2NuclideRelation, RUBIONUser

from wagtail.contrib.modeladmin.helpers import PageButtonHelper, ButtonHelper
from wagtail.contrib.modeladmin.options import (
    modeladmin_register, ModelAdmin, ModelAdminGroup
)

from wagtail.core import hooks
from website.mixins import ForcedModelAdminForPageModels


# register url to add a pre-filled SafetyRelation 

@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^snippets/', include('userdata.urls'))#urls, app_name='userdata', namespace='userdata') )
    ]

class NoButtonHelper ( ButtonHelper ):
    def get_buttons_for_obj(self, obj, **kwargs):
        return []

class UserContainerMA( HiddenModelAdmin ):
    model = UserContainer
    exclude_from_explorer = True

modeladmin_register( UserContainerMA )    

class StaffUserModelAdmin ( ModelAdmin ):
    model = StaffUser
    button_helper_class = NoCopyButtonHelper
    menu_label = _l('staff')
    menu_icon = ' icon-fa-user-circle'
    list_display = ('title_', 'job', 'phone', 'room', 'mail', 'tasks')
    menu_order = 300
    form_fields_exclude = ['orcid']
    search_fields = ('title','last_name','first_name')
    exclude_from_explorer = True

    def title_( self, obj ):
        return obj.title
    title_.short_description = _('Name, First name')

    def job ( self, obj ):
        return obj.get_parent().title
    job.short_description = _('staff group')
    
    def mail( self, obj):
        return obj.mail

    mail.short_description = _('e-mail')

    def tasks( self, obj ):
        # Yes! role.role.role! 
        # The implementation of m2m-relations is funny...
        return ",".join([role.role.role for role in obj.roles.all() ])
    tasks.short_description = _('tasks')

class RadionuclideProjectsModelAdmin( ModelAdmin ):
    model = Project2NuclideRelation
    menu_label = _l('Radionuclides')
    list_display = ('_snippet', 'room', 'group', 'project','max_order','amount_per_experiment')
    list_filter = (ProjectActiveFilter, IsotopeFilter, 'room', GroupFilter)
    button_helper_class = NoButtonHelper
    index_template_name = 'userdata/admin/index_project2nuclide.html'
    index_view_class = Project2NuclideIndexView

    def group (self, obj):
        return "{} ({})".format(obj.project_page.specific.get_workgroup(),obj.project_page.specific.get_workgroup().get_head())

#    def room (self, obj):
#        return obj.project_page.specific.room

    def _snippet(self, obj):
        return obj.snippet;
    _snippet.short_description = _('Isotope')

    def project(self, obj):
        return obj.project_page
    project.admin_order_field = 'project_page'
    project.short_description = _('Project')

class StaffUserModelProxy(StaffUser):
    class Meta:
        proxy = True
        verbose_name = _('Safety instruction for RUBION staff')
        verbose_name_plural = _('Safety instructions for RUBION staff')

class StaffSafetyInstructionModelAdmin( SafetyModelAdmin ):
    model = StaffUserModelProxy
    menu_label = _('Safety Instructions')
    list_display = ( 'name', 'safety_instructionp38', 'safety_instruction_general', 'safety_instrucions_il',  'safety_instrucions_acc', 'laser_safety', 'crane_license', 'forklift_license', 'hazardous_materials_instrucions')
    lookup_field = 'rubion_staff'
    index_template_name = 'modeladmin/userinput/rubionuserproxymodel/index.html'

    def name (self, obj):
        return render_to_string(
            'userinput/admin/name_in_si_list.html', 
            {
                'name' : '{}, {}'.format(obj.last_name, obj.first_name),
                'instructions' : SafetyInstructionsSnippet.objects.all(),
                'obj' : obj,
                'usertype' : 'rstaff'
            }
        )


    name.short_description = _('name')


class RUBIONModelAdminGroup( ModelAdminGroup ):
    menu_label = _('RUBION')
    menu_icon = 'home'
    
    items = ( StaffUserModelAdmin, RadionuclideProjectsModelAdmin, StaffSafetyInstructionModelAdmin)
    menu_order = 30

modeladmin_register(RUBIONModelAdminGroup)


