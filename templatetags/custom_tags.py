from django import template

register = template.Library()


@register.filter
def verbose_name(obj):
    if hasattr(obj, "_meta"):
        return obj._meta.verbose_name
    return obj


@register.filter
def verbose_name_plural(obj):
    if hasattr(obj, "_meta"):
        return obj._meta.verbose_name_plural
    return obj


@register.filter
def get_class(obj):
    if not isinstance(obj, str):
        return obj.__class__.__name__.lower()
    return obj
