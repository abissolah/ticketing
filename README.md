# Ticketing SaaS — Django 5.2 LTS

Outil de ticketing en SaaS avec deux types de comptes : **prestataire** (et collaborateurs) et **client**.  
Création des comptes uniquement depuis l’admin Django (pas de formulaire public d’inscription).

## Prérequis

- Python 3.10+
- Django 5.2 LTS

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Configuration des comptes (admin)

1. **Prestataire** : Créer une entrée dans *Ticketing > Prestataires* (nom de la société).
2. **Utilisateurs** : Créer les comptes dans *Auth > Utilisateurs* (identifiant + mot de passe).
3. **Clients** : Dans *Ticketing > Clients*, créer la société cliente et associer **un** utilisateur (compte de connexion de la société). Lier le client à un prestataire. Ajouter les **membres** (nom, prénom, email, couleur) en inline.
4. **Collaborateurs** : Dans *Ticketing > Collaborateurs*, lier un utilisateur à un prestataire, renseigner nom/prénom/fonction, assigner les **clients** sur lesquels il intervient. Cocher *Admin prestataire* pour celui qui peut créer clients/collaborateurs (en plus des droits ticket).

Les comptes à créer depuis l’admin sont donc : **Clients** (un compte par société) et **Collaborateurs** (un compte par collaborateur du prestataire).

## Fonctionnalités

- **Connexion / Déconnexion** (pas d’inscription publique).
- **Liste des tickets** (non archivés) : vue tableau ou tuiles, filtres (statut, priorité, type, membre, affecté à, période), listes déroulantes avec recherche (Select2), export Excel.
- **Détail ticket** : description WYSIWYG (Summernote), pièces jointes, commentaires avec PJ, temps prévu/effectif (côté prestataire).
- **Statistiques** : choix des widgets (tickets ouverts/fermés, par statut, priorité, type, par collaborateur affecté).
- **Priorités** : Basse (vert), Moyenne (orange), Haute (rouge). Ligne barrée si statut « Validé ».

## Structure des rôles

- **Client** : une société = un compte User. Plusieurs **membres** (nom, prénom, email, couleur) pour qualifier qui a initié le ticket.
- **Prestataire** : société avec **collaborateurs** (1 à 10, un compte par collaborateur). Un collaborateur peut être **admin prestataire** (création clients/collaborateurs en plus des droits ticket).
- Un ticket est lié à un client, un membre (initiateur), priorité, statut, type (bug/évol/exploit), optionnellement affecté à un collaborateur.

## Fichiers principaux

- `config/settings.py` — réglages Django
- `tickets/models.py` — Prestataire, Client, ClientMember, Collaborateur, Ticket, TicketComment, TicketAttachment
- `tickets/views.py` — liste, détail, création/édition, export Excel, stats, quick-update
- `tickets/utils.py` — visibilité des tickets (client vs collaborateur)
- `templates/` — Bootstrap 5, responsive

## Variables d’environnement (optionnel)

- `DJANGO_SECRET_KEY` — clé secrète (par défaut une valeur de dev).
- `DEBUG` — `True` / `False`.
- `ALLOWED_HOSTS` — liste séparée par des virgules.
