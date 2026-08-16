# PartnersHub AI — Hostinger VPS production deployment

This deployment path preserves the existing `p0_runtime.py` and runs the application through `wsgi.py`, Gunicorn and PostgreSQL.

## 1. Hostinger VPS prerequisites

Install/enable:

- Docker Engine
- Docker Compose plugin
- Git
- NGINX
- Certbot (for the domain/HTTPS)
- UFW/firewall rules allowing 22, 80 and 443

Recommended application directory:

```bash
sudo mkdir -p /opt/partnershub-ai
sudo chown "$USER":"$USER" /opt/partnershub-ai
cd /opt/partnershub-ai
git clone https://github.com/prashantpbp47-coder/Agent-Ai-coach.git .
```

## 2. Production environment

Copy the template:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Set at minimum:

```text
PUBLIC_BASE_URL=https://your-real-domain
SECRET_KEY=<random secret>
JWT_SECRET_KEY=<random secret>
POSTGRES_PASSWORD=<strong random password>
```

Configure the actual AI/WhatsApp provider keys only after the application health and database checks pass.

## 3. Start the application

```bash
cd /opt/partnershub-ai
./deploy/deploy.sh
```

The container entrypoint runs `alembic upgrade head` before Gunicorn starts.

## 4. NGINX

Copy `deploy/nginx.conf` into the server NGINX site configuration and point `proxy_pass` to `127.0.0.1:8000`.

After DNS is pointing to the VPS:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Then issue/renew HTTPS with Certbot and redirect port 80 to HTTPS.

## 5. Health verification

```bash
BASE_URL=http://127.0.0.1:8000 ./deploy/healthcheck.sh
```

Expected:

```text
Application health: PASS
P20 WhatsApp boundary health: PASS
```

## 6. Backup

Run from the application directory with the same `.env.production`:

```bash
set -a
. ./.env.production
set +a
./deploy/backup.sh
```

Schedule it daily with cron/systemd timers. Keep at least 14 days of backups and periodically test restoration.

## 7. Rollback

A rollback should be performed to a previously validated image/commit. Do not downgrade the database blindly. If a migration is not backward-compatible, restore the database snapshot first and then deploy the known-good application image.

## 8. Real data go-live order

1. Validate HTTPS and login.
2. Validate PostgreSQL and migrations.
3. Import a small non-production report with `dry_run=true`.
4. Validate partner-wise and renewal mapping.
5. Import the approved operational report.
6. Connect provider credentials.
7. Test webhook with the provider's test mechanism.
8. Send one controlled live message to an internal test number.
9. Enable normal operations.

Never place customer CSV/XLSX files in GitHub.
