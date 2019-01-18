from wagtail.users.forms import UsernameForm

from .auth import fetch_user_info, LDAPBackend

from django.utils.translation import ugettext as _
from django import forms
from django.contrib.auth import get_user_model, authenticate
import re

User = get_user_model()

class LoginForm ( forms.Form ):
    required_css_class = "required"
    username = forms.CharField(
        required = True
    )
    password = forms.CharField(
        required = True,
        widget = forms.PasswordInput
    )
    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean( self ):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        self.user_cache = authenticate(username=username, password=password)
        if self.user_cache is None:
            raise forms.ValidationError(
                _('Username and password did not match.'), 
                code = 'authentication'
            )
        
    def get_user( self ):
        return self.user_cache


class RUBUserForm( UsernameForm ):
        
    required_css_class = "required"
    password_required = False
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'unknown_LDAP_username': _("A user with that username is not known on the LDAP server."),
    }

    is_superuser = forms.BooleanField(
        label=_("Administrator"), required=False,
        help_text=_('Administrators have full access to manage any object '
                    'or setting.'))

    def __init__(self, *args, **kwargs):
        super(UsernameForm, self).__init__(*args, **kwargs)



    # We cannot call this method clean_username since this the name of the
    # username field may be different, so clean_username would not be reliably
    # called. We therefore call _clean_username explicitly in _clean_fields.
    def _clean_username(self):
        username_field = User.USERNAME_FIELD
        # This method is called even if username if empty, contrary to clean_*
        # methods, so we have to check again here that data is defined.
        if username_field not in self.cleaned_data:
            return
        username = self.cleaned_data[username_field]

        users = User._default_manager.all()
        if self.instance.pk is not None:
            users = users.exclude(pk=self.instance.pk)
        if users.filter(**{username_field: username}).exists():
            self.add_error(User.USERNAME_FIELD, forms.ValidationError(
                self.error_messages['duplicate_username'],
                code='duplicate_username',
            ))
        self._userinfo = fetch_user_info( username ) 
        if self._userinfo is None:
            self.add_error(User.USERNAME_FIELD, forms.ValidationError(
                self.error_messages['unknown_LDAP_username'],
                code='unknown_LDAP_username',
            ))

        return username


    def _clean_fields( self ):
        super( RUBUserForm, self )._clean_fields()
        self._clean_username()

    def save( self, commit = True ):
        user = super( RUBUserForm, self ).save( commit=False )
        user.email = self._userinfo[ 'email' ].replace('ruhr-uni-bochum', 'rub')
        user.first_name = self._userinfo[ 'first_name' ]
        user.last_name = self._userinfo[ 'last_name' ]
        user.set_password( None )
        if commit:
            user.save()
            self.save_m2m()
        return user



    
class RUBUserCreationForm( RUBUserForm ):
    class Meta:
        model = User
        fields = set(['username', 'is_superuser', 'groups'])
        widgets = {
            'groups': forms.CheckboxSelectMultiple
        }


class IdentificationForm( forms.Form ):
    required_css_class = "required"

    RUB = 'RUB'
    EXT = 'EXT'
    user_choices = (
        ( RUB, _('RUB member') ),
        ( EXT, _('External') )
    )

    usertype = forms.ChoiceField(
        choices = user_choices,
        label = _('Type of user (RUB-member or external)')
    )
    rub_id = forms.CharField(
        required = False,
        label = _('RUB-ID')
    )
    rub_pwd = forms.CharField(
        required = False,
        widget = forms.PasswordInput,
        label = _('RUB-Password')
    )
    
    email = forms.CharField(
        required = False,
        label = _('E-Mail')
    )

    def __init__(self, *args, **kwargs):
        self.rub_username = None
        self.rub_login_valid = False
        self.email = None
        super().__init__(*args, **kwargs) 

    def clean( self ):
        if self.cleaned_data['usertype'] == self.RUB:
            self.clean_rub()
        else:
            self.clean_ext()

    def clean_ext( self ):
        email = self.cleaned_data.get('email', None)
        if not re.match("[^@]+@[^@]+\.[^@]+", email):
            self.add_error('email', forms.ValidationError(
                _("The email-adress is syntactically incorrect."), 
                code = "Incorrect email address"
            ))
        else:
            self.email = email

    def clean_rub( self ):
        rub_id = self.cleaned_data.get('rub_id', None)
        rub_pwd = self.cleaned_data.get('rub_pwd', None)
        if rub_id and rub_pwd:
            if LDAPBackend.ldap_authenticate(rub_id, rub_pwd):
                self.rub_username = rub_id
                self.rub_login_valid = True
            else:
                self.add_error('__all__', forms.ValidationError(
                    _("Your RUB ID and password did not match."), 
                    code = "Credentials do not match"
                ))
        else:
            if not rub_id:
                self.add_error('rub_id', forms.ValidationError(
                    _("A RUB-ID is required for login."), 
                    code = "missing data"
                ))
            if not rub_pwd:
                self.add_error('rub_pwd', forms.ValidationError(
                    _("A password is required for login."), 
                    code = "missing data"
                ))
        
