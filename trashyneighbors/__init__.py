from pathlib import Path
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import load_site_config
from .extensions import db, limiter, login_manager, mail, migrate
from .models import User


def create_app(admin_mode=False):
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        instance_relative_config=False,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
    )

    site_cfg = load_site_config()
    app.config.update(site_cfg)

    if admin_mode:
        app.config["TRASHYNEIGHBORS_ADMIN_MODE"] = True

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    from .blueprints.auth import bp as auth_bp
    from .blueprints.main import bp as main_bp
    from .blueprints.api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    if admin_mode:
        from .blueprints.adminpanel import bp as admin_bp

        app.register_blueprint(admin_bp, url_prefix="/adminpanel")

    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
