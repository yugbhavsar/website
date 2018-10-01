RUBION_NOTIFICATIONS = []    
    
def register_notification( notification ):
    if notification not in RUBION_NOTIFICATIONS:
        RUBION_NOTIFICATIONS.append ( notification )

def get_notification_choices():
    choices = [ (n.identifier, n.description) for n in RUBION_NOTIFICATIONS ]
    return tuple(choices)
