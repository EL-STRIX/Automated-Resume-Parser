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


def extract_name(text):
    if not text:
        return None
    lines = [line.strip() for line in text.splitlines() if line.strip()][:10]
    if not lines:
        return None

    for line in lines:
        doc = nlp(line)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = " ".join(ent.text.split())
                if (
                    name
                    and "@" not in name
                    and not any(ch.isdigit() for ch in name)
                    and name.lower() not in _SKILL_MAP
                ):
                    return name

    for line in lines:
        if not any(ch.isdigit() for ch in line) and "@" not in line:
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
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    results = []
    seen = set()

    for i, line in enumerate(lines):
        deg_match = _DEGREE_RE.search(line)
        if not deg_match:
            continue
        degree = deg_match.group(0)
        institution = None

        if _INSTITUTION_RE.search(line):
            parts = [p.strip() for p in re.split(r"[,|\-]", line) if _INSTITUTION_RE.search(p)]
            institution = parts[0] if parts else line
        elif i + 1 < len(lines) and _INSTITUTION_RE.search(lines[i + 1]):
            institution = lines[i + 1]
        elif i - 1 >= 0 and _INSTITUTION_RE.search(lines[i - 1]):
            institution = lines[i - 1]

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
