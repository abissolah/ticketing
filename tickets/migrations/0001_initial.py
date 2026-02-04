# Generated manually for tickets app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Prestataire",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Nom")),
            ],
            options={
                "verbose_name": "Prestataire",
                "verbose_name_plural": "Prestataires",
            },
        ),
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Nom de la société")),
                ("prestataire", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="clients", to="tickets.prestataire")),
                ("user", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="client_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Client",
                "verbose_name_plural": "Clients",
            },
        ),
        migrations.CreateModel(
            name="ClientMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254)),
                ("first_name", models.CharField(max_length=100, verbose_name="Prénom")),
                ("last_name", models.CharField(max_length=100, verbose_name="Nom")),
                ("color", models.CharField(default="#6c757d", max_length=7, verbose_name="Couleur")),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="members", to="tickets.client")),
            ],
            options={
                "verbose_name": "Membre client",
                "verbose_name_plural": "Membres client",
                "ordering": ["last_name", "first_name"],
            },
        ),
        migrations.CreateModel(
            name="Collaborateur",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=100, verbose_name="Prénom")),
                ("last_name", models.CharField(max_length=100, verbose_name="Nom")),
                ("function", models.CharField(blank=True, max_length=150, verbose_name="Fonction")),
                ("is_prestataire_admin", models.BooleanField(default=False, verbose_name="Admin prestataire (création clients/collaborateurs)")),
                ("clients", models.ManyToManyField(blank=True, related_name="collaborateurs", to="tickets.client", verbose_name="Clients assignés")),
                ("prestataire", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="collaborateurs", to="tickets.prestataire")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="collaborateur_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Collaborateur",
                "verbose_name_plural": "Collaborateurs",
                "ordering": ["last_name", "first_name"],
            },
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=300, verbose_name="Titre")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("priority", models.CharField(choices=[("low", "Basse"), ("medium", "Moyenne"), ("high", "Haute")], default="medium", max_length=20, verbose_name="Priorité")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Date de création")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Mise à jour")),
                ("status", models.CharField(choices=[("created", "Non affecté"), ("assigned", "Affecté"), ("in_progress", "En cours"), ("delivered_preprod", "Livré préprod"), ("delivered_prod", "Livré prod"), ("validated", "Validé"), ("archived", "Archivé"), ("cancelled", "Annulé")], default="created", max_length=30, verbose_name="Statut")),
                ("type", models.CharField(choices=[("bug", "Bug"), ("evol", "Évolution"), ("exploit", "Exploitation")], default="evol", max_length=20, verbose_name="Type")),
                ("estimated_time", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name="Temps prévu (h)")),
                ("actual_time", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name="Temps effectif (h)")),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_tickets", to="tickets.collaborateur", verbose_name="Affecté à")),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to="tickets.client")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_tickets", to=settings.AUTH_USER_MODEL)),
                ("member", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tickets", to="tickets.clientmember", verbose_name="Membre initiateur")),
            ],
            options={
                "verbose_name": "Ticket",
                "verbose_name_plural": "Tickets",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField(verbose_name="Contenu")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Date")),
                ("author", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ticket_comments", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="tickets.ticket")),
            ],
            options={
                "verbose_name": "Commentaire",
                "verbose_name_plural": "Commentaires",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="tickets/attachments/", verbose_name="Fichier")),
                ("name", models.CharField(blank=True, max_length=255, verbose_name="Nom")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("comment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="tickets.ticketcomment")),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="tickets.ticket")),
            ],
            options={
                "verbose_name": "Pièce jointe",
                "verbose_name_plural": "Pièces jointes",
            },
        ),
    ]
