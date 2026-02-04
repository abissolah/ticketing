# Déploiement — Ticketing SaaS sur Ubuntu 24

Guide pour installer et déployer l’application sur un serveur **Ubuntu 24** avec un **nom de domaine** déjà en votre possession. Stack : **Nginx**, **Gunicorn**, **PostgreSQL**, **Certbot** (HTTPS). En développement, sans variables PostgreSQL, l’application utilise SQLite.

---

## 1. Prérequis

- Un serveur Ubuntu 24 (VPS ou dédié) avec accès root ou sudo.
- Un nom de domaine pointant vers l’IP du serveur (ex. `ticketing.votredomaine.com`).

### DNS

Créez un enregistrement **A** (ou **AAAA** pour IPv6) pointant votre sous-domaine vers l’IP publique du serveur, par exemple :

| Type | Nom (sous-domaine) | Valeur        | TTL  |
|------|---------------------|---------------|------|
| A    | ticketing           | IP_DU_SERVEUR | 300  |

Attendez la propagation DNS (quelques minutes à quelques heures) avant de continuer. Vous pouvez vérifier avec : `dig ticketing.votredomaine.com +short`.

---

## 2. Connexion et mise à jour du serveur

```bash
ssh root@IP_DU_SERVEUR
# ou : ssh ubuntu@IP_DU_SERVEUR  (selon votre fournisseur)
```

```bash
apt update && apt upgrade -y
```

---

## 3. Paquets système

```bash
apt install -y python3 python3-pip python3-venv python3-dev \
  nginx certbot python3-certbot-nginx \
  git build-essential \
  postgresql postgresql-contrib libpq-dev
```

- **python3-venv** : environnements virtuels  
- **nginx** : reverse proxy et serveur web  
- **certbot** + **python3-certbot-nginx** : certificat SSL Let’s Encrypt  
- **postgresql**, **postgresql-contrib** : base de données  
- **libpq-dev** : en-têtes pour le client Python PostgreSQL (psycopg2)  

---

## 4. Installation et configuration de PostgreSQL

### Démarrer PostgreSQL

```bash
systemctl start postgresql
systemctl enable postgresql
```

### Créer l’utilisateur et la base de données

L’utilisateur PostgreSQL peut avoir le même nom que l’utilisateur système `app` (créé à l’étape 5) pour simplifier, ou un nom dédié. Ici on utilise `ticketing_app` comme utilisateur PostgreSQL pour éviter les confusions avec l’utilisateur système `app`.

```bash
sudo -u postgres psql -c "CREATE USER ticketing_app WITH PASSWORD 'CHANGER_MOT_DE_PASSE';"
sudo -u postgres psql -c "CREATE DATABASE ticketing_db OWNER ticketing_app ENCODING 'UTF8';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ticketing_db TO ticketing_app;"
sudo -u postgres psql -c "ALTER DATABASE ticketing_db SET timezone TO 'Europe/Paris';"
```

**Important :** remplacez `CHANGER_MOT_DE_PASSE` par un mot de passe fort et notez-le pour le fichier `.env` (étape 9).

Pour permettre à l’utilisateur de créer des schémas (utile pour certaines migrations Django) :

```bash
sudo -u postgres psql -d ticketing_db -c "GRANT ALL ON SCHEMA public TO ticketing_app;"
sudo -u postgres psql -d ticketing_db -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ticketing_app;"
```

### Vérification

```bash
sudo -u postgres psql -c "\l"
```

Vous devez voir la base `ticketing_db` avec le propriétaire `ticketing_app`.

---

## 5. Utilisateur dédié pour l’application

Ne pas faire tourner l’app en root. Créer un utilisateur dédié :

```bash
adduser --disabled-password --gecos "" app
```

Choisir un mot de passe si besoin, ou garder la connexion par clé SSH pour l’utilisateur qui déploiera (ex. votre utilisateur avec sudo).

Le déploiement suivant peut être fait en tant que `root` ou en tant qu’utilisateur avec sudo ; on suppose que les commandes sont exécutées avec les droits nécessaires. Le service Gunicorn pourra être lancé sous l’utilisateur `app` (voir plus bas).

---

## 6. Répertoire de l’application

Remplacer `ticketing.votredomaine.com` par votre sous-domaine ou domaine si vous n’utilisez pas de sous-domaine.

```bash
export DOMAIN="ticketing.votredomaine.com"
export APP_DIR="/var/www/ticketing"
mkdir -p "$APP_DIR"
cd "$APP_DIR"
```

---

## 7. Cloner le projet depuis GitHub

```bash
git clone https://github.com/abissolah/ticketing.git .
```

Si le dépôt est privé, configurer l’accès (clé SSH déployée sur le serveur ou token HTTPS).

---

## 8. Environnement virtuel Python et dépendances

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

Le fichier `requirements.txt` inclut déjà `psycopg2-binary` pour PostgreSQL. Conserver `gunicorn` dans le projet (optionnel) :

```bash
echo "gunicorn" >> requirements.txt
```

---

## 9. Variables d’environnement

Créer un fichier `.env` à la racine du projet (ne pas le commiter ; il est déjà ignoré par `.gitignore`) :

```bash
nano .env
```

Contenu type (à adapter) — **remplacer** les valeurs entre chevrons par les vôtres :

```env
DJANGO_SECRET_KEY=votre-cle-secrete-longue-et-aleatoire
DEBUG=False
ALLOWED_HOSTS=ticketing.votredomaine.com,www.ticketing.votredomaine.com

# PostgreSQL (obligatoire en production avec ce guide)
DB_NAME=ticketing_db
DB_USER=ticketing_app
DB_PASSWORD=CHANGER_MOT_DE_PASSE
DB_HOST=127.0.0.1
DB_PORT=5432
```

Utilisez le même mot de passe que celui défini pour l’utilisateur PostgreSQL à l’étape 4 (`DB_PASSWORD`).

Générer une clé secrète forte :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Coller le résultat dans `DJANGO_SECRET_KEY`. Sauvegarder (Ctrl+O, Entrée, Ctrl+X).

Charger les variables dans le shell pour les commandes suivantes :

```bash
set -a
source .env
set +a
```

Le service systemd (section 12) charge ce fichier via `EnvironmentFile=/var/www/ticketing/.env`, donc Django et Gunicorn recevront bien `DB_*` et les autres variables.

**Configuration Django et PostgreSQL :** le projet est déjà configuré pour utiliser PostgreSQL lorsque les variables `DB_NAME`, `DB_USER`, `DB_PASSWORD`, etc. sont présentes (`config/settings.py`). Aucune modification de code n’est nécessaire.

---

## 10. Adapter Django pour charger le fichier .env (optionnel)

Par défaut, Django ne lit pas un fichier `.env`. Deux possibilités :

- **A)** Exporter les variables dans le service systemd (recommandé, pas de dépendance supplémentaire).  
- **B)** Utiliser `python-dotenv` et charger `.env` dans `settings.py`.

### Option B (si vous préférez un fichier .env)

```bash
pip install python-dotenv
```

Dans `config/settings.py`, en tout début (après les imports existants) :

```python
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
```

Puis laisser `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` tels qu’ils sont (déjà basés sur `os.environ`).  
Si vous choisissez l’option B, ajoutez `python-dotenv` dans `requirements.txt`.

---

## 11. Migrations, fichiers statiques, superutilisateur

Toujours avec le venv activé (`source .venv/bin/activate`) et depuis `/var/www/ticketing` :

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Répondre aux questions (identifiant, email, mot de passe) pour le compte admin Django.

---

## 12. Service Gunicorn (systemd)

Créer un fichier de service pour lancer Gunicorn au démarrage et sous l’utilisateur `app` :

```bash
nano /etc/systemd/system/ticketing.service
```

Contenu (remplacer `ticketing.votredomaine.com` par votre domaine) :

```ini
[Unit]
Description=Gunicorn pour Ticketing SaaS
After=network.target postgresql.service

[Service]
User=app
Group=app
WorkingDirectory=/var/www/ticketing
Environment="PATH=/var/www/ticketing/.venv/bin"
EnvironmentFile=/var/www/ticketing/.env
ExecStart=/var/www/ticketing/.venv/bin/gunicorn \
  --workers 3 \
  --bind unix:/var/www/ticketing/gunicorn.sock \
  config.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Si vous n’utilisez pas l’option B (python-dotenv), le fait d’avoir `EnvironmentFile=/var/www/ticketing/.env` suffit pour que Gunicorn reçoive toutes les variables (`DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_*`).

Donner la propriété du répertoire à l’utilisateur `app` :

```bash
chown -R app:app /var/www/ticketing
```

Activer et démarrer le service :

```bash
systemctl daemon-reload
systemctl enable ticketing
systemctl start ticketing
systemctl status ticketing
```

En cas d’erreur : `journalctl -u ticketing -n 50 -f`.

---

## 13. Configuration Nginx

Créer un vhost pour votre domaine :

```bash
nano /etc/nginx/sites-available/ticketing
```

Contenu (remplacer `ticketing.votredomaine.com` par votre domaine) :

```nginx
server {
    listen 80;
    server_name ticketing.votredomaine.com www.ticketing.votredomaine.com;
    client_max_body_size 50M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/ticketing/staticfiles/;
    }

    location /media/ {
        alias /var/www/ticketing/media/;
    }

    location / {
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/var/www/ticketing/gunicorn.sock;
    }
}
```

Activer le site et tester la configuration :

```bash
ln -s /etc/nginx/sites-available/ticketing /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

À ce stade, le site doit répondre en **HTTP** sur `http://ticketing.votredomaine.com`. Vérifier que la page de login s’affiche.

---

## 14. Certificat SSL (HTTPS) avec Let’s Encrypt

```bash
certbot --nginx -d ticketing.votredomaine.com -d www.ticketing.votredomaine.com
```

Suivre les instructions (email, acceptation des CGU). Certbot modifie automatiquement la config Nginx pour servir en HTTPS et rediriger le HTTP vers HTTPS.

Renouvellement automatique (déjà configuré par défaut) :

```bash
certbot renew --dry-run
```

---

## 15. Firewall (recommandé)

Autoriser SSH, HTTP et HTTPS, activer le pare-feu :

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ufw status
```

---

## 16. Résumé des chemins et commandes utiles

| Élément              | Valeur |
|----------------------|--------|
| Répertoire app       | `/var/www/ticketing` |
| Environnement virtuel| `/var/www/ticketing/.venv` |
| Fichier .env         | `/var/www/ticketing/.env` |
| Socket Gunicorn      | `/var/www/ticketing/gunicorn.sock` |
| Service systemd      | `ticketing.service` |

**Redémarrer l’application :**

```bash
sudo systemctl restart ticketing
```

**Voir les logs Gunicorn :**

```bash
sudo journalctl -u ticketing -f
```

**Après un `git pull` (mises à jour) :**

```bash
cd /var/www/ticketing
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart ticketing
```

**Admin Django :**  
`https://ticketing.votredomaine.com/admin/` (avec le superutilisateur créé à l’étape 11).

---

## 17. Utiliser SQLite en développement (optionnel)

Sans définir les variables `DB_NAME`, `DB_USER`, etc., Django utilise automatiquement **SQLite** (`db.sqlite3`). C’est le comportement par défaut en local : pas besoin d’installer PostgreSQL sur votre machine de dev.

---

## 18. Checklist finale

- [ ] DNS : enregistrement A (ou AAAA) pointant vers le serveur  
- [ ] Paquets installés (Python, Nginx, Certbot, **PostgreSQL**)  
- [ ] **PostgreSQL** : service démarré, utilisateur `ticketing_app` et base `ticketing_db` créés  
- [ ] Projet cloné dans `/var/www/ticketing`  
- [ ] `.venv` créé, `requirements.txt` installé (dont `psycopg2-binary`), `gunicorn` installé  
- [ ] Fichier `.env` avec `DJANGO_SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, **`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`**  
- [ ] `migrate`, `collectstatic`, `createsuperuser`  
- [ ] Service `ticketing` (systemd) activé et démarré  
- [ ] Nginx configuré, site activé, `nginx -t` et reload  
- [ ] Certificat SSL installé avec Certbot  
- [ ] UFW activé (SSH + Nginx Full)  
- [ ] Test : https://votredomaine → page de login et /admin/  

En cas de problème, vérifier les logs : `journalctl -u ticketing -n 100`, `tail -f /var/log/nginx/error.log`, et `sudo -u postgres psql -d ticketing_db -c "\dt"` pour lister les tables Django.
