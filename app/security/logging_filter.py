"""Keep personal data out of logs: e-mail addresses are masked in every log message."""
import logging
import re

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        redacted = _EMAIL.sub("[email]", msg)
        if redacted != msg:
            record.msg, record.args = redacted, ()
        return True
