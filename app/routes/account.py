import json

from flask import Blueprint, Response, flash, redirect, render_template, session, url_for
from flask_login import current_user, logout_user

from ..extensions import limiter
from ..forms import DeleteAccountForm
from ..models.resume import Resume
from ..security.rbac import roles_required
from ..services import account_service
from ..services.auth_service import AuthError

bp = Blueprint("account", __name__, url_prefix="/account")


@bp.get("/")
@roles_required("candidate")
def index():
    return render_template("account/index.html", form=DeleteAccountForm(),
                           n_resumes=Resume.query.filter_by(user_id=current_user.id).count())


@bp.get("/export.json")
@limiter.limit("10 per hour")
@roles_required("candidate")
def export():
    data = account_service.export_user_data(current_user)
    return Response(json.dumps(data, indent=2), mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=my-data.json"})


@bp.post("/delete")
@limiter.limit("5 per hour")
@roles_required("candidate")
def delete():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        try:
            account_service.delete_account(current_user, form.password.data)
        except AuthError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("account.index"))
        session.clear()
        logout_user()
        flash("Your account and all stored data were permanently deleted.", "info")
        return redirect(url_for("auth.login"))
    flash("Please enter your password and type DELETE to confirm.", "danger")
    return redirect(url_for("account.index"))
