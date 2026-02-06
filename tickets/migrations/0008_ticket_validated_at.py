# Generated manually for Ticket.validated_at

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0007_commentreadreceipt"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="validated_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Renseigné automatiquement lorsque le statut passe à Validé.",
                null=True,
                verbose_name="Date de validation",
            ),
        ),
    ]
