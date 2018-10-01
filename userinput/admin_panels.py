from django.template.loader import render_to_string

from userinput.models import RUBIONUser


class UserInitiallySeenPanel( object ):
    template = 'userinput/admin/inititally_seen.html'
    def __init__ ( self, request ):
        self.request = request
        self.users = None#RUBIONUser.objects.filter( inititally_seen = False )

    def render ( self ):
        return render_to_string( 
            self.template, 
            {
                'users' : self.users,
            },
            request = self.request
        )


class UserKeyApplicationPanel( object ):
    template = 'userinput/admin/key_applications_panel.html'
    name = 'key_application'
    order = 199
    def __init__ ( self, request ):
        # Since we do not have a distinct snippet or model
        # for the application, an application is simply a user with
        # needs_key = True
        # key_number = None
        self.request = request
        self.key_applications = (
            RUBIONUser.objects.
            filter( needs_key = True ).
            filter( key_number = '' ).
            filter( is_validated = True )
        )


#        print ('Number of key applications: {}'.format(self.key_applications.count()))

    def render(self):
        return render_to_string(self.template, {
            'key_applications': self.key_applications,
        }, request=self.request)
