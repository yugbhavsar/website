from .safety_instructions import get_instruction_information, SAFETYINSTRUCTION_NAMES, GENERAL_ACCELERATOR_LAB, P38_INSTRUCTIONS, GENERAL_ISOTOP_LAB
from .notifications import SafetyInstractionExpiredMailNotification

import datetime

from dateutil.relativedelta import relativedelta

from django.db.models import Q
from django.utils import translation
from django_cron import CronJobBase, Schedule

import logging

from notifications.models import SafetyInstructionExpiredNotifications


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
        self.one_year_ago = self.today + relativedelta(years=-1)
        
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
                new_notifications = self.needs_to_be_sent( ru, expired, soon_expired, not_given_yet, info )
                
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
                    SafetyInstractionExpiredMailNotification(
                        ru, context['not_given'], context['expired'], context['soon']).notify()

    def needs_to_be_sent( self, ru, expired, soon, not_given, info ):
        #combine expired and soon (remove duplicates)

        candidates = list(set(expired + soon + not_given))
        
        # Get all notifications for user `ru` sent in the past two weeks
        notifications = SafetyInstructionExpiredNotifications.objects.filter(r_user = ru, mail__sent_at__gt = self.two_weeks_ago)

        for n in notifications.all():
            try:
                candidates.remove(n.instruction)
            except ValueError:
                pass

            
        # If the ru only has an electronic dosemeter and the only notifications are §38 and
        # general safety (accel/isotope), then report only once

        if (
            ru.dosemeter == RUBIONUser.ELECTRONIC_DOSEMETER and (
                sorted(candidates) == sorted([GENERAL_ACCELERATOR_LAB, P38_INSTRUCTIONS]) or
                sorted(candidates) == sorted([GENERAL_ISOTOPE_LAB, P38_INSTRUCTIONS]) 
            )
        ):
            for i in [GENERAL_ISOTOPE_LAB, GENERAL_ACCELERATOR_LAB, P38_INSTRUCTIONS]:
                if info[i]['required']:
                    last = info[i]['last']
                    last_st = last + relativedelta(weeks= -4)
                    if SafetyInstructionExpiredNotifications.objects.filter(
                            r_user = ru,
                            mail__sent_at__gte = last_st,
                            instruction = i).exists():
                        try:
                            candidates.remove(i)
                        except ValueError:
                            pass

        
        return candidates
                
        
