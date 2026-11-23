"""Skill taxonomy and explicit/inferred skill extraction (pure Python, no Flask)."""
import re
from dataclasses import dataclass

CATEGORIES = ("cybersecurity", "programming", "tools", "soft")

# (name, category, aliases). The admin interface extends this through the database.
SEED = [
    # Cyber security
    ("Network Security", "cybersecurity", ["network defense", "network defence"]),
    ("Information Security", "cybersecurity", ["infosec", "cybersecurity fundamentals"]),
    ("Digital Forensics", "cybersecurity", ["computer forensics", "forensic analysis", "forensic investigation", "dfir"]),
    ("Incident Response", "cybersecurity", ["incident handling", "dfir"]),
    ("SIEM", "cybersecurity", ["security information and event management"]),
    ("SOC Operations", "cybersecurity", ["security operations center", "security operations centre", "soc monitoring"]),
    ("Penetration Testing", "cybersecurity", ["pentesting", "pen testing", "pentest", "ethical hacking", "vapt"]),
    ("Vulnerability Assessment", "cybersecurity", ["vulnerability scanning", "vulnerability management"]),
    ("Threat Intelligence", "cybersecurity", ["cyber threat intelligence", "cti"]),
    ("Threat Hunting", "cybersecurity", []),
    ("Malware Analysis", "cybersecurity", ["malware reverse engineering"]),
    ("Cloud Security", "cybersecurity", ["aws security", "azure security"]),
    ("Cryptography", "cybersecurity", ["encryption", "pki"]),
    ("Security Auditing", "cybersecurity", ["security audit", "it audit"]),
    ("Risk Management", "cybersecurity", ["risk assessment"]),
    ("Web Application Security", "cybersecurity", ["owasp", "owasp top 10"]),
    ("MITRE ATT&CK", "cybersecurity", ["mitre attack"]),
    # Programming
    ("Python", "programming", []),
    ("Java", "programming", []),
    ("C", "programming", []),
    ("C++", "programming", []),
    ("JavaScript", "programming", []),
    ("SQL", "programming", []),
    ("Bash", "programming", ["shell scripting", "bash scripting"]),
    ("PowerShell", "programming", []),
    # Tools
    ("Wireshark", "tools", []),
    ("Nmap", "tools", []),
    ("Metasploit", "tools", ["msfconsole"]),
    ("Burp Suite", "tools", ["burpsuite", "burp"]),
    ("Splunk", "tools", []),
    ("ELK Stack", "tools", ["elk", "elasticsearch logstash kibana"]),
    ("Nessus", "tools", []),
    ("Kali Linux", "tools", ["kali"]),
    ("Autopsy", "tools", []),
    ("Volatility", "tools", ["volatility framework"]),
    ("Snort", "tools", []),
    ("Suricata", "tools", []),
    ("OpenVAS", "tools", []),
    ("Linux", "tools", []),
    ("Git", "tools", []),
    ("Active Directory", "tools", []),
    # Non-technical
    ("Communication", "soft", ["communication skills", "written communication", "verbal communication"]),
    ("Teamwork", "soft", ["team player", "collaboration"]),
    ("Report Writing", "soft", ["technical writing"]),
    ("Leadership", "soft", ["team lead"]),
    ("Problem Solving", "soft", ["analytical skills", "critical thinking"]),
]

# Skill -> broader skills it suggests. Used ONLY to create *inferred* skills (lower confidence).
IMPLIES = {
    "Splunk": ["SIEM"], "ELK Stack": ["SIEM"], "SIEM": ["SOC Operations"],
    "Wireshark": ["Network Security"], "Snort": ["Network Security"], "Suricata": ["Network Security"],
    "Nmap": ["Vulnerability Assessment", "Network Security"], "Nessus": ["Vulnerability Assessment"],
    "OpenVAS": ["Vulnerability Assessment"], "Metasploit": ["Penetration Testing"],
    "Burp Suite": ["Penetration Testing", "Web Application Security"], "Kali Linux": ["Penetration Testing"],
    "Autopsy": ["Digital Forensics"], "Volatility": ["Digital Forensics", "Malware Analysis"],
}
INFERRED_CONFIDENCE = 0.6

_AMBIGUOUS = {"c", "r", "go"}  # single letters / common words: case-sensitive, delimiter-bounded


@dataclass
class SkillMatch:
    name: str
    category: str
    source_type: str        # explicit | inferred
    confidence: float
    term: str               # text that matched (explicit) or "implied by X" (inferred)
    start: int = -1
    end: int = -1
    snippet: str = ""
    occurrences: int = 1


def _term_regex(term: str):
    esc = re.escape(term.strip()).replace(r"\ ", r"[\s\-]+")
    if term.lower() in _AMBIGUOUS:
        pre, post = r"(?:(?<=^)|(?<=[,;:|/•·(\n])\s*)", r"(?=\s*(?:[,;|/•·)\n]|$))"
        return re.compile(pre + esc + post, re.M)          # case-sensitive
    return re.compile(r"(?<![\w+#])" + esc + r"(?![\w+#])", re.I)


class SkillMatcher:
    def __init__(self, records):
        """records: iterable of (name, category, aliases_list)."""
        self.skills = {}
        self._patterns = []
        for name, category, aliases in records:
            self.skills[name] = category
            for term in [name] + list(aliases or []):
                if term.strip():
                    self._patterns.append((name, term, _term_regex(term)))

    @classmethod
    def from_seed(cls):
        return cls(SEED)

    def category_of(self, name: str) -> str:
        return self.skills.get(name, "")

    def find_explicit(self, text: str) -> list:
        found = {}
        for name, term, rx in self._patterns:
            for m in rx.finditer(text):
                cur = found.get(name)
                if cur is None:
                    s, e = m.start(), m.end()
                    lo, hi = max(0, s - 40), min(len(text), e + 40)
                    window = re.sub(r"\s+", " ", text[lo:hi]).strip()
                    if lo > 0 and " " in window:
                        window = window.split(" ", 1)[1]          # drop a word cut by the window
                    if hi < len(text) and " " in window:
                        window = window.rsplit(" ", 1)[0]
                    snippet = window
                    found[name] = SkillMatch(name, self.skills[name], "explicit", 1.0,
                                             m.group(0), s, e, snippet)
                else:
                    cur.occurrences += 1
        return sorted(found.values(), key=lambda x: x.start)

    def find_all(self, text: str) -> list:
        """Explicit matches plus inferred skills (never duplicating an explicit one)."""
        explicit = self.find_explicit(text)
        have = {m.name for m in explicit}
        inferred = {}
        for m in explicit:
            for implied in IMPLIES.get(m.name, []):
                if implied in self.skills and implied not in have and implied not in inferred:
                    inferred[implied] = SkillMatch(implied, self.skills[implied], "inferred",
                                                   INFERRED_CONFIDENCE, f"implied by {m.name}",
                                                   snippet=f"Inferred from mention of {m.name}")
        return explicit + list(inferred.values())
