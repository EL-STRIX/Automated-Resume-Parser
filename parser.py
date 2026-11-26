import csv
import os
import re
import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load("en_core_web_sm")

_SKILLS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills.csv")
_SKILL_MAP = {}
_MATCHER = PhraseMatcher(nlp.vocab, attr="LOWER")

with open(_SKILLS_PATH, "r", encoding="utf-8", newline="") as _f:
    _patterns = []
    for _row in csv.DictReader(_f):
        _skill = _row["skill"].strip()
        _category = _row["category"].strip()
        if _skill:
            _SKILL_MAP[_skill.lower()] = (_skill, _category)
            _patterns.append(nlp.make_doc(_skill))
    _MATCHER.add("SKILLS", _patterns)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\(?\d[\d\s\-\(\)]{8,18}\d)")
_DEGREE_RE = re.compile(
    r"(?i:\b(?:B\.?Tech|B\.?Sc|BCA|M\.?Tech|MCA|MBA|M\.?Sc|Ph\.?D\.?|Bachelor(?:'s)?|Master(?:'s)?|Diploma|12th|10th)\b)"
    r"|(?:\bB\.?E\.?\b)"
)
_INSTITUTION_RE = re.compile(r"\b(university|college|institute|school)\b", re.IGNORECASE)


def extract_email(text):
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text):
    if not text:
        return None
    for match in _PHONE_RE.finditer(text):
        candidate = match.group(0).strip()
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 13:
            return candidate
    return None


_SECTION_END_RE = re.compile(
    r"^(?:summary|objective|skills|technical skills|experience|work experience|projects|certifications|achievements|awards|languages|interests|references)\b",
    re.IGNORECASE,
)
_EDU_START_RE = re.compile(r"^(?:education|academic background|academics|qualifications)\b", re.IGNORECASE)


def extract_name(text):
    if not text:
        return None
    lines = [line.strip() for line in text.splitlines() if line.strip()][:10]
    if not lines:
        return None

    for line in lines:
        if ":" in line and not line.lower().startswith("name:"):
            continue
        candidate_line = line[5:].strip() if line.lower().startswith("name:") else line
        doc = nlp(candidate_line.title() if candidate_line.isupper() else candidate_line)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = " ".join(ent.text.split())
                if (
                    name
                    and "@" not in name
                    and not any(ch.isdigit() for ch in name)
                    and name.lower() not in _SKILL_MAP
                ):
                    return candidate_line if candidate_line.isupper() else name

    for line in lines:
        if not any(ch.isdigit() for ch in line) and "@" not in line and ":" not in line:
            return line
    return None


def extract_skills(text):
    if not text:
        return []
    doc = nlp(text)
    seen = set()
    skills = []
    for _, start, end in _MATCHER(doc):
        key = doc[start:end].text.lower()
        if key in _SKILL_MAP and key not in seen:
            seen.add(key)
            skills.append(_SKILL_MAP[key])
    return skills


def extract_education(text):
    if not text:
        return []
    all_lines = [line.strip() for line in text.splitlines() if line.strip()]

    edu_lines = []
    in_edu = False
    for line in all_lines:
        if _EDU_START_RE.match(line):
            in_edu = True
            edu_lines.append(line)
            continue
        if in_edu:
            if _SECTION_END_RE.match(line):
                break
            edu_lines.append(line)

    lines = edu_lines if edu_lines else all_lines
    results = []
    seen = set()

    for i, line in enumerate(lines):
        deg_match = _DEGREE_RE.search(line)
        if not deg_match:
            continue

        segments = [s.strip() for s in re.split(r"[,|\-\u2013\u2014\t]+", line) if s.strip()]
        deg_seg = next((s for s in segments if _DEGREE_RE.search(s)), deg_match.group(0))
        deg_seg = re.sub(r"\s+(?:expected\b.*|(?:19|20)\d{2}\b.*)$", "", deg_seg, flags=re.IGNORECASE).strip()
        degree = (deg_seg or deg_match.group(0))[:100]

        institution = None
        inst_segs = [s for s in segments if s != deg_seg and _INSTITUTION_RE.search(s)]
        if inst_segs:
            institution = inst_segs[0][:255]
        elif _INSTITUTION_RE.search(line) and not inst_segs:
            institution = line[:255]
        elif i + 1 < len(lines) and _INSTITUTION_RE.search(lines[i + 1]):
            institution = lines[i + 1][:255]
        elif i - 1 >= 0 and _INSTITUTION_RE.search(lines[i - 1]):
            institution = lines[i - 1][:255]

        key = (degree.lower(), (institution or "").lower())
        if key not in seen:
            seen.add(key)
            results.append({"degree": degree, "institution": institution})

    return results


def parse_resume(text):
    if not text:
        return {
            "name": None,
            "email": None,
            "phone": None,
            "skills": [],
            "education": [],
        }
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
    }
