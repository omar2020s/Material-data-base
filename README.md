# Repair Material Calculator Pro - Flask + PostgreSQL

## Render Settings

Build Command:
```bash
pip install -r requirements.txt
```

Start Command:
```bash
gunicorn app:app
```

Environment Variables:
```text
DATABASE_URL=your Render Internal Database URL
SECRET_KEY=any strong secret key
```

Important:
- Do not upload runtime.txt.
- Use `.python-version` with only `3.11.9`.
- Requirements uses `psycopg[binary]` not `psycopg2-binary`.
