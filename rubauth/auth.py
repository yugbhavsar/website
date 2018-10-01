from ldap3 import Server, Connection
from ldap3.core.exceptions import LDAPSocketOpenError
from django.contrib.auth import get_user_model, login
from django.conf import settings
from django.contrib.auth.backends import ModelBackend


UserModel = get_user_model()

class LDAPBackend( ModelBackend ):

    def authenticate( self, request, username = None, password = None ):
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            return None
        try:
            if LDAPBackend.ldap_authenticate( username, password ):
                return user
        except LDAPSocketOpenError:
            return None
        return None

    def get_user( self, user_id ):
        try:
            user = UserModel.objects.get(pk = user_id)
            return user
        except UserModel.DoesNotExist:
            return None
            
    @staticmethod
    def ldap_authenticate( username, password ):        
        connection = LDAPBackend.ldap_open_authenticated( username, password )
        
        if connection.bind():
            connection.unbind()
            return True
        return False

    @staticmethod
    def ldap_open_authenticated ( 
            username, password, 
            user = 'uid={},ou=users,dc=ruhr-uni-bochum,dc=de' ):   
        server = Server(
            host = settings.RUB_LDAP_SERVER, 
            port = settings.RUB_LDAP_PORT,
            use_ssl = settings.RUB_LDAP_USE_SSL
        )
        connection = Connection( 
            server,
            user = user.format(username),
            password = password
        )
        return connection

    

def fetch_user_info( username ):
    connection = LDAPBackend.ldap_open_authenticated( 
        settings.RUB_LDAP_CONNECTION_USERNAME,
        settings.RUB_LDAP_CONNECTION_PASSWORD,
        user = '{}'
    )
    if connection.bind():
        connection.search(
            search_base = settings.RUB_LDAP_SEARCH_BASE,
            search_filter='(uid={})'.format(username),
            attributes=['sn', 'givenName', 'mail', 'matrikelnr' ]
        )
        attr =  connection.response[0]['attributes']
        info = {
            'last_name'  : attr['sn'][0],
            'first_name' : attr['givenName'][0],
            'email'      : attr['mail'][0].lower(),
        }
        try:
            info['student_id'] = attr['matrikelnr'][0] 
        except IndexError:
            info['student_id'] = None
        connection.unbind()
        return info
    return None
