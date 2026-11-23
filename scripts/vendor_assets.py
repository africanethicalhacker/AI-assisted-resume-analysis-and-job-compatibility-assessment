"""Download Bootstrap and Chart.js into app/static/vendor so the app serves them itself.

Run once with internet access: python scripts/vendor_assets.py
Afterwards the app automatically drops the CDN from its Content-Security-Policy.
The printed SRI hashes let you verify the files later.
"""
import base64
import hashlib
import os
import urllib.request

ASSETS = {
    "bootstrap.min.css": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
    "chart.umd.min.js": "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js",
}
dest = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static", "vendor")
os.makedirs(dest, exist_ok=True)
for name, url in ASSETS.items():
    with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310 - fixed https URLs above
        data = resp.read()
    if len(data) < 10_000:
        raise SystemExit(f"{name}: download looks wrong ({len(data)} bytes)")
    with open(os.path.join(dest, name), "wb") as fh:
        fh.write(data)
    print(f"{name}: {len(data)} bytes  sha384-{base64.b64encode(hashlib.sha384(data).digest()).decode()}")
print("Done. Restart the app.")
