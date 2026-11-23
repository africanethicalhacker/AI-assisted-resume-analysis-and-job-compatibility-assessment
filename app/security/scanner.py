"""ClamAV client (clamd). Fails closed unless CLAMD_REQUIRED=false (dev only)."""
import io
from dataclasses import dataclass


@dataclass
class ScanResult:
    status: str            # clean | infected | error
    signature: str = ""


class ClamAVScanner:
    def __init__(self, socket_path: str = "", host: str = "", port: int = 3310, timeout: float = 30):
        self.socket_path, self.host, self.port, self.timeout = socket_path, host, port, timeout

    def _client(self):
        import clamd

        if self.socket_path:
            return clamd.ClamdUnixSocket(path=self.socket_path, timeout=self.timeout)
        return clamd.ClamdNetworkSocket(host=self.host or "localhost", port=self.port, timeout=self.timeout)

    def scan(self, data: bytes) -> ScanResult:
        try:
            resp = self._client().instream(io.BytesIO(data))
            status, signature = resp.get("stream", (None, None))
        except Exception:  # noqa: BLE001 - any failure means "could not scan"
            return ScanResult("error")
        if status == "OK":
            return ScanResult("clean")
        if status == "FOUND":
            return ScanResult("infected", str(signature or ""))
        return ScanResult("error")


def get_scanner():
    from flask import current_app

    scanner = current_app.extensions.get("scanner")
    if scanner is None:
        c = current_app.config
        scanner = ClamAVScanner(c["CLAMD_SOCKET"], c["CLAMD_HOST"], c["CLAMD_PORT"])
        current_app.extensions["scanner"] = scanner
    return scanner
