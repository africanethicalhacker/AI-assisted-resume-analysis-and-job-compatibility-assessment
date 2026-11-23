import json

from ..ai.parsing.errors import ParseError
from ..ai.parsing.extractor import PARSER_VERSION, extract_profile
from ..ai.parsing.readers import read_document
from ..extensions import db
from ..models.profile import CandidateProfile, CandidateSkill
from ..models.resume import Resume
from ..security.audit import log_event
from ..security.crypto import get_crypto
from ..security.sanitise import detect_injection, normalise_text
from . import resume_service
from .taxonomy_service import get_matcher, skill_id_map


def _profile_aad(resume: Resume) -> bytes:
    return b"profile:" + resume.stored_name.encode()


def _skill_aad(resume: Resume, name: str) -> bytes:
    return b"skill-evidence:" + resume.stored_name.encode() + b":" + name.encode()


def parse_resume(user, resume: Resume) -> CandidateProfile:
    """Decrypt, read, sanitise, extract, then store the profile encrypted. Raises ParseError."""
    crypto = get_crypto()
    try:
        data = resume_service.read_plaintext(resume)
        read = read_document(data, resume.detected_mime)
    except ParseError as exc:
        log_event("resume.parse", "failure", user_id=user.id, resource_type="resumes",
                  resource_id=resume.id, detail="read_error")
        raise
    text = normalise_text(read.text)
    profile = extract_profile(text, get_matcher())
    profile["text"] = text[:60000]  # encrypted with the profile; used for matching
    profile["security"] = {
        "injection_findings": detect_injection(text),
        "hidden_text_removed_chars": read.hidden_chars,
        "white_text_chars": read.white_text_chars,
    }

    existing = resume.profile
    if existing is not None:
        db.session.delete(existing)
        db.session.flush()
    row = CandidateProfile(resume_id=resume.id, user_id=user.id, parser_version=PARSER_VERSION,
                           resume_quality_score=float(profile["quality"]["score"]),
                           profile_enc=crypto.encrypt_field(json.dumps(profile).encode(), _profile_aad(resume)))
    db.session.add(row)
    db.session.flush()
    ids = skill_id_map()
    for s in profile["skills"]:
        if s["name"] in ids:
            row.skills.append(CandidateSkill(
                skill_id=ids[s["name"]], source_type=s["source_type"], confidence=s["confidence"],
                evidence_enc=crypto.encrypt_field(s["evidence"]["text"][:300].encode(), _skill_aad(resume, s["name"]))))
    db.session.commit()
    flags = len(profile["security"]["injection_findings"])
    log_event("resume.parse", "success", user_id=user.id, resource_type="resumes", resource_id=resume.id,
              detail=f"skills={len(profile['skills'])} injection_flags={flags}")
    return row


def load_profile(resume: Resume):
    if resume.profile is None:
        return None
    raw = get_crypto().decrypt_field(resume.profile.profile_enc, _profile_aad(resume))
    return json.loads(raw)
