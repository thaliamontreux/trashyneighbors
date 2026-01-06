from flask import Blueprint, abort, render_template
from flask_login import current_user

from ..models import UserRole

bp = Blueprint("adminpanel", __name__)


@bp.get("/")
def admin_index():
    if not current_user.is_authenticated:
        abort(403)
    if current_user.role not in (
        UserRole.MODERATOR,
        UserRole.ADMINISTRATOR,
        UserRole.SUPER_ADMINISTRATOR,
    ):
        abort(403)
    return render_template("admin/index.html")
