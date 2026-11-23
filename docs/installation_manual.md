# Installation manual (Kali Linux)

## Requirements
Hardware: 4-core CPU, 8 GB RAM (16 GB recommended), 20 GB free disk, internet for the first install and model download.
Software: Kali Linux, Python 3.10 or later, MariaDB or MySQL 8, ClamAV with the daemon, libmagic.

## 1. System packages
```bash
sudo apt update
sudo apt install -y unzip python3-venv python3-pip python3-dev build-essential libmagic1 mariadb-server clamav clamav-daemon
sudo systemctl stop clamav-freshclam && sudo freshclam
sudo systemctl enable --now clamav-freshclam clamav-daemon mariadb
```
## 2. Database
```bash
sudo mysql
```
```sql
CREATE DATABASE resume_ai CHARACTER SET utf8mb4;
CREATE USER 'resume_app'@'localhost' IDENTIFIED BY 'YOUR-OWN-PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES ON resume_ai.* TO 'resume_app'@'localhost';
FLUSH PRIVILEGES;
```
## 3. Application
```bash
unzip resume_ai_final.zip -d ~/ && cd ~/resume_ai
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords
cp .env.example .env
read -s -p "DB password: " DBPASS; echo
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')|" .env
sed -i "s|^MASTER_KEY=.*|MASTER_KEY=$(python -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())')|" .env
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=mysql+pymysql://resume_app:$DBPASS@localhost:3306/resume_ai?charset=utf8mb4|" .env
chmod 600 .env
```
Back up the `MASTER_KEY` line. Without it, stored resumes cannot be decrypted.
## 4. Create tables, taxonomy and an administrator
```bash
flask --app run db init
flask --app run db migrate -m "initial schema"
flask --app run db upgrade
python scripts/seed_taxonomy.py
python scripts/create_admin.py
```
## 5. Optional hardening
```bash
python scripts/vendor_assets.py        # serve Bootstrap and Chart.js locally, then drop the CDN from the CSP
```
## 6. Check and run
```bash
python scripts/check_env.py
python -m pytest -v
python run.py                           # http://127.0.0.1:5000
```
## Production-style deployment (outline)
Gunicorn behind Nginx with a TLS certificate, `FLASK_ENV=production`, `COOKIE_SECURE=true`, Redis for rate limiting, a key store for
`MASTER_KEY`, a restricted database user, and a daily `python scripts/purge_expired.py`.

## Updating after a new release
Unzip over the folder (`unzip -o`), `pip install -r requirements.txt`, then `flask --app run db migrate -m "update"` and `flask --app run db upgrade`.

## Upgrading to the job board
This release adds three columns to `job_descriptions` (`is_public`, `status`, `threshold`). After unzipping, run:
```bash
flask --app run db migrate -m "job board"
flask --app run db upgrade
```
Existing jobs keep working: they default to private, open, threshold 60.
