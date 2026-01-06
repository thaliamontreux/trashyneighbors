#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/trashyneighbors"
APP_USER="trashyneighbors"
APP_GROUP="trashyneighbors"

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "This installer must be run as root." >&2
    exit 1
  fi
}

ensure_user() {
  if ! id "${APP_USER}" >/dev/null 2>&1; then
    useradd --system --home "${APP_ROOT}" --shell /usr/sbin/nologin "${APP_USER}"
  fi
}

install_apt_deps() {
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    curl \
    git \
    nginx \
    mariadb-server \
    python3 \
    python3-venv \
    python3-pip \
    build-essential \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    tk-dev \
    tcl-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    libmariadb-dev \
    libssl-dev
}

ensure_app_root() {
  mkdir -p "${APP_ROOT}"
}

ensure_venv() {
  if [[ ! -d "${APP_ROOT}/venv" ]]; then
    python3 -m venv "${APP_ROOT}/venv"
  fi
  "${APP_ROOT}/venv/bin/python" -m pip install --upgrade pip
}

install_python_deps() {
  if [[ ! -f "${APP_ROOT}/requirements.txt" ]]; then
    echo "Missing ${APP_ROOT}/requirements.txt. Did you clone the repo into ${APP_ROOT}?" >&2
    exit 1
  fi
  "${APP_ROOT}/venv/bin/pip" install -r "${APP_ROOT}/requirements.txt"
}

prompt_db() {
  read -r -p "MariaDB host [127.0.0.1]: " DB_HOST
  DB_HOST=${DB_HOST:-127.0.0.1}

  read -r -p "MariaDB port [3306]: " DB_PORT
  DB_PORT=${DB_PORT:-3306}

  read -r -p "MariaDB database name [trashyneighbors]: " DB_NAME
  DB_NAME=${DB_NAME:-trashyneighbors}

  read -r -p "MariaDB app username [trashyapp]: " DB_USER
  DB_USER=${DB_USER:-trashyapp}

  read -r -s -p "MariaDB app user password (will be created): " DB_PASSWORD
  echo

  read -r -p "Public base URL (used in emails) [https://www.trashyneighbors.com]: " PUBLIC_BASE_URL
  PUBLIC_BASE_URL=${PUBLIC_BASE_URL:-https://www.trashyneighbors.com}

  read -r -p "Mail server [localhost]: " MAIL_SERVER
  MAIL_SERVER=${MAIL_SERVER:-localhost}

  read -r -p "Mail port [25]: " MAIL_PORT
  MAIL_PORT=${MAIL_PORT:-25}

  read -r -p "Mail default sender [no-reply@trashyneighbors.com]: " MAIL_SENDER
  MAIL_SENDER=${MAIL_SENDER:-no-reply@trashyneighbors.com}

  read -r -p "Google OAuth client id (optional): " GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-""}

  read -r -p "Google OAuth client secret (optional): " GOOGLE_CLIENT_SECRET
  GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-""}
}

prompt_admin_bootstrap() {
  read -r -p "Create initial Super Admin now? [y/N]: " CREATE_ADMIN
  CREATE_ADMIN=${CREATE_ADMIN:-N}

  if [[ "${CREATE_ADMIN}" =~ ^[Yy]$ ]]; then
    read -r -p "Admin email: " ADMIN_EMAIL
    read -r -p "Admin screen name: " ADMIN_SCREEN_NAME
    read -r -s -p "Admin password: " ADMIN_PASSWORD
    echo
  fi
}

setup_mariadb() {
  systemctl enable --now mariadb

  mariadb -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
  mariadb -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';"
  mariadb -e "ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';"
  mariadb -e "GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';"
  mariadb -e "FLUSH PRIVILEGES;"
}

generate_siteconfig() {
  if [[ -f "${APP_ROOT}/siteconfig.cfg" ]]; then
    echo "siteconfig.cfg already exists; leaving as-is."
    return
  fi

  "${APP_ROOT}/venv/bin/python" "${APP_ROOT}/scripts/generate_siteconfig.py" \
    --db-host "${DB_HOST}" \
    --db-port "${DB_PORT}" \
    --db-user "${DB_USER}" \
    --db-password "${DB_PASSWORD}" \
    --db-name "${DB_NAME}" \
    --public-base-url "${PUBLIC_BASE_URL}" \
    --mail-server "${MAIL_SERVER}" \
    --mail-port "${MAIL_PORT}" \
    --mail-default-sender "${MAIL_SENDER}" \
    --google-client-id "${GOOGLE_CLIENT_ID}" \
    --google-client-secret "${GOOGLE_CLIENT_SECRET}"

  chown "${APP_USER}:${APP_GROUP}" "${APP_ROOT}/siteconfig.cfg"
  chmod 0600 "${APP_ROOT}/siteconfig.cfg"
}

init_app_tables() {
  "${APP_ROOT}/venv/bin/python" "${APP_ROOT}/scripts/init_app_db.py"
}

import_seed_sql() {
  if [[ ! -f "${APP_ROOT}/zip_codes_states.sql" ]]; then
    echo "Missing ${APP_ROOT}/zip_codes_states.sql" >&2
    exit 1
  fi
  if [[ ! -f "${APP_ROOT}/fielddata.sql" ]]; then
    echo "Missing ${APP_ROOT}/fielddata.sql" >&2
    exit 1
  fi
  if [[ ! -f "${APP_ROOT}/open_vehicle_db.sql" ]]; then
    echo "Missing ${APP_ROOT}/open_vehicle_db.sql" >&2
    exit 1
  fi

  "${APP_ROOT}/venv/bin/python" "${APP_ROOT}/scripts/bootstrap_db.py" \
    --host "${DB_HOST}" \
    --port "${DB_PORT}" \
    --user "${DB_USER}" \
    --password "${DB_PASSWORD}" \
    --database "${DB_NAME}" \
    --sql "${APP_ROOT}/zip_codes_states.sql" \
    --sql "${APP_ROOT}/fielddata.sql" \
    --sql "${APP_ROOT}/open_vehicle_db.sql"
}

create_initial_admin() {
  if [[ ! "${CREATE_ADMIN}" =~ ^[Yy]$ ]]; then
    return
  fi

  "${APP_ROOT}/venv/bin/python" "${APP_ROOT}/scripts/create_admin.py" \
    --email "${ADMIN_EMAIL}" \
    --screen-name "${ADMIN_SCREEN_NAME}" \
    --password "${ADMIN_PASSWORD}"
}

install_systemd_units() {
  install -m 0644 "${APP_ROOT}/install/ubuntu/systemd/trashyneighbors.service" /etc/systemd/system/trashyneighbors.service
  install -m 0644 "${APP_ROOT}/install/ubuntu/systemd/trashyneighbors-admin.service" /etc/systemd/system/trashyneighbors-admin.service

  systemctl daemon-reload
  systemctl enable --now trashyneighbors.service
  systemctl enable --now trashyneighbors-admin.service
}

install_nginx() {
  install -m 0644 "${APP_ROOT}/install/ubuntu/nginx/trashyneighbors.conf" /etc/nginx/sites-available/trashyneighbors
  ln -sf /etc/nginx/sites-available/trashyneighbors /etc/nginx/sites-enabled/trashyneighbors

  nginx -t
  systemctl reload nginx
}

fix_permissions() {
  chown -R "${APP_USER}:${APP_GROUP}" "${APP_ROOT}"
}

main() {
  require_root

  if [[ ! -d "${APP_ROOT}" ]]; then
    echo "Expected code to be present at ${APP_ROOT}." >&2
    echo "Clone your repo there first (see install/ubuntu/INSTALL.md)." >&2
    exit 1
  fi

  cd "${APP_ROOT}"

  install_apt_deps
  ensure_user
  ensure_app_root
  ensure_venv
  install_python_deps

  prompt_db
  prompt_admin_bootstrap
  setup_mariadb

  generate_siteconfig
  init_app_tables
  import_seed_sql
  create_initial_admin

  fix_permissions
  install_systemd_units
  install_nginx

  echo "Install complete. Main site: http://<server>/  Admin panel: http://<server>:81/adminpanel/"
}

main "$@"
