# AI-Assisted Resume Analysis and Job Compatibility Assessment

M.Sc. Cyber Security project, NFSU Gandhinagar. A secure, explainable decision-support system. It never makes hiring decisions.

## Quick start (Kali)
See `docs/installation_manual.md`. In short:

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env            # then fill SECRET_KEY, MASTER_KEY, DATABASE_URL
    flask --app run db init && flask --app run db migrate -m "initial" && flask --app run db upgrade
    python scripts/seed_taxonomy.py && python scripts/create_admin.py
    python -m pytest -v && python run.py

## What is where
| Folder | Contents |
|---|---|
| `app/` | Flask application: models, routes, services, ai (parsing, skills, jobs, matching, recommend), security, reporting |
| `experiments/` | Six reproducible experiments (see its README) |
| `tests/` | Unit, integration and security tests |
| `scripts/` | Setup, maintenance and self-test scripts |
| `docs/` | SRS, manuals, schema, diagrams, thesis chapters (`docs/report/`), viva questions |

## Phases
1-2 design | 3 environment | 4 database | 5 authentication | 6 upload | 7-9 parsing, jobs, skills | 10-11 matching and scoring |
12-13 gaps and recommendations | 14 dashboard | 15 PDF report | 16 hardening | 17 experiments | 18 documentation
