from django import template

register = template.Library()


@register.filter
def get_item(d, key):
    """Retourne d[key] ou 0 si absent (pour ticket_unread_counts)."""
    if d is None:
        return 0
    return d.get(key, 0)
