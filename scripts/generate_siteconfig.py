import argparse
import secrets
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-host", default="127.0.0.1")
    parser.add_argument("--db-port", default="3306")
    parser.add_argument("--db-user", required=True)
    parser.add_argument("--db-password", required=True)
    parser.add_argument("--db-name", required=True)
    parser.add_argument("--public-base-url", default="http://localhost")
    parser.add_argument("--mail-server", default="localhost")
    parser.add_argument("--mail-port", default="25")
    parser.add_argument("--mail-default-sender", default="no-reply@trashyneighbors.com")
    parser.add_argument("--google-client-id", default="")
    parser.add_argument("--google-client-secret", default="")
    args = parser.parse_args()

    secret_key = secrets.token_urlsafe(48)

    content = (
        "[app]\n"
        f"secret_key={secret_key}\n"
        f"public_base_url={args.public_base_url}\n"
        f"google_oauth_client_id={args.google_client_id}\n"
        f"google_oauth_client_secret={args.google_client_secret}\n"
        "rate_limit_default=200 per hour\n"
        "\n"
        "[database]\n"
        f"host={args.db_host}\n"
        f"port={args.db_port}\n"
        f"user={args.db_user}\n"
        f"password={args.db_password}\n"
        f"name={args.db_name}\n"
        "\n"
        "[mail]\n"
        f"server={args.mail_server}\n"
        f"port={args.mail_port}\n"
        "use_tls=0\n"
        "use_ssl=0\n"
        "username=\n"
        "password=\n"
        f"default_sender={args.mail_default_sender}\n"
    )

    out_path = Path("siteconfig.cfg").resolve()
    if out_path.exists():
        raise SystemExit(f"Refusing to overwrite existing config: {out_path}")

    out_path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
