import datetime

from django.views.generic.base import TemplateView

from userinput.models import WorkGroup, Project



class StatisticsOverview( TemplateView ):
    page_title = 'Statistics'
    template_name = 'rubionadmin/statistics/overview.html'


    def get_context_data( self, **kwargs ):
        context = super().get_context_data(**kwargs)
        self.today = datetime.date.today()
        context['groups'] = self.get_group_context()
        context['projects'] = self.get_project_context()
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
                external = external + 1
        return {
            'internal' : internal,
            'internal_inactive' : internal_inactive,
            'external' : external,
            'external_inactive' : external_inactive,
            'total' : external + internal
        }

    def get_project_context( self ):
        total = Project.objects.filter(expire_at__lt = datetime.date.today()).count()
        
        finished = Project.objects.filter(expire_at__lt = datetime.date.today()).count()
    
        return {
            'total' : total
        }
