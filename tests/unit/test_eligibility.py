from app.ai.matching.eligibility import decide
from app.ai.matching.scoring import DEFAULT_WEIGHTS, score_assessment
from app.ai.matching.similarity import semantic_similarity
from app.ai.pipeline import analyse_job_text, analyse_resume, score_pair
from app.ai.skills.taxonomy import SkillMatcher

M = SkillMatcher.from_seed()

RESUME = """Asha Rao
asha@example.com

EDUCATION
M.Sc. Cyber Security, National Forensic Sciences University 2024 - 2026

TECHNICAL SKILLS
Python, Splunk, Wireshark, Nmap

EXPERIENCE
Security Analyst - ExampleCorp  Jan 2023 - Jan 2025
- Monitored alerts

CERTIFICATIONS
CompTIA Security+
"""
JOB = """Job Title: SOC Analyst

Requirements
- Hands-on Splunk and Wireshark
- 2+ years of experience
- Bachelor's degree in computer science
- CompTIA Security+ certification
"""


def run(resume=RESUME, job=JOB, threshold=60):
    prof, jb = analyse_resume(resume, M), analyse_job_text(job, M)
    res = score_pair(prof, jb, M)
    return decide(res["components"], res["final_score"], threshold), res


def test_all_mandatory_met_and_high_match_is_eligible():
    e, res = run(threshold=30)
    assert e["verdict"] == "eligible" and e["percentage"] == int(round(res["final_score"]))
    assert all(c["status"] == "met" for c in e["checks"]) and e["label"] == "Likely eligible"
    assert {c["type"] for c in e["checks"]} == {"Skill", "Education", "Experience", "Certification"}


def test_threshold_decides_between_eligible_and_partial():
    e_low, res = run(threshold=30)
    pct = int(round(res["final_score"]))
    e_high, _ = run(threshold=pct + 10)
    assert e_low["verdict"] == "eligible"
    assert e_high["verdict"] == "partial" and "below" in e_high["reasons"][0]
    e_far, _ = run(threshold=min(100, pct + 40))
    assert e_far["verdict"] == "not_eligible"


def test_missing_mandatory_skill_blocks_eligibility_even_with_high_score():
    e, _ = run(resume=RESUME.replace("Splunk, ", "").replace("Wireshark, ", ""), threshold=10)
    assert e["verdict"] != "eligible"
    assert any(c["status"] == "not met" and c["requirement"] == "Splunk" for c in e["checks"])
    assert any("not met" in r.lower() for r in e["reasons"])


def test_two_unmet_mandatory_requirements_is_not_eligible():
    weak = "Asha Rao\n\nTECHNICAL SKILLS\nPython\n"
    e, _ = run(resume=weak, threshold=5)
    assert len([c for c in e["checks"] if c["status"] == "not met"]) >= 2
    assert e["verdict"] == "not_eligible"


def test_inferred_only_skill_is_unconfirmed_not_failed():
    job = "SOC Analyst\n\nRequirements\n- Experience with SIEM tools\n"
    resume = "Asha Rao\n\nTECHNICAL SKILLS\nSplunk\n"
    e, _ = run(resume=resume, job=job, threshold=10)
    assert [c["status"] for c in e["checks"] if c["requirement"] == "SIEM"] == ["unconfirmed"]
    assert e["verdict"] == "partial"                      # cannot be fully eligible until the skill is written explicitly


def test_preferred_requirements_do_not_block():
    job = "SOC Analyst\n\nRequirements\n- Hands-on Splunk\n\nNice to have\n- Kali Linux\n"
    e, _ = run(job=job, threshold=10)
    assert e["verdict"] == "eligible" and [c["requirement"] for c in e["checks"] if c["type"] == "Skill"] == ["Splunk"]


def test_job_without_mandatory_items_depends_on_score_only():
    e, res = run(job="SOC Analyst\n\nNice to have\n- Kali Linux\n", threshold=0)
    assert e["checks"] == [] and e["verdict"] == "eligible"


def test_percentage_matches_final_score_and_rule_text_present():
    e, res = run()
    assert e["percentage"] == int(round(res["final_score"])) and "screening aid" in e["rule"]
