# Réception d'e-mails → création de tickets

Un e-mail reçu sur une adresse dédiée peut créer automatiquement un ticket.

## Règles

- **Expéditeur** : l’adresse e-mail doit correspondre à un **membre client** (champ `ClientMember.email`). Sinon le mail est ignoré.
- **Client** : le ticket est rattaché au client du membre trouvé.
- **Titre** : le sujet du mail (les balises `[bug]`, `[evol]`, `[exploit]` sont retirées du titre affiché).
- **Description** : le corps du mail (texte), converti en HTML.
- **Pièces jointes** : les pièces jointes du mail sont enregistrées sur le ticket (section « Pièces jointes (description) »). Limite : 20 fichiers max, 10 Mo par fichier.
- **Type** : déduit du sujet :
  - sujet contient `[bug]` → type **Bug**
  - sujet contient `[evol]` → type **Évolution**
  - sujet contient `[exploit]` → type **Exploitation**
  - sinon → type **Bug** par défaut
- **Priorité** : toujours **Moyenne** par défaut.
- **Doublons** : si un `Message-ID` est fourni et déjà en base, le mail n’est pas retraité.

## 1. Réception par IMAP (polling)

Une commande Django interroge une boîte IMAP et crée les tickets pour les mails non lus.

### Configuration (.env ou variables d’environnement)

```env
EMAIL_IMAP_HOST=imap.example.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USER=support@example.com
EMAIL_IMAP_PASSWORD=mot_de_passe
EMAIL_IMAP_MAILBOX=INBOX
EMAIL_IMAP_USE_SSL=true
```

### Lancer la commande

```bash
python manage.py fetch_email_tickets
```

- Les messages **non lus** sont traités puis marqués comme lus.
- Option `--dry-run` : affiche les mails sans créer de tickets.
- Option `--no-mark-read` : ne pas marquer les messages comme lus.

### Cron (toutes les 5 minutes)

```cron
*/5 * * * * cd /var/www/tickets/ticketing && .venv/bin/python manage.py fetch_email_tickets
```

Adaptez le chemin au répertoire de votre projet.

---

## 2. Réception par webhook (Mailgun, SendGrid, etc.)

Un service d’e-mail peut envoyer une requête HTTP (POST) à votre application quand un mail est reçu.

### URL du webhook

```
POST https://votredomaine.com/webhook/inbound-email/
```

### Sécurité

Définir un secret partagé :

```env
EMAIL_WEBHOOK_SECRET=votre_secret_long_aleatoire
```

Le client doit envoyer ce secret soit :
- en paramètre POST `token`, soit
- en en-tête HTTP `X-Webhook-Token`.

Si `EMAIL_WEBHOOK_SECRET` est vide, la vérification est désactivée (à réserver au dev).

### Format du corps POST (Mailgun)

- `sender` : adresse de l’expéditeur
- `subject` : sujet
- `body-plain` : corps texte
- `Message-Id` : optionnel (évite les doublons)

L’application accepte aussi `From`, `Subject`, `body_plain`, `stripped-text`, `Message-ID`.

### Exemple Mailgun

Dans Mailgun, créer une route « Catch-all » ou une route sur l’adresse qui reçoit les mails, et définir l’URL de forwarding :

```
https://tickets.abissol.info/webhook/inbound-email/
```

En « Advanced », ajouter un paramètre `token` égal à `EMAIL_WEBHOOK_SECRET` si vous n’utilisez pas l’en-tête.

### Réponse

- **200** : `{"ok": true, "ticket_id": 123}`
- **400** : `{"ok": false, "error": "message"}` (ex. membre inconnu)
- **401** : secret invalide ou manquant

---

## Admin

Le modèle **E-mails entrants** (`InboundEmail`) liste les mails déjà traités (Message-ID, expéditeur, sujet, ticket créé). Utile pour le débogage et éviter les doublons.

## Migrations

Après mise à jour du code, appliquer les migrations pour créer la table `InboundEmail` :

```bash
python manage.py migrate
```
