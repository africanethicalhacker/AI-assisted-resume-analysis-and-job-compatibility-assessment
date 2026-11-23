"""Job board for candidates: browse open jobs posted by administrators and check eligibility with a CV."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from ..extensions import limiter
from ..forms import EligibilityCheckForm
from ..models.assessment import Assessment
from ..models.job import JobDescription
from ..models.resume import Resume
from ..security.rbac import get_owned_or_404, roles_required
from ..services import board_service, job_service, resume_service
from ..services.assessment_service import AssessmentError
from ..services.resume_service import UploadError

bp = Blueprint("board", __name__, url_prefix="/board")


@bp.get("/")
@roles_required("candidate")
def index():
    jobs = JobDescription.query.filter_by(is_public=True, status="open").order_by(JobDescription.created_at.desc()).all()
    counts = {j.id: sum(r.strength == "mandatory" and r.kind != "responsibility" for r in j.requirements) for j in jobs}
    return render_template("board/index.html", jobs=jobs, counts=counts)


@bp.route("/<int:job_id>", methods=["GET", "POST"])
@limiter.limit("40 per hour", methods=["POST"])
@roles_required("candidate")
def detail(job_id):
    job = job_service.get_posting(job_id, open_only=True)
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).all()
    form = EligibilityCheckForm()
    form.resume_id.choices = [(0, "None: I will upload a CV below")] + [(r.id, resume_service.display_name(r)) for r in resumes]
    if form.validate_on_submit():
        try:
            a = board_service.run_check(current_user, job, form.resume_id.data, form.file.data)
            return redirect(url_for("board.result", assessment_id=a.id))
        except (UploadError, AssessmentError) as exc:
            flash(str(exc), "danger")
    groups = {"mandatory": [], "preferred": [], "optional": []}
    responsibilities = []
    for r in job.requirements:
        (responsibilities if r.kind == "responsibility" else groups[r.strength]).append(r)
    return render_template("board/detail.html", job=job, form=form, groups=groups, responsibilities=responsibilities,
                           description=job_service.load_text(job))


@bp.get("/result/<int:assessment_id>")
@roles_required("candidate")
def result(assessment_id):
    a = get_owned_or_404(Assessment, assessment_id, current_user)
    meta = a.meta or {}
    if not meta.get("eligibility"):
        return redirect(url_for("assessments.detail", assessment_id=a.id))
    order = ["skills", "semantic", "education", "experience", "projects_certs"]
    details = sorted(a.details, key=lambda d: order.index(d.component) if d.component in order else 99)
    return render_template("board/result.html", a=a, meta=meta, elig=meta["eligibility"], details=details,
                           priorities=(meta.get("gap") or {}).get("priorities", [])[:5])
