import datetime

from dateutil.relativedelta import relativedelta

from django.db.models import Q

from django_cron import CronJobBase, Schedule

import logging

from notifications.models import SafetyInstructionExpiredNotifications

from userdata.safety_instructions import get_instruction_information
from userinput.models import RUBIONUser


from website.models import EMailText

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
            info = get_instruction_information(ru)
            for si, i in info.items():
                if i.required:
                    if i.last < self.today:
                        expired.append(si)
                    elif i.last < self.next_month:
                        soon_expired.append(si)
            if expired or soon_expired:
                mail = EMailText.objects.get(identifier = 'warning.safety_instruction')
        

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
                
        
