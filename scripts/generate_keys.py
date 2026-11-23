"""Generate SECRET_KEY and MASTER_KEY values for .env. Output goes to your terminal only."""
import base64
import secrets

print("SECRET_KEY=" + secrets.token_hex(32))
print("MASTER_KEY=" + base64.b64encode(secrets.token_bytes(32)).decode())
print("\nPaste these into .env. Back up MASTER_KEY securely: losing it makes stored resumes unrecoverable.")
