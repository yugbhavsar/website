import datetime

from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from notifications.models import ProjectExpiredNotifications

from userinput.models import Project, RUBIONUser

from website.models import EMailText

class Command(BaseCommand):
    help = 'Sends an notification mail to users whose projects are about to run out.'

    def __init__(self, *args, **kwargs):
        self.today = datetime.datetime.today()
        self.next_month =  self.today + relativedelta(months = +1)
        self.two_weeks_ago = self.today + relativedelta(weeks=-2)
        self.one_weeks_ago = self.today + relativedelta(weeks=-1)
        super(Command, self).__init__(*args, **kwargs)
    
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lists the projects on STDOUT',
        )

    
    def handle(self, *args, **options):
        recently_send = ProjectExpiredNotifications.objects.filter(mail__sent_at__gt = self.one_weeks_ago)
        ids = []
        for rs in recently_send.all():
            ids.append(rs.id)
        projects_soon = Project.objects.filter(
            expire_at__gt = self.today, expire_at__lt = self.next_month, locked = False
        ).exclude(id__in = ids)
        projects_expired = Project.objects.filter(expire_at__lte = self.today, locked = False)
        
        if options['list']:
            self.list_projects("Expired projects", projects_expired)
            self.list_projects("Projects expiring soon", projects_soon)

        else:
            for project in projects_expired:
                if self.needs_to_be_sent( project ):
                    self.send_expired_mail( project )

            for project in projects_soon:
                if self.needs_to_be_sent( project ):
                    self.send_will_soon_expire_mail( project )


    def send_expired_mail( self, project ):
        mail = EMailText.objects.get(identifier = 'warning.project.expired')
        self.send_mail(mail, project)
        
        
    def send_will_soon_expire_mail( self, project ):
        mail = EMailText.objects.get(identifier = 'warning.project.will_expire')
        self.send_mail(mail, project)

    def send_mail( self, mail, project ):
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
            
    def needs_to_be_sent( self, project ):
        notifications = ProjectExpiredNotifications.objects.filter(project = project).order_by('-mail__sent_at')
        try:
            last = notifications[0]
        except IndexError:
            return True

        if last.mail.sent_at < self.two_weeks_ago:
            return True

        return False
            

        
    def list_projects(self, title, projects):
        self.stdout.write("\n{}:".format(title))
        self.stdout.write("--------------------------------------------------")
        for project in projects:
            wg = project.get_workgroup()
            self.stdout.write("\n{}: {}".format(str(project.expire_at),str(project)))
            self.stdout.write("Group: {}".format(wg))
            self.stdout.write("Head of group: {}".format(wg.get_head()))
            self.stdout.write("Contacts:")
            for con in self.get_contacts(wg).all():
                self.stdout.write(" -  {} <{}>".format(con.full_name(), con.email))

            self.stdout.write("Needs to be sent: {}".format(self.needs_to_be_sent(project)))

    def get_contacts(self, wg):
        return RUBIONUser.objects.live().descendant_of(wg).filter(
            Q(is_leader = True) | Q(may_create_projects = True)
        )
            
            
            
