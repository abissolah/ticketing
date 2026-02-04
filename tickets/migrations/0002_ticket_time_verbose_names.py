# Update verbose names for time fields to "jours"

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ticket",
            name="estimated_time",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=6,
                null=True,
                verbose_name="Temps prévu (jours)",
            ),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="actual_time",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=6,
                null=True,
                verbose_name="Temps effectif (jours)",
            ),
        ),
    ]
