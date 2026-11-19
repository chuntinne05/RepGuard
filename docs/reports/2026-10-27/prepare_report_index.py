"""Normalize report typography and verify references/local links, docs only."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN = HERE / "REPGUARD_LITERATURE_REVIEW_VA_BAO_CAO_TIEN_DO.md"
SLIDES = HERE / "SLIDE_OUTLINE_VA_CAU_HOI_BAO_VE.md"


def typography(text):
    # Leave fenced/inline code and link targets byte-for-byte intact.
    protected = []
    pattern = r"```[\s\S]*?```|`[^`\n]+`|\]\([^\n]*?\)|\[R\d{2}(?:[^\]\n]*)\]|\b(?:Qwen3(?:\.5)?|Gemma4|R2-Router|C3|Q4_K_M|[0-9]+B|[0-9]{4}\.[0-9]{4,5}v[0-9]+|v[0-9]+)\b"
    def hide(match):
        protected.append(match.group())
        return f"\ue000{len(protected)-1}\ue001"
    text = re.sub(pattern, hide, text)
    # Whitespace between prose and quantities; retain decimal separators.
    letter = r"[^\W\d_]"
    text = re.sub(f"({letter})(?=[0-9])", r"\1 ", text)
    text = re.sub(f"(?<=[0-9])(?={letter})", " ", text)
    text = re.sub(f"([,;])(?={letter})", r"\1 ", text)
    text = re.sub(r";(?=\d)", "; ", text)
    text = re.sub(r"→", " → ", text)
    text = re.sub(r"(?<!\n) {2,}", " ", text)
    replacements = {
        "vớiThầy": "với Thầy", "Thầyliệu": "Thầy liệu", "Thầyđịnh": "Thầy định",
        "đúngmetric": "đúng metric", "CaseFRTđã": "Case FRT đã",
        "caseFRTđã": "case FRT đã", "testCPU": "test CPU",
        "label revelationchỉ": "label revelation chỉ", "gánscarcitygiả": "gán scarcity giả",
        "policyA": "policy A", "Bphải": "B phải", "Files": "files",
        "hayunit": "hay unit", "làgold": "là gold", "sốcase": "số case",
        "ởdeployment": "ở deployment", "hạnlabel": "hạn label",
        "Pythonfiles": "Python files", "tênpaper": "tên paper",
        "DARTghi": "DART ghi", "cầnThầy": "cần Thầy",
        "FindingsEMNLP": "Findings of EMNLP", "C 3": "C3",
        "auditPASS": "audit PASS", "gateFAIL": "gate FAIL", "đềuFAIL": "đều FAIL",
        "lệchA–B": "lệch A–B", "10%gold": "10% gold", "PairedSH[": "PairedSH [",
        "]pp": "] pp", "trên24": "trên 24", "trên20": "trên 20",
        "priors": "priors", "risk–coverage": "risk–coverage",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    text = re.sub(r"\ue000(\d+)\ue001", lambda m: protected[int(m.group(1))], text)
    text = re.sub(r"(\d{4}\.\d{4,5})\s+v\s*(\d+)\b", r"\1v\2", text)
    text = re.sub(r"\bv\s+(\d+)\b", r"v\1", text)
    text = re.sub(r"(?<=[^\W\d_]):(?=\d)", ": ", text)
    text = re.sub(r":(?=[^\W\d_])", ": ", text)
    text = re.sub(r"(?<=[^\W\d_])“", " “", text)
    text = re.sub(r"”(?=[^\W\d_])", "” ", text)
    return text


def main():
    for path in [MAIN, SLIDES]:
        path.write_text(typography(path.read_text()))
    text = MAIN.read_text()
    references = []
    pattern = re.compile(r"^- \*\*\[(R\d+)\]\*\* (.+?) \((\d{4})([^)]*)\)\. \*(.+?)\*\. (.+?) \[([^\]]+)\]\((https://[^)]+)\)\.", re.M)
    for m in pattern.finditer(text):
        key, authors, year, year_note, title, publication, label, url = m.groups()
        references.append({"id": key, "authors_as_cited": authors, "year": int(year),
                           "version_year_note": year_note.strip(), "title": title,
                           "publication_or_version": publication, "primary_url": url,
                           "checked_on": "2026-10-27", "independently_reproduced_by_this_review": False})
    assert len(references) == 49, len(references)
    assert [r["id"] for r in references] == [f"R{i:02}" for i in range(1, 50)]
    (HERE / "references.json").write_text(json.dumps(references, ensure_ascii=False, indent=2) + "\n")
    # Minimal BibTeX with only metadata verified in the cited primary records.
    # Use misc entries so venue/version notes are retained without inventing DOI/volume.
    bib = ["% RepGuard review sources, checked 2026-10-27.",
           "% Minimal verified metadata; published venue or preprint version is in note.", ""]
    for ref in references:
        authors = ref["authors_as_cited"].replace(" và cộng sự", " and others").replace("; ", " and ")
        def esc(s):
            return s.replace("&", r"\&").replace("%", r"\%")
        bib += [f"@misc{{{ref['id']},", f"  author = {{{esc(authors)}}},",
                f"  title = {{{esc(ref['title'])}}},", f"  year = {{{ref['year']}}},",
                f"  note = {{{esc(ref['publication_or_version'])}}},",
                f"  url = {{{ref['primary_url']}}},", "  urldate = {2026-10-27}", "}", ""]
    (HERE / "references.bib").write_text("\n".join(bib))
    missing = []
    for path in [MAIN, SLIDES, HERE / "source_inventory.md"]:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if target.startswith(("http://", "https://", "#")):
                continue
            candidate = (path.parent / target.split("#")[0]).resolve()
            if not candidate.exists():
                missing.append({"document": path.name, "target": target})
    assert not missing, missing
    for path in [MAIN, SLIDES]:
        value = path.read_text()
        assert value.count("```") % 2 == 0
        assert not re.search(r"\ue000|\ue001|turn\d+(?:view|search)|TODO|TBD", value)
    qa = {"local_markdown_links_pass": True, "reference_count": len(references),
          "primary_source_domains": sorted({r["primary_url"].split('/')[2] for r in references}),
          "slide_count": len(re.findall(r"^### Slide\s*\d+", SLIDES.read_text(), re.M)),
          "qa_question_count": len(re.findall(r"^### \d+\. “", SLIDES.read_text(), re.M)),
          "documents": [{"name": p.name, "characters": len(p.read_text()),
                         "whitespace_words": len(p.read_text().split()),
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in [MAIN, SLIDES]]}
    assert qa["slide_count"] == 22 and qa["qa_question_count"] == 22
    (HERE / "editorial_checks.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
