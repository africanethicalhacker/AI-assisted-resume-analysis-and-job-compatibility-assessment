from flask import Blueprint, Response, flash, redirect, render_template, url_for
from flask_login import current_user

from ..forms import AssessmentForm
from ..models.assessment import Assessment
from ..models.job import JobDescription
from ..models.resume import Resume
from ..extensions import limiter
from ..security.rbac import get_owned_or_404, roles_required
from ..services import assessment_service, report_service, resume_service
from ..services.assessment_service import AssessmentError

bp = Blueprint("assessments", __name__, url_prefix="/assessments")


@bp.route("/", methods=["GET", "POST"])
@limiter.limit("60 per hour", methods=["POST"])
@roles_required("candidate")
def index():
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).all()
    jobs = JobDescription.query.filter_by(user_id=current_user.id).order_by(JobDescription.created_at.desc()).all()
    form = AssessmentForm()
    form.resume_id.choices = [(r.id, resume_service.display_name(r)) for r in resumes]
    form.job_id.choices = [(j.id, j.title) for j in jobs]
    if form.validate_on_submit():
        try:
            a = assessment_service.run_assessment(current_user, form.resume_id.data, form.job_id.data)
            return redirect(url_for("assessments.detail", assessment_id=a.id))
        except AssessmentError as exc:
            flash(str(exc), "warning")
    history = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.created_at.desc()).limit(50).all()
    return render_template("assessments/index.html", form=form, history=history, have_inputs=bool(resumes and jobs))


@bp.get("/<int:assessment_id>")
@roles_required("candidate")
def detail(assessment_id):
    a = get_owned_or_404(Assessment, assessment_id, current_user)
    order = ["skills", "semantic", "education", "experience", "projects_certs"]
    details = sorted(a.details, key=lambda d: order.index(d.component) if d.component in order else 99)
    skills_rows = next((d.explanation["details"].get("skills", []) for d in details if d.component == "skills"), [])
    return render_template("assessments/detail.html", a=a, details=details, skills_rows=skills_rows, meta=a.meta or {})


@bp.post("/<int:assessment_id>/delete")
@roles_required("candidate")
def delete(assessment_id):
    a = get_owned_or_404(Assessment, assessment_id, current_user)
    assessment_service.delete_assessment(current_user, a)
    flash("Assessment deleted.", "info")
    return redirect(url_for("assessments.index"))


@bp.get("/<int:assessment_id>/report.pdf")
@limiter.limit("30 per hour")
@roles_required("candidate")
def report(assessment_id):
    a = get_owned_or_404(Assessment, assessment_id, current_user)
    pdf = report_service.make_pdf(current_user, a)
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=assessment-{a.id}.pdf",
                             "X-Content-Type-Options": "nosniff"})
