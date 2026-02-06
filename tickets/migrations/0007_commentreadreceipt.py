# Generated manually for CommentReadReceipt (pastille commentaires non lus)

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tickets', '0006_alter_ticket_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentReadReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('read_at', models.DateTimeField(auto_now_add=True, verbose_name='Lu le')),
                ('comment', models.ForeignKey(on_delete=models.CASCADE, related_name='read_receipts', to='tickets.ticketcomment')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='comment_read_receipts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': "Lecture d'un commentaire",
                'verbose_name_plural': 'Lectures des commentaires',
            },
        ),
        migrations.AddConstraint(
            model_name='commentreadreceipt',
            constraint=models.UniqueConstraint(fields=('comment', 'user'), name='tickets_commentreadreceipt_comment_user_unique'),
        ),
    ]
