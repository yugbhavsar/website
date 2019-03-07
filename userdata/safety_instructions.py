from django.utils.translation import ugettext_lazy as _l
from userinput.models import RUBIONUser
from .models import StaffUser, SafetyInstructionUserRelation


GENERAL = 'general_safety_info'
GENERAL_ISOTOPE_LAB = 'general_safety_info_radionuclides'
GENERAL_ACCELERATOR_LAB = 'general_safety_info_accelerators'
P38_INSTRUCTIONS = 'p38_safety_info'
LASER_INSTRUCTIONS = 'laser_safety'
CRANE_LICENSE = 'crane_license'
FORKLIFT_LICENSE = 'forklift_license'
HAZARDOUS_MATERIAL = 'hazardous_materials_instrucions'

# to be able to loop through the SIs
AVALABLE_SAFETY_INSTRUCTIONS = [
    GENERAL, GENERAL_ISOTOPE_LAB, GENERAL_ACCELERATOR_LAB,
    P38_INSTRUCTIONS, LASER_INSTRUCTIONS, CRANE_LICENSE, FORKLIFT_LICENSE,
    HAZARDOUS_MATERIAL
]

SAFETYINSTRUCTION_ICONS = {
    GENERAL : 'fas fa-notes-medical',
    GENERAL_ISOTOPE_LAB: 'fas fa-flask',
    GENERAL_ACCELERATOR_LAB: 'flaticon-electrocution-risk-sign',
    P38_INSTRUCTIONS: 'fas fa-radiation',
    LASER_INSTRUCTIONS :'science-016-laser',
    CRANE_LICENSE: 'flaticon-hook-hanging-material',
    FORKLIFT_LICENSE: 'flaticon-forklift',
    HAZARDOUS_MATERIAL: 'fas fa-skull-crossbones'
}

SAFETYINSTRUCTION_NAMES = {
    GENERAL : _l('general safety instruction'),
    GENERAL_ISOTOPE_LAB: _l('general safety in the isotope lab'),
    GENERAL_ACCELERATOR_LAB: _l('general safety in the accellerator lab'),
    P38_INSTRUCTIONS: _l('radiation safety (§38 StrSchV)'),
    LASER_INSTRUCTIONS : _l('laser safety'),
    CRANE_LICENSE: _l('crane license'),
    FORKLIFT_LICENSE: _l('forklift license'),
    HAZARDOUS_MATERIAL: _l('safety instruction for handling hazardous material')
}

def get_required_instructions (obj):
    ins = {}
    for asi in AVALABLE_SAFETY_INSTRUCTIONS:
        ins[asi] = False

    for req in obj.needs_safety_instructions.all():
        for asi in AVALABLE_SAFETY_INSTRUCTIONS:
            instruction = getattr(req, 'contains_{}'.format(asi))
            if instruction:
                ins[asi] = True

    return ins

def get_instruction_information( obj ):
    instructions = get_required_instructions( obj )
    if issubclass(obj.__class__, RUBIONUser):
        qs = SafetyInstructionUserRelation.objects.filter(rubion_user = obj)
    elif issubclass(obj.__class__, StaffUser):
        qs = SafetyInstructionUserRelation.objects.filter(rubion_staff = obj)

    information = {}
    for instruction, required in instructions.items():
        information[instruction] = { 'required' : required }
        kwargs = { 'instruction__contains_{}'.format(instruction) : True }

        relation = qs.filter(**kwargs).order_by("-date").first()
        if relation:
            information[instruction].update({'last' : relation.date})
        else:
            information[instruction].update({'last' : None})

    return information
            
