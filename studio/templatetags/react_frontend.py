from django import template
from django.contrib.staticfiles import finders
register = template.Library()

@register.simple_tag
def react_frontend_available():
    return bool(finders.find("studio/react/landing.js"))
