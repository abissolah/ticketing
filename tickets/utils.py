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
    Return base queryset of tickets the user is allowed to see (non archivés).
    """
    client = get_user_client(user)
    collab = get_user_collaborateur(user)

    if client:
        return Ticket.objects.filter(client=client, archived=False)
    if collab:
        ids_prestataire = set(
            collab.prestataire.clients.values_list("id", flat=True)
        )
        ids_collab = set(collab.clients.values_list("id", flat=True))
        client_ids = ids_prestataire | ids_collab
        return Ticket.objects.filter(client_id__in=client_ids, archived=False)
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
        return Ticket.objects.filter(client=client, archived=True)
    if collab:
        ids_prestataire = set(
            collab.prestataire.clients.values_list("id", flat=True)
        )
        ids_collab = set(collab.clients.values_list("id", flat=True))
        client_ids = ids_prestataire | ids_collab
        return Ticket.objects.filter(client_id__in=client_ids, archived=True)
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


def get_ticket_unread_comment_count(ticket, user):
    """Nombre de commentaires non lus par user sur ce ticket (écrits par l'autre camp)."""
    from .models import CommentReadReceipt, Collaborateur
    if not user or not user.is_authenticated or not ticket.client:
        return 0
    read_ids = set(
        CommentReadReceipt.objects.filter(user=user, comment__ticket=ticket).values_list("comment_id", flat=True)
    )
    client = get_user_client(user)
    collab = get_user_collaborateur(user)
    is_client_viewer = client and ticket.client_id == client.id
    collab_visible = bool(collab and ticket.client_id in set(get_clients_for_collaborateur(collab).values_list("id", flat=True)))
    client_user_id = ticket.client.user_id

    author_ids = list(ticket.comments.exclude(author_id__isnull=True).values_list("author_id", flat=True).distinct())
    collab_author_ids = set(Collaborateur.objects.filter(user_id__in=author_ids).values_list("user_id", flat=True)) if author_ids else set()

    count = 0
    for c in ticket.comments.all():
        if c.id in read_ids or not c.author_id:
            continue
        if is_client_viewer:
            if c.author_id != user.id and c.author_id in collab_author_ids:
                count += 1
        elif collab_visible and client_user_id and c.author_id == client_user_id:
            count += 1
    return count


def get_tickets_unread_counts(ticket_ids, user):
    """Retourne un dict {ticket_id: nombre de commentaires non lus} pour une liste de tickets."""
    if not user or not user.is_authenticated or not ticket_ids:
        return {tid: 0 for tid in ticket_ids}
    from .models import Ticket
    result = {}
    for ticket in Ticket.objects.filter(id__in=ticket_ids).prefetch_related("comments", "comments__read_receipts"):
        result[ticket.id] = get_ticket_unread_comment_count(ticket, user)
    for tid in ticket_ids:
        result.setdefault(tid, 0)
    return result
