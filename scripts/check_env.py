"""Verify the development environment. Run: python scripts/check_env.py"""
import importlib
import os
import sys

from dotenv import load_dotenv

load_dotenv()
results = []


def check(name, fn):
    try:
        detail = fn() or ""
        results.append((name, True, str(detail)))
    except Exception as exc:  # noqa: BLE001 - we want every failure reported
        results.append((name, False, f"{type(exc).__name__}: {exc}"))


def python_version():
    assert sys.version_info >= (3, 10), f"Python 3.10+ required, found {sys.version.split()[0]}"
    return sys.version.split()[0]


def imports():
    mods = ["flask", "flask_sqlalchemy", "flask_login", "flask_wtf", "flask_migrate",
            "flask_limiter", "pymysql", "argon2", "cryptography", "fitz", "docx",
            "spacy", "nltk", "sklearn", "numpy", "pandas", "sentence_transformers",
            "reportlab", "matplotlib"]
    missing = [m for m in mods if importlib.util.find_spec(m) is None]
    assert not missing, "missing: " + ", ".join(missing)
    return f"{len(mods)} packages found"


def spacy_model():
    import spacy
    spacy.load("en_core_web_sm")
    return "en_core_web_sm loaded"


def nltk_data():
    import nltk
    for res in ("tokenizers/punkt", "corpora/stopwords"):
        nltk.data.find(res)
    return "punkt and stopwords present"


def sbert():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    dim = len(model.encode("test sentence"))
    return f"all-MiniLM-L6-v2 loaded, embedding size {dim}"


def libmagic():
    import magic
    return magic.from_buffer(b"%PDF-1.4\n", mime=True)


def env_keys():
    assert os.getenv("SECRET_KEY"), "SECRET_KEY empty in .env"
    import base64
    assert len(base64.b64decode(os.getenv("MASTER_KEY", ""))) == 32, "MASTER_KEY must decode to 32 bytes"
    return "keys present (values not printed)"


def mysql():
    import sqlalchemy
    url = os.getenv("DATABASE_URL")
    assert url, "DATABASE_URL empty"
    with sqlalchemy.create_engine(url).connect() as conn:
        return conn.execute(sqlalchemy.text("SELECT VERSION()")).scalar()


def clamav():
    import clamd
    sock, host = os.getenv("CLAMD_SOCKET"), os.getenv("CLAMD_HOST")
    cd = clamd.ClamdUnixSocket(sock) if sock else clamd.ClamdNetworkSocket(host or "localhost", int(os.getenv("CLAMD_PORT", "3310")))
    return cd.ping()


for label, fn in [("Python version", python_version), ("Package imports", imports),
                  ("spaCy model", spacy_model), ("NLTK data", nltk_data),
                  ("Sentence-BERT model", sbert), ("libmagic", libmagic),
                  (".env keys", env_keys), ("MySQL connection", mysql), ("ClamAV daemon", clamav)]:
    check(label, fn)

width = max(len(n) for n, _, _ in results)
for name, ok, detail in results:
    print(f"[{'PASS' if ok else 'FAIL'}] {name.ljust(width)}  {detail}")
sys.exit(0 if all(ok for _, ok, _ in results) else 1)
