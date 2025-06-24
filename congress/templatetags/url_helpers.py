from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def url_with_params(context, **kwargs):
    """Build URL with current GET parameters plus any new ones"""
    request = context['request']
    params = request.GET.copy()
    
    for key, value in kwargs.items():
        params[key] = value
    
    return f"?{params.urlencode()}"