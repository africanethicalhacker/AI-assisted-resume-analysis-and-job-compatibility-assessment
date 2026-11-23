"""Career recommendation engine (Phase 13). Recommends roles only from skills evidenced in the profile.

fit(role) = 100 x sum(w x credit) / sum(w)   core skills w=2, supporting skills w=1,
credit: explicit 1.0, inferred 0.5, absent 0. A role is shown only if at least one core skill is
explicitly evidenced and fit >= MIN_FIT. Weights and thresholds are experimental.
Nothing here predicts hiring, pay, or certification eligibility.
"""
import re

from ..matching.scoring import INFERRED_CREDIT

MIN_FIT = 30.0
DISCLAIMER = ("Suggestions are based only on skills found in your resume. They are not a prediction of employment, "
              "and certification prerequisites change, so check each issuer's current requirements.")

ROLES = [
    {"name": "SOC Analyst",
     "core": ["SIEM", "SOC Operations", "Incident Response", "Network Security"],
     "support": ["Splunk", "ELK Stack", "Wireshark", "Threat Intelligence", "MITRE ATT&CK", "Linux", "Report Writing"],
     "certs": ["CompTIA Security+", "CompTIA CySA+", "Blue Team Level 1 (BTL1)"]},
    {"name": "Cyber Security Analyst",
     "core": ["Information Security", "Network Security", "Risk Management", "Vulnerability Assessment"],
     "support": ["SIEM", "Incident Response", "Python", "Linux", "Security Auditing", "Report Writing"],
     "certs": ["CompTIA Security+", "CompTIA CySA+", "Certified Ethical Hacker (CEH)"]},
    {"name": "Security Operations Engineer",
     "core": ["SIEM", "SOC Operations", "Incident Response", "Linux"],
     "support": ["Splunk", "ELK Stack", "Python", "Bash", "PowerShell", "Cloud Security", "Snort", "Suricata"],
     "certs": ["CompTIA CySA+", "Splunk Core Certified User", "Microsoft SC-200"]},
    {"name": "Penetration Tester",
     "core": ["Penetration Testing", "Web Application Security", "Kali Linux", "Metasploit"],
     "support": ["Burp Suite", "Nmap", "Python", "Bash", "Linux", "Network Security", "Report Writing", "Cryptography"],
     "certs": ["eJPT", "CompTIA PenTest+", "PNPT", "OSCP"]},
    {"name": "Digital Forensics Analyst",
     "core": ["Digital Forensics", "Autopsy", "Volatility", "Incident Response"],
     "support": ["Malware Analysis", "Linux", "Python", "Report Writing", "Cryptography", "Wireshark"],
     "certs": ["GIAC GCFE", "GIAC GCFA", "CHFI"]},
    {"name": "Incident Response Analyst",
     "core": ["Incident Response", "Digital Forensics", "SIEM", "Malware Analysis"],
     "support": ["Threat Hunting", "Volatility", "Splunk", "MITRE ATT&CK", "PowerShell", "Report Writing", "Wireshark"],
     "certs": ["GIAC GCIH", "GIAC GCFA", "CompTIA CySA+"]},
    {"name": "Vulnerability Assessment Analyst",
     "core": ["Vulnerability Assessment", "Nessus", "Nmap", "Risk Management"],
     "support": ["OpenVAS", "Network Security", "Linux", "Report Writing", "Penetration Testing", "Python"],
     "certs": ["CompTIA Security+", "CompTIA PenTest+", "Certified Ethical Hacker (CEH)"]},
    {"name": "Security Consultant",
     "core": ["Risk Management", "Security Auditing", "Information Security", "Communication"],
     "support": ["Report Writing", "Cloud Security", "Cryptography", "Leadership", "Vulnerability Assessment", "Problem Solving"],
     "certs": ["CISSP", "CISM", "CISA", "ISO/IEC 27001 Lead Implementer"]},
    {"name": "Cloud Security Analyst",
     "core": ["Cloud Security", "Information Security", "Network Security", "Linux"],
     "support": ["Python", "Bash", "Risk Management", "SIEM", "Cryptography", "Security Auditing"],
     "certs": ["AWS Certified Security - Specialty", "Microsoft AZ-500", "CCSP"]},
    {"name": "Threat Intelligence Analyst",
     "core": ["Threat Intelligence", "MITRE ATT&CK", "Malware Analysis", "Threat Hunting"],
     "support": ["Python", "SIEM", "Report Writing", "Wireshark", "Incident Response", "Communication"],
     "certs": ["GIAC GCTI", "CompTIA CySA+"]},
]

_ACTIONS = {
    "SIEM": "Learn how log collection, correlation and alerting work; build a small home lab and write a few detection rules.",
    "SOC Operations": "Learn the alert workflow (detect, triage, escalate, document) and practise on public blue-team exercises.",
    "Incident Response": "Study an incident response lifecycle such as NIST SP 800-61 and write a mock incident report.",
    "Network Security": "Review firewalls, IDS/IPS, segmentation and common protocols; practise by analysing traffic in a lab.",
    "Digital Forensics": "Practise acquiring and analysing disk images and memory with open-source tools, documenting chain of custody.",
    "Penetration Testing": "Follow a structured methodology on legal practice targets you own and write a sample report for each.",
    "Web Application Security": "Study the OWASP Top 10 and practise on deliberately vulnerable applications that you run yourself.",
    "Vulnerability Assessment": "Scan a lab network with an authorised scanner, prioritise findings by risk and write a remediation report.",
    "Threat Intelligence": "Learn to collect and assess indicators and map behaviour to MITRE ATT&CK; write a short threat report.",
    "Threat Hunting": "Form hypotheses from ATT&CK techniques and search lab logs for them.",
    "MITRE ATT&CK": "Map your lab exercises and detections to ATT&CK techniques.",
    "Malware Analysis": "Learn static and dynamic analysis inside an isolated virtual machine using well-documented samples.",
    "Cloud Security": "Learn the shared-responsibility model and practise securing identities, storage and logging in a free-tier account.",
    "Risk Management": "Learn risk assessment basics (asset, threat, vulnerability, impact) and build a simple risk register.",
    "Security Auditing": "Study a control framework such as ISO/IEC 27001 and practise mapping controls to evidence.",
    "Information Security": "Cover the CIA triad, access control and security policy basics, and summarise them in your own notes.",
    "Cryptography": "Review symmetric and asymmetric encryption, hashing and PKI; build a small demo with a vetted library.",
    "Python": "Write small security scripts (log parsers, checks for your own lab) and publish them with documentation.",
    "Bash": "Automate routine lab tasks with shell scripts and keep them in a documented repository.",
    "PowerShell": "Automate Windows administration and log queries in a lab and document the scripts.",
    "Linux": "Run a Linux VM daily; practise users, permissions, services and log files.",
    "Splunk": "Practise searches, dashboards and alerts using free sample data.",
    "ELK Stack": "Build a small stack, ingest logs and create dashboards.",
    "Wireshark": "Capture and analyse traffic in a lab and practise with sample packet captures.",
    "Nmap": "Scan your own lab to learn host discovery and service detection, and interpret the output.",
    "Metasploit": "Use it only against lab machines you own to understand exploitation workflows.",
    "Burp Suite": "Intercept and test requests against intentionally vulnerable apps running locally.",
    "Kali Linux": "Set up a VM and learn the standard toolset for your own lab.",
    "Nessus": "Run authenticated and unauthenticated scans against a lab and compare the results.",
    "OpenVAS": "Run scans against a lab network and compare findings with another scanner.",
    "Autopsy": "Analyse a sample disk image and generate a timeline of events.",
    "Volatility": "Analyse sample memory images to list processes and network connections.",
    "Snort": "Write and test simple detection rules against lab traffic.",
    "Suricata": "Run it on lab traffic and tune a few rules.",
    "Communication": "Practise explaining technical findings to a non-technical reader and ask for feedback.",
    "Report Writing": "Write and revise clear technical reports, and have a peer review them.",
    "Leadership": "Lead a small project or study group and note the outcomes.",
    "Problem Solving": "Document how you diagnosed a hard problem step by step.",
}
_DEFAULT_ACTION = "Build working knowledge of {skill}, then show it in a small hands-on project you can list on your resume."


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9+]", "", (name or "").lower())


def _roadmap(missing_core, partial, missing_support, limit=6):
    steps = []
    for skill, kind in [(s, "core") for s in missing_core + partial] + [(s, "supporting") for s in missing_support]:
        if len(steps) >= limit:
            break
        steps.append({"step": len(steps) + 1, "skill": skill, "priority": kind,
                      "action": _ACTIONS.get(skill, _DEFAULT_ACTION.format(skill=skill))})
    return steps


def recommend_roles(profile: dict, top_n: int = 5, min_fit: float = MIN_FIT) -> list:
    have = {s["name"]: s for s in profile.get("skills", [])}
    held = [_norm(c["name"]) for c in profile.get("certifications", [])]
    out = []
    for role in ROLES:
        num = den = 0.0
        explicit_core = 0
        matching, partial, missing_core, missing_support = [], [], [], []
        for names, w, is_core in ((role["core"], 2.0, True), (role["support"], 1.0, False)):
            for n in names:
                s = have.get(n)
                den += w
                if s and s["source_type"] == "explicit":
                    num += w
                    matching.append(n)
                    explicit_core += is_core
                elif s:
                    num += w * INFERRED_CREDIT
                    partial.append(n) if is_core else matching.append(n + " (inferred)")
                else:
                    (missing_core if is_core else missing_support).append(n)
        fit = 100.0 * num / den
        if explicit_core < 1 or fit < min_fit:
            continue
        certs = [{"name": c, "already_held": any(_norm(c) == h or (len(_norm(c)) >= 4 and _norm(c) in h) for h in held if h)}
                 for c in role["certs"]]
        out.append({"role_name": role["name"], "fit_score": round(fit, 1),
                    "evidence_level": "strong" if fit >= 60 else "moderate" if fit >= 40 else "emerging",
                    "matching_skills": matching, "missing_skills": missing_core + missing_support,
                    "missing_core_skills": missing_core, "partial_core_skills": partial,
                    "suggested_certs": certs, "roadmap": _roadmap(missing_core, partial, missing_support)})
    out.sort(key=lambda r: -r["fit_score"])
    for i, r in enumerate(out[:top_n], 1):
        r["rank"] = i
    return out[:top_n]
