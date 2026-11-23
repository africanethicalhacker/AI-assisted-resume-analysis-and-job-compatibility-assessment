import pytest

from app.ai.matching.scoring import DEFAULT_WEIGHTS, score_assessment
from app.ai.matching.similarity import semantic_similarity
from app.ai.recommend.gap import analyse_gap
from app.ai.recommend.roles import ROLES, recommend_roles
from app.ai.skills.taxonomy import SEED, SkillMatcher
from tests.unit.test_matching import JOB, PROFILE, REQS, RESUME

M = SkillMatcher.from_seed()


def _result():
    sem = semantic_similarity(RESUME, JOB, "tfidf", None)
    return score_assessment(PROFILE, REQS, DEFAULT_WEIGHTS, sem, M)


def test_gap_structure_and_priorities():
    r = _result()
    gap = analyse_gap(PROFILE, REQS, r["components"])
    s = gap["skills"]
    assert [m["skill"] for m in s["matched"]] == ["Splunk", "Wireshark"]
    assert [p["skill"] for p in s["partial"]] == ["SIEM"]
    assert [m["skill"] for m in s["missing"]["preferred"]] == ["Kali Linux"]
    assert s["missing"]["mandatory"] == []
    assert "Python" in s["additional"]                           # explicit, relevant, not required by the job
    assert gap["education"]["level_met"] is True
    assert gap["experience"]["shortfall_months"] == 16.0         # 24 required - 8 effective
    assert gap["certifications"]["missing"] == [] and gap["certifications"]["held"] == ["Security+"]
    # potential points: Kali is worth skills_weight x 100 x 2/10
    eff = next(c for c in r["components"] if c["name"] == "skills")["effective_weight"]
    assert s["missing"]["preferred"][0]["potential_points"] == pytest.approx(eff * 100 * 0.2, abs=0.01)
    assert gap["priorities"][0]["potential_points"] >= gap["priorities"][-1]["potential_points"]


def test_gap_handles_job_without_skills():
    sem = semantic_similarity(RESUME, JOB, "tfidf", None)
    r = score_assessment(PROFILE, [{"kind": "domain", "text": "x", "strength": "mandatory"}], DEFAULT_WEIGHTS, sem, M)
    gap = analyse_gap(PROFILE, [], r["components"])
    assert gap["skills"]["applicable"] is False and gap["summary"]["matched"] == 0


def test_roles_only_reference_taxonomy_skills():
    names = {s[0] for s in SEED}
    for role in ROLES:
        assert set(role["core"]) <= names and set(role["support"]) <= names, role["name"]


def test_recommendations_evidence_based():
    profile = {"skills": [
        {"name": "Splunk", "source_type": "explicit"}, {"name": "SIEM", "source_type": "explicit"},
        {"name": "SOC Operations", "source_type": "explicit"}, {"name": "Incident Response", "source_type": "explicit"},
        {"name": "Linux", "source_type": "explicit"}, {"name": "Python", "source_type": "explicit"}],
        "certifications": [{"name": "CompTIA Security+"}]}
    recs = recommend_roles(profile)
    assert recs[0]["role_name"] in {"SOC Analyst", "Security Operations Engineer"}
    assert [r["rank"] for r in recs] == list(range(1, len(recs) + 1))
    assert all(r["fit_score"] >= 30 for r in recs)
    soc = next(r for r in recs if r["role_name"] == "SOC Analyst")
    assert "SIEM" in soc["matching_skills"] and "Network Security" in soc["missing_core_skills"]
    assert next(c for c in soc["suggested_certs"] if c["name"] == "CompTIA Security+")["already_held"] is True
    assert soc["roadmap"][0]["priority"] == "core" and soc["roadmap"][0]["skill"] == "Network Security"
    assert not any(r["role_name"] == "Penetration Tester" for r in recs)          # no pentest evidence


def test_no_evidence_means_no_recommendations():
    assert recommend_roles({"skills": [], "certifications": []}) == []
    only_inferred = {"skills": [{"name": "SIEM", "source_type": "inferred"}, {"name": "SOC Operations", "source_type": "inferred"}], "certifications": []}
    assert recommend_roles(only_inferred) == []                                     # needs an explicit core skill
