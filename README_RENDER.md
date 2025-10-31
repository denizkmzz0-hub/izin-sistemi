# Deploy instructions for Render (render.com)

This project is prepared to be deployable on Render (or similar PaaS) with PostgreSQL support.

## Quick steps (Render)
1. Push this repository to GitHub.
2. Create a new **Web Service** on Render and connect to the GitHub repo.
3. Set the **Build Command** to:
   ```bash
   pip install -r requirements.txt
   ```
4. Set the **Start Command** to:
   ```bash
   gunicorn app:app
   ```
5. Add a **Postgres** database from Render's dashboard; it will provide a `DATABASE_URL` env var.
6. In Render service settings, add env vars:
   - `DATABASE_URL` (auto-provided if you added the DB)
   - `FLASK_SECRET_KEY` (set a secure random value)
7. Deploy. After successful deploy your app will be available at `https://<your-service>.onrender.com`.

## Local testing with SQLite
1. Create virtualenv and install requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. Initialize DB (SQLite):
   ```bash
   python init_db_render.py
   ```
3. Run locally (development):
   ```bash
   python app.py
   ```

## Notes
- This project supports both SQLite (default) and Postgres via `DATABASE_URL`.
- If you use Postgres, run `python init_db_render.py` after setting `DATABASE_URL` to create tables.
