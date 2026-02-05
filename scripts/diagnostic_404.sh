#!/bin/bash
# À lancer sur le serveur en SSH pour diagnostiquer une 404.
# Usage: bash diagnostic_404.sh [répertoire_app]
# Exemple: bash diagnostic_404.sh /var/www/tickets/ticketing

set -e
APP_DIR="${1:-/var/www/ticketing}"
echo "=== Diagnostic 404 (app=$APP_DIR) ==="
echo ""

echo "1. Sites activés Nginx (sites-enabled):"
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || true
echo ""

echo "2. Socket Gunicorn:"
SOCKET=$(find /var/www -name "gunicorn.sock" 2>/dev/null | head -1)
if [ -z "$SOCKET" ]; then
  echo "   Aucun gunicorn.sock trouvé sous /var/www"
else
  echo "   Trouvé: $SOCKET"
  ls -la "$SOCKET" 2>/dev/null || true
  echo ""
  echo "3. Test direct du socket (bypass Nginx) - requête GET / :"
  if curl -sS -o /dev/null -w "%{http_code}" --unix-socket "$SOCKET" http://localhost/ 2>/dev/null; then
    CODE=$(curl -sS -o /dev/null -w "%{http_code}" --unix-socket "$SOCKET" http://localhost/)
    echo "   -> HTTP $CODE (200 = Django répond OK)"
  else
    echo "   -> Échec (curl ne peut pas joindre le socket)"
  fi
fi
echo ""

echo "4. Contenu du service systemd ticketing (bind + WorkingDirectory):"
grep -E "WorkingDirectory|ExecStart|bind" /etc/systemd/system/ticketing.service 2>/dev/null || true
echo ""

echo "5. Nginx proxy_pass pour ce site:"
grep -A1 "proxy_pass" /etc/nginx/sites-available/ticketing 2>/dev/null || true
echo ""

echo "6. Dernières lignes des logs Nginx error:"
sudo tail -5 /var/log/nginx/error.log 2>/dev/null || true
echo ""

echo "7. ALLOWED_HOSTS dans .env:"
grep ALLOWED_HOSTS "$APP_DIR/.env" 2>/dev/null || echo "   (fichier .env non trouvé ou pas de ALLOWED_HOSTS)"
echo ""

echo "8. Test curl depuis le serveur (remplacer VOTRE_DOMAINE par votre nom de domaine):"
echo "   curl -v -H 'Host: VOTRE_DOMAINE' http://127.0.0.1/  -> à lancer manuellement"
echo ""
echo "=== Fin diagnostic ==="
