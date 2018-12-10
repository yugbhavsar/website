
from .helpers import get_staff_obj
from .models import Project

from dateutil.relativedelta import relativedelta
import datetime


from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from userdata.filters import ListFilterWithoutAll
from userdata.models import SafetyInstructionUserRelation, SafetyInstructionsSnippet

from wagtail.contrib.modeladmin.helpers.url import AdminURLHelper

class RUserDataSubmissionToCROFilter( admin.SimpleListFilter ):
    ALL = 'all'
    OPEN = 'open'
    title = _('Submissions')
    
    parameter_name = 'submissions'
    
    def lookups( self, request, model_admin ):
        return (
            (self.OPEN, _('open')),
        )

    def queryset( self, request, queryset):
        if self.value():
            if self.value() == self.OPEN:
                return queryset.filter(central_radiation_safety_data_submissions__isnull = True)
        return queryset


class ProjectExpiredFilter( ListFilterWithoutAll ):
    ALL = 'all'
    ACTIVE = 'active'
    EXPIRED = 'expired'
    title = _('Status')

    parameter_name = 'status'

    def lookups( self, request, model_admin ):

        return (
            (self.ACTIVE ,_('active')),
            (self.EXPIRED ,_('expired')),
            (self.ALL, _('all')),
        )
    
    def queryset(self, request, queryset):
        if self.value() is None:
            self.used_parameters[self.parameter_name] = self.ACTIVE
        else:
            self.used_parameters[self.parameter_name] = self.value()

        
        if self.value() == self.ALL:
            return queryset.all()
        if self.value() == self.ACTIVE:
            return queryset.filter( expire_at__gte = datetime.datetime.now() )
        if self.value() == self.EXPIRED:
            return queryset.filter( expire_at__lt = datetime.datetime.now() )
        return queryset.filter( expire_at__gte = datetime.datetime.now() )


class RUserExpiredFilter(ProjectExpiredFilter):
    def lookups( self, request, model_admin ):

        return (
            (self.ACTIVE ,_('active')),
            (self.EXPIRED ,_('inactive')),
            (self.ALL, _('all')),
        )
    def queryset(self, request, queryset):
        if self.value() is None:
            self.used_parameters[self.parameter_name] = self.ACTIVE
        else:
            self.used_parameters[self.parameter_name] = self.value()

        
        if self.value() == self.ALL:
            return queryset.all()
        if self.value() == self.ACTIVE:
            return queryset.filter( expire_at__isnull = True)
        if self.value() == self.EXPIRED:
            return queryset.filter( expire_at__lt = datetime.datetime.now() )
        return queryset.filter( expire_at__isnull = True )
    

class RUsersExpiredSafetyInstructions( ListFilterWithoutAll ):
    parameter_name = 'status'
    title = _('Expiry date')
    ALL = 'all'
    EXPIRED = 'expired'
    NEARLY_EXPIRED = 'nearly'

    default = NEARLY_EXPIRED

    def lookups( self, request, model_admin ):
        return (
            (self.NEARLY_EXPIRED, _('expires soon') ),
            (self.EXPIRED, _('expired') ),
            (self.ALL, _('all') ),
        )

    def queryset(self, request, queryset):
     
        if self.value() is None:
            self.used_parameters[self.parameter_name] = self.NEARLY_EXPIRED
        else:
            self.used_parameters[self.parameter_name] = self.value()

        today = datetime.datetime.now()

        # These fields are used in the instruction definition to determine what a certain instruction provides
        safety_infos = [
            'contains_general_safety_info',
            'contains_general_safety_info_radionuclides',
            'contains_general_safety_info_accelerators',
            'contains_p38_safety_info',
            'contains_laser_safety'
            'contains_crane_license',
            'contains_forklift_license',
            'contains_hazardous_materials_instrucions'            
        ]                

        # Show all, if requested
        if self.value() == self.ALL:
            return queryset


        # One of the following two will match
        if self.value() is None or self.value() == self.NEARLY_EXPIRED:
            expiry_date = today + relativedelta(months=-11, hour = 0, minute = 0, second = 0, microsecond = 0 )
        if self.value() == self.EXPIRED:
            expiry_date = today + relativedelta(years=-1, hour = 0, minute = 0, second = 0, microsecond = 0 )

        include_ids = []

        for ruser in queryset:
            needs = set()
            
            #if user is RUBION staff, use that settings

            obj = get_staff_obj( ruser )
            if not obj:
                obj = ruser

            # Populate `needs` with the instruction-content (see `safety_infos`) required for the user
            for SI in obj.needs_safety_instructions.all():
                for info in safety_infos:
                    if getattr(SI, info) == True:
                        needs.add(info)


            # get the last valid SafetyInstruction for this user
            valid_sis = SafetyInstructionUserRelation.objects.filter(
                rubion_user=ruser,
                date__gte = expiry_date
            )
            
            # now remove every instruction-content that is still valid
            for SI in valid_sis:
                for info in safety_infos:
                    if getattr(SI.instruction, info) == True:
                        try:
                            needs.remove(info)
                        except KeyError:
                            pass

            # if `needs` is not empty, an instruction is missing, include user
            if needs:
                include_ids.append(ruser.id)
                
        return queryset.filter(id__in = include_ids)




class RUserSafetyInstructionFilter( admin.SimpleListFilter ):
    parameter_name = 'instruction'
    title = _('required instruction')
    related_filter_param = RUsersExpiredSafetyInstructions.parameter_name
    
    GENERAL = 'general'
    P38 = 'p38'
    GENERAL_ISO = 'general_iso'
    GENERAL_ACC = 'general_acc'
    LASER = 'laser'
    CRANE = 'crane'
    FORKLIFT = 'forklift'
    HAZARDOUS = 'hazardous'    

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        rel = request.GET.get(self.related_filter_param, None)
        if not rel:
            self._related_value = RUsersExpiredSafetyInstructions.default
        else:
            self._related_value = rel
        

    def related_value( self ):
        return self._related_value

    def lookups( self, request, model_admin ):
        return (
            ( self.P38, _( 'Radiation safety instructions (§38)' )),
            ( self.GENERAL, _( 'General safety instructions' )),
            ( self.GENERAL_ISO, _( 'General safety instruction (isotope lab)' )),
            ( self.GENERAL_ACC, _( 'General safety instructions (accelerator labs)' )),
            ( self.LASER, _( 'Laser safety instructions' )),
            ( self.CRANE, _( 'Crane license update' )),
            ( self.FORKLIFT, _( 'Forklift license update' )),
            ( self.HAZARDOUS, _( 'Hazardous materials instructions' )),            
        )

    def queryset(self, request, queryset):

        if self.value() is None:
            return queryset

        filter_values = {
            self.P38: 'contains_p38_safety_info',
            self.GENERAL : 'contains_general_safety_info',
            self.GENERAL_ISO: 'contains_general_safety_info_radionuclides',
            self.GENERAL_ACC: 'contains_general_safety_info_accelerators',
            self.LASER : 'contains_laser_safety'
            self.CRANE : 'contains_crane_license',
            self.FORKLIFT : 'contains_forklift_license',
            self.HAZARDOUS : 'contains_hazardous_materials_instrucions'            
        }

        if self.related_value() == RUsersExpiredSafetyInstructions.ALL:
            fargs = { filter_values[self.value()] : True }
            SIs = SafetyInstructionsSnippet.objects.filter( **fargs )
            return queryset.filter(needs_safety_instructions__in = SIs)
        else:
            today = datetime.datetime.now()

            if self.related_value() == RUsersExpiredSafetyInstructions.NEARLY_EXPIRED:
                expiry_date = today + relativedelta(months=-11, hour = 0, minute = 0, second = 0, microsecond = 0 )
            elif self.related_value() == RUsersExpiredSafetyInstructions.EXPIRED:
                expiry_date = today + relativedelta( years=-1 )

            include_ids = []
            fargs = {"instruction__{}".format(filter_values[self.value()]) : True}
            iargs = {"{}".format(filter_values[self.value()]) : True}
            for ruser in queryset.all():
                
                usr = get_staff_obj( ruser )
                if not usr:
                    usr = ruser
                
                is_required = usr.needs_safety_instructions.filter(**iargs).exists()
                qs = SafetyInstructionUserRelation.objects.filter(rubion_user=ruser).filter(**fargs)
                if qs.filter(date__gte = expiry_date).exists():
                    is_required = False
                if is_required:
                    include_ids.append(ruser.id)
                    
            return queryset.filter(id__in = include_ids)
            
            
        return queryset

