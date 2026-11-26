# Automated Resume Parser

A Flask and PostgreSQL web application that extracts candidate details from PDF and DOCX resumes, categorizes skills, and provides a searchable candidate directory.

## Features

- **Multi-file Upload:** Drag-and-drop or browse to upload one or more `.pdf` / `.docx` resumes (invalid files are skipped without stopping the batch).
- **Text & Field Extraction:**
  - Reads PDF pages (`pdfplumber`) and DOCX headers, paragraphs, and tables (`python-docx`).
  - Extracts **Name**, **Email**, **Phone**, **Skills** (categorized via `skills.csv` into *Programming*, *Database*, *Web*, *Data/ML*, and *Tools*), and **Education** (degree and institution).
- **Search & Filter:** Search candidates by name, comma-separated skills (must match all listed skills), and degree (including common abbreviations like `BCA`, `B.Tech`, `MCA`, `M.Tech`).
- **Candidate Management:** View full categorized skills and education on a detail page, and delete candidates with inline confirmation.

## Tech Stack

- **Backend:** Python 3.10+, Flask
- **NLP / Parsing:** spaCy (`en_core_web_sm`), built-in `re`
- **File Extraction:** `pdfplumber` (PDF), `python-docx` (DOCX)
- **Database:** PostgreSQL + `psycopg2-binary`
- **Frontend:** HTML, CSS, vanilla JavaScript (no external frameworks or CDNs)

## Project Structure

```text
app.py                  # Flask routes (/, /upload, /candidate/<id>, /candidate/<id>/delete)
db.py                   # PostgreSQL connection and queries
extractor.py            # PDF and DOCX text extraction
parser.py               # Field extraction (name, email, phone, skills, education)
skills.csv              # Fixed list of categorized skills
schema.sql              # PostgreSQL tables and search indexes
requirements.txt        # Python dependencies
templates/
  index.html            # Upload, search, and candidate list
  candidate.html        # Candidate detail view
```

## Setup Guide

### 1. Create Virtual Environment & Install Dependencies

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Create the PostgreSQL Database

Ensure PostgreSQL is running, then create the database and apply `schema.sql`:

```powershell
psql -U postgres -d postgres -c "CREATE DATABASE resume_parser;"
psql -U postgres -d resume_parser -f schema.sql
```

### 3. Configure `DATABASE_URL` & Run the App

> If your password contains special characters (such as `@`, `,`, or spaces), URL-encode them in `DATABASE_URL`.

**Windows (PowerShell):**
```powershell
$env:DATABASE_URL = "postgresql://postgres:<password>@localhost:5432/resume_parser"
flask --app app run
```

**macOS / Linux:**
```bash
export DATABASE_URL="postgresql://postgres:<password>@localhost:5432/resume_parser"
flask --app app run
```

Open `http://127.0.0.1:5000` in your browser.
