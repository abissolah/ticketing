from django import template
from django.utils.html import strip_tags

register = template.Library()


@register.filter
def get_item(d, key):
    """Retourne d[key] ou 0 si absent (pour ticket_unread_counts)."""
    if d is None:
        return 0
    return d.get(key, 0)


@register.filter
def description_preview(html_content, max_len=400):
    """Retourne un extrait texte de la description (sans HTML), tronqué à max_len caractères."""
    if not html_content:
        return "Aucune description."
    text = strip_tags(html_content).strip()
    text = " ".join(text.split())
    if not text:
        return "Aucune description."
    if len(text) > max_len:
        return text[: max_len - 3].rstrip() + "..."
    return text
