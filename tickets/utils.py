"""Helpers for role and ticket visibility."""
from .models import Client, Collaborateur, Ticket


def get_user_client(user):
    """Return the Client profile for this user if they are a client, else None."""
    if not user or not user.is_authenticated:
        return None
    return getattr(user, "client_profile", None)


def get_user_collaborateur(user):
    """Return the Collaborateur profile for this user if they are a collaborator, else None."""
    if not user or not user.is_authenticated:
        return None
    return getattr(user, "collaborateur_profile", None)


def user_is_client(user):
    return get_user_client(user) is not None


def user_is_collaborateur(user):
    return get_user_collaborateur(user) is not None


def user_is_prestataire_admin(user):
    collab = get_user_collaborateur(user)
    return collab is not None and collab.is_prestataire_admin


def get_visible_tickets_queryset(user):
    """
    Return base queryset of tickets the user is allowed to see.
    Excludes archived by default; call .filter(status='archived') if needed.
    """
    client = get_user_client(user)
    collab = get_user_collaborateur(user)

    if client:
        return Ticket.objects.filter(client=client).exclude(status="archived")
    if collab:
        # Union : clients du prestataire + clients assignés au collaborateur (au cas où un client n'a pas de prestataire)
        ids_prestataire = set(
            collab.prestataire.clients.values_list("id", flat=True)
        )
        ids_collab = set(collab.clients.values_list("id", flat=True))
        client_ids = ids_prestataire | ids_collab
        return Ticket.objects.filter(client_id__in=client_ids).exclude(status="archived")
    return Ticket.objects.none()


def get_all_tickets_queryset(user):
    """Tous les tickets visibles (y compris archivés). Pour la liste quand on filtre par statut."""
    client = get_user_client(user)
    collab = get_user_collaborateur(user)
    if client:
        return Ticket.objects.filter(client=client)
    if collab:
        ids_prestataire = set(
            collab.prestataire.clients.values_list("id", flat=True)
        )
        ids_collab = set(collab.clients.values_list("id", flat=True))
        client_ids = ids_prestataire | ids_collab
        return Ticket.objects.filter(client_id__in=client_ids)
    return Ticket.objects.none()


def get_archived_tickets_queryset(user):
    """Return queryset of archived tickets the user is allowed to see."""
    client = get_user_client(user)
    collab = get_user_collaborateur(user)

    if client:
        return Ticket.objects.filter(client=client, status="archived")
    if collab:
        ids_prestataire = set(
            collab.prestataire.clients.values_list("id", flat=True)
        )
        ids_collab = set(collab.clients.values_list("id", flat=True))
        client_ids = ids_prestataire | ids_collab
        return Ticket.objects.filter(client_id__in=client_ids, status="archived")
    return Ticket.objects.none()


def get_editable_tickets_queryset(user):
    """Same as visible, for now (both client and collaborateur can edit within their scope)."""
    return get_visible_tickets_queryset(user)


def can_create_ticket(user):
    return user_is_client(user) or user_is_collaborateur(user)


def can_manage_clients_collaborateurs(user):
    """Only prestataire admin can create/edit clients and collaborators (in app, not only admin)."""
    return user_is_prestataire_admin(user)


def get_clients_for_collaborateur(collab):
    """Clients que le collaborateur peut choisir (création ticket) : prestataire + M2M."""
    if not collab:
        return Client.objects.none()
    ids_prestataire = set(
        collab.prestataire.clients.values_list("id", flat=True)
    )
    ids_collab = set(collab.clients.values_list("id", flat=True))
    return Client.objects.filter(id__in=ids_prestataire | ids_collab).order_by("name")
