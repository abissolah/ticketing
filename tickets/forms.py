from django import forms
from django_summernote.widgets import SummernoteWidget
from .models import (
    Ticket,
    TicketComment,
    ClientMember,
    Collaborateur,
    PRIORITY_CHOICES,
    STATUS_CHOICES,
    TYPE_CHOICES,
)
from .utils import get_user_client, get_user_collaborateur, get_clients_for_collaborateur


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "title",
            "description",
            "member",
            "priority",
            "type",
            "status",
            "archived",
            "assigned_to",
            "estimated_time",
            "actual_time",
        ]
        widgets = {
            "description": SummernoteWidget(),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "member": forms.Select(attrs={"class": "form-select select2"}),
            "priority": forms.Select(attrs={"class": "form-select select2"}),
            "type": forms.Select(attrs={"class": "form-select select2"}),
            "status": forms.Select(attrs={"class": "form-select select2"}),
            "archived": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "assigned_to": forms.Select(attrs={"class": "form-select select2"}),
            "estimated_time": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01", "placeholder": "ex. 1,50"}),
            "actual_time": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01", "placeholder": "ex. 1,50"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.client = kwargs.pop("client", None)
        self.collaborateur = kwargs.pop("collaborateur", None)
        super().__init__(*args, **kwargs)
        if self.client:
            self.fields["member"].queryset = ClientMember.objects.filter(
                client=self.client
            ).order_by("last_name", "first_name")
            self.fields["member"].required = True
            # Client ne peut pas modifier assigned_to, status (sauf peut-être demander annulation)
            if not self.collaborateur:
                self.fields.pop("assigned_to", None)
                self.fields.pop("estimated_time", None)
                self.fields.pop("actual_time", None)
                self.fields.pop("archived", None)
                # Status: limit to few choices for client if we allow
                if "status" in self.fields:
                    self.fields["status"].choices = [
                        c for c in STATUS_CHOICES
                        if c[0] in ("created", "assigned", "in_progress", "delivered_preprod", "delivered_prod", "validated", "cancelled")
                    ]
        if self.collaborateur:
            self.fields["assigned_to"].queryset = Collaborateur.objects.filter(
                prestataire=self.collaborateur.prestataire
            ).order_by("last_name", "first_name")
            # En édition : limiter les membres à ceux du client du ticket
            if self.instance and self.instance.pk and getattr(self.instance, "client_id", None):
                self.fields["member"].queryset = ClientMember.objects.filter(
                    client_id=self.instance.client_id
                ).order_by("last_name", "first_name")
            self.fields["member"].required = False


class TicketCreateForm(forms.ModelForm):
    """Form for creating a ticket (client field set in view for collaborateur)."""
    class Meta:
        model = Ticket
        fields = ["title", "description", "member", "priority", "type"]
        widgets = {
            "description": SummernoteWidget(),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "member": forms.Select(attrs={"class": "form-select select2"}),
            "priority": forms.Select(attrs={"class": "form-select select2"}),
            "type": forms.Select(attrs={"class": "form-select select2"}),
        }

    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop("client", None)
        self.collaborateur = kwargs.pop("collaborateur", None)
        super().__init__(*args, **kwargs)
        if self.client:
            self.fields["member"].queryset = ClientMember.objects.filter(
                client=self.client
            ).order_by("last_name", "first_name")
        if self.collaborateur:
            qs = get_clients_for_collaborateur(self.collaborateur)
            self.fields["client"] = forms.ModelChoiceField(
                queryset=qs,
                label="Client",
                widget=forms.Select(attrs={"class": "form-select select2", "id": "id_client"}),
            )
            self.fields["member"].required = False
            self.fields["member"].queryset = ClientMember.objects.none()
            self.fields["member"].widget.attrs["id"] = "id_member"

    def clean_member(self):
        member = self.cleaned_data.get("member")
        client = self.cleaned_data.get("client") or self.client
        if client and member and member.client_id != client.id:
            raise forms.ValidationError("Ce membre n'appartient pas au client choisi.")
        return member


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ["content"]
        widgets = {
            "content": SummernoteWidget(attrs={"summernote": {"height": 150}}),
        }


class TicketAttachmentForm(forms.Form):
    file = forms.FileField(label="Fichier", widget=forms.FileInput(attrs={"class": "form-control"}))
