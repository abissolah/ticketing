from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Prestataire(models.Model):
    """Société prestataire (cabinet / agence)."""
    name = models.CharField("Nom", max_length=200)

    class Meta:
        verbose_name = "Prestataire"
        verbose_name_plural = "Prestataires"

    def __str__(self):
        return self.name


class Client(models.Model):
    """Société cliente (un compte User par client)."""
    prestataire = models.ForeignKey(
        "Prestataire",
        on_delete=models.CASCADE,
        related_name="clients",
        null=True,
        blank=True,
    )
    name = models.CharField("Nom de la société", max_length=200)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        return self.name


class ClientMember(models.Model):
    """Membre d'une société cliente (profil pour qualifier qui a créé le ticket)."""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="members")
    email = models.EmailField()
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)
    color = models.CharField("Couleur", max_length=7, default="#6c757d")  # hex

    class Meta:
        verbose_name = "Membre client"
        verbose_name_plural = "Membres client"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.client.name})"


class Collaborateur(models.Model):
    """Collaborateur du prestataire (un compte User par collaborateur)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collaborateur_profile",
    )
    prestataire = models.ForeignKey(
        Prestataire, on_delete=models.CASCADE, related_name="collaborateurs"
    )
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)
    function = models.CharField("Fonction", max_length=150, blank=True)
    clients = models.ManyToManyField(
        Client, related_name="collaborateurs", blank=True, verbose_name="Clients assignés"
    )
    is_prestataire_admin = models.BooleanField(
        "Admin prestataire (création clients/collaborateurs)",
        default=False,
    )

    class Meta:
        verbose_name = "Collaborateur"
        verbose_name_plural = "Collaborateurs"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.prestataire.name})"

    @property
    def display_name(self):
        return f"{self.first_name} {self.last_name}"


PRIORITY_CHOICES = [
    ("low", "Basse"),
    ("medium", "Moyenne"),
    ("high", "Haute"),
]

STATUS_CHOICES = [
    ("created", "Non affecté"),
    ("assigned", "Affecté"),
    ("in_progress", "En cours"),
    ("delivered_preprod", "Livré préprod"),
    ("delivered_prod", "Livré prod"),
    ("validated", "Validé"),
    ("archived", "Archivé"),
    ("cancelled", "Annulé"),
]

TYPE_CHOICES = [
    ("bug", "Bug"),
    ("evol", "Évolution"),
    ("exploit", "Exploitation"),
]


class Ticket(models.Model):
    title = models.CharField("Titre", max_length=300)
    description = models.TextField("Description", blank=True)  # HTML (Summernote)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tickets")
    member = models.ForeignKey(
        ClientMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
        verbose_name="Membre initiateur",
    )
    priority = models.CharField(
        "Priorité", max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour", auto_now=True)
    status = models.CharField(
        "Statut", max_length=30, choices=STATUS_CHOICES, default="created"
    )
    type = models.CharField(
        "Type", max_length=20, choices=TYPE_CHOICES, default="bug"
    )
    assigned_to = models.ForeignKey(
        "Collaborateur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="Affecté à",
    )
    # Champs prestataire
    estimated_time = models.DecimalField(
        "Temps prévu (jours)",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
    )
    actual_time = models.DecimalField(
        "Temps effectif (jours)",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tickets",
    )

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_validated(self):
        return self.status == "validated"

    @property
    def is_archived(self):
        return self.status == "archived"

    @property
    def member_color(self):
        if not self.member:
            return "#6c757d"
        c = (self.member.color or "").strip()
        if not c:
            return "#6c757d"
        if not c.startswith("#"):
            c = "#" + c
        return c

    @property
    def member_color_bg(self):
        """Couleur de fond en rgba pour la ligne (compatible tous navigateurs)."""
        hex_c = self.member_color.lstrip("#")
        if len(hex_c) == 6:
            try:
                r = int(hex_c[0:2], 16)
                g = int(hex_c[2:4], 16)
                b = int(hex_c[4:6], 16)
                return f"rgba({r}, {g}, {b}, 0.15)"
            except ValueError:
                pass
        return "rgba(108, 117, 125, 0.15)"

    @property
    def priority_hex(self):
        return {"low": "#198754", "medium": "#fd7e14", "high": "#dc3545"}.get(
            self.priority, "#6c757d"
        )

    @property
    def priority_select_style(self):
        """Style pour le select priorité : fond + texte (high rouge, medium orange, low vert clair)."""
        styles = {
            "low": "background-color: #d4edda !important; color: #155724 !important;",
            "medium": "background-color: #fd7e14 !important; color: #fff !important;",
            "high": "background-color: #dc3545 !important; color: #fff !important;",
        }
        return styles.get(self.priority, "")


class TicketComment(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ticket_comments"
    )
    content = models.TextField("Contenu")  # HTML
    created_at = models.DateTimeField("Date", auto_now_add=True)

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ["created_at"]

    def __str__(self):
        return f"Commentaire #{self.ticket_id} par {self.author}"


def ticket_attachment_upload_to(instance, filename):
    if instance.comment_id:
        return f"tickets/{instance.ticket_id}/comments/{instance.comment_id}/{filename}"
    return f"tickets/{instance.ticket_id}/attachments/{filename}"


class TicketAttachment(models.Model):
    """Pièce jointe sur un ticket (description ou commentaire)."""
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="attachments"
    )
    comment = models.ForeignKey(
        TicketComment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="attachments",
    )
    file = models.FileField("Fichier", upload_to=ticket_attachment_upload_to)
    name = models.CharField("Nom", max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
