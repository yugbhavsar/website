from .models import CourseInformationPage, Course

import datetime

from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from wagtail.contrib.modeladmin.helpers.url import AdminURLHelper

class CoursesOrgaFilter( admin.SimpleListFilter ):
    RUBION = 'rubion'
    ALL = 'all'
    OTHER = 'other'

    title = _('organizer')

    parameter_name = 'orga'

    def lookups( self, request, model_admin ):
        return (
            (self.RUBION, _('RUBION')),
            (self.OTHER, _('other'))
        )

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == self.RUBION:
                courses_qs = CourseInformationPage.objects.filter(register_via_website = True)
                qs = queryset.filter(overrule_parent = True).filter(register_via_website = True)
                for course in courses_qs:
                    qs = qs | Course.objects.child_of(course).filter(overrule_parent = False)
                return queryset & qs
                    
            if self.value() == self.OTHER:
                courses_qs = CourseInformationPage.objects.filter(register_via_website = False)
                qs = queryset.filter(overrule_parent = True).filter(register_via_website = False)
                for course in courses_qs:
                    qs = qs | Course.objects.child_of(course).filter(overrule_parent = False)
                return queryset & qs


        return queryset


class CoursesDateFilter( admin.SimpleListFilter ):
    ALL = 'all'
    UPCOMING = 'upcoming'
    PAST = 'past'
    title = _('Date')

    parameter_name = 'status'

    def lookups( self, request, model_admin ):

        return (
#            (self.ALL, _('all')),
            (self.UPCOMING ,_('upcoming')),
            (self.PAST ,_('past')),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            if self.value() == self.ALL:
                return queryset.all()
            if self.value() == self.UPCOMING:
                return queryset.filter( end__gte = datetime.datetime.now() )
            if self.value() == self.PAST:
                return queryset.filter( end__lt = datetime.datetime.now() )
        return queryset
