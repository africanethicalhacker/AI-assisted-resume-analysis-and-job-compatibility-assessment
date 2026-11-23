from ..ai.skills.taxonomy import SEED, SkillMatcher
from ..extensions import db
from ..models.profile import Skill


def ensure_seed() -> int:
    """Insert missing seed skills (idempotent). Returns number added."""
    existing = {s.name.lower() for s in Skill.query.with_entities(Skill.name).all()}
    added = 0
    for name, category, aliases in SEED:
        if name.lower() not in existing:
            db.session.add(Skill(name=name, category=category, aliases="|".join(aliases), is_active=True))
            added += 1
    if added:
        db.session.commit()
    return added


def get_matcher() -> SkillMatcher:
    if Skill.query.count() == 0:
        ensure_seed()
    rows = Skill.query.filter_by(is_active=True).all()
    return SkillMatcher((r.name, r.category, [a for a in (r.aliases or "").split("|") if a.strip()]) for r in rows)


def skill_id_map() -> dict:
    return {s.name: s.id for s in Skill.query.all()}
