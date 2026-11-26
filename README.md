# Automated Resume Parser

## Setup

1. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Install dependencies and download the spaCy model:
   ```powershell
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

## Create the Database

1. Create a PostgreSQL database (for example `resume_parser`) and apply `schema.sql`:
   ```powershell
   psql -U postgres -d postgres -c "CREATE DATABASE resume_parser;"
   psql -U postgres -d resume_parser -f schema.sql
   ```
2. Set the `DATABASE_URL` environment variable:
   ```powershell
   $env:DATABASE_URL = "postgresql://postgres:<password>@localhost:5432/resume_parser"
   ```

## Run the App

```powershell
flask --app app run
```

Open `http://127.0.0.1:5000` in your browser.
