from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from ..extensions import limiter
from ..forms import JobForm
from ..models.job import JobDescription
from ..security.rbac import get_owned_or_404, roles_required
from ..services import job_service
from ..services.job_service import JobError

bp = Blueprint("jobs", __name__, url_prefix="/jobs")


@bp.route("/", methods=["GET", "POST"])
@limiter.limit("40 per hour", methods=["POST"])
@roles_required("candidate")
def index():
    from flask import current_app
    form = JobForm()
    if form.validate_on_submit():
        try:
            text = (form.text.data or "").strip()
            if form.file.data and getattr(form.file.data, "filename", ""):
                text = job_service.text_from_upload(current_user, form.file.data, current_app.config)
            if not text:
                raise JobError("Paste a job description or upload a file.")
            job = job_service.create_job(current_user, text, form.title.data or "", form.organization.data or "")
            flash("Job description analysed.", "success")
            return redirect(url_for("jobs.detail", job_id=job.id))
        except JobError as exc:
            flash(str(exc), "danger")
    jobs = JobDescription.query.filter_by(user_id=current_user.id).order_by(JobDescription.created_at.desc()).all()
    return render_template("jobs/index.html", form=form, jobs=jobs)


@bp.get("/<int:job_id>")
@roles_required("candidate")
def detail(job_id):
    job = get_owned_or_404(JobDescription, job_id, current_user)
    groups = {"mandatory": [], "preferred": [], "optional": []}
    responsibilities = []
    for r in job.requirements:
        (responsibilities if r.kind == "responsibility" else groups[r.strength]).append(r)
    return render_template("jobs/detail.html", job=job, groups=groups, responsibilities=responsibilities)


@bp.post("/<int:job_id>/delete")
@roles_required("candidate")
def delete(job_id):
    job = get_owned_or_404(JobDescription, job_id, current_user)
    job_service.delete_job(current_user, job)
    flash("Job description deleted.", "info")
    return redirect(url_for("jobs.index"))
