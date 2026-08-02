from django import template

register = template.Library()

@register.filter
def translated_title(scheme, lang):
    """Template filter: {{ scheme|translated_title:request.LANGUAGE_CODE }}"""
    try:
        return scheme.get_title(lang)
    except Exception:
        return getattr(scheme, 'title', '')

@register.filter
def translated_description(scheme, lang):
    """Template filter: {{ scheme|translated_description:request.LANGUAGE_CODE }}"""
    try:
        return scheme.get_description(lang)
    except Exception:
        return getattr(scheme, 'description', '')
