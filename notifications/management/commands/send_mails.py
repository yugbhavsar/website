'''
send_mails command for notification-app

Sends emails for new news.

Call it as manage.py send_mails notifications 
'''

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.html import strip_tags

from notifications.models import NewsSnippet

from website.models import EMailText

from userinput.models import RUBIONUser

class Command(BaseCommand):

    def handle(self, *args, **options):
        open_news = (
            NewsSnippet.objects.filter(mail_was_sent = False)
            .filter(
                Q(send_mail_to_all = True) | 
                Q(method__isnull = False ) |
                Q(instrument__isnull = False ) |
                Q(workgroup__isnull = False ) 
            )
        )

        for news in open_news:
            try:
                mail = EMailText.objects.get(identifier = 'news')
                mail.subject_en = news.title_en
                mail.subject_de = news.title_de
            except EMailText.DoesNotExist:
                mail = EMailText(
                    identifier = 'tmp',     # We have to fake this 
                    description_en = 'tmp', # We have to fake this 
                    description_de = 'tmp', # We have to fake this 
                    subject_de = news.title_de,
                    subject_en = news.title_en,
                    text_de = news.content_de,
                    text_en = news.content_en
                )
            usrs = self.get_receivers(news)
            for usr in usrs:
                mail.send( 
                    usr.email, 
                    {
                        'full_name_en' : usr.full_name(language = 'en'),
                        'full_name_de' : usr.full_name(language = 'de'),
                        'news_en' : strip_tags(news.content_en),
                        'news_de' : strip_tags(news.content_de),
                    },
                    lang = usr.preferred_language)
            
            news.mail_was_sent = True
            news.save()
                                          

    def get_receivers( self, news ):
        addresses = set()
        for usr in RUBIONUser.objects.filter(locked = False):
            if news.send_mail_to_all:
                addresses.add(usr)
            wg = usr.get_workgroup()
            wgs = [w.page for w in news.workgroup.all()]
            if  wg in wgs:
                addresses.add(usr)
            methods = [m.page for m in news.method.all()]
            for meth in wg.get_methods():
                if meth in methods:
                    addresses.add(usr)
            instruments = [i.page for i in news.instrument.all()]
            for inst in usr._get_instruments():
                if inst in instruments:
                    addresses.add(usr)
        return list(addresses)


