# Migration: remplacer le statut "archived" par un champ booléen archived

from django.db import migrations, models


def migrate_archived_status(apps, schema_editor):
    """Pour les tickets ayant status='archived', mettre archived=True et status='validated'."""
    Ticket = apps.get_model("tickets", "Ticket")
    Ticket.objects.filter(status="archived").update(archived=True, status="validated")


def noop_reverse(apps, schema_editor):
    """Pas de retour arrière automatique (on ne recrée pas status='archived')."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0004_inboundemail"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="archived",
            field=models.BooleanField(default=False, verbose_name="Archivé"),
        ),
        migrations.RunPython(migrate_archived_status, noop_reverse),
    ]
