#!/usr/bin/env bash
# One-shot setup/update on PythonAnywhere. Safe to re-run: keeps an existing .env and database.
set -euo pipefail

USERNAME="${USER}"
DOMAIN="${USERNAME}.pythonanywhere.com"
BACKEND="$HOME/shopping-app-backend"
FRONTEND="$HOME/shopping-app-frontend-dist"
VENV="$HOME/.virtualenvs/shop"
PY="python3.13"

echo "==> Code"
[ -d "$BACKEND/.git" ] || git clone https://github.com/Ziyodullodev/shopping-app-backend.git "$BACKEND"
git -C "$BACKEND" pull --ff-only
if [ -d "$FRONTEND/.git" ]; then
  git -C "$FRONTEND" fetch -q origin build && git -C "$FRONTEND" reset -q --hard origin/build
else
  git clone -q -b build --single-branch https://github.com/Ziyodullodev/shopping-app-frontend.git "$FRONTEND"
fi

echo "==> Virtualenv"
[ -x "$VENV/bin/python" ] || $PY -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"

echo "==> .env"
if [ ! -f "$BACKEND/.env" ]; then
  "$VENV/bin/python" - "$BACKEND" "$DOMAIN" "$FRONTEND" <<'PY'
import secrets, sys
from pathlib import Path
backend, domain, frontend = sys.argv[1:4]
values = {
    "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
    "DJANGO_DEBUG": "false",
    "DJANGO_ALLOWED_HOSTS": domain,
    "DJANGO_CSRF_TRUSTED_ORIGINS": f"https://{domain}",
    "CORS_ALLOWED_ORIGINS": f"https://{domain}",
    "TELEGRAM_DEV_AUTH": "false",
    "FRONTEND_DIST": frontend,
}
lines = []
for line in (Path(backend) / ".env.example").read_text().splitlines():
    key = line.split("=", 1)[0]
    lines.append(f"{key}={values[key]}" if key in values and "=" in line else line)
env = Path(backend) / ".env"
env.write_text("\n".join(lines) + "\n")
env.chmod(0o600)
print("created", env)
PY
else
  echo "kept existing .env"
fi
# Make sure a webhook secret exists (older .env files were created without it).
"$VENV/bin/python" - "$BACKEND/.env" <<'PY'
import secrets, sys
from pathlib import Path
env = Path(sys.argv[1])
lines = env.read_text().splitlines()
keys = {l.split("=", 1)[0]: i for i, l in enumerate(lines) if "=" in l and not l.startswith("#")}
idx = keys.get("TELEGRAM_WEBHOOK_SECRET")
if idx is None or not lines[idx].split("=", 1)[1].strip():
    line = f"TELEGRAM_WEBHOOK_SECRET={secrets.token_urlsafe(32)}"
    if idx is None:
        lines.append(line)
    else:
        lines[idx] = line
    env.write_text("\n".join(lines) + "\n")
    print("generated TELEGRAM_WEBHOOK_SECRET")
PY

echo "==> Database and static files"
cd "$BACKEND"
"$VENV/bin/python" manage.py migrate --noinput
"$VENV/bin/python" manage.py seed_catalog
"$VENV/bin/python" manage.py collectstatic --noinput -v 0
mkdir -p "$BACKEND/media"

echo "==> WSGI file"
WSGI="/var/www/${USERNAME}_pythonanywhere_com_wsgi.py"
if [ -f "$WSGI" ] && ! grep -q "shopping-app-backend" "$WSGI"; then cp "$WSGI" "$WSGI.bak"; fi
sed "s/^USERNAME = .*/USERNAME = \"${USERNAME}\"/" "$BACKEND/deploy/pythonanywhere_wsgi.py" > "$WSGI"

"$VENV/bin/python" manage.py check --deploy --fail-level ERROR

echo "==> Telegram bot"
if grep -qE '^TELEGRAM_BOT_TOKEN=.+' "$BACKEND/.env"; then
  "$VENV/bin/python" manage.py setup_bot || echo "setup_bot failed; reload the web app and run: $VENV/bin/python manage.py setup_bot"
else
  echo "TELEGRAM_BOT_TOKEN is empty, skipping bot setup"
fi
echo "==> Done. Set the Web tab paths and static mappings, then press Reload."
