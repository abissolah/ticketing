"""
Notifications e-mail au client : nouveau commentaire (par un collaborateur)
ou changement de statut (livré prod / validé) par un collaborateur.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    "delivered_prod": "Livré en production",
    "validated": "Validé",
}


def get_client_email(ticket):
    """
    Retourne l'adresse e-mail à notifier : en priorité le membre initiateur du ticket
    (ticket.member.email), sinon le compte client (ticket.client.user.email).
    """
    if not ticket or not ticket.client_id:
        return None
    # Priorité : membre initiateur du ticket (a toujours un email)
    member = getattr(ticket, "member", None)
    if member and getattr(member, "email", None):
        email = (member.email or "").strip()
        if email:
            return email
    # Sinon : compte utilisateur du client
    user = getattr(ticket.client, "user", None)
    if not user:
        return None
    email = getattr(user, "email", None) or ""
    return email.strip() or None


def _build_absolute_uri(request, path):
    """Construit l'URL absolue du ticket (pour le lien dans le mail)."""
    if request:
        return request.build_absolute_uri(path)
    # Fallback si pas de request (ex. depuis une commande)
    from django.contrib.sites.models import Site
    try:
        domain = Site.objects.get_current().domain
        scheme = "https" if getattr(settings, "SECURE_SSL_REDIRECT", False) else "http"
        return f"{scheme}://{domain}{path}"
    except Exception:
        return path


def notify_client_new_comment(ticket, comment, request=None):
    """
    Envoie un e-mail au client quand un collaborateur ajoute un commentaire.
    """
    email = get_client_email(ticket)
    if not email:
        logger.warning(
            "Notification commentaire non envoyée (ticket %s) : pas d'e-mail (ni membre initiateur, ni compte client) pour client_id=%s.",
            ticket.pk,
            getattr(ticket, "client_id", None),
        )
        return
    author_name = "Un collaborateur"
    if comment.author_id and comment.author:
        fn = getattr(comment.author, "get_full_name", None)
        author_name = (fn() if callable(fn) else None) or getattr(comment.author, "username", None) or author_name
    path = reverse("tickets:detail", kwargs={"pk": ticket.pk})
    url = _build_absolute_uri(request, path)
    subject = f"[Ticket #{ticket.pk}] Nouveau commentaire : {ticket.title}"
    # Contenu texte court (pas de HTML pour éviter les soucis)
    content_preview = strip_tags(comment.content or "")[:300]
    if len((comment.content or "")) > 300:
        content_preview += "..."
    body = f"""Bonjour,

{author_name} a ajouté un commentaire sur le ticket #{ticket.pk} :

  {ticket.title}

Commentaire :
{content_preview}

Voir le ticket et répondre : {url}

—
Cet e-mail a été envoyé automatiquement par l'application de ticketing."""
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    logger.info("Envoi notification commentaire (ticket %s) vers %s, from=%s.", ticket.pk, email, from_email)
    try:
        sent = send_mail(
            subject,
            body,
            from_email,
            [email],
            fail_silently=True,
        )
        if sent:
            logger.info("Notification commentaire envoyée au client pour le ticket %s.", ticket.pk)
        else:
            logger.warning(
                "Notification commentaire non envoyée (ticket %s) : send_mail a retourné 0. Vérifiez EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD dans .env.",
                ticket.pk,
            )
    except Exception as e:
        logger.exception("Échec envoi notification commentaire (ticket %s) : %s", ticket.pk, e)


def notify_client_status_changed(ticket, new_status, request=None):
    """
    Envoie un e-mail au client quand le statut passe à « Livré prod » ou « Validé »
    (action faite par un collaborateur).
    """
    if new_status not in ("delivered_prod", "validated"):
        return
    email = get_client_email(ticket)
    if not email:
        logger.warning(
            "Notification statut non envoyée (ticket %s) : pas d'e-mail (ni membre initiateur, ni compte client) pour client_id=%s.",
            ticket.pk,
            getattr(ticket, "client_id", None),
        )
        return
    label = STATUS_LABELS.get(new_status, new_status)
    path = reverse("tickets:detail", kwargs={"pk": ticket.pk})
    url = _build_absolute_uri(request, path)
    subject = f"[Ticket #{ticket.pk}] Statut : {label} — {ticket.title}"
    body = f"""Bonjour,

Le statut du ticket #{ticket.pk} a été mis à jour :

  {ticket.title}

Nouveau statut : {label}

Voir le ticket : {url}

—
Cet e-mail a été envoyé automatiquement par l'application de ticketing."""
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    logger.info("Envoi notification statut '%s' (ticket %s) vers %s, from=%s.", new_status, ticket.pk, email, from_email)
    try:
        sent = send_mail(
            subject,
            body,
            from_email,
            [email],
            fail_silently=True,
        )
        if sent:
            logger.info("Notification statut '%s' envoyée au client pour le ticket %s.", new_status, ticket.pk)
        else:
            logger.warning(
                "Notification statut non envoyée (ticket %s) : send_mail a retourné 0. Vérifiez EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD.",
                ticket.pk,
            )
    except Exception as e:
        logger.exception("Échec envoi notification statut (ticket %s) : %s", ticket.pk, e)
