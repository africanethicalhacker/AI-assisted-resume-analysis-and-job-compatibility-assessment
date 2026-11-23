"""SYNTHETIC data generator for SMOKE-TESTING the experiment code only.

The labels here come from the same templates that generate the text, so any score computed on this
data says nothing about real-world accuracy. Use it to check that scripts run; use real, consented or
anonymised, human-labelled data for the numbers you report (see experiments/README.md).
"""
import csv
import json
import os
import random

ROLES = {
    "soc": {"title": "SOC Analyst", "skills": ["SIEM", "Splunk", "Incident Response", "Wireshark", "SOC Operations"], "cert": "CompTIA Security+"},
    "pentest": {"title": "Penetration Tester", "skills": ["Penetration Testing", "Kali Linux", "Metasploit", "Burp Suite", "Nmap"], "cert": "eJPT"},
    "forensics": {"title": "Digital Forensics Analyst", "skills": ["Digital Forensics", "Autopsy", "Volatility", "Incident Response", "Python"], "cert": "CHFI"},
    "cloud": {"title": "Cloud Security Analyst", "skills": ["Cloud Security", "Linux", "Python", "Cryptography", "Risk Management"], "cert": "AWS Certified Security - Specialty"},
}
ADJACENT = {("soc", "forensics"), ("forensics", "soc"), ("soc", "pentest"), ("pentest", "soc"), ("cloud", "soc"), ("soc", "cloud")}
NAMES = ["Aarav Sharma", "Priya Nair", "Kwame Mensah", "Chidinma Okafor", "Rahul Verma", "Sneha Patel", "Tunde Bello", "Ananya Iyer",
         "Mohammed Ali", "Fatima Khan", "Ravi Kumar", "Neha Gupta", "Ibrahim Musa", "Kavya Reddy", "Arjun Mehta", "Zainab Yusuf"]
INSTITUTIONS = ["National Forensic Sciences University", "University of Mumbai", "Gujarat Technological University", "Anna University"]


def _resume(rng, rid, role, name):
    r = ROLES[role]
    skills = rng.sample(r["skills"], k=rng.randint(3, len(r["skills"]))) + rng.sample(["Python", "Linux", "SQL", "Bash"], k=2)
    skills = sorted(set(skills))
    inst = rng.choice(INSTITUTIONS)
    start = rng.randint(2019, 2023)
    months = rng.choice([0, 6, 12, 18, 24])
    exp = (f"EXPERIENCE\nSecurity Analyst - ExampleCorp  Jan {start + 2} - " + (f"{['Jan', 'Jul'][months % 12 == 6]} {start + 2 + months // 12}" if months else f"Jan {start + 2}") + "\n- Worked on monitoring and reporting\n") if months else ""
    text = (f"{name}\n{name.split()[0].lower()}.{rid}@example.com\n\nEDUCATION\nM.Sc. Cyber Security, {inst} {start} - {start + 2}\n\n"
            f"TECHNICAL SKILLS\n{', '.join(skills)}\n\n{exp}PROJECTS\n{r['title']} Lab\n- Built a small lab using {skills[0]}\n\nCERTIFICATIONS\n{r['cert']}\n")
    return {"id": rid, "text": text}, {"id": rid, "name": name, "email": f"{name.split()[0].lower()}.{rid}@example.com", "skills": skills,
                                        "certifications": [r["cert"]], "highest_education_level": "master", "professional_months": months}


def generate(out_dir, n_resumes=24, seed=7):
    rng = random.Random(seed)
    os.makedirs(out_dir, exist_ok=True)
    roles = list(ROLES)
    resumes, gold, groups, resume_role = [], [], [], {}
    for i in range(n_resumes):
        role = roles[i % len(roles)]
        rid = f"R{i:03d}"
        res, g = _resume(rng, rid, role, NAMES[i % len(NAMES)])
        resumes.append(res), gold.append(g)
        resume_role[rid] = role
        groups.append((rid, "group_a" if i % 2 == 0 else "group_b"))
    jobs = []
    for role in roles:
        r = ROLES[role]
        jobs.append({"id": f"J_{role}", "text": f"Job Title: {r['title']}\nCompany: ExampleCorp\n\nRequirements\n- Hands-on experience with {r['skills'][0]} and {r['skills'][1]}\n"
                     f"- Knowledge of {r['skills'][2]}\n- Bachelor's degree in computer science or a related field\n\nPreferred\n- {r['cert']}\n"})
    with open(os.path.join(out_dir, "resumes.jsonl"), "w") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in resumes)
    with open(os.path.join(out_dir, "jobs.jsonl"), "w") as fh:
        fh.writelines(json.dumps(j) + "\n" for j in jobs)
    with open(os.path.join(out_dir, "gold_extraction.jsonl"), "w") as fh:
        fh.writelines(json.dumps(g) + "\n" for g in gold)
    with open(os.path.join(out_dir, "labels.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["job_id", "resume_id", "relevance"])
        for j in jobs:
            jr = j["id"][2:]
            for rid, rr in resume_role.items():
                w.writerow([j["id"], rid, 3 if rr == jr else 1 if (rr, jr) in ADJACENT else 0])
    with open(os.path.join(out_dir, "groups.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["resume_id", "group"])
        w.writerows(groups)
    return out_dir


if __name__ == "__main__":
    import sys
    print("Wrote SYNTHETIC smoke-test data to", generate(sys.argv[1] if len(sys.argv) > 1 else "experiments/data_synthetic"))
