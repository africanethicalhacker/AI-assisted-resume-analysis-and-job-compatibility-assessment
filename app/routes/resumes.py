from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from ..extensions import limiter
from ..forms import UploadForm
from ..models.resume import Resume
from ..security.audit import log_event
from ..security.rbac import get_owned_or_404, roles_required
from ..ai.parsing.errors import ParseError
from ..services import profile_service, resume_service
from ..services.resume_service import UploadError

bp = Blueprint("resumes", __name__, url_prefix="/resumes")


@bp.route("/", methods=["GET", "POST"])
@limiter.limit("20 per hour", methods=["POST"])
@roles_required("candidate")
def index():
    form = UploadForm()
    if form.validate_on_submit():
        try:
            resume = resume_service.upload_resume(current_user, form.file.data)
            try:
                profile_service.parse_resume(current_user, resume)
                flash("Resume uploaded, scanned, encrypted and analysed.", "success")
            except ParseError as exc:
                flash(f"Resume stored securely, but it could not be analysed: {exc}", "warning")
            return redirect(url_for("resumes.detail", resume_id=resume.id))
        except UploadError as exc:
            flash(str(exc), "danger")
    items = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).all()
    rows = [(r, resume_service.display_name(r)) for r in items]
    return render_template("resumes/index.html", form=form, rows=rows)


@bp.get("/<int:resume_id>")
@roles_required("candidate")
def detail(resume_id):
    resume = get_owned_or_404(Resume, resume_id, current_user)
    log_event("resume.view", "success", user_id=current_user.id, resource_type="resumes", resource_id=resume.id)
    return render_template("resumes/detail.html", resume=resume,
                           name=resume_service.display_name(resume),
                           profile=profile_service.load_profile(resume))


@bp.post("/<int:resume_id>/delete")
@roles_required("candidate")
def delete(resume_id):
    resume = get_owned_or_404(Resume, resume_id, current_user)
    resume_service.delete_resume(current_user, resume)
    flash("Resume permanently deleted.", "info")
    return redirect(url_for("resumes.index"))


@bp.post("/<int:resume_id>/reparse")
@roles_required("candidate")
def reparse(resume_id):
    resume = get_owned_or_404(Resume, resume_id, current_user)
    try:
        profile_service.parse_resume(current_user, resume)
        flash("Resume re-analysed with the current skill taxonomy.", "success")
    except ParseError as exc:
        flash(f"Could not analyse the resume: {exc}", "warning")
    return redirect(url_for("resumes.detail", resume_id=resume.id))
