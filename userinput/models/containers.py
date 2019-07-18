from .project import Project
from .workgroup import WorkGroup

from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from ugc.models import UGCContainer2, UGCCreatePage2

from wagtail.admin.edit_handlers import (
    FieldPanel, StreamFieldPanel 
)


from website.decorators import only_content, default_panels
from website.models import AbstractContainerPage


@only_content
class WorkGroupContainer ( UGCContainer2 ):
    is_creatable = False
    create_title = "Apply for Workgroup registration"
    create_title_de = "Aufnahme der Arbeitsgruppe beantragen"
    template = 'userinput/list_of_workgroups_page.html'
    subpage_types = [ WorkGroup, UGCCreatePage2 ]
    parent_page_types = [ 'website.StartPage' ]
    for_model = WorkGroup

    content_panels = [
        FieldPanel( 'title' ),
        FieldPanel( 'title_de' ),
        StreamFieldPanel( 'introduction_en' ),
        StreamFieldPanel( 'introduction_de' ),
    ]

    def get_visible_children( self ):
        if translation.get_language() == 'de':
            order = 'title_de'
        else:
            order = 'title'
        return WorkGroup.objects.filter(has_unpublished_changes = False).order_by(order)

    def get_context( self, request ):
        context = super(WorkGroupContainer, self).get_context(request)
        context['workgroups'] = self.get_visible_children()
        return context


@only_content
class ProjectContainer ( UGCContainer2 ):
    create_title = "Apply for Project"
    create_title_de = "Projekt beantragen"
    is_creatable = False
    subpage_types = [ UGCCreatePage2, Project ]
    parent_page_types = [ WorkGroup ]
    for_model = Project

    sidebar_text = _('''
<h3>Information</h3>
<p>The information about your project will be publicly available on our website</p>
<p>If your project should be treated confidential, please check "Hide Project"</p>
<p>Select all methods you think you will use in this project.</p>
<p>Use the last field to explain your project to us in more detail.</p>
    ''')
    
    content_panels = [
        FieldPanel( 'title' ),
        FieldPanel( 'title_de' ),
        StreamFieldPanel( 'introduction_en' ),
        StreamFieldPanel( 'introduction_de' ),
    ]
    def get_visible_children( self ):
        return Project.objects.child_of(self)

    
@default_panels
class ListOfProjectsPage ( AbstractContainerPage ):
    subpage_types = []
    template = 'userinput/list_of_projects_page.html'

    is_creatable = False

    def get_visible_children( self, active = True ):
        if translation.get_language() == 'de':
            title_field = 'title_de'
        else:
            title_field = 'title'
        pages = (Project.objects.live().
                 filter(is_confidential = False).
                 filter(has_unpublished_changes = False).
                 filter(locked = (not active) ) 
        )
                

        return pages.order_by(title_field)

    def get_context( self, request ):
        context = super(ListOfProjectsPage, self).get_context(request)
        if request.GET.get('status', None) == 'closed':
            context['projects'] = self.get_visible_children( active = False )
            context['show_active'] = False
        else:
            context['projects'] = self.get_visible_children()
            context['show_active'] = True
        return context
            
