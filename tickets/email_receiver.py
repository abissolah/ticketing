"""
Création de tickets à partir d'e-mails entrants.
Règles : sujet → type ([bug], [evol], [exploit]), expéditeur → membre client.
Pièces jointes du mail enregistrées en TicketAttachment (sans commentaire).
"""
import html
import logging
import os
import re

from django.core.files.base import ContentFile
from django.db import transaction

from .models import ClientMember, InboundEmail, Ticket, TicketAttachment

# Taille max par pièce jointe (10 Mo), max 20 pièces
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_ATTACHMENTS = 20

logger = logging.getLogger(__name__)

TYPE_TAGS = [
    ("[bug]", "bug"),
    ("[evol]", "evol"),
    ("[exploit]", "exploit"),
]

DEFAULT_TYPE = "bug"
DEFAULT_PRIORITY = "medium"


def parse_type_and_title(subject):
    """
    Extrait le type depuis le sujet (balises [bug], [evol], [exploit])
    et retourne un titre nettoyé (sans ces balises).
    Retourne (type, title_clean).
    """
    if not subject:
        return DEFAULT_TYPE, ""
    subject = subject.strip()
    ticket_type = DEFAULT_TYPE
    title_clean = subject
    for tag, t in TYPE_TAGS:
        if tag.lower() in subject.lower():
            ticket_type = t
            title_clean = re.sub(re.escape(tag), "", title_clean, flags=re.IGNORECASE)
    title_clean = re.sub(r"\s+", " ", title_clean).strip()
    return ticket_type, title_clean or subject[:300]


def body_to_html(body_plain):
    """Convertit un corps de mail texte en HTML pour la description (échappement XSS)."""
    if not body_plain:
        return ""
    escaped = html.escape(body_plain)
    return f"<p>{escaped.replace(chr(10), '</p><p>')}</p>"


def _sanitize_filename(name):
    """Garde un nom de fichier sûr (évite path traversal)."""
    if not name or not name.strip():
        return "piece_jointe"
    name = os.path.basename(name).strip()
    if not name:
        return "piece_jointe"
    return name[:255]


def create_ticket_from_email(from_email, subject, body_plain, message_id=None, attachments=None):
    """
    Crée un ticket à partir d'un e-mail reçu.

    - from_email : adresse de l'expéditeur (doit correspondre à un ClientMember.email)
    - subject : sujet du mail (peut contenir [bug], [evol], [exploit] pour le type)
    - body_plain : corps du mail (texte brut)
    - message_id : Message-ID du mail (optionnel, évite les doublons)
    - attachments : liste de (filename, bytes) ou None ; enregistrées en TicketAttachment (description)

    Retourne (ticket, error_message).
    Si succès : (ticket, None).
    Si erreur : (None, "message d'erreur").
    """
    from_email = (from_email or "").strip().lower()
    if not from_email:
        return None, "Adresse expéditeur vide"

    # Déjà traité ?
    if message_id:
        existing = InboundEmail.objects.filter(message_id=message_id).first()
        if existing:
            return existing.ticket, "Déjà traité (message_id connu)"

    # Trouver le membre par e-mail (insensible à la casse)
    member = ClientMember.objects.filter(email__iexact=from_email).select_related("client").first()
    if not member:
        logger.warning("E-mail entrant ignoré : aucun membre avec l'adresse %s", from_email)
        return None, f"Aucun membre client avec l'adresse {from_email}"

    client = member.client
    ticket_type, title = parse_type_and_title(subject or "")
    if len(title) > 300:
        title = title[:297] + "..."

    description = body_to_html(body_plain or "")

    attachments = attachments or []
    if len(attachments) > MAX_ATTACHMENTS:
        attachments = attachments[:MAX_ATTACHMENTS]

    try:
        with transaction.atomic():
            ticket = Ticket.objects.create(
                title=title or "(Sans titre)",
                description=description,
                client=client,
                member=member,
                priority=DEFAULT_PRIORITY,
                status="created",
                type=ticket_type,
                created_by=None,
            )
            if message_id:
                InboundEmail.objects.create(
                    message_id=message_id,
                    ticket=ticket,
                    from_email=from_email,
                    subject=subject or "",
                )
            for filename, content in attachments:
                if not isinstance(content, bytes):
                    content = content.read() if hasattr(content, "read") else b""
                if len(content) > MAX_ATTACHMENT_SIZE:
                    logger.warning("Pièce jointe %s ignorée (trop volumineuse)", filename)
                    continue
                safe_name = _sanitize_filename(filename)
                TicketAttachment.objects.create(
                    ticket=ticket,
                    comment=None,
                    file=ContentFile(content, name=safe_name),
                    name=safe_name,
                )
            logger.info(
                "Ticket #%s créé depuis e-mail de %s (sujet: %s, %s PJ)",
                ticket.id, from_email, subject, len(attachments),
            )
            return ticket, None
    except Exception as e:
        logger.exception("Erreur création ticket depuis e-mail: %s", e)
        return None, str(e)
