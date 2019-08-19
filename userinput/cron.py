import datetime

from dateutil.relativedelta import relativedelta

from django.db.models import Q

from django_cron import CronJobBase, Schedule

import logging

from notifications.models import ProjectExpiredNotifications

from userinput.models import Project, RUBIONUser
from userinput.notifications import ProjectExpiredMailNotification

from website.models import EMailText

logger = logging.getLogger('warn_projects')

class WarnProjects( CronJobBase ):
    RUN_EVERY_MINS = 24 * 60 # once a day

    schedule = Schedule(run_every_mins = RUN_EVERY_MINS)

    code = 'userinput.warn_projects'

    def do( self ):

        self.today = datetime.datetime.today()
        self.next_month =  self.today + relativedelta(months = +1)
        self.two_weeks_ago = self.today + relativedelta(weeks=-2)
        self.one_weeks_ago = self.today + relativedelta(weeks=-1)

        recently_send = ProjectExpiredNotifications.objects.filter(mail__sent_at__gt = self.one_weeks_ago)
        ids = []
        for rs in recently_send.all():
            ids.append(rs.id)
        projects_soon = Project.objects.filter(
            expire_at__gt = self.today, expire_at__lt = self.next_month, locked = False
        ).exclude(id__in = ids)
        projects_expired = Project.objects.filter(expire_at__lte = self.today, locked = False).exclude(id__in = ids)
        for project in projects_expired:
            if self.needs_to_be_sent( project ):
                self.send_expired_mail( project )
                
        for project in projects_soon:
            if self.needs_to_be_sent( project ):
                self.send_will_soon_expire_mail( project )


    def needs_to_be_sent( self, project ):
        notifications = ProjectExpiredNotifications.objects.filter(project = project).order_by('-mail__sent_at')
        try:
            last = notifications[0]
        except IndexError:
            return True

        if last.mail.sent_at < self.two_weeks_ago:
            return True

        return False

    def get_contacts(self, wg):
        return RUBIONUser.objects.live().descendant_of(wg).filter(
            Q(is_leader = True) | Q(may_create_projects = True)
        )

    def send_expired_mail( self, project ):
        mail = EMailText.objects.get(identifier = 'warning.project.expired')
        self.send_mail(mail, project)
        
        
    def send_will_soon_expire_mail( self, project ):
        mail = EMailText.objects.get(identifier = 'warning.project.will_expire')
        self.send_mail(mail, project)

    def send_mail( self, mail, project ):
        print ('sending mail')
        contacts = self.get_contacts( project.get_workgroup() )
        to = []
        languages = []
        for contact in contacts:
            to.append(contact.email)
            if contact.preferred_language is not None:
                languages.append(contact.preferred_language)

        languages = list(set(languages)) # removes duplicates
        if len(languages) == 1:
            languages = languages[0]
        else:
            languages = None
            
        sent_mail = mail.send(
            to, {
                'contacts' : contacts,
                'project_de' : project.title_de,
                'project_en' : project.title,
                'expires' : project.expire_at
            },
            lang = languages 
        )
        noti = ProjectExpiredNotifications(
            project=project, mail = sent_mail
        ).save()

        ProjectExpiredMailNotification( project, contacts ).notify()
        
        logger.info('Sent mail for project {} to {}'.format(project.title_de, ", ".join(to))) 
        
