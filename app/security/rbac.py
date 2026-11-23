"""Server-side authorisation: role checks and ownership checks."""
from functools import wraps

from flask import abort, request
from flask_login import current_user

from ..extensions import db, login_manager
from .audit import log_event


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                log_event("authz.denied", "denied", user_id=current_user.id,
                          detail=f"role={current_user.role} endpoint={request.endpoint}")
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_owned_or_404(model, obj_id, user):
    """Return the record only if it belongs to `user`.

    Non-owners get 404 (not 403) so record IDs cannot be probed for existence.
    """
    obj = db.session.get(model, obj_id)
    if obj is None:
        abort(404)
    if getattr(obj, "user_id", None) != user.id:
        log_event("authz.denied", "denied", user_id=user.id,
                  resource_type=model.__tablename__, resource_id=obj_id, detail="not owner")
        abort(404)
    return obj
