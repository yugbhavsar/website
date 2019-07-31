import datetime

from dateutil.relativedelta import relativedelta

from django.db.models import Q
from django.utils import translation
from django_cron import CronJobBase, Schedule

import logging

from notifications.models import SafetyInstructionExpiredNotifications

from userdata.safety_instructions import get_instruction_information, SAFETYINSTRUCTION_NAMES
from userinput.models import RUBIONUser


from website.models import EMailText

logger = logging.getLogger('warn_safety_instructions')

class WarnSafetyInstruction( CronJobBase ):
    RUN_EVERY_MINS = 24 * 60 * 7 # once a week

    schedule = Schedule(run_every_mins = RUN_EVERY_MINS)

    code = 'userdata.warn_safety_instructions'

    def do( self ):
        self.today = datetime.datetime.today()
        self.next_month =  self.today + relativedelta(months = +1)
        self.two_weeks_ago = self.today + relativedelta(weeks=-2)
        self.one_weeks_ago = self.today + relativedelta(weeks=-1)

        for ru in RUBIONUser.objects.live().all():
            expired = []
            soon_expired = []
            not_given_yet = []
            info = get_instruction_information(ru)
            for si, i in info.items():
                
                if i['required']:
                    if not i['last']:
                        not_given_yet.append(si)
                    else:
                        if i['last'] < self.today.date():
                            expired.append(si)
                        elif i['last'] < self.next_month:
                            soon_expired.append(si)
            if expired or soon_expired or not_given_yet:
                new_notifications = self.needs_to_be_sent( ru, expired, soon_expired )
                
                if new_notifications:
                    mail = EMailText.objects.get(identifier = 'warning.safety_instruction')
                    context = {}
                    context['ru'] = ru
                    context['not_given'] = []
                    for i in not_given_yet:
                        context['not_given'].append(SAFETYINSTRUCTION_NAMES[i])
                    context['expired'] = []
                    for i in expired:
                        context['expired'].append(SAFETYINSTRUCTION_NAMES[i])
                    context['soon'] = []
                    for i in soon_expired:
                        context['soon'].append(SAFETYINSTRUCTION_NAMES[i])
                    sent = mail.send(ru.email, context, lang = ru.preferred_language)
                    sent.save()
                    logger.info('Warned {} of incomplete safety instructions'.format(ru))                     
                    for i in list(set(expired+soon_expired+not_given_yet)):
                        noti = SafetyInstructionExpiredNotifications(
                            r_user = ru,
                            mail = sent,
                            instruction = i
                        )
                        noti.save()


    def needs_to_be_sent( self, ru, expired, soon ):
        #combine expired and soon (remove duplicates)

        candidates = list(set(expired + soon))
        
        # Get all notifications for user `ru` sent in the past two weeks
        notifications = SafetyInstructionExpiredNotifications.objects.filter(r_user = ru, mail__sent_at__gt = self.two_weeks_ago)

        for n in notifications.all():
            try:
                candidates.remove(n.instruction)
            except ValueError:
                pass
        return candidates
                
        
