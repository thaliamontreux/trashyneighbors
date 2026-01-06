import argparse
from datetime import datetime

from werkzeug.security import generate_password_hash

from trashyneighbors import create_app
from trashyneighbors.extensions import db
from trashyneighbors.models import User, UserRole


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--screen-name", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    app = create_app(admin_mode=True)

    with app.app_context():
        email = args.email.strip().lower()
        screen_name = args.screen_name.strip()

        if db.session.query(User).filter_by(email=email).first() is not None:
            raise SystemExit("User with that email already exists")

        if db.session.query(User).filter_by(screen_name=screen_name).first() is not None:
            raise SystemExit("User with that screen name already exists")

        user = User(
            email=email,
            screen_name=screen_name,
            password_hash=generate_password_hash(args.password),
            role=UserRole.SUPER_ADMINISTRATOR,
            email_verified_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()

    print("Created super admin user")


if __name__ == "__main__":
    main()
