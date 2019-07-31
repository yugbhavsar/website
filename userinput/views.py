from .forms import (
    RUBIONUserModelForm, RUBIONUserSelfModelForm, 
    ExternalRUBIONUserSelfModelForm, 
    ExternalRUBIONUserSelfModelFormPWD
)
from .models import RUBIONUser
from .notifications import RUBIONUserAddedNotification, RUBIONUserChangedNotification

import datetime 

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext as _, get_language
from django.views.generic.edit import View

from userdata.models import StaffUser, SafetyInstructionsSnippet, SafetyInstructionUserRelation
from ugc.models import UserGeneratedContent2

from wagtail.contrib.modeladmin.helpers.permission import PermissionHelper
from wagtail.core.models import PageRevision, UserPagePermissionsProxy


@login_required
def current_user( request ):
    from .models import RUBIONUser
    try:
        rubion_user = RUBIONUser.objects.get(linked_user = request.user).specific
        project_perm = rubion_user.may('project')
        member_perm = rubion_user.may('member')
        try:
            wg = (
                PageRevision.objects.filter(page = rubion_user.get_workgroup()).
                order_by('-created_at').first()
            )

        except PageRevision.DoesNotExist:
            wg = None
        approval = False
        if wg:
            approval = wg.submitted_for_moderation
        
    except RUBIONUser.DoesNotExist:
        rubion_user = None
        project_perm = False
        member_perm = False
        approval = False
    try:
        staff_user = StaffUser.objects.get(user = request.user).specific
    except StaffUser.DoesNotExist:
        staff_user = None
    # if len( rubion_user ) == 0:
    #     rubion_user = None
    # else:
    #     rubion_user.


    return render(
        request,
        'userinput/home.html',
        {
            'user': request.user,
            'RUBIONUser': rubion_user,
            'StaffUser': staff_user,
            'allowed_to_add' : {
                'project': project_perm,
                'member': member_perm,
            },
            'awaits_approval' : approval
        }
    )


class RUBIONUserEditView( View ):
    def __init__( self, *args, **kwargs ):
        self.form = None
        super(RUBIONUserEditView, self).__init__(*args, **kwargs)


    def get_form( self, request, instance ):


        if instance.linked_user == request.user:
            if instance.is_rub:

                form = RUBIONUserSelfModelForm

            else:
                if request.user.has_usable_password():
                    form = ExternalRUBIONUserSelfModelForm
                else:
                    form = ExternalRUBIONUserSelfModelFormPWD
        else:
            form = RUBIONUserModelForm

        return form

    def get( self, request, *args, **kwargs):
        instance = kwargs['instance']

        allowed = instance.user_passes_test( request.user, instance.EDIT )

        if not allowed:
            raise PermissionDenied

        return TemplateResponse(
            request,
            'ugc/ugc_create_page.html',
            {
                'pagetitle' : '{}, {}'.format(instance.name, instance.first_name),
                'page': instance,
                'form' : self.get_form(request, instance)(instance = instance)
            }
        )
        
    def post(self, request, *args, **kwargs):
        instance = kwargs['instance']
        form = self.get_form( request, instance )(request.POST, instance = instance)
        user_has_changed = False
        user_has_changed_pwd = False
        if form.is_valid():
            try:
                request.user.set_password(form.pwd)
                user_has_changed_pwd = True
            except AttributeError:
                pass
            # @TODO: It is really strange how this form data is saved.
            # I don't remember the reason why I didn't simply use form.save()
                
            newinstance = form.save( commit = False )
            for f in ['sex', 'academic_title', 'preferred_language', 'phone', 'labcoat_size', 'entrance', 'overshoe_size' ]:
                setattr(instance, f, getattr( newinstance, f) )
            try:
                instance.has_agreed =  form.cleaned_data['terms_conditions']
            except KeyError:
                pass

            if not instance.is_rub:
                if request.user.last_name != newinstance.name_db:
                    request.user.last_name = newinstance.name_db;
                    instance.name_db = newinstance.name_db
                    user_has_changed = True
                if request.user.first_name != newinstance.first_name_db:
                    request.user.first_name = newinstance.first_name_db;
                    instance.first_name_db = newinstance.first_name_db
                    user_has_changed = True
                if user_has_changed or user_has_changed_pwd:
                    old_user = request.user
                    rev = request.user.save()
                if user_has_changed_pwd:
                    update_session_auth_hash(request, old_user)

            revision = instance.save_revision_and_publish( user = request.user )
            messages.success( request, _('Your information has been updated.') )
            create_noti = RUBIONUserAddedNotification(instance).notify()
            if not create_noti:
                RUBIONUserChangedNotification(instance).notify()

            return HttpResponseRedirect( reverse('userhome') )
        else:
            messages.error( request, _('An error occured.') )
            return TemplateResponse(
                request,
                'ugc/ugc_create_page.html',
                {
                    'page': instance,
                    'form' : form
                }
            )

# Ajax-views for admin

def safety_instruction_helper( request, user_id, instruction_id ):
    from .models import RUBIONUser
    r_user = get_object_or_404(RUBIONUser, pk = user_id)

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(r_user).can_edit() or not request.is_ajax():
        raise PermissionDenied

    si = get_object_or_404(SafetyInstructionsSnippet, pk = instruction_id)
    instructions = r_user.needs_safety_instructions.all()
    response = {
        'del_link' : reverse('rubionadmin:user_safety_instruction_del', args=[user_id, instruction_id]),
        'add_link' : reverse('rubionadmin:user_safety_instruction_add', args=[user_id, instruction_id])
    }
    return [r_user, si, instructions, response]


def user_safety_instruction_add( request, user_id, instruction_id ):
    r_user, si, instructions, response = safety_instruction_helper( request, user_id, instruction_id )
    if si not in instructions:
        r_user.needs_safety_instructions.add(si)
        r_user.save()
    response['needs_it'] = si in r_user.needs_safety_instructions.all()
    return JsonResponse(response)

def user_safety_instruction_del( request, user_id, instruction_id ):
    r_user, si, instructions, response = safety_instruction_helper( request, user_id, instruction_id )
    if si in instructions:
        r_user.needs_safety_instructions.remove(si)
        r_user.save()
    response['needs_it'] = si in r_user.needs_safety_instructions.all()
    return JsonResponse(response)

    
def set_safety_instruction_date( request, r_user_id, instruction_id, usertype = 'ruser' ):
    from .models import RUBIONUser
    from userdata.models import StaffUser

    ph = PermissionHelper(SafetyInstructionUserRelation)
    if ph.user_can_create(request.user) and request.is_ajax():
        si_snippet = get_object_or_404(SafetyInstructionsSnippet, pk = instruction_id)


        # Test if a RUBION Staff member is connected to the RUBION User and, if yes, get it

        si = SafetyInstructionUserRelation()
            
        si.instruction = si_snippet
        if usertype == 'ruser':
            r_user = get_object_or_404(RUBIONUser, pk = r_user_id)
            si.rubion_user = r_user
        elif usertype == 'rstaff':
            r_staff = get_object_or_404(StaffUser, pk = r_user_id)
            si.rubion_staff = r_staff
        si.date = datetime.date.today()
        si.save()
        return JsonResponse({'r_user_id':r_user_id, 'instruction_id':instruction_id, 'lang' : get_language()})
        
    raise PermissionDenied        
