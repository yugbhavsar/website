from django.core.mail import send_mail
from django.utils.translation import ugettext as _

CREATED = 0

STATUS = (
    (CREATED, _('created')),
)
def send_staff_mail( instance, what ):
    pass
