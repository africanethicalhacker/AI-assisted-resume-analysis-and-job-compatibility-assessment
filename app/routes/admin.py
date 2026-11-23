import re

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db, limiter
from ..forms import JobPostForm, ScoringForm, SkillForm
from ..models.profile import Skill
from ..security.audit import log_event
from ..models.job import JobDescription
from ..services import job_service, scoring_config
from ..services.job_service import JobError
from ..services.taxonomy_service import ensure_seed

from ..models.audit import AuditLog
from ..models.user import User
from ..security.audit import verify_chain
from ..security.rbac import roles_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@roles_required("administrator")
def index():
    ok, bad_id = verify_chain()
    recent = AuditLog.query.order_by(AuditLog.id.desc()).limit(50).all()
    return render_template("admin/index.html", users=User.query.count(),
                           chain_ok=ok, bad_id=bad_id, recent=recent)


_ALIAS_OK = re.compile(r"^[A-Za-z0-9 .+#&/\-]{1,60}$")


@bp.route("/skills", methods=["GET", "POST"])
@roles_required("administrator")
def skills():
    ensure_seed()
    form = SkillForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        aliases = [a.strip() for a in (form.aliases.data or "").split("|") if a.strip()]
        if not _ALIAS_OK.match(name) or any(not _ALIAS_OK.match(a) for a in aliases):
            flash("Names and aliases may only use letters, digits, spaces and . + # & / -", "danger")
        elif Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first():
            flash("That skill already exists.", "danger")
        else:
            sk = Skill(name=name, category=form.category.data, aliases="|".join(aliases), created_by=current_user.id)
            db.session.add(sk)
            db.session.commit()
            log_event("admin.skill_add", "success", user_id=current_user.id, resource_type="skills", resource_id=sk.id)
            flash("Skill added.", "success")
            return redirect(url_for("admin.skills"))
    return render_template("admin/skills.html", form=form,
                           skills=Skill.query.order_by(Skill.category, Skill.name).all())


@bp.post("/skills/<int:skill_id>/toggle")
@roles_required("administrator")
def toggle_skill(skill_id):
    sk = db.session.get(Skill, skill_id)
    if sk is None:
        from flask import abort
        abort(404)
    sk.is_active = not sk.is_active
    db.session.commit()
    log_event("admin.skill_toggle", "success", user_id=current_user.id, resource_type="skills",
              resource_id=sk.id, detail=f"active={sk.is_active}")
    return redirect(url_for("admin.skills"))


@bp.route("/scoring", methods=["GET", "POST"])
@roles_required("administrator")
def scoring():
    cfg = scoring_config.load()
    form = ScoringForm(data={**cfg["weights"], "semantic_mode": cfg["semantic_mode"], "blend_alpha": cfg["blend_alpha"]})
    if form.validate_on_submit():
        new = {"weights": {k: getattr(form, k).data for k in cfg["weights"]},
               "semantic_mode": form.semantic_mode.data, "blend_alpha": form.blend_alpha.data}
        try:
            saved = scoring_config.save(new)
        except scoring_config.ConfigError as exc:
            flash(str(exc), "danger")
        else:
            log_event("admin.scoring_update", "success", user_id=current_user.id,
                      detail=" ".join(f"{k}={v}" for k, v in saved["weights"].items()) + f" mode={saved['semantic_mode']}")
            flash("Scoring configuration saved. It applies to new assessments only.", "success")
            return redirect(url_for("admin.scoring"))
    return render_template("admin/scoring.html", form=form)


# ---------------- job postings ----------------
@bp.route("/jobs", methods=["GET", "POST"])
@limiter.limit("40 per hour", methods=["POST"])
@roles_required("administrator")
def jobs():
    form = JobPostForm()
    if form.validate_on_submit():
        try:
            text = (form.text.data or "").strip()
            if form.file.data and getattr(form.file.data, "filename", ""):
                text = job_service.text_from_upload(current_user, form.file.data, current_app.config)
            if not text:
                raise JobError("Paste the job description or upload a file.")
            job = job_service.create_job(current_user, text, form.title.data, form.organization.data or "",
                                         public=True, threshold=form.threshold.data)
            flash("Job posted. Review the requirements below before candidates use it.", "success")
            return redirect(url_for("admin.job_detail", job_id=job.id))
        except JobError as exc:
            flash(str(exc), "danger")
    postings = JobDescription.query.filter_by(is_public=True).order_by(JobDescription.created_at.desc()).all()
    stats = {j.id: job_service.posting_stats(j) for j in postings}
    return render_template("admin/jobs.html", form=form, postings=postings, stats=stats)


@bp.get("/jobs/<int:job_id>")
@roles_required("administrator")
def job_detail(job_id):
    job = job_service.get_posting(job_id)
    reqs = [r for r in job.requirements if r.kind != "responsibility"]
    reqs.sort(key=lambda r: ("mandatory", "preferred", "optional").index(r.strength))
    return render_template("admin/job_detail.html", job=job, reqs=reqs, stats=job_service.posting_stats(job),
                           description=job_service.load_text(job))


@bp.post("/jobs/<int:job_id>/requirements")
@roles_required("administrator")
def job_requirements(job_id):
    job = job_service.get_posting(job_id)
    strengths, removals = {}, set()
    for r in job.requirements:
        value = request.form.get(f"strength_{r.id}")
        if value:
            strengths[r.id] = value
        if request.form.get(f"remove_{r.id}"):
            removals.add(r.id)
    if "threshold" in request.form:
        try:
            job_service.set_threshold(current_user, job, int(request.form["threshold"]))
        except ValueError:
            flash("The threshold must be a whole number from 0 to 100.", "danger")
    job_service.update_requirements(current_user, job, strengths, removals)
    flash("Requirements updated. Changes apply to checks made from now on.", "success")
    return redirect(url_for("admin.job_detail", job_id=job.id))


@bp.post("/jobs/<int:job_id>/status")
@roles_required("administrator")
def job_status(job_id):
    job = job_service.get_posting(job_id)
    job_service.set_status(current_user, job, "closed" if job.status == "open" else "open")
    flash(f"Job is now {job.status}.", "info")
    return redirect(url_for("admin.job_detail", job_id=job.id))


@bp.post("/jobs/<int:job_id>/delete")
@roles_required("administrator")
def job_delete(job_id):
    job = job_service.get_posting(job_id)
    try:
        job_service.delete_posting(current_user, job)
    except JobError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.job_detail", job_id=job.id))
    flash("Job deleted.", "info")
    return redirect(url_for("admin.jobs"))
