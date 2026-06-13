# Repair Material Calculator Pro - Web Version

Flask web app with PostgreSQL support for Render deployment.

## Local Run

```bash
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Render Deployment

1. Push all files to GitHub.
2. Create PostgreSQL database on Render.
3. Create Web Service from GitHub repo.
4. Build Command:

```bash
pip install -r requirements.txt
```

5. Start Command:

```bash
gunicorn app:app
```

6. Add Environment Variables:

```text
DATABASE_URL = your Render PostgreSQL internal database URL
SECRET_KEY = any strong random text
```

The app creates tables automatically on first run.
