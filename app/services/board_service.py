"""Eligibility check: a candidate tests a CV against a job posted by an administrator."""
from ..ai.parsing.errors import ParseError
from ..models.resume import Resume
from ..security.rbac import get_owned_or_404
from . import assessment_service, profile_service, resume_service
from .assessment_service import AssessmentError


def run_check(user, job, resume_id: int, file_storage=None):
    """Upload (optional), analyse the CV, and assess it against `job`. Returns the Assessment."""
    if file_storage is not None and getattr(file_storage, "filename", ""):
        resume = resume_service.upload_resume(user, file_storage)          # raises UploadError with a safe message
    elif resume_id:
        resume = get_owned_or_404(Resume, resume_id, user)
    else:
        raise AssessmentError("Choose a CV you already uploaded, or upload one now.")
    if resume.profile is None:
        try:
            profile_service.parse_resume(user, resume)
        except ParseError as exc:
            raise AssessmentError(f"Your CV was stored securely but could not be analysed: {exc}") from exc
    return assessment_service.run_assessment(user, resume.id, job.id)
