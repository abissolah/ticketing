# Generated for email receiver (InboundEmail)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0003_alter_ticket_actual_time_alter_ticket_estimated_time_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="InboundEmail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message_id", models.CharField(db_index=True, max_length=500, unique=True, verbose_name="Message-ID")),
                ("from_email", models.EmailField(max_length=254, verbose_name="Expéditeur")),
                ("subject", models.CharField(blank=True, max_length=500, verbose_name="Sujet")),
                ("received_at", models.DateTimeField(auto_now_add=True, verbose_name="Reçu le")),
                (
                    "ticket",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inbound_emails",
                        to="tickets.ticket",
                    ),
                ),
            ],
            options={
                "verbose_name": "E-mail entrant",
                "verbose_name_plural": "E-mails entrants",
                "ordering": ["-received_at"],
            },
        ),
    ]
