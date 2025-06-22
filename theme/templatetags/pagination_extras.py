from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_params_without_page(context):
    """Get all query parameters except 'page' for pagination links"""
    request = context["request"]
    params = request.GET.copy()
    if "page" in params:
        del params["page"]
    return params.urlencode()
