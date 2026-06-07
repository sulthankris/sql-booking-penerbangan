# Render Deployment

## Required Files

Keep these files in the GitHub repository:

- `app.py`
- `flight-booking.db`
- `requirements.txt`
- `render.yaml`
- `runtime.txt`

Do not ignore `flight-booking.db`; the app reads this SQLite file at runtime.

## Deploy With Blueprint

1. Push this project folder to GitHub.
2. Open Render.
3. Choose **New +** → **Blueprint**.
4. Select the GitHub repository.
5. Render will read `render.yaml` and create the free web service.

## Manual Render Settings

If not using Blueprint, create a **Web Service** with these settings:

- Environment: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`

## Free Plan Notes

- The service sleeps when inactive.
- First load after sleeping can be slow.
- GUI inserts into SQLite may reset after redeploy.
- The seed database remains reproducible through the ordered scripts.
