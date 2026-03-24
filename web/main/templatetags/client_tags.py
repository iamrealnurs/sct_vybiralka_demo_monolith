from django import template

register = template.Library()

@register.filter(name='split_email_name')
def split_email_name(value):
    if not value:
        return ""
    return value.split('@')[0]
