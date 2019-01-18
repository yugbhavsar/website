from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

import importlib

from instruments.models import InstrumentByProjectBooking, MethodsByProjectBooking

from userinput.models import WorkGroup, Project, UserComment

from wagtail.core.models import UserPagePermissionsProxy



def class_for_name(module_name, class_name):
    # load the module, will raise ImportError if module cannot be loaded
    m = importlib.import_module(module_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c

class AbstractModerationPanel( object ):
    model = None
    template = None

    def __init__(self, request):
        self.request = request
        user_perms = UserPagePermissionsProxy(request.user)
        revisions = user_perms.revisions_for_moderation().select_related('page', 'user').order_by('-created_at')
        pages = [ rev.page for rev in revisions ]
        content_type_id = ContentType.objects.get_for_model( self.model ).id
        self.page_revisions_for_moderation = [
            revision for revision in revisions if revision.page.content_type_id == content_type_id 
        ]
        self.user_comments = {}
        for revision in self.page_revisions_for_moderation:
            self.user_comments[ revision.page_id ] = (
                UserComment.objects.filter(page_id = revision.page_id).
                order_by('-created_at')
            )

    def render(self):
        return render_to_string(self.template, {
            'page_revisions_for_moderation': self.page_revisions_for_moderation,
            'user_comments' : self.user_comments
        }, request=self.request)
    

class WorkgroupsForModerationPanel( AbstractModerationPanel ):
    name = 'workgroups_for_moderation'
    order = 200
    model = WorkGroup
    template = 'wagtailadmin/home/workgroups_for_moderation.html'

class ProjectsForModerationPanel( AbstractModerationPanel ):
    name = 'projects_for_moderation'
    order = 201
    model = Project
    template = 'wagtailadmin/home/projects_for_moderation.html'

class InstrumentBookingsForModerationPanel( object ):
    name = 'bookings_for_moderation'
    order = 203
    model = InstrumentByProjectBooking
    template = 'wagtailadmin/home/bookings_for_moderation.html'

    def __init__(self, request):
        self.request = request
        self.booking_requests = self.model.objects.filter( start__isnull = True ) 
        

    def render(self):
        return render_to_string(self.template, {
            'booking_requests': self.booking_requests,
        }, request=self.request)


class MethodsBookingsForModerationPanel( object ):
    name = 'bookings_for_moderation'
    order = 202
    model = MethodsByProjectBooking
    template = 'wagtailadmin/home/method_bookings_for_moderation.html'

    def __init__(self, request):
        self.request = request
        self.booking_requests = self.model.objects.filter( start__isnull = True ) 

    def render(self):
        return render_to_string(self.template, {
            'booking_requests': self.booking_requests,
        }, request=self.request)
