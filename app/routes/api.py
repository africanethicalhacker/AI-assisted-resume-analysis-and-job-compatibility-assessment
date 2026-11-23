from flask import Blueprint, jsonify
from flask_login import current_user

from ..models.assessment import Assessment
from ..security.rbac import get_owned_or_404, roles_required
from ..services import dashboard_service

bp = Blueprint("api", __name__, url_prefix="/api/v1")


@bp.get("/dashboard-data")
@roles_required("candidate")
def dashboard_data():
    return jsonify(dashboard_service.dashboard_data(current_user))


@bp.get("/assessments/<int:assessment_id>/chart-data")
@roles_required("candidate")
def chart_data(assessment_id):
    a = get_owned_or_404(Assessment, assessment_id, current_user)
    return jsonify(dashboard_service.assessment_chart_data(a))
