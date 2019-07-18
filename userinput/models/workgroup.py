from django.db import models
from django.http import Http404
from django.shortcuts import redirect
from django.template.defaultfilters import slugify
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from rubauth.models import Identification

from ugc.models import UserGeneratedPage2, UGCCreatePage2

from wagtail.admin.edit_handlers import (
    FieldPanel, StreamFieldPanel, MultiFieldPanel,
    FieldRowPanel, InlinePanel, TabbedInterface, 
    ObjectList, PageChooserPanel 
)

from website.models import TranslatedField

class WorkGroup ( UserGeneratedPage2 ):

    #--------------------------------------------------
    #
    # settings
    #
    #--------------------------------------------------
    
    subpage_types = [
        'userinput.MemberContainer',
        'userinput.ProjectContainer',

    ]
    parent_page_types = [ 'userinput.WorkGroupContainer' ]
    child_template = 'userinput/workgroup_child.html'
    view_template =  'userinput/workgroup_view.html'

    class Meta:
        verbose_name = _('workgroup')
        verbose_name_plural = _('workgroups')

    #--------------------------------------------------
    #
    # model definition
    #
    #--------------------------------------------------

    department_de = models.CharField(
        max_length = 64,
        blank = True,
        null = True,
        verbose_name = _('department (de)')
    )
    department_en = models.CharField(
        max_length = 64,
        blank = True,
        null = True,
        verbose_name = _('department (en)')
    )

    institute_en = models.CharField(
        max_length = 64,
        verbose_name = _('institute (en)')
    )
    institute_de = models.CharField(
        max_length = 64,
        verbose_name = _('institute (de)')
    )

    university_de = models.CharField(
        max_length = 64,
        verbose_name = _('university (de)')
    )
    university_en = models.CharField(
        max_length = 64,
        verbose_name = _('university (en)')
    )
        
    department = TranslatedField('department')
    institute = TranslatedField('institute')
    university = TranslatedField('university')

    homepage = models.CharField(
        max_length = 128,
        blank = True, null = True,
        verbose_name = _( 'internet address' ),
        help_text = _('Please include http:// or https:// and www, if required.')
    )

    #--------------------------------------------------
    #
    # edit handlers
    #
    #--------------------------------------------------

    content_panels = [
        MultiFieldPanel([
            FieldPanel('title_de'),
            FieldPanel('institute_de'),
            FieldPanel('department_de'),
            FieldPanel('university_de'),
        ], heading =_ ('German Information')),
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('institute_en'),
            FieldPanel('department_en'),
            FieldPanel('university_en'),
        ], heading =_ ('English Information')),
        MultiFieldPanel([
            FieldPanel('homepage'),
        ], heading =_ ('Additional Information')),
    ]
    comment_panel = [
        FieldPanel('internal_rubion_comment')
    ]

    edit_handler = TabbedInterface([
        ObjectList( content_panels, _('Information')),
        ObjectList( comment_panel, _('Internal comments')),
    ])

    #--------------------------------------------------
    #
    # properties
    #
    #--------------------------------------------------
    
    @property
    def under_revision( self ):
        return self.has_unpublished_changes

    @property
    def is_active( self ):
        return self.get_projects().filter(expire_at__gte = datetime.datetime.now()).exists()

    #--------------------------------------------------
    #
    # METHODS
    #
    #--------------------------------------------------
    
    def add_member_container( self ):
        # Generates a container for the workgroup members

        if len( MemberContainer.objects.child_of( self ) ) == 0:
            title = "Members"
            title_de = "Mitglieder"
            mc = MemberContainer()
            mc.title = title
            mc.title_de = title_de
            mc.slug = "members"
            self.add_child( instance = mc )

    def add_project_container( self ):
        # Generate a container for Projects
        
        if len( ProjectContainer.objects.child_of( self ) ) == 0:
            title = "Projects"
            title_de = "Projekte"
            pc = ProjectContainer()
            pc.title = title
            pc.title_de = title_de
            pc.slug = "project"
            self.add_child( instance = pc )

    def after_create_hook( self, request ):

        # Auto-generate child containers        
        self.add_member_container()
        self.add_project_container()

        # Adding a workgroup requires revision by RUBION
        
#        self.unpublish()
#        self.save_revision()

    def serve_success( self, request, edit = False ):
        if edit:
        # if edited, the workgroup is available
            return redirect( self.url )
        else:
        # Created, workgroup awaits verification. Show add user page to add work group leader
            ident = Identification()
            ident.page = self
            ident.create_user = True
            ident.login_user = True
            ident.mail_text = 'Workgroup.create.identify'
            ident.save()
            pk = ident.id
            return redirect( reverse('rubauth.identify', kwargs = {'pk' : pk}) )
 

    def create_project_page( self ):
        pc = ProjectContainer.objects.child_of(self).first()
        return UGCCreatePage2.objects.child_of(pc).first()

    def create_member_page( self ):
        mc = MemberContainer.objects.child_of(self).first()
        return UGCCreatePage2.objects.child_of(mc).first()

    def get_head( self ):
        return RUBIONUser.objects.live().descendant_of(self).filter(is_leader=True).first()
    
    # for displaying in the admin overview:
    get_head.short_description = _('Group leader')


    def get_members( self ):
        return RUBIONUser.objects.live().descendant_of(self).filter(expire_at__isnull = True)

    def get_projects( self ):
        return Project.objects.live().descendant_of(self)

    def get_methods( self ):
        
        projects = self.get_projects()
        methods = []
        for project in projects:
            pr_methods = project.get_methods()
            for method in pr_methods:
                if method not in methods:
                    methods.append(method) 

        return methods

    def create_group_leader ( self, user ):
        mc = MemberContainer.objects.child_of(self).first()
        group_leader = RUBIONUser()
        group_leader.is_leader = True
        group_leader.linked_user = user
        group_leader.owner = user
        group_leader.is_rub = user.username.find('@') == -1
        group_leader.may_create_projects = True

        if not group_leader.is_rub:
            group_leader.title = user.username
            group_leader.title_de = user.username
            group_leader.slug = slugify(user.username)

            # Avoid cleaning on save...
            group_leader.dont_clean = True
        else:
            group_leader.title = '{}, {}'.format(user.last_name, user.first_name)
            group_leader.title_de = '{}, {}'.format(user.last_name, user.first_name)
            group_leader.slug = slugify('{}, {}'.format(user.last_name, user.first_name))
            group_leader.first_name_db = user.first_name
            group_leader.last_name_db = user.last_name

        mc.add_child(group_leader)

        group_leader.save_revision(
            submitted_for_moderation = True,
            user = user
        )

        return group_leader

    def validate( self, request, user = None, username = None):
        if RUBIONUser.exists( user ):
            return TemplateResponse(
                request,
                'userinput/errors/user_has_workgroup.html',
                {
                    'user' : user
                }
            )
        else:
            self.save()
            r_user = self.create_group_leader( user )
            self.owner = r_user.linked_user
            self.save_revision(submitted_for_moderation = True, user = r_user.linked_user)
            
            return redirect (r_user.full_url + r_user.reverse_subpage('edit'))

    def user_passes_test( self, user, what ):
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        r_user = RUBIONUser.objects.get( linked_user = user )
        user_in_wg = r_user.get_workgroup() == self

        # Every RUBION-User may see the workgroups
        if what == self.VIEW:
            if self.under_revision:
                # Instead of returning False, which would result in a `403 Forbidden`
                # response, I raise a `404 Not found` here. A 403 would indicate that the group 
                # has applied to work in RUBION, which should be treated confidential.
                #
                # Of course, someone would have to guess the name of the group to construct 
                # the URL. But anyway...
                if  not user_in_wg:
                    raise Http404()

            return user.is_authenticated

        if what == self.EDIT:
            r_user = RUBIONUser.objects.get( linked_user = user )
            return r_user == self.get_head()
        
        return False

    def get_context(self, request):
        context = super(WorkGroup, self).get_context(request)
        context['user_may_edit'] = self.user_passes_test(request.user, self.EDIT)
        context['user_is_workgroup_member'] = False
        if request.user.is_authenticated:
            try:
                r_user = RUBIONUser.objects.get(linked_user = request.user)
            except:
                r_user = None
            if r_user:
                is_workgroup_member = ( r_user.get_workgroup() == self ) 
                context['user_is_workgroup_member'] = is_workgroup_member
                if is_workgroup_member:
                    context['user_may_add_projects'] = r_user.may('project')
                    context['user_may_add_members'] = r_user.may('member')
        return context


    def clean( self ):
        if not self.slug:
            self.slug = self._get_autogenerated_slug( slugify( self.title ) )

    def inactivate( self, user = None ):
        # inactivate this group.
        now = datetime.datetime.now()
        self.expire_at = now
        if user:
            self.save_revision_and_publish(user=user)
        else:
            self.save_revision_and_publish()

        for member in self.get_members():
            member.inactivate(user = user)

        for project in self.get_projects():
            if project.expire_at > now:
                project._close(user = user)
        
            

    def __str__( self ):
        if self.department:
            return '{}, {}, {}, {}'.format( self.title_trans, self.institute, self.department, self.university )
        else:
            return '{}, {}, {}'.format( self.title_trans, self.institute, self.university )
