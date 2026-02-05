"""
Commande pour récupérer les e-mails depuis une boîte IMAP et créer des tickets.

Configuration (variables d'environnement ou .env) :
- EMAIL_IMAP_HOST (ex. imap.example.com)
- EMAIL_IMAP_PORT (optionnel, défaut 993)
- EMAIL_IMAP_USER (adresse de la boîte qui reçoit les mails)
- EMAIL_IMAP_PASSWORD
- EMAIL_IMAP_MAILBOX (optionnel, défaut INBOX)
- EMAIL_IMAP_USE_SSL (optionnel, défaut true)

À lancer par cron toutes les 1 à 5 minutes, ex. :
  */5 * * * * cd /var/www/tickets/ticketing && .venv/bin/python manage.py fetch_email_tickets
"""
import email
import imaplib
import logging
import os
from email.header import decode_header
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from tickets.email_receiver import create_ticket_from_email

# Charger le .env au démarrage de la commande (pour que os.environ soit rempli)
def _load_dotenv():
    try:
        from dotenv import load_dotenv
        base_dir = getattr(settings, "BASE_DIR", None)
        if base_dir is None:
            # commands/fetch_email_tickets.py -> management -> tickets -> racine projet
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
        env_path = Path(base_dir) / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except Exception:
        pass
_load_dotenv()

logger = logging.getLogger(__name__)


def decode_mime_header(s):
    """Décode un en-tête MIME (sujet, from, etc.)."""
    if not s:
        return ""
    parts = decode_header(s)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result).strip()


def get_body_text(msg):
    """Extrait le corps texte du message (plain text de préférence)."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    body = part.get_payload(decode=True)
                    if body:
                        body = body.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
                except Exception:
                    pass
        if not body and msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    try:
                        body = part.get_payload(decode=True)
                        if body:
                            body = body.decode(part.get_content_charset() or "utf-8", errors="replace")
                        if body:
                            body = body.replace("<", " <").replace(">", "> ")[:50000]
                        break
                    except Exception:
                        pass
    else:
        try:
            body = msg.get_payload(decode=True)
            if body:
                body = body.decode(msg.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            body = str(msg.get_payload() or "")[:50000]
    return (body or "")[:50000]


def get_from_address(msg):
    """Retourne l'adresse e-mail de l'expéditeur (From)."""
    from_header = msg.get("From", "")
    decoded = decode_mime_header(from_header)
    if "<" in decoded and ">" in decoded:
        start = decoded.index("<") + 1
        end = decoded.index(">")
        return decoded[start:end].strip().lower()
    return decoded.strip().lower() if decoded else ""


# Limite taille pièce jointe (10 Mo), max 20 pièces (aligné avec email_receiver)
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_ATTACHMENTS = 20


def get_attachments(msg):
    """Extrait les pièces jointes du message. Retourne une liste de (filename, bytes)."""
    result = []
    if not msg.is_multipart():
        return result
    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue
        filename = decode_mime_header(filename)
        if not filename:
            filename = "piece_jointe"
        try:
            content = part.get_payload(decode=True)
            if not content or len(content) > MAX_ATTACHMENT_SIZE:
                continue
            result.append((filename, content))
            if len(result) >= MAX_ATTACHMENTS:
                break
        except Exception:
            continue
    return result


class Command(BaseCommand):
    help = "Récupère les e-mails non lus sur la boîte IMAP configurée et crée des tickets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les mails sans créer de tickets.",
        )
        parser.add_argument(
            "--mark-read",
            action="store_true",
            default=True,
            help="Marquer les messages comme lus (défaut: True).",
        )
        parser.add_argument(
            "--no-mark-read",
            action="store_false",
            dest="mark_read",
            help="Ne pas marquer les messages comme lus.",
        )

    def _get_imap_config(self):
        """Lit la config IMAP depuis os.environ ou Django settings."""
        def get(key, default=""):
            v = os.environ.get(key)
            if v is not None and str(v).strip():
                return str(v).strip()
            return getattr(settings, key, default) or default
        return {
            "host": get("EMAIL_IMAP_HOST"),
            "user": get("EMAIL_IMAP_USER"),
            "password": get("EMAIL_IMAP_PASSWORD"),
            "port": int(get("EMAIL_IMAP_PORT") or "993"),
            "mailbox": get("EMAIL_IMAP_MAILBOX") or "INBOX",
            "use_ssl": (get("EMAIL_IMAP_USE_SSL") or "true").lower() in ("true", "1", "yes"),
        }

    def handle(self, *args, **options):
        config = self._get_imap_config()
        host = config["host"]
        user = config["user"]
        password = config["password"]
        if not all([host, user, password]):
            self.stderr.write(
                self.style.ERROR(
                    "Configurez EMAIL_IMAP_HOST, EMAIL_IMAP_USER, EMAIL_IMAP_PASSWORD dans le fichier .env "
                    "(à la racine du projet, à côté de manage.py)."
                )
            )
            return

        port = config["port"]
        mailbox = config["mailbox"]
        use_ssl = config["use_ssl"]

        dry_run = options["dry_run"]
        mark_read = options["mark_read"]

        try:
            if use_ssl:
                conn = imaplib.IMAP4_SSL(host, port=port)
            else:
                conn = imaplib.IMAP4(host, port=port)
            conn.login(user, password)
            conn.select(mailbox, readonly=False)
            typ, data = conn.search(None, "UNSEEN")
            if typ != "OK":
                self.stdout.write("Aucun message non lu ou erreur search.")
                conn.logout()
                return

            ids = data[0].split()
            if not ids:
                self.stdout.write("Aucun message non lu.")
                conn.logout()
                return

            created = 0
            errors = 0
            for uid in ids:
                try:
                    typ, msg_data = conn.fetch(uid, "(RFC822)")
                    if typ != "OK" or not msg_data:
                        continue
                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)
                    from_addr = get_from_address(msg)
                    subject = decode_mime_header(msg.get("Subject", ""))
                    body = get_body_text(msg)
                    message_id = (msg.get("Message-ID") or "").strip() or None
                    attachments = get_attachments(msg)

                    if dry_run:
                        pj = f", {len(attachments)} PJ" if attachments else ""
                        self.stdout.write(f"  [DRY-RUN] De: {from_addr} | Sujet: {subject[:60]}{pj}")
                        continue

                    ticket, err = create_ticket_from_email(
                        from_addr, subject, body, message_id=message_id, attachments=attachments
                    )
                    if ticket:
                        created += 1
                        pj = f", {len(attachments)} PJ" if attachments else ""
                        self.stdout.write(self.style.SUCCESS(f"  Ticket #{ticket.id} créé (de {from_addr}{pj})"))
                    else:
                        errors += 1
                        self.stdout.write(self.style.WARNING(f"  Ignoré: {err}"))

                    if mark_read:
                        conn.store(uid, "+FLAGS", "\\Seen")
                except Exception as e:
                    errors += 1
                    logger.exception("Erreur traitement message %s: %s", uid, e)
                    self.stdout.write(self.style.ERROR(f"  Erreur: {e}"))

            conn.logout()
            self.stdout.write(self.style.SUCCESS(f"Terminé: {created} ticket(s) créé(s), {errors} ignoré(s)/erreur(s)."))
        except imaplib.IMAP4.error as e:
            self.stderr.write(self.style.ERROR(f"Erreur IMAP: {e}"))
        except Exception as e:
            logger.exception("Erreur fetch_email_tickets: %s", e)
            self.stderr.write(self.style.ERROR(str(e)))
