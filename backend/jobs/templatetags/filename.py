import os
from django import template

register = template.Library()

@register.filter
def filename(value):
    return os.path.basename(value.file.name)

@register.filter(name='split')
def split(value, key):
  return value.split(key)