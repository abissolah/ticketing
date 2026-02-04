import django_filters
from django import forms
from .models import Ticket, PRIORITY_CHOICES, STATUS_CHOICES, TYPE_CHOICES

INPUT_CLASS = "form-control form-control-sm"
SELECT_CLASS = "form-select form-select-sm"


class TicketFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=STATUS_CHOICES,
        widget=forms.SelectMultiple(attrs={"class": SELECT_CLASS + " select2-multi"}),
        label="Statut",
    )
    priority = django_filters.MultipleChoiceFilter(
        choices=PRIORITY_CHOICES,
        widget=forms.SelectMultiple(attrs={"class": SELECT_CLASS + " select2-multi"}),
        label="Priorité",
    )
    type = django_filters.MultipleChoiceFilter(
        choices=TYPE_CHOICES,
        widget=forms.SelectMultiple(attrs={"class": SELECT_CLASS + " select2-multi"}),
        label="Type",
    )
    member = django_filters.ModelChoiceFilter(
        queryset=None,
        label="Membre",
        empty_label="Tous les membres",
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )
    assigned_to = django_filters.ModelChoiceFilter(
        queryset=None,
        label="Affecté à",
        empty_label="Tous",
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )
    date_after = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Créé après",
        widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLASS}),
    )
    date_before = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Créé avant",
        widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLASS}),
    )
    search = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
        label="Recherche (titre)",
        widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Titre..."}),
    )

    def __init__(self, *args, **kwargs):
        self.client_ids = kwargs.pop("client_ids", None)
        self.collaborateur = kwargs.pop("collaborateur", None)
        super().__init__(*args, **kwargs)
        from .models import ClientMember, Collaborateur
        if self.client_ids is not None:
            self.filters["member"].queryset = ClientMember.objects.filter(
                client_id__in=self.client_ids
            ).order_by("last_name", "first_name")
        if self.collaborateur is not None:
            qs = Collaborateur.objects.filter(
                prestataire=self.collaborateur.prestataire
            )
            self.filters["assigned_to"].queryset = qs.order_by("last_name", "first_name")
        else:
            self.filters["assigned_to"].queryset = Collaborateur.objects.none()

    class Meta:
        model = Ticket
        fields = []
