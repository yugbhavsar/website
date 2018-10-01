from .admin_forms import WorkgroupChooserForm, InactivateUserForm
from .helpers import get_staff_obj
from .models import RUBIONUser
from .pdfhandling import RUBIONBadge


import datetime

from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _



from wagtail.contrib.modeladmin.views import (
    ChooseParentView, InstanceSpecificView, InspectView
)

from userdata.models import SafetyInstructionUserRelation

class RUBIONUserBadgeView( InstanceSpecificView ):
    
    def get( self, request ):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachement; filename="badge-{}.pdf"'.format(self.instance.name)

        if self.instance.academic_title:
            title = self.instance.get_academic_title_display()
        else:
            title = None

        if self.instance.labcoat_size:
            labcoat_size = self.instance.get_labcoat_size_display()
        else:
            labcoat_size = None

        if self.instance.overshoe_size:
            overshoe_size = self.instance.get_overshoe_size_display()
        else:
            overshoe_size = None

        if self.instance.entrance:
            entrance = self.instance.get_entrance_display()
        else:
            entrance = None

        badge = RUBIONBadge(
            self.instance.first_name, 
            self.instance.last_name,
            self.instance.get_workgroup(),
            title,
            labcoat_size,
            overshoe_size,
            entrance
        )
        return badge.get_in_response(response)

class RUBIONUserInactivateView(InstanceSpecificView):

    def get_context_data( self, *args, **kwargs ):
        context = super(RUBIONUserInactivateView, self).get_context_data( *args, **kwargs)
        context['confirmation_warning'] = _(
            'Inactivate this user? An e-mail will be send to the user to inform him/her about the inactivation.'
        )
        
        if self.instance.is_leader:
            context['leader_warning'] = _(
                'This user is the leader of the group %s. Inactivating a group leader requires a decision about the future of the group.' % self.instance.get_workgroup().title_trans
            )
        return context
    
    def get( self, request ):
        form = InactivateUserForm(self.instance)
        context = self.get_context_data()
        context.update({
            'form' : form,
        })

        return render(
            request, 
            'modeladmin/userinput/rubionuser/confirm_user_inactivation.html',
            context
        )
        
    def post( self, request):
        form = InactivateUserForm(self.instance, request.POST)
        if form.is_valid():
            self.inactivate(form.decision, form.new_head, request)

            self.instance.expire_at = datetime.datetime.now()
            self.instance.save_revision_and_publish(user=request.user)
        
            opts = self.instance.__class__._meta
           
            messages.success(request, _('User %s was inactivated.' % self.instance.full_name))

            return redirect(
                reverse(
                    '%s_%s_modeladmin_%s' % (opts.app_label, opts.model_name, 'index')
                )
            )

        else:
            
            context = self.get_context_data()
            context.update({'form' : form })
            return render(
            request, 
            'modeladmin/userinput/rubionuser/confirm_user_inactivation.html',
            context
        )

    def inactivate( self, decision, new_head, request ):
        # todo
        if decision == 'inactivate_group':
            # inactivates the wg and all users
            wg = self.instance.get_workgroup().inactivate( user = request.user )
        else:
            new_leader = RUBIONUser.objects.get(id = new_head)
            new_leader.is_leader=True
            new_leader.save_revision_and_publish( user = request.user )
            self.instance.inactivate(user = request.user )


class AddRUBIONUserChooseWorkgroupView( ChooseParentView ):
    def get_context_data( self, *args, **kwargs ):
        context = super(AddRUBIONUserChooseWorkgroupView, self).get_context_data(*args, **kwargs)
        context['parent_name'] = _('Workgroup')
        context['introduction'] = _('Which Workgroup does the new RUBION user belong to?')
        return context

    def get_form(self, request):
        parents = self.permission_helper.get_valid_parent_pages(request.user)
        return WorkgroupChooserForm(parents, request.POST or None)
    
    
class RUBIONUserInspectView(InspectView):

    def get_page_title( self ):
        return self.instance.full_name(include_first = True)

    def get_page_subtitle( self ):
        if self.instance.is_leader:
            return "({}: {})".format(_('Group leader'), self.instance.get_workgroup())
        else:
            return "({})".format(self.instance.get_workgroup())


    def get_field_label(self, field_name, field=None):
        if field_name == 'last_safety_instruction':
            return _('last safety instruction')
        

        # in all other cases...    
        return super().get_field_label(field_name, field)

    def get_field_display_value(self, field_name, field=None):
        if field_name == 'last_safety_instruction':

            insts = []
            for inst_type in self.instance.needs_safety_instructions.all():
                inst = (SafetyInstructionUserRelation.objects.
                        filter(rubion_user = self.instance).
                        filter(instruction = inst_type)
                        .order_by('date').first()
                )
                if inst:
                    insts.append('<li>{}: {}</li>'.format(inst_type, inst.date))
                else:
                    insts.append('<li>{}: {}</li>'.format(inst_type, _('not instructed')))
            return mark_safe('<ul>{}</ul>'.format(', '.join(insts)))

        # in all other cases...    
        return super().get_field_display_value(field_name, field)

class WorkGroupInspectView(InspectView):
    def get_page_title( self ):
        return self.instance.title_trans

    def get_field_display_value(self, field_name, field=None):
        if field_name == 'leader':
            return self.instance.get_head()
        if field_name == 'members':
            return _('Members...')
        return super().get_field_display_value(field_name, field=None)


    def get_context_data(self, **kwargs):
        context = {
            'head': [self.instance.get_head()], # yes, should be a list!
            'members' : [
                member for member in self.instance.get_members() if not member.is_leader 
            ],
            'active_projects' : self.instance.get_projects().filter( expire_at__gte = datetime.datetime.now() ),
            'old_projects' : self.instance.get_projects().filter( expire_at__lt = datetime.datetime.now() )
        }
        context.update(kwargs)
        return super().get_context_data(**context)

