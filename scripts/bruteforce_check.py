"""Self-test of login protection against YOUR OWN local instance (refuses any other host).

Usage: python scripts/bruteforce_check.py http://127.0.0.1:5000 someone@example.com
Sends repeated wrong passwords and reports when throttling (HTTP 429) or lockout appears.
Do not point this at systems you do not own or have written permission to test.
"""
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:5000"
email = sys.argv[2] if len(sys.argv) > 2 else "nobody@example.com"
host = urllib.parse.urlparse(base).hostname
if host not in ("127.0.0.1", "localhost", "::1"):
    raise SystemExit("Refusing: this check only runs against localhost.")

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
for attempt in range(1, 31):
    page = opener.open(base + "/auth/login").read().decode()
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page).group(1)
    body = urllib.parse.urlencode({"csrf_token": token, "email": email, "password": f"wrong-password-{attempt}"}).encode()
    try:
        r = opener.open(base + "/auth/login", body)
        status = r.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    print(f"attempt {attempt:2d}: HTTP {status}")
    if status == 429:
        print("Rate limiting engaged. PASS")
        break
else:
    print("No HTTP 429 within 30 attempts. Check the limiter configuration. (Account lockout may still protect a real account.)")
