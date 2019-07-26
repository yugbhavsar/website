from .admin_views import (
    RUBIONUserBadgeView, AddRUBIONUserChooseWorkgroupView, 
    RUBIONUserInspectView, WorkGroupInspectView,
    RUBIONUserInactivateView, ProjectInspectView
)
from .helpers import (
    RUBIONUserButtonHelper, get_staff_obj, get_key_if_staff, 
    RUBIONUserSafetyRelationButtonHelper, RUserDataSubmissionButtonHelper,
    RUserDataSubmissionPermissionHelper
)
from .models import (
    RUBIONUser, WorkGroup, Project,
    WorkGroupContainer, ProjectContainer,
    ListOfProjectsPage
)
from .filters import (
    ProjectExpiredFilter, RUsersExpiredSafetyInstructions, 
    RUserSafetyInstructionFilter, RUserDataSubmissionToCROFilter,
    RUserExpiredFilter
)

import datetime
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

from django.conf.urls import url
from django.contrib.admin.utils import quote
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.utils.text import format_lazy
from django.urls import reverse
from django.template.loader import render_to_string

from notifications.models import (
    PageNotificationCounter, 
)
from notifications.mail import send_staff_mail, CREATED

from rubionadmin.admin import NoCopyButtonHelper, HiddenModelAdmin

from userdata.models import SafetyInstructionUserRelation, SafetyInstructionsSnippet
from userdata.model_admin import SafetyModelAdmin

from wagtail.contrib.modeladmin.helpers.button import ButtonHelper
from wagtail.contrib.modeladmin.helpers.url import PageAdminURLHelper
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register, ModelAdminGroup)
from wagtail.core import hooks
from wagtail.core.models import PageRevision, PageQuerySet, PageManager
from wagtail.core.signals import page_published

from website.mixins import ForcedModelAdminForPageModels


class RUBIONUserModelAdmin ( ModelAdmin ):
    model = RUBIONUser
    button_helper_class = RUBIONUserButtonHelper
    menu_label = _l( 'User' )
    menu_icon = 'user'
    list_display = ('wa_name', 'first_name', 'get_workgroup', 'phone', '_key_number', 'safety_information', 'safety_instructions', 'comment')
    list_filter = (RUserExpiredFilter, )
    menu_order = 200
    exclude_from_explorer = True
    search_fields = ['title','name_db','first_name_db', 'key_number']
    index_view_extra_css = ['css/admin/ruser_index_view.css']
    index_view_extra_js = ['js/admin/ruser_index_view.js','js/admin/fix_admin_headers.js']
    choose_parent_view_class = AddRUBIONUserChooseWorkgroupView
    choose_parent_template_name = 'userinput/admin/choose_workgroup.html'
    inspect_view_enabled=True
    inspect_template_name = 'userinput/admin/inspect_rubionuser.html'
    inspect_view_class = RUBIONUserInspectView

    inspect_view_fields = [
        'email', 'phone', 'key_number', 'needs_dosemeter',
        'needs_safety_instructions', 'last_safety_instruction',
        'date_of_birth', 'place_of_birth','overshoe_size','labcoat_size'
    ]
    def wa_name(self, obj):
        return obj.name
    wa_name.admin_order_field = 'linked_user__last_name'
    wa_name.short_description = 'Name'
    
    def safety_information( self, obj ):
        items = []
        if obj.needs_labcoat:
            if obj.labcoat_size:
                items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('labcoat size'), obj.get_labcoat_size_display()))
            else:
                items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('labcoat size'), _l('not provided')))
        else:
            items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('labcoat'), _l('not required')))
                             
        if obj.needs_overshoes:
            if obj.overshoe_size:
                items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('overshoe size'), obj.get_overshoe_size_display()))
            else:
                items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('overshoe size'), _l('not provided')))
        else:
            items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('overshoes'), _l('not required')))
                             
        if obj.needs_entrance:
            if obj.entrance:
                items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('entrance'), obj.get_entrance_display()))
            else:
                items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('entrance'), _l('not provided')))
        else:
            items.append(format_html('<li><strong>{}:</strong> {}</li>', _l('special entrance'), _l('not required')))

        safety_info = mark_safe(''.join(items))

        return mark_safe(format_html('<ul>{}</ul>',safety_info))

    safety_information.short_description = _l('safety information')

    def comment( self, obj ):
        return mark_safe(obj.internal_rubion_comment)
    comment.short_description = _l('Comment')

    def safety_instructions( self, obj ):

        usr = get_staff_obj( obj ) 
        if not usr:
            usr = obj

        if not usr.needs_safety_instructions:
            
            return _l('Not required')
        sis = []
        qs = SafetyInstructionUserRelation.objects.filter(rubion_user = obj) 
        for si in usr.needs_safety_instructions.all():
            relation = qs.filter(instruction = si).order_by("-date").first()
            today = datetime.date.today()
            try:
                diff = (today.year - relation.date.year) * 12 + today.month - relation.date.month
                if diff == 0:
                    display_text = _l('this month')
                    cls = 'yes'
                elif diff == 1:
                    display_text = _l('last month')
                    cls = 'yes'
                else:
                    display_text = _l('{} months ago'.format(diff))
                    cls = 'yes'
                    if diff > 10:
                        cls = ''
                    if diff > 12:
                        cls = 'no'
                
                dat = mark_safe(
                    format_html(
                        '<a class="button button-small {} ajax-button" href="{}"><span class="">{}:</span> <span class="time">{}</span></a>', 
                        cls, reverse('rubionadmin:set_safety_instruction_date',args=[obj.id, relation.instruction.id]), si.title_short, display_text
                    )
                )
                
            except AttributeError:
                dat = mark_safe(
                    format_html(
                        '<a class="button button-small no ajax-button" href="{}"><span class="">{}:</span> <span class="time">{}</span></a>',
                        reverse('rubionadmin:set_safety_instruction_date',args=[obj.id, si.id]), si.title_short, _l('not instructed')
                    )
                )
            
            sis.append(format_html("<li>{}</li>", dat))
        return mark_safe(format_html("<ul class=\"si-list\">{}</ul>",mark_safe("".join(sis))))
    safety_instructions.short_description = _l('Safety instructions')

    def _key_number(self, obj):
        kn = get_key_if_staff( obj )
        if not kn:
            if obj.needs_key:
                kn = obj.key_number
            else:
                kn = _l('not required')

        return kn
    _key_number.short_description = _l('Key number')

    def badge_view(self, request, instance_pk):
        kwargs = { 'model_admin' : self, 'instance_pk' : instance_pk }
        return RUBIONUserBadgeView.as_view(**kwargs)(request)

    def inactivate_view(self, request, instance_pk):
        kwargs = { 'model_admin' : self, 'instance_pk' : instance_pk }
        return RUBIONUserInactivateView.as_view(**kwargs)(request)

    def get_admin_urls_for_registration( self ):
        urls = super(RUBIONUserModelAdmin, self).get_admin_urls_for_registration()
        urls = urls + (
            url(self.url_helper.get_action_url_pattern('badge'), 
                self.badge_view, 
                name=self.url_helper.get_action_url_name('badge')),
            url(self.url_helper.get_action_url_pattern('inactivate'), 
                self.inactivate_view, 
                name=self.url_helper.get_action_url_name('inactivate')),
        )
        return urls


class WorkgroupContainerMA( HiddenModelAdmin ):
    model = WorkGroupContainer
    exclude_from_explorer = True

modeladmin_register( WorkgroupContainerMA )

class ProjectContainerMA( HiddenModelAdmin ):
    model = ProjectContainer
    exclude_from_explorer = True

modeladmin_register( ProjectContainerMA )

class ListOfProjectsPageMA( HiddenModelAdmin ):
    model = ListOfProjectsPage
    exclude_from_explorer = True

modeladmin_register( ListOfProjectsPageMA )

class WorkgroupsModelAdmin ( ModelAdmin ):
    model = WorkGroup
    menu_label = _l('workgroups')
    menu_icon = 'group'
    list_display = ('_title','get_head', 'university','institute', 'department', 'methods')
    index_view_extra_js = ['js/admin/fix_admin_headers.js']
    menu_order = 300
    exclude_from_explorer = True
    button_helper_class = NoCopyButtonHelper
    inspect_view_enabled=True
    inspect_template_name = 'userinput/admin/inspect_workgroup.html'
    inspect_view_class = WorkGroupInspectView

    search_fields = [
        'title','title_de',
        'institute_en','institute_de',
        'department_en','department_de',
        'university_en','university_de',
    ]
    list_filter = (RUserExpiredFilter, ) 
    def _title( self, obj ):
        return obj.title_trans
    _title.short_description = _l('title')

    def institute( self, obj ):
        return obj.institute
    institute.short_description = _l('institute')
    def university( self, obj ):
        return obj.university
    university.short_description = _l('university')
    def department( self, obj ):
        return obj.department
    department.short_description = _l('department')
    def methods( self, obj ):
        return obj.get_methods()
    methods.short_description = _l('methods')



class ProjectURLHelper( PageAdminURLHelper ):
    def get_action_url(self, action, *args, **kwargs):
        if action in ('add', 'edit', 'delete', 'unpublish', 'copy'):
            url_name = 'wagtailadmin_pages:%s' % action
            target_url = reverse(url_name, args=args, kwargs=kwargs)
            return '%s?next=%s' % (target_url, quote(self.index_url))

        if action in ('prolong'):
            pass
        return super(PageAdminURLHelper, self).get_action_url(action, *args,
                                                              **kwargs)
class ProjectButtonHelper( NoCopyButtonHelper ):

    prolong_button_classnames = []
    
    def prolong_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.prolong_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('prolong', quote(pk)),
            'label': _l('Prolong'),
            'classname': cn,
            'title': _l('Prolong this %s') % self.verbose_name,
        }

    def get_buttons_for_obj(
            self, obj, exclude=None, classnames_add=None,
            classnames_exclude=None
    ):
        if exclude is None:
            exclude = []
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        ph = self.permission_helper
        usr = self.request.user
        pk = getattr(obj, self.opts.pk.attname)
        btns = []
        if('inspect' not in exclude and ph.user_can_inspect_obj(usr, obj)):
            btns.append(
                self.inspect_button(pk, classnames_add, classnames_exclude)
            )
        if('edit' not in exclude and ph.user_can_edit_obj(usr, obj)):
            btns.append(
                self.edit_button(pk, classnames_add, classnames_exclude)
            )
        if('delete' not in exclude and ph.user_can_delete_obj(usr, obj)):
            btns.append(
                self.delete_button(pk, classnames_add, classnames_exclude)
            )
#        if('prolong' not in exclude):
#            btns.append(
#                self.prolong_button(pk,classnames_add, classnames_exclude)
#            )
        return btns

class ProjectModelAdmin ( ModelAdmin ):
    model = Project
    menu_label = _l('Projects')
    menu_icon = ' icon-fa-calendar'
    list_display = ('title','active_since', 'expires_at', 'workgroup','public')
    index_view_extra_js = ['js/admin/fix_admin_headers.js']
    menu_order = 400
    exclude_from_explorer = False
    list_filter = (ProjectExpiredFilter,)
    button_helper_class = ProjectButtonHelper
    inspect_view_enabled = True
    inspect_view_class = ProjectInspectView
    inspect_template_name = 'userinput/admin/inspect_project.html'
    
    def active_since( self, obj ):
        return obj.go_live_at
    active_since.short_description = _l('active since')
    def expires_at( self, obj ):
        return obj.expire_at
    expires_at.short_description = _l('Will expire at')

    def workgroup( self, obj ):
        try:
            return "{}: {}".format(
                obj.get_workgroup().get_head().full_name(), 
                obj.get_workgroup_info())
        except:
            return "{}".format(
#                obj.get_workgroup().get_head().full_name(), 
                obj.get_workgroup_info())
    workgroup.short_description= _l('Workgroup')

    def public( self, obj ):
        if obj.is_confidential:
            return _l("No")
        else:
            return _l("Yes")
    public.short_description = _l('public')


class RUserProxyModelManager(PageManager):
    def get_queryset(self):
        qs = super().get_queryset()
        ids = []
        for usr in qs:
            # Staff superseeds RUBIONUser
            staff = get_staff_obj(usr)
            if (staff and staff.needs_safety_instructions) or usr.needs_safety_instructions:
                ids.append(usr.id)
        return qs.filter(id__in = ids)


        
class RUBIONUserProxyModel(RUBIONUser):
    class Meta:
        proxy = True
        verbose_name = _l('Safety instruction for RUBION users')
        verbose_name_plural = _l('Safety instructions for RUBION users')

    objects = RUserProxyModelManager()
    

class RUserSafetyInstructionsModelAdmin( SafetyModelAdmin ):
    model = RUBIONUserProxyModel
    menu_label = _l('Safety instructions')
    lookup_field = 'rubion_user'
    list_filter = (RUsersExpiredSafetyInstructions, RUserSafetyInstructionFilter)
    button_helper_class = RUBIONUserSafetyRelationButtonHelper
    search_fields = ('name_db', 'first_name_db', 'linked_user__first_name', 'linked_user__last_name')
    index_view_extra_js = ['js/admin/fix_admin_headers.js']    


    def name (self, obj):
        return render_to_string(
            'userinput/admin/name_in_si_list.html', 
            {
                'name' : '{}, {}'.format(obj.name, obj.first_name),
                'instructions' : SafetyInstructionsSnippet.objects.all(),
                'dates' : {
                    'today' : datetime.date.today(),
                    'yesterday': datetime.date.today() - relativedelta(days=-1)
                },
                'obj' : obj,
                'usertype' : 'ruser'
            }
        )

    def _get_si( self, obj, instruction ):
        return super()._get_si(obj, instruction, rstaff = get_staff_obj( obj ))


class RUBIONUserModelManagerForCRO(PageManager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(dosemeter=RUBIONUser.OFFICIAL_DOSEMETER)


class RUBIONUserProxyForCRO( RUBIONUser ):
    class Meta:
        proxy = True
        verbose_name = _l('Data submission to CRO')
        verbose_name_plural = _l('Data submissions to CRO')
    objects = RUBIONUserModelManagerForCRO()

class RUBIONUserProxyForCROMA( ModelAdmin ):
    menu_label = _l('Central radiation safety office')
    model = RUBIONUserProxyForCRO
    list_display = ('_title', 'last_submission', 'last_revision', 'last_revision_by_user', 'data_complete' )
    search_fields = ('name_db', 'first_name_db', 'linked_user__first_name', 'linked_user__last_name')
    list_filter = (RUserDataSubmissionToCROFilter,)
    button_helper_class = RUserDataSubmissionButtonHelper
    permission_helper_class = RUserDataSubmissionPermissionHelper
    def _title( self, obj ):
        return obj.title
    _title.short_description = _('name, first name')
    _title.admin_order_field = 'title'

    def last_submission( self, obj ):
        if obj.data_has_been_submitted:
            sub = obj.central_radiation_safety_data_submissions.order_by('-date').first()
            via = _('email')
            if sub.email is None:
                via = ('manual')
            return "{} ({})".format(sub.date.strftime('%d %B %Y, %H:%M'), via)  
        else:
            return None
    last_submission.short_description = _l('last submission')

    def last_revision( self, obj ):
        revisions = PageRevision.objects.filter(page = obj).order_by('-created_at').first()
        return format_lazy(
            "{} {} {} {}", 
            revisions.created_at.strftime('%d %B %Y, %H:%M'), _('by'), 
            revisions.user.first_name, revisions.user.last_name
        )
    last_revision.short_description = _l('last revision')
    def last_revision_by_user( self, obj ):
        if PageRevision.objects.filter(page = obj, user = obj.linked_user).exists():
            revisions = PageRevision.objects.filter(page = obj, user = obj.linked_user).order_by('-created_at').first()
            return revisions.created_at
        else:
            return None
    last_revision_by_user.short_description = _l('last revision by user')

    def data_complete( self, obj ):
        if obj.date_of_birth and obj.place_of_birth:
            return _('Yes')
        else:
            return _('No')

class UserInputModelAdminGroup( ModelAdminGroup ):
    menu_label = _l('User data')
    menu_icon = 'user'
    menu_order = 10
    items = (ProjectModelAdmin, RUBIONUserModelAdmin, WorkgroupsModelAdmin, RUserSafetyInstructionsModelAdmin, RUBIONUserProxyForCROMA)
    
modeladmin_register( UserInputModelAdminGroup )


