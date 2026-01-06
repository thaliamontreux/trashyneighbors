import argparse

from trashyneighbors import create_app
from trashyneighbors.extensions import db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--drop-first",
        action="store_true",
        help="Drop all app tables before creating them.",
    )
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        if args.drop_first:
            db.drop_all()
        db.create_all()

    print("App tables created")


if __name__ == "__main__":
    main()
