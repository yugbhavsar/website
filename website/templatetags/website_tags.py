from datetime import datetime

from django import template
from django.conf import settings
from django.urls import resolve, translate_url 
from django.db.models import Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from notifications.models import NewsSnippet

from rubauth.models import LoginPage
from rubauth.forms import LoginForm

from userinput.models import RUBIONUser
from userdata.models import StaffUser


from website.models import Menu



register = template.Library()

@register.simple_tag( takes_context=True ) 
def change_lang( context, lang=None, *args, **kwargs ): 
    path = context['request'].path 
    return translate_url(path, lang)

@register.simple_tag
def get_login_url():
    p = LoginPage.objects.live().first()
    if p:
        return p.url
    else:
        return ''

@register.simple_tag( takes_context = True )
def get_site_root( context ):
    return context['request'].site.root_page

def has_menu_children( page ):
    return page.get_children().live().in_menu().exists()

@register.inclusion_tag(
    'tags/top_menu.html',
    takes_context = True
)
def get_menu_container( context, page ):
    m = Menu.objects.live()
    user = context['request'].user
    is_logged_in = user.is_authenticated
    rubion_user = None
    try:
        page.url
    except AttributeError:
        page = None

    if is_logged_in:
        try:
            rubion_user = RUBIONUser.objects.get(linked_user = user)
        except:
            pass
    if page is None:
        return {
            'menu_root' : m[1],
            'rubion_user' : rubion_user,
            'logged_in' : is_logged_in,
        }        
    return {
        'menu_root' : m[1],
        'rubion_user' : rubion_user,
        'logged_in' : is_logged_in,
        'page' : page
    }

@register.simple_tag(takes_context = True)
def userinfo(context):
    user = context['request'].user
    is_logged_in = user.is_authenticated
    rubion_user = None
    staff_user = None
    if is_logged_in:
        try:
            rubion_user = RUBIONUser.objects.get(linked_user = user)
        except:
            pass
        try:
            staff_user = StaffUser.objects.get(user = user).specific
        except:
            pass

    return {
        'user' : user,
        'rubion_user' : rubion_user,
        'staff_user' : staff_user,
        'logged_in' : is_logged_in,
        'admin' : user.is_superuser
    }
@register.simple_tag
def loginform():
    return {'form' : LoginForm(), 'login_page': LoginPage.objects.live().first() }
@register.inclusion_tag(
    'tags/main_menu.html'
)
def get_main_menu_container():
    m = Menu.objects.live()
    return {
        'menu_root' : m.first()
    }


@register.inclusion_tag(
    'tags/news.html'
)
def news():
    news = NewsSnippet.objects.order_by('date_published')

@register.inclusion_tag(
    'tags/additional_list_info.html'
)
def add_additional_list_info( page ):
    pass

@register.simple_tag
def render_as_child( page ):
    return page.specific.render_as_child()

@register.inclusion_tag(
    'tags/extra_css.html'
)
def get_extra_css( page ):
    try:
        css = page.extra_css
    except AttributeError:
        return None
@register.inclusion_tag(
    'tags/viewmore.html'
)
def viewmore( page ):
    return { 'page' : page  }
@register.inclusion_tag(
    'tags/news_list.html'
)
def news_list():
    latest_news = (
        NewsSnippet.objects
        .filter( date_published__lte = datetime.now() )
        .filter(
            Q(date_unpublish = None) | 
            Q(date_unpublish__gte = datetime.now())
        )
        .order_by( '-date_published' )
    )
    return {
        'news' : latest_news
    }

@register.inclusion_tag('tags/breadcrumb.html', takes_context=True)
def breadcrumb(context, page = None, include_self=True):
    if page:
        root = page.get_site().root_page
        pages = page.get_ancestors(inclusive=include_self).descendant_of(root, inclusive=False)
        return {
            'root' : root,
            'pages': pages
        }
    return {}

@register.inclusion_tag('tags/sidebar.html')
def render_sidebar( page ):

    try:
        return {
            'contacts' : page.contact_persons,
            'other' : page.sidebar_content,
        }
    except AttributeError:
        try:
            return {
                'contacts' : page.contact_persons,
                #            'other' : page.sidebar_content                                           
            }
        except AttributeError:
            try:
                return {
                    'other' : page.sidebar_content,
                }
            except AttributeError:
                return {}

@register.filter
def strip_colon(txt):
    return format_html(txt.replace(':',''))

@register.inclusion_tag('tags/form_element.html')
def form_element( element ):
    return { 
        'element' : element,
        'checkbox': element.field.widget.__class__.__name__ == 'StyledCheckbox',
        'select': element.field.widget.__class__.__name__ == 'Select',
        'radio': element.field.widget.__class__.__name__ == 'RadioSelect',
        'dateselect' : element.field.widget.__class__.__name__ == 'StyledDateSelect',
        'termsconditions' : element.field.widget.__class__.__name__ == 'TermsAndConditionsWidget',
    }

@register.inclusion_tag('tags/form_element_select.html')
def form_element_select( element ):
    return { 'element' : element }

@register.filter
def append_if_not_none_or_empty(val, append):
    if isinstance(val, type(None)) or val == '':
        return ''
    return format_html('{}{}', val, mark_safe(append))
        

@register.filter('get_value_from_dict')
def get_value_from_dict(dict_data, key):
    """
    usage example {{ your_dict|get_value_from_dict:your_key }}
    """
    if key:
        return dict_data.get(key)

@register.filter('addhttp')
def addhttp( address ):
    if not (address.startswith('http://') or address.startswith('https://')):
        return "http://{}".format(address)
    return address

@register.inclusion_tag('tags/button.html')
def button (text, href, icon, classes = []):
    return {
        'href' : href,
        'icon' : icon,
        'classes' : classes,
        'text' : text
    }

@register.simple_tag
def translated_legend(form, legend):
    return form.get_legend_trans(legend)


@register.inclusion_tag('tags/toc.html')
def render_toc (body):
    
    return {
        'href' : href,
        'icon' : icon,
        'classes' : classes,
        'text' : text
    }

