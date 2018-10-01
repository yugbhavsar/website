from userinput.models import Project2NuclideRelation


from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

from wagtail.contrib.modeladmin.helpers.url import AdminURLHelper


class IsotopeFilter( SimpleListFilter ):

    title = _('Isotope')
    parameter_name = 'isotope'

    def lookups( self, request, model_admin ):
        p2nrs = Project2NuclideRelation.objects.all()

        used_nuclides = (
            (p2nr.snippet_id, p2nr.snippet) for p2nr in p2nrs
        )

        return used_nuclides


    def queryset(self, request, queryset):
        if self.value():
            if self.value() == 'all':
                return queryset.all()
            else:
                return queryset.filter(snippet = self.value())

class ListFilterWithoutAll( SimpleListFilter ):
    def choices(self, changelist):
        
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }


class GroupFilter( SimpleListFilter ):
    title = _('Group')
    parameter_name = 'group'

    def lookups( self, request, model_admin ):
        p2nrs = Project2NuclideRelation.objects.all()
        groups = []
        
        for p2nr in p2nrs:
            group = p2nr.project_page.specific.get_workgroup()
            item = (group.id, '{} ({})'.format(group, group.get_head()))
            if  item not in groups:
                groups.append( item )

        return tuple(groups)

    def queryset( self, request, queryset ):
        if self.value():
            result_ids = []
            for item in queryset:

                wg = item.project_page.specific.get_workgroup()

                if wg.id == int(self.value()):
                    result_ids.append(item.id)
            return queryset.filter(id__in = result_ids)

        return queryset

class ProjectActiveFilter( ListFilterWithoutAll ):
    title = _('Project status')
    parameter_name = 'status'
    
    ACTIVE = 'active'
    ALL = 'all'
    FINISHED = 'finished'


    def lookups(self, request, model_admin ):
        return (
            (self.ACTIVE, _('active')),
            (self.FINISHED, _('finished')),
            (self.ALL, _('all')),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            self.used_parameters[self.parameter_name] = self.ACTIVE
        else:
            self.used_parameters[self.parameter_name] = self.value()
        return queryset

    def choices(self, changelist):

        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }

class SafetyRelationDateFilter( ListFilterWithoutAll ):
    ALL = 'all'
    LAST = 'last'
    EXPIRED = 'expired'
    NEARLY_EXPIRED = 'nearly'

    title = _('Date')
    parameter_name = 'status'


    def lookups( self, request, model_admin ):
        return(
            (self.LAST, _('last')),
            (self.EXPIRED, _('expired')),
            (self.NEARLY_EXPIRED, _('nearly')),
            (self.ALL, _('all')),
        )
        
    def queryset(self, request, queryset):
        if self.value() is None:
            self.used_parameters[self.parameter_name] = self.LAST
        else:
            self.used_parameters[self.parameter_name] = self.value()
        return queryset
