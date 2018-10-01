from django.core.mail import send_mail as django_mail
from django.conf import settings

import textwrap

def wrap ( body ):
    line_length = 70
    wrapped_body = ''

    for line in body.split('\n'):
        if len(line) <= line_length :
            wrapped_body += line + '\n'
        else:
            wrapped_body += textwrap.fill(
                line, 
                break_long_words = False, 
                break_on_hyphens = False,
                width = line_length
            )+'\n'
            
    return wrapped_body


def send_mail( to, subject, body, attachement = None ):

    # Make sure `to` is a list
    if isinstance(to, str):
        to = [ to ]

    wrapped_body = wrap( body )

    # Send the mail
    if not attachement:
        django_mail(
            subject,
            wrapped_body,
            settings.RUBION_MAIL_FROM,
            to,
            fail_silently = False
        )

    # Save a copy of the mail in the SentMail module
    from .models import SentMail
    mail = SentMail()
    mail.sender = settings.RUBION_MAIL_FROM
    mail.to = ', '.join(to)
    mail.subject = subject
    mail.body = wrapped_body
    mail.save()

