"""PDF assessment report (Phase 15) built with ReportLab; the chart is drawn with Matplotlib.

Every string that comes from a resume or job description is XML-escaped before it reaches
ReportLab, so malformed or hostile markup in a document cannot break or alter the report.
"""
import io
import logging
import os
from html import escape as _html_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

log = logging.getLogger(__name__)
DISCLAIMER = "Decision-support report. Not a hiring decision."


def _register_fonts(unicode_font: bool):
    if unicode_font:
        try:
            import matplotlib
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            d = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
            pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(d, "DejaVuSans.ttf")))
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(d, "DejaVuSans-Bold.ttf")))
            pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")
            return "DejaVu", "DejaVu-Bold"
        except Exception as exc:  # noqa: BLE001 - fall back to the built-in font
            log.warning("Unicode font unavailable (%s); using Helvetica", type(exc).__name__)
    return "Helvetica", "Helvetica-Bold"


def _styles(base, bold):
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=ss["Title"], fontName=bold, fontSize=20, spaceAfter=4),
        "h1": ParagraphStyle("h1", parent=ss["Heading2"], fontName=bold, fontSize=13, spaceBefore=12, spaceAfter=4,
                             textColor=colors.HexColor("#0b3d91")),
        "h2": ParagraphStyle("h2", parent=ss["Heading3"], fontName=bold, fontSize=10.5, spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("b", parent=ss["BodyText"], fontName=base, fontSize=9, leading=12),
        "small": ParagraphStyle("s", parent=ss["BodyText"], fontName=base, fontSize=7.5, leading=9.5, textColor=colors.HexColor("#444444")),
        "cell": ParagraphStyle("c", parent=ss["BodyText"], fontName=base, fontSize=8, leading=10),
        "cellb": ParagraphStyle("cb", parent=ss["BodyText"], fontName=bold, fontSize=8, leading=10),
        "big": ParagraphStyle("big", parent=ss["Title"], fontName=bold, fontSize=34, spaceAfter=0),
    }


def esc(value) -> str:
    return _html_escape("" if value is None else str(value), quote=False)


def _short(text, n=110):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def component_chart(components: list) -> bytes:
    from matplotlib.figure import Figure

    rows = [c for c in components if c.get("applicable")]
    fig = Figure(figsize=(6.6, 0.55 * max(len(rows), 1) + 0.8), dpi=150)
    ax = fig.subplots()
    labels = [c["label"] for c in rows]
    scores = [c["score"] or 0 for c in rows]
    ax.barh(labels, scores, color="#0d6efd")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Component score (0-100)")
    ax.invert_yaxis()
    for i, s in enumerate(scores):
        ax.text(min(s + 1.5, 92), i, f"{s:.0f}", va="center", fontsize=8)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    return buf.getvalue()


class _Builder:
    def __init__(self, data, st):
        self.d, self.st, self.flow = data, st, []

    def h(self, n, title):
        self.flow.append(Paragraph(f"{n}. {esc(title)}", self.st["h1"]))

    def sub(self, title):
        self.flow.append(Paragraph(esc(title), self.st["h2"]))

    def p(self, text, style="body"):
        self.flow.append(Paragraph(esc(text), self.st[style]))

    def gap(self, h=4):
        self.flow.append(Spacer(1, h))

    def table(self, header, rows, widths):
        cell, cellb = self.st["cell"], self.st["cellb"]
        data = [[Paragraph(esc(h), cellb) for h in header]] + [[Paragraph(esc(c), cell) for c in r] for r in rows]
        t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eefb")),
                               ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b8c2d9")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
        self.flow.append(t)

    def none(self, text="None found."):
        self.p(text, "small")


def build_pdf(data: dict, unicode_font: bool = True, compress: bool = True) -> bytes:
    base, bold = _register_fonts(unicode_font)
    st = _styles(base, bold)
    b = _Builder(data, st)
    cand, ext, job = data.get("candidate", {}), data.get("extraction", {}), data.get("job", {})
    comps, gap, sem = data.get("components", []), data.get("gap", {}), data.get("semantic", {})
    asm = data["assessment"]

    b.flow.append(Paragraph("AI-Assisted Resume Analysis and Job Compatibility Assessment", st["title"]))
    b.p(f"Assessment #{asm['id']} · generated {data.get('generated_at', '')} UTC · {DISCLAIMER}", "small")
    b.gap(6)

    # 1. Candidate summary
    b.h(1, "Candidate summary")
    b.table(["Field", "Value"], [
        ["Name", cand.get("name") or "not found"], ["Email", cand.get("email") or "not found"],
        ["Phone", cand.get("phone") or "not found"], ["Links", ", ".join(cand.get("links", [])) or "none found"],
        ["Resume completeness (heuristic)", f"{cand['quality_score']:.0f} / 100" if cand.get("quality_score") is not None else "n/a"],
        ["Sections found", ", ".join(ext.get("sections_found", [])) or "none"]], [50, 120])
    if cand.get("summary"):
        b.gap(); b.p("Summary stated in the resume: " + _short(cand["summary"], 500), "small")

    # 2. Resume extraction results
    b.h(2, "Resume extraction results")
    b.p("Extraction is rule-based and keeps the source text for each item. Nothing is inferred beyond what is written, except skills labelled “inferred”.", "small")
    b.sub("Education")
    edu = ext.get("education", [])
    b.table(["Degree", "Level", "Field", "Institution", "Years"],
            [[e.get("degree"), e.get("level"), e.get("field") or "-", e.get("institution") or "-",
              f"{e.get('start_year') or ''}-{e.get('end_year') or ''}".strip("-")] for e in edu], [38, 20, 36, 52, 24]) if edu else b.none()
    b.sub("Skills")
    sk = ext.get("skills", [])
    b.table(["Skill", "Category", "Type", "Confidence", "Evidence"],
            [[s["name"], s["category"], s["source_type"], f"{s['confidence'] * 100:.0f}%", _short(s["evidence"]["text"], 90)] for s in sk],
            [30, 24, 17, 22, 77]) if sk else b.none()
    b.sub("Certifications")
    b.p(", ".join(c["name"] for c in ext.get("certifications", [])) or "None found.")
    b.sub("Experience and internships")
    es = ext.get("experience_summary", {})
    jobs = ext.get("experience", []) + ext.get("internships", [])
    b.table(["Role / organisation", "Period", "Months"], [[e["title"], f"{e['start']} – {e['end']}", e.get("months") if e.get("months") is not None else "-"] for e in jobs],
            [100, 50, 20]) if jobs else b.none("No dated experience entries found.")
    b.p(f"Professional months: {es.get('professional_months', 0)}; internship months: {es.get('internship_months', 0)}.", "small")
    b.sub("Projects")
    b.p("; ".join(p["title"] for p in ext.get("projects", [])) or "None found.")
    b.sub("Achievements")
    b.p("; ".join(a["text"] for a in ext.get("achievements", [])) or "None found.")

    # 3. Job description summary
    b.h(3, "Job description summary")
    b.p(f"Title: {job.get('title') or 'not stated'} · Organisation: {job.get('organization') or 'not stated'}")
    reqs = job.get("requirements", [])
    for strength in ("mandatory", "preferred", "optional"):
        rows = [r for r in reqs if r["strength"] == strength and r["kind"] != "responsibility"]
        b.sub(f"{strength.capitalize()} requirements ({len(rows)})")
        b.table(["Type", "Requirement"], [[r["kind"], _short(r["requirement_text"], 140)] for r in rows], [28, 142]) if rows else b.none("None identified.")
    b.p("A requirement is marked mandatory only when the job text says so.", "small")

    # 4. Compatibility score
    b.h(4, "Compatibility score")
    b.flow.append(Paragraph(f"{asm['final_score']:.1f} / 100", st["big"]))
    b.p(f"Model: {asm.get('model_version', '')}. This score supports a human decision and must not be used alone.", "small")
    elig = data.get("eligibility")
    if elig:
        b.sub(f"Eligibility screening: {elig['label']} (match {elig['percentage']}% against a {elig['threshold']}% threshold)")
        for r in elig.get("reasons", []):
            b.p("• " + r, "small")
        b.p(elig.get("rule", ""), "small")
    if any(c.get("applicable") for c in comps):
        b.flow.append(Image(io.BytesIO(component_chart(comps)), width=165 * mm, height=165 * mm * (0.55 * sum(1 for c in comps if c.get("applicable")) + 0.8) / 6.6))

    # 5. Component-wise scoring
    b.h(5, "Component-wise scoring")
    rows = []
    for c in comps:
        if c.get("applicable"):
            rows.append([c["label"], f"{c['score']:.1f}", f"{c['effective_weight'] * 100:.0f}%", f"{c['contribution']:.1f}"])
        else:
            rows.append([c["label"], "n/a", "0%", "0.0"])
    rows.append(["Total", "", "100%", f"{asm['final_score']:.1f}"])
    b.table(["Component", "Score (0-100)", "Weight used", "Points added"], rows, [70, 35, 35, 30])
    b.p("Weight used = configured weight divided by the total weight of applicable components. n/a means the job description gave nothing to compare.", "small")
    b.p(f"Semantic similarity method: {sem.get('method_used', 'n/a')}; TF-IDF cosine {sem.get('tfidf_cosine', 'n/a')}; SBERT coverage {sem.get('sbert_coverage', 'n/a')}. {sem.get('note', '')}", "small")

    # 6. Matching skills
    sg = gap.get("skills", {})
    b.h(6, "Matching skills")
    m = sg.get("matched", [])
    b.table(["Skill", "Required as", "Evidence"], [[x["skill"], x["strength"], _short(x["evidence"], 100)] for x in m], [35, 25, 110]) if m else b.none("No required skills were found in the resume.")
    if sg.get("partial"):
        b.sub("Partially matching (inferred from related tools, half credit)")
        b.p(", ".join(x["skill"] for x in sg["partial"]))
    if sg.get("additional"):
        b.sub("Additional relevant skills not required by this job")
        b.p(", ".join(sg["additional"]))

    # 7. Missing skills
    b.h(7, "Missing skills")
    miss = sg.get("missing", {})
    any_missing = False
    for strength in ("mandatory", "preferred", "optional"):
        rows = miss.get(strength, [])
        if rows:
            any_missing = True
            b.sub(strength.capitalize())
            b.table(["Skill", "Potential points"], [[r["skill"], f"+{r['potential_points']}"] for r in rows], [100, 40])
    if not any_missing:
        b.none("No required skills are missing.")
    if gap.get("priorities"):
        b.sub("Suggested order of work")
        b.p("; ".join(f"{p['item']} ({p['type']}, about +{p['potential_points']})" for p in gap["priorities"][:6]))
    b.p("Potential points estimate how much of the skills component each item is worth. They are for prioritising only.", "small")

    # 8. Education analysis
    b.h(8, "Education analysis")
    ge = gap.get("education")
    if ge:
        b.p(f"Required level: {ge['required']}. Candidate's highest level: {ge['candidate']}. Level met: {'yes' if ge['level_met'] else 'no' if ge['level_met'] is False else 'not stated'}. "
            f"Field relevance score: {ge.get('field_score') if ge.get('field_score') is not None else 'not assessed'}.")
    else:
        b.p("The job description states no education requirement that could be compared.")

    # 9. Experience analysis
    b.h(9, "Experience analysis")
    gx = gap.get("experience")
    if gx:
        b.p(f"Required: {gx['required_months']} months. Candidate's effective experience: {gx['effective_months']} months "
            f"(professional months plus half of internship months). Shortfall: {gx['shortfall_months']} months.")
    else:
        b.p("The job description states no experience requirement in years.")
    gc = gap.get("certifications")
    if gc:
        b.p("Certifications held that the job asks for: " + (", ".join(gc["held"]) or "none") + ". Not found: " + (", ".join(c["certification"] for c in gc["missing"]) or "none") + ".")

    # 10. Recommendations
    b.h(10, "Recommendations")
    recs = data.get("recommendations", [])
    if not recs:
        b.none("Not enough skill evidence in the resume to suggest roles.")
    for r in recs:
        b.sub(f"{r['rank']}. {r['role_name']} ({r['evidence_level']} evidence, fit {r['fit_score']})")
        b.p("Matching skills: " + (", ".join(r["matching_skills"]) or "none") + ". To build: " + (", ".join(r["missing_skills"][:6]) or "nothing major") + ".", "small")
        b.p("Certifications often associated: " + ", ".join(c["name"] + (" (held)" if c["already_held"] else "") for c in r["suggested_certs"]) + ".", "small")
        for s in r.get("roadmap", [])[:4]:
            b.p(f"  Step {s['step']} – {s['skill']}: {s['action']}", "small")
    b.p("Suggestions use only skills evidenced in the resume. They do not predict employment, and certification prerequisites change; check each issuer's current requirements.", "small")

    # 11. Methodology
    b.h(11, "Scoring methodology")
    w = data.get("weights_configured", {})
    b.p("Final score = Σ (wᵢ / W) × Sᵢ over applicable components, W = sum of their configured weights. With all five components this equals "
        "0.35×Skills + 0.25×Semantic + 0.15×Education + 0.15×Experience + 0.10×Projects&Certifications when default weights are used.")
    b.table(["Component", "Configured weight"], [[k.replace("_", " "), f"{v * 100:.0f}%"] for k, v in w.items()], [90, 40])
    for line in [
        "Technical skills: 100 × Σ(weight × credit) / Σ(weight); weights mandatory 3, preferred 2, optional 1; credit explicit 1.0, inferred 0.5, missing 0.",
        "Semantic similarity: Sentence-BERT (all-MiniLM-L6-v2) coverage, the mean over job passages of the best cosine match among resume passages; TF-IDF cosine (sublinear tf, smoothed idf, unigrams and bigrams) is reported alongside or used when SBERT is unavailable.",
        "Education: 70% level match (diploma < bachelor < master < doctorate) and 30% field relevance, when stated.",
        "Experience: min(100, 100 × (professional months + 0.5 × internship months) / required months).",
        "Projects and certifications: average of the share of job skills evidenced in projects and the share of required certifications held.",
        "All weights and rule values are experimental hypotheses validated through experiments; they are not established constants."]:
        b.p("• " + line, "small")

    # 12. Limitations
    b.h(12, "Assessment limitations")
    for line in [
        "Extraction is rule-based and can miss or misread information, particularly in complex layouts. Scanned documents are not supported.",
        "The skill taxonomy is finite and focused on cyber security; skills outside it are not recognised.",
        "Semantic models can reflect biases in their training data. Fairness checks reduce, but cannot remove, this risk.",
        "A compatibility score is not a prediction of job performance and must not be the sole basis for any employment decision.",
        "Instruction-like text inside documents is treated as data and excluded from matching; detection is pattern-based and not exhaustive."]:
        b.p("• " + line, "small")
    for f in data.get("flags", []):
        b.p("Integrity note: " + f["message"], "small")

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(base, 7)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(15 * mm, 9 * mm, DISCLAIMER)
        canvas.drawRightString(195 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=16 * mm,
                            title=f"Assessment {asm['id']}", author="Resume AI", pageCompression=1 if compress else 0)
    doc.build(b.flow, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
