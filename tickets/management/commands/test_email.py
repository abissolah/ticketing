"""
Commande pour tester l'envoi d'e-mails (notifications client).

Usage :
  python manage.py test_email                    # affiche la config et vérifie qu'un client a un email
  python manage.py test_email dest@example.com   # envoie un mail de test à cette adresse

Variables .env à vérifier :
  DEFAULT_FROM_EMAIL  (obligatoire)
  EMAIL_HOST          (obligatoire pour envoi réel, sinon backend console)
  EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand


def _load_dotenv():
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv(Path(settings.BASE_DIR) / ".env")
    except ImportError:
        pass


class Command(BaseCommand):
    help = "Affiche la config e-mail et/ou envoie un mail de test."

    def add_arguments(self, parser):
        parser.add_argument(
            "dest",
            nargs="?",
            default=None,
            help="Adresse e-mail de destination pour le mail de test (optionnel).",
        )

    def handle(self, *args, **options):
        _load_dotenv()

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        email_host = getattr(settings, "EMAIL_HOST", None)
        email_port = getattr(settings, "EMAIL_PORT", None)
        email_user = getattr(settings, "EMAIL_HOST_USER", None)
        has_password = bool(getattr(settings, "EMAIL_HOST_PASSWORD", None))
        backend = getattr(settings, "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")

        self.stdout.write("--- Configuration e-mail ---")
        self.stdout.write(f"  DEFAULT_FROM_EMAIL = {from_email!r}")
        self.stdout.write(f"  EMAIL_HOST         = {email_host!r}")
        self.stdout.write(f"  EMAIL_PORT         = {email_port!r}")
        self.stdout.write(f"  EMAIL_HOST_USER    = {email_user!r}")
        self.stdout.write(f"  EMAIL_HOST_PASSWORD défini : {has_password}")
        self.stdout.write(f"  EMAIL_BACKEND      = {backend}")

        if not email_host:
            self.stdout.write(self.style.WARNING(
                "EMAIL_HOST n'est pas défini dans .env → Django utilisera le backend par défaut (souvent console ou localhost)."
            ))
            self.stdout.write("  Ajoutez dans .env : EMAIL_HOST=smtp.votreserveur.com (et EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)")
        if not from_email:
            self.stdout.write(self.style.WARNING("DEFAULT_FROM_EMAIL n'est pas défini."))

        dest = options.get("dest")
        if dest:
            self.stdout.write("")
            self.stdout.write(f"Envoi d'un mail de test vers {dest}...")
            try:
                from django.core.mail import send_mail
                n = send_mail(
                    "[Ticketing] Mail de test",
                    "Ceci est un mail de test envoyé par la commande manage.py test_email.",
                    from_email or "noreply@example.com",
                    [dest],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f"Envoi réussi (retour={n}). Vérifiez la boîte de réception (et les spams)."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Échec envoi : {e}"))
        else:
            self.stdout.write("")
            self.stdout.write("Pour envoyer un mail de test : python manage.py test_email votre@email.com")
