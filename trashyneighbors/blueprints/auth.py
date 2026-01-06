import json
from datetime import datetime

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, limiter, mail
from ..models import AuditEventType, AuditLog, User, UserRole

bp = Blueprint("auth", __name__)

oauth = OAuth()


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _audit(event_type, entity_type=None, entity_id=None, payload=None):
    payload = payload or {}
    log = AuditLog(
        event_type=event_type,
        actor_user_id=(current_user.user_id if current_user.is_authenticated else None),
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        user_agent=request.headers.get("User-Agent"),
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        event_json=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        created_at=datetime.utcnow(),
    )
    db.session.add(log)


def _send_verification_email(user: User):
    token = _serializer().dumps({"user_id": user.user_id, "email": user.email})
    base_url = current_app.config["TRASHYNEIGHBORS_PUBLIC_BASE_URL"].rstrip("/")
    verify_url = f"{base_url}{url_for('auth.verify_email', token=token)}"

    msg = Message(
        subject="Verify your TrashyNeighbors email",
        recipients=[user.email],
        body=(
            "Welcome to TrashyNeighbors.\n\n"
            "Verify your email by clicking this link:\n\n"
            f"{verify_url}\n"
        ),
    )
    mail.send(msg)


@bp.before_app_request
def init_oauth():
    if not hasattr(current_app, "_trash_oauth_initialized"):
        oauth.init_app(current_app)
        client_id = current_app.config.get("TRASHYNEIGHBORS_GOOGLE_OAUTH_CLIENT_ID")
        client_secret = current_app.config.get(
            "TRASHYNEIGHBORS_GOOGLE_OAUTH_CLIENT_SECRET"
        )
        if client_id and client_secret:
            oauth.register(
                name="google",
                client_id=client_id,
                client_secret=client_secret,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={"scope": "openid email profile"},
            )
        current_app._trash_oauth_initialized = True


@bp.get("/register")
@limiter.limit("20 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/register.html")


@bp.post("/register")
@limiter.limit("20 per hour")
def register_post():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    email = (request.form.get("email") or "").strip().lower()
    screen_name = (request.form.get("screen_name") or "").strip()
    password = request.form.get("password") or ""

    if not email or not screen_name or not password:
        flash("All fields are required.")
        return redirect(url_for("auth.register"))

    if db.session.query(User).filter_by(email=email).first() is not None:
        flash("Email already registered.")
        return redirect(url_for("auth.register"))

    if db.session.query(User).filter_by(screen_name=screen_name).first() is not None:
        flash("Screen name already taken.")
        return redirect(url_for("auth.register"))

    user = User(
        email=email,
        screen_name=screen_name,
        password_hash=generate_password_hash(password),
        role=UserRole.UNVERIFIED,
    )
    db.session.add(user)
    db.session.flush()

    _audit(AuditEventType.REGISTER.value, entity_type="user", entity_id=user.user_id)
    db.session.commit()

    _send_verification_email(user)
    flash("Check your email to verify your account.")
    return redirect(url_for("auth.login"))


@bp.get("/verify-email/<token>")
def verify_email(token):
    try:
        data = _serializer().loads(token, max_age=60 * 60 * 24 * 3)
    except BadSignature:
        flash("Invalid or expired verification link.")
        return redirect(url_for("auth.login"))

    user_id = data.get("user_id")
    email = data.get("email")
    if not user_id or not email:
        flash("Invalid verification link.")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, int(user_id))
    if user is None or user.email != email:
        flash("Invalid verification link.")
        return redirect(url_for("auth.login"))

    if user.email_verified_at is None:
        user.email_verified_at = datetime.utcnow()
        user.role = UserRole.VERIFIED
        _audit(
            AuditEventType.VERIFY_EMAIL.value, entity_type="user", entity_id=user.user_id
        )
        db.session.commit()

    flash("Email verified. You can now post, comment, and vote.")
    return redirect(url_for("auth.login"))


@bp.get("/login")
@limiter.limit("50 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")


@bp.post("/login")
@limiter.limit("50 per hour")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    user = db.session.query(User).filter_by(email=email).first()
    if user is None or not user.password_hash:
        flash("Invalid credentials.")
        return redirect(url_for("auth.login"))

    if not check_password_hash(user.password_hash, password):
        flash("Invalid credentials.")
        return redirect(url_for("auth.login"))

    login_user(user)
    _audit(AuditEventType.LOGIN.value, entity_type="user", entity_id=user.user_id)
    db.session.commit()
    return redirect(url_for("main.index"))


@bp.get("/login/google")
@limiter.limit("20 per hour")
def login_google():
    google = oauth.create_client("google")
    if google is None:
        flash("Google login is not configured.")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.login_google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@bp.get("/login/google/callback")
def login_google_callback():
    google = oauth.create_client("google")
    if google is None:
        flash("Google login is not configured.")
        return redirect(url_for("auth.login"))

    token = google.authorize_access_token()
    userinfo = google.parse_id_token(token)

    email = (userinfo.get("email") or "").strip().lower()
    if not email:
        flash("Google login failed.")
        return redirect(url_for("auth.login"))

    user = db.session.query(User).filter_by(email=email).first()
    if user is None:
        screen_name = (userinfo.get("name") or email.split("@")[0]).strip()[:64]
        candidate = screen_name
        suffix = 1
        while db.session.query(User).filter_by(screen_name=candidate).first() is not None:
            suffix += 1
            candidate = f"{screen_name[:58]}_{suffix}"

        user = User(
            email=email,
            screen_name=candidate,
            password_hash=None,
            role=UserRole.VERIFIED,
            email_verified_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.flush()

    login_user(user)
    _audit(AuditEventType.LOGIN.value, entity_type="user", entity_id=user.user_id)
    db.session.commit()

    return redirect(url_for("main.index"))


@bp.get("/logout")
@login_required
def logout():
    _audit(AuditEventType.LOGOUT.value, entity_type="user", entity_id=current_user.user_id)
    logout_user()
    db.session.commit()
    return redirect(url_for("main.index"))
