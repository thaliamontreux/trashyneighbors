# TrashyNeighbors Ubuntu 24.04 Install

Target path: `/opt/trashyneighbors/`

## 1) Create private GitHub repo

- Create a new **private** repo in GitHub (no README/license required).
- Add yourself as owner.

## 2) On Ubuntu: clone into /opt

```bash
sudo mkdir -p /opt/trashyneighbors
sudo chown -R $USER:$USER /opt/trashyneighbors

git clone <YOUR_PRIVATE_REPO_URL> /opt/trashyneighbors
```

## 3) Run installer

```bash
cd /opt/trashyneighbors
sudo bash install/ubuntu/install.sh
```

## pip note (directive requirement)

If you choose to install Python packages system-wide (not recommended; this installer uses a venv), the directives require documenting:

```bash
pip install --break-system-packages -r requirements.txt
```

The installer will:

- Install apt deps (nginx, mariadb-server, python)
- Create system user `trashyneighbors`
- Create a venv in `/opt/trashyneighbors/venv`
- Generate `siteconfig.cfg`
- Create app tables
- Import seed SQL files:
  - `zip_codes_states.sql`
  - `fielddata.sql`
  - `open_vehicle_db.sql`
- Configure systemd services
- Configure nginx to proxy:
  - main site: `:80` -> gunicorn `127.0.0.1:8000`
  - admin: `:81/adminpanel/` -> gunicorn `127.0.0.1:8001`

## Services

```bash
sudo systemctl status trashyneighbors
sudo systemctl status trashyneighbors-admin
```

## Notes

- `siteconfig.cfg` is the only configuration file and is generated during install.
- The app itself runs behind nginx and must respect `X-Forwarded-*` headers.
