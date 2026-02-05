# Config déploiement — tickets.abissol.info (/var/www/tickets/ticketing)

Utilisez ces configs telles quelles, puis exécutez les commandes de vérification en bas.

---

## 1. Fichier .env

Emplacement : `/var/www/tickets/ticketing/.env`

```env
DJANGO_SECRET_KEY=votre-cle-secrete
DEBUG=False
ALLOWED_HOSTS=tickets.abissol.info,www.tickets.abissol.info,localhost,127.0.0.1

DB_NAME=ticketing_db
DB_USER=ticketing_app
DB_PASSWORD=votre_mot_de_passe_postgres
DB_HOST=127.0.0.1
DB_PORT=5432
```

---

## 2. Service systemd (Gunicorn)

Fichier : `/etc/systemd/system/ticketing.service`

```ini
[Unit]
Description=Gunicorn pour Ticketing SaaS
After=network.target postgresql.service

[Service]
User=app
Group=app
WorkingDirectory=/var/www/tickets/ticketing
Environment="PATH=/var/www/tickets/ticketing/.venv/bin"
EnvironmentFile=/var/www/tickets/ticketing/.env
ExecStart=/var/www/tickets/ticketing/.venv/bin/gunicorn \
  --workers 3 \
  --bind unix:/var/www/tickets/ticketing/gunicorn.sock \
  config.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

---

## 3. Nginx — site ticketing

Fichier : `/etc/nginx/sites-available/ticketing`

```nginx
server {
    listen 80;
    server_name tickets.abissol.info www.tickets.abissol.info;
    client_max_body_size 50M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/tickets/ticketing/staticfiles/;
    }

    location /media/ {
        alias /var/www/tickets/ticketing/media/;
    }

    location / {
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/var/www/tickets/ticketing/gunicorn.sock;
    }
}
```

---

## 4. Commandes à exécuter sur le serveur (dans l’ordre)

**A. Vérifier qu’il n’y a que le site ticketing sur le port 80**
```bash
ls -la /etc/nginx/sites-enabled/
```
Il doit y avoir **uniquement** un lien vers `ticketing` (pas `default`). Si `default` est présent :
```bash
sudo rm /etc/nginx/sites-enabled/default
```

**B. Mettre la config Nginx ci-dessus**
```bash
sudo nano /etc/nginx/sites-available/ticketing
```
Coller le bloc Nginx (section 3), sauvegarder.

**C. Activer le site et tester Nginx**
```bash
sudo ln -sf /etc/nginx/sites-available/ticketing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**D. Mettre le service systemd ci-dessus**
```bash
sudo nano /etc/systemd/system/ticketing.service
```
Coller le bloc service (section 2), sauvegarder.

**E. Redémarrer Gunicorn**
```bash
sudo systemctl daemon-reload
sudo systemctl restart ticketing
sudo systemctl status ticketing
```

**F. Vérifier que le socket existe**
```bash
ls -la /var/www/tickets/ticketing/gunicorn.sock
```
Vous devez voir le fichier socket.

**G. Test direct Django (doit donner 302)**
```bash
curl -sS -w "\nHTTP %{http_code}\n" -o /dev/null --unix-socket /var/www/tickets/ticketing/gunicorn.sock http://localhost/
```

**H. Test avec le nom de domaine (depuis le serveur)**
```bash
curl -sS -w "\nHTTP %{http_code}\n" -o /dev/null -H "Host: tickets.abissol.info" http://127.0.0.1/
```
Attendu : **HTTP 302** (redirection vers login). Si vous avez **404**, Nginx n’envoie pas au bon serveur ou le socket est incorrect.

**I. Logs en cas de problème**
```bash
# Dernières erreurs Nginx quand vous faites une requête
sudo tail -20 /var/log/nginx/error.log

# Dernières lignes Gunicorn
sudo journalctl -u ticketing -n 30 --no-pager
```

---

## 5. Checklist rapide

| Élément | Valeur attendue |
|--------|------------------|
| Domaine | tickets.abissol.info |
| Racine projet | /var/www/tickets/ticketing |
| Socket | /var/www/tickets/ticketing/gunicorn.sock |
| ALLOWED_HOSTS | tickets.abissol.info,www.tickets.abissol.info,localhost,127.0.0.1 |
| sites-enabled | uniquement ticketing (pas default) |
| proxy_pass | unix:/var/www/tickets/ticketing/gunicorn.sock |
| server_name | tickets.abissol.info www.tickets.abissol.info |

---

## 6. Si vous avez encore 404

1. **Vérifier quel serveur Nginx répond**  
   Depuis le serveur :
   ```bash
   curl -v -H "Host: tickets.abissol.info" http://127.0.0.1/ 2>&1 | head -30
   ```
   Regarder les en-têtes de réponse et le code HTTP.

2. **Vérifier que Nginx lit bien le bon fichier**
   ```bash
   sudo nginx -T 2>/dev/null | grep -A2 "server_name tickets.abissol"
   ```
   Vous devez voir `server_name tickets.abissol.info` et le bloc avec `proxy_pass` vers le socket.

3. **Tester en mettant ce site en default_server** (pour forcer Nginx à l’utiliser)  
   Dans `/etc/nginx/sites-available/ticketing`, ligne `listen` :
   ```nginx
   listen 80 default_server;
   server_name tickets.abissol.info www.tickets.abissol.info;
   ```
   Puis :
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```
   Retester dans le navigateur avec `http://tickets.abissol.info`.
