from dateutils import relativedelta
import datetime

from django.db.models import Q
from django.utils.safestring import mark_safe
from django.views.generic.base import TemplateView

from userinput.models import WorkGroup, Project, RUBIONUser



class StatisticsOverview( TemplateView ):
    page_title = 'Statistics'
    template_name = 'rubionadmin/statistics/overview.html'


    def get_context_data( self, **kwargs ):
        context = super().get_context_data(**kwargs)
        self.today = datetime.date.today()
        context['groups'] = self.get_group_context()
        context['projects'] = self.get_project_context()
        context['users_by_time'] = self.get_user_by_time_context()
        return context

    def get_group_context( self ):
        internal = 0
        internal_inactive = 0
        external = 0
        external_inactive = 0
        for group in WorkGroup.objects.live():
            head = group.specific.get_head()
            if not head:
                continue
            if head.is_rub:
                if Project.objects.descendant_of(group).filter(expire_at__gte = self.today).exists():
                    internal = internal + 1
                else:
                    internal_inactive = internal_inactive + 1
            else:
                if Project.objects.descendant_of(group).filter(expire_at__gte = self.today).exists():
                    external = external + 1
                else:
                    external_inactive = external_inactive + 1
        return {
            'internal' : internal,
            'internal_inactive' : internal_inactive,
            'external' : external,
            'external_inactive' : external_inactive,
            'total' : external + internal
        }

    def get_user_by_time_context( self ):
        months = []
        usercounts = []
        eusercounts = []
        iusercounts = []
        for m in range(24,-1,-1):
            d = self.today - relativedelta(months = m, day=1)
            months.append('\'{m}/{y}\''.format(m=d.month, y=d.year))
            
            usercounts.append(
                str(RUBIONUser.objects.filter(Q(first_published_at__lte = d) & (
                    Q(expire_at = None) | Q(expire_at__gte = d)
                )).count())
            )
            iusercounts.append(
                str(RUBIONUser.objects.filter(Q(first_published_at__lte = d) & (
                    Q(expire_at = None) | Q(expire_at__gte = d)
                ) & Q(is_rub = True)).count())
            )
            eusercounts.append(
                str(RUBIONUser.objects.filter(Q(first_published_at__lte = d) & (
                    Q(expire_at = None) | Q(expire_at__gte = d)
                ) & Q(is_rub = False)).count())
            )
        return {
            'months' : mark_safe(','.join(months)),
            'usercount' : ','.join(usercounts),
            'eusercount' : ','.join(eusercounts),
            'iusercount' : ','.join(iusercounts)
        }
            
        
    
    def get_project_context( self ):
        total = Project.objects.filter(expire_at__gte = datetime.date.today()).count()
        
        finished = Project.objects.filter(expire_at__lt = datetime.date.today()).count()
    
        return {
            'total' : total
        }
