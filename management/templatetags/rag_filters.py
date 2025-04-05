from django import template

register = template.Library()

@register.filter
def zip_lists(a, b):
    return zip(a, b)

@register.filter
def zip_with(value, arg):
    """
    Zip a list with another list.
    Usage: {{ list1|zip_with:list2 }}
    """
    return zip(value, arg)
