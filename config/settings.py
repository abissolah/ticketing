"""
Django settings for ticketing SaaS - Django 5.2 LTS
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Charger le fichier .env en production si présent (optionnel)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-production")

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_filters",
    "django_summernote",
    "tickets",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de données : PostgreSQL en production (variables d'env), SQLite en dev
if os.environ.get("DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "ticketing_db"),
            "USER": os.environ.get("DB_USER", "app"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "tickets:login"
LOGIN_REDIRECT_URL = "tickets:home"
LOGOUT_REDIRECT_URL = "tickets:login"

# Summernote WYSIWYG
SUMMERNOTE_CONFIG = {
    "summernote": {
        "width": "100%",
        "height": "300",
        "toolbar": [
            ["style", ["style"]],
            ["font", ["bold", "italic", "underline"]],
            ["para", ["ul", "ol", "paragraph"]],
            ["insert", ["link", "picture"]],
            ["view", ["codeview"]],
        ],
    },
}

# Priority colors for UI
TICKET_PRIORITY_COLORS = {
    "low": "#198754",
    "medium": "#fd7e14",
    "high": "#dc3545",
}

# Réception e-mails → création de tickets
# IMAP (commande fetch_email_tickets)
EMAIL_IMAP_HOST = os.environ.get("EMAIL_IMAP_HOST", "")
EMAIL_IMAP_PORT = int(os.environ.get("EMAIL_IMAP_PORT", "993"))
EMAIL_IMAP_USER = os.environ.get("EMAIL_IMAP_USER", "")
EMAIL_IMAP_PASSWORD = os.environ.get("EMAIL_IMAP_PASSWORD", "")
EMAIL_IMAP_MAILBOX = os.environ.get("EMAIL_IMAP_MAILBOX", "INBOX")
EMAIL_IMAP_USE_SSL = os.environ.get("EMAIL_IMAP_USE_SSL", "true").lower() in ("true", "1", "yes")
# Webhook (Mailgun / SendGrid) — secret pour authentifier les POST
EMAIL_WEBHOOK_SECRET = os.environ.get("EMAIL_WEBHOOK_SECRET", "")

# Envoi d'e-mails (notifications client : commentaires, statut)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Ticketing <noreply@example.com>")
# Optionnel : SMTP (si non défini, Django utilise le backend console en dev)
if os.environ.get("EMAIL_HOST"):
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
