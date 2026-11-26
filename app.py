import os
from flask import Flask, abort, flash, redirect, render_template, request, url_for
import db
import extractor
import parser

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "resume-parser-secret")


@app.get("/")
def index():
    name = request.args.get("name", "").strip()
    skill_param = request.args.get("skill", "").strip()
    degree = request.args.get("degree", "").strip()

    skills = [s.strip() for s in skill_param.split(",") if s.strip()] if skill_param else None
    candidates = db.search_candidates(
        name=name or None,
        skills=skills,
        degree=degree or None,
    )
    return render_template(
        "index.html",
        candidates=candidates,
        name=name,
        skill=skill_param,
        degree=degree,
    )


@app.post("/upload")
def upload():
    files = request.files.getlist("resumes")
    valid_files = [f for f in files if f and f.filename]
    if not valid_files:
        flash("Please select at least one PDF or DOCX file.", "error")
        return redirect(url_for("index"))

    uploaded_count = 0
    for file in valid_files:
        try:
            raw_text = extractor.extract_text(file)
            parsed = parser.parse_resume(raw_text)
            db.add_candidate(
                file_name=file.filename,
                name=parsed["name"],
                email=parsed["email"],
                phone=parsed["phone"],
                raw_text=raw_text,
                skills=parsed["skills"],
                education=parsed["education"],
            )
            uploaded_count += 1
        except Exception as exc:
            flash(f"Skipped '{file.filename}': {exc}", "error")

    if uploaded_count:
        flash(f"Uploaded and parsed {uploaded_count} resume(s).", "success")
    return redirect(url_for("index"))


@app.get("/candidate/<int:candidate_id>")
def candidate_detail(candidate_id):
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        abort(404)
    return render_template("candidate.html", candidate=candidate)


@app.post("/candidate/<int:candidate_id>/delete")
def delete_candidate_route(candidate_id):
    if not db.delete_candidate(candidate_id):
        abort(404)
    flash("Candidate deleted.", "success")
    return redirect(url_for("index"))
