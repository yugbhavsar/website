ATTENDEE_TYPES = []

def register_attendee( pt ):
    if pt not in ATTENDEE_TYPES:
        ATTENDEE_TYPES.append(pt)

def get_attendee_choices():
    choices = [(ATT.identifier, ATT._meta.verbose_name) for ATT in ATTENDEE_TYPES]
    return tuple(choices)

def get_attendee_class( identifier ):
    for ATT in ATTENDEE_TYPES:
        if ATT.identifier == identifier:
            return ATT

    return None
