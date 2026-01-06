import configparser
from pathlib import Path


def load_site_config():
    cfg_path = Path("siteconfig.cfg").resolve()
    if not cfg_path.is_file():
        raise RuntimeError(
            "Missing required siteconfig.cfg. Run scripts/generate_siteconfig.py"
        )

    parser = configparser.ConfigParser()
    parser.read(cfg_path, encoding="utf-8")

    if "app" not in parser or "database" not in parser:
        raise RuntimeError("siteconfig.cfg must contain [app] and [database]")

    app_cfg = parser["app"]
    db_cfg = parser["database"]

    secret_key = app_cfg.get("secret_key")
    if not secret_key:
        raise RuntimeError("[app] secret_key is required")

    db_user = db_cfg.get("user")
    db_password = db_cfg.get("password")
    db_host = db_cfg.get("host", "127.0.0.1")
    db_port = db_cfg.get("port", "3306")
    db_name = db_cfg.get("name")

    if not db_user or db_password is None or not db_name:
        raise RuntimeError("[database] user, password, name are required")

    sqlalchemy_uri = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        "?charset=utf8mb4"
    )

    mail_cfg = parser["mail"] if "mail" in parser else {}

    cfg = {
        "SECRET_KEY": secret_key,
        "SQLALCHEMY_DATABASE_URI": sqlalchemy_uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "RATELIMIT_DEFAULT": app_cfg.get("rate_limit_default", "200 per hour"),
        "MAIL_SERVER": mail_cfg.get("server", "localhost"),
        "MAIL_PORT": int(mail_cfg.get("port", "25")),
        "MAIL_USE_TLS": mail_cfg.get("use_tls", "0") == "1",
        "MAIL_USE_SSL": mail_cfg.get("use_ssl", "0") == "1",
        "MAIL_USERNAME": mail_cfg.get("username"),
        "MAIL_PASSWORD": mail_cfg.get("password"),
        "MAIL_DEFAULT_SENDER": mail_cfg.get("default_sender"),
        "TRASHYNEIGHBORS_PUBLIC_BASE_URL": app_cfg.get(
            "public_base_url", "http://localhost"
        ),
        "TRASHYNEIGHBORS_GOOGLE_OAUTH_CLIENT_ID": app_cfg.get(
            "google_oauth_client_id", ""
        ),
        "TRASHYNEIGHBORS_GOOGLE_OAUTH_CLIENT_SECRET": app_cfg.get(
            "google_oauth_client_secret", ""
        ),
    }

    return cfg
