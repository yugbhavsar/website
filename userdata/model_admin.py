
from .models.users import SafetyInstructionUserRelation, SafetyInstructionsSnippet

from dateutil.relativedelta import relativedelta
import datetime


from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from django.utils.safestring import mark_safe

from wagtail.contrib.modeladmin.options import ModelAdmin

class SafetyModelAdmin( ModelAdmin ):
    menu_icon = 'fa-exclamation-triangle'#'fa-medkit'
    list_display = ( 'name', 'safety_instructionp38', 'safety_instruction_general', 'safety_instrucions_il',  'safety_instrucions_acc', 'laser_safety', 'crane_license', 'forklift_license', 'hazardous_materials_instrucions')
    index_view_extra_css = ['css/admin/additional-help-boxes.css']
    

    def safety_instruction_general( self, obj ):
        return self._get_si(obj, 'contains_general_safety_info')
    
    safety_instruction_general.short_description = _l('General safety instructions')
               
    def safety_instructionp38( self, obj ):
        return self._get_si(obj, 'contains_p38_safety_info')

    safety_instructionp38.short_description = _l('Radiation safety instructions (§38 StrlSchV)')

    def safety_instrucions_il(self, obj):
        return self._get_si( obj, 'contains_general_safety_info_radionuclides')
    safety_instrucions_il.short_description = _l('Safety instruction (Isotope lab)')

    def safety_instrucions_acc(self, obj):
        return self._get_si(obj, 'contains_general_safety_info_accelerators')
    safety_instrucions_acc.short_description = _l('Safety instruction (Accelerator labs)')

    def laser_safety(self, obj):
        return self._get_si(obj, 'contains_laser_safety')
    laser_safety.short_description = _l('Laser safety')
    
    def crane_license( self, obj):
        return self._get_si(obj, 'contains_crane_license')
    crane_license.short_description = _l('Crane license update')

    def forklift_license( self, obj):
        return self._get_si(obj, 'contains_forklift_license')
    forklift_license.short_description = _l('Forklift license update')

    def hazardous_materials_instrucions(self, obj):
        return self._get_si(obj, 'contains_hazardous_materials_instrucions')
    hazardous_materials_instrucions.short_description = _l('Hazardous materials instructions')
 
    def _get_si ( self, obj, instruction, rstaff = None ):

        required = False
        fargs = { instruction : True }

        if rstaff:
            userobj = rstaff
        else:
            userobj = obj

        if userobj.needs_safety_instructions.filter(**fargs).exists():
            required = True
        
        kwargs = { instruction : True }
        insts = SafetyInstructionsSnippet.objects.filter(**kwargs)
        kwargs2 = { self.lookup_field : obj }
        sir = (SafetyInstructionUserRelation.objects
               .filter(**kwargs2)
               .filter(instruction__in = insts)
               .order_by("-date")
        )
        try:
            date = sir.first().date
            
            cls = "help-block help-okay"
            
            

            if date < (datetime.date.today() + relativedelta(years=-1)) and required:
                cls = "help-block help-critical"
            elif date < (datetime.date.today() + relativedelta(months=-11))  and required:
                cls = "help-block help-warning"
        except AttributeError:
            cls = "help-block help-info"
            if required:
                cls = "help-block help-critical"

            date = _('Not instructed')
            
        if required:
            return mark_safe('<div style="margin:0; clear:None" class="{}"><strong>{}</strong></div>'.format(cls, date))
        else:
            return mark_safe('<div style="margin:0; clear:None" class="{}">{}</div>'.format('help-block help-neutral', date))
