"""Fixes for the four Bandit findings. Run from the project root: python apply_fixes.py"""
import re

def edit(path, old, new, count=1):
    s = open(path, encoding="utf-8").read()
    if new in s:                      # already applied (checked first, because `new` often contains `old`)
        print("already applied:", path); return
    assert old in s, f"pattern not found in {path}: {old[:50]!r}"
    open(path, "w", encoding="utf-8").write(s.replace(old, new, count))
    print("patched:", path)

# 1. B105 false positive: a regular expression named TOKEN_PATTERN is not a password
edit("app/ai/matching/tfidf.py",
     'TOKEN_PATTERN = r"[a-z0-9][a-z0-9+#]*"',
     'TOKEN_PATTERN = r"[a-z0-9][a-z0-9+#]*"  # nosec B105 - a regular expression, not a credential')

# 2. B105: do not keep any fixed secret in the code base, even for tests
edit("app/config.py", 'import base64\nimport os\n', 'import base64\nimport os\nimport secrets\n')
edit("app/config.py", 'SECRET_KEY = "test-only-secret-not-for-use"', 'SECRET_KEY = secrets.token_hex(32)   # random per process; used only by the test configuration')

# 3. B406: use html.escape (same effect for ReportLab markup) instead of xml.sax.saxutils.escape
edit("app/reporting/pdf_report.py", "from xml.sax.saxutils import escape\n", "from html import escape as _html_escape\n")
edit("app/reporting/pdf_report.py", '    return escape("" if value is None else str(value))',
     '    return _html_escape("" if value is None else str(value), quote=False)')

# 4. B110: log why the Unicode font was not used instead of silently ignoring it
edit("app/reporting/pdf_report.py", "import io\nimport os\n", "import io\nimport logging\nimport os\n")
edit("app/reporting/pdf_report.py", "DISCLAIMER = ", "log = logging.getLogger(__name__)\nDISCLAIMER = ")
edit("app/reporting/pdf_report.py",
     "        except Exception:  # noqa: BLE001 - fall back to the built-in font\n            pass",
     "        except Exception as exc:  # noqa: BLE001 - fall back to the built-in font\n            log.warning(\"Unicode font unavailable (%s); using Helvetica\", type(exc).__name__)")

# 5. keep the form library below the release that removes tuple choices
s = open("requirements.txt").read()
if "WTForms" not in s:
    open("requirements.txt", "a").write("\nWTForms>=3.1,<3.4\n")
    print("patched: requirements.txt")
if "setuptools" not in s:
    open("requirements.txt", "a").write("setuptools>=84.1.0\n")
