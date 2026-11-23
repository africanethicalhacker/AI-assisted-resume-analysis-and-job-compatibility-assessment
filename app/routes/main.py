from flask import Blueprint, current_app, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..services import admin_service, dashboard_service

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return redirect(url_for("main.dashboard" if current_user.is_authenticated else "auth.login"))


@bp.get("/dashboard")
@login_required
def dashboard():
    if current_user.role == "administrator":
        return render_template("dashboard.html", admin=True, data=None, ov=admin_service.overview(current_app.extensions))
    return render_template("dashboard.html", admin=False, ov=None, data=dashboard_service.dashboard_data(current_user))
