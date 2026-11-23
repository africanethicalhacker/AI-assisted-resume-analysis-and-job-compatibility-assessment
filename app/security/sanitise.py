"""Treat every document as untrusted text. Normalise it and flag instruction-like content.

The scoring pipeline is deterministic arithmetic, so injected instructions cannot change a
score. Flags exist so reviewers see manipulation attempts and so they can be audited.
"""
import re
import unicodedata

_INVISIBLE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_INJECTION_PATTERNS = [
    ("ignore_instructions", r"\b(ignore|disregard|forget|override)\b.{0,30}\b(previous|prior|above|earlier|all|any|your)\b.{0,30}\b(instructions?|prompts?|rules?|guidelines?)\b"),
    ("role_override", r"\byou\s+are\s+(now\s+)?(an?\s+|the\s+)?(ai|assistant|language\s+model|chatbot|chatgpt|hiring\s+(manager|bot))\b"),
    ("system_prompt", r"\b(system\s+prompt|developer\s+message|hidden\s+instructions?)\b"),
    ("score_manipulation", r"\b(give|assign|rate|score|rank|mark)\b.{0,40}\b(candidate|resume|applicant|me)\b.{0,40}\b(100|highest|maximum|perfect|10/10|top|best|full\s+marks)\b"),
    ("hire_directive", r"\b(hire|select|shortlist|recommend|prioriti[sz]e)\s+(this|the)\s+(candidate|applicant|resume)\b"),
    ("persona_switch", r"\b(act\s+as|pretend\s+to\s+be|roleplay\s+as)\b"),
    ("markup_injection", r"<\s*/?\s*(system|assistant|instructions?)\s*>"),
]
_COMPILED = [(label, re.compile(rx, re.I | re.S)) for label, rx in _INJECTION_PATTERNS]


def count_invisible_chars(text: str) -> int:
    return len(_INVISIBLE.findall(text))


def normalise_text(text: str, max_chars: int = 200_000) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = _INVISIBLE.sub("", text)
    text = _CONTROL.sub(" ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:max_chars].strip()


def detect_injection(text: str) -> list:
    findings = []
    for label, rx in _COMPILED:
        m = rx.search(text)
        if m:
            findings.append({"label": label, "start": m.start(),
                             "snippet": re.sub(r"\s+", " ", m.group(0))[:80]})
    return findings
