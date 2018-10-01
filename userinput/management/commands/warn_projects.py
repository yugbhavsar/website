import datetime

from django.core.management.base import BaseCommand, CommandError

from userinput.models import Project


class Command(BaseCommand):
    help = 'Sends an notification mail to users whose projects are about to run out.'
    
    def handle(self, *args, **options):
        pass
    
