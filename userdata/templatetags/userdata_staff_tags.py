from django import template
register = template.Library()

@register.inclusion_tag(
    'tags/connections.html'
)
def render_connections( user ):
    return {
        'user' : user
    }
