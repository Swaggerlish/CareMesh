# CareMesh

CareMesh is a Nigeria-focused healthcare discovery and planning app built for hackathon/demo use.
It helps users:

- search hospitals by state and LGA
- view coverage and medical desert insights
- book appointments
- simulate or process payments
- chat with a hosted AI assistant from the backend

## Stack

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: SQLite locally, PostgreSQL-ready
- Maps: Leaflet / React Leaflet
- AI: Hugging Face Inference Providers
- Payments: Interswitch

## Project Structure

```text
CareMesh/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      main.py
      seed.py
    alembic/
    data/
      planning/
    requirements.txt
    .env
    caremesh.db
  frontend/
    src/
      components/
      api.js
      App.jsx
    package.json
```

## Features

- Hospital search by state, LGA, and hospital
- Medical desert and planning analysis
- Hospital coverage map
- Appointment booking flow
- Payment payload/callback flow
- Hugging Face powered assistant with automatic model fallback

## Local Setup

### 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend runs on `http://localhost:8000`.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

## Environment

Main backend environment values live in `backend/.env`.
You can start from `backend/.env.example` when setting up a fresh environment.

Important values:

```env
# Local SQLite
DATABASE_URL=sqlite:///./caremesh.db

# Deployment PostgreSQL example
# DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@HOST:5432/DB_NAME

HF_TOKEN=your_huggingface_token
HF_MODEL=CohereLabs/tiny-aya-global:cohere
HF_FALLBACK_MODELS=zai-org/GLM-5:together,zai-org/GLM-4.7:cerebras
HF_BASE_URL=https://router.huggingface.co/v1/chat/completions
APP_DEBUG=true
```

Main frontend environment value:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## AI Chat Notes

CareMesh AI uses Hugging Face router models from the backend.

The app now:

- tries the primary HF model first
- automatically retries configured fallback models
- shows a clearer message when a selected model is unsupported

If none of the configured models are available for your Hugging Face provider setup, the app falls back to a safe explanatory message instead of crashing.

## Planning Data

Planning CSVs are stored in:

- `backend/data/planning/lga_profiles_nigeria_worldpop_v2.csv`
- `backend/data/planning/hospital_capacities_nigeria_grid3_baseline.csv`

These are used for:

- facilities summary
- medical desert detection
- inventory signals

## Build Checks

Frontend production build:

```powershell
cd frontend
npm run build
```

Backend syntax check:

```powershell
python -m compileall backend\app
```

## Deployment Notes

For GitHub + cloud deployment, PostgreSQL is the safer choice.

Why:

- SQLite is file-based and not ideal for many cloud runtimes
- PostgreSQL handles persistence and concurrent writes more reliably
- your SQLAlchemy setup is already compatible with PostgreSQL

Current compatibility check:

- `backend/app/db/session.py` already switches `check_same_thread` only for SQLite
- `backend/alembic/env.py` already reads `DATABASE_URL` from settings
- `psycopg2-binary` is already present in `backend/requirements.txt`

Recommended deployment flow:

1. Create a PostgreSQL database on your host platform
2. Set `DATABASE_URL` to the PostgreSQL connection string
3. Set `FRONTEND_URL` to your deployed frontend URL
4. Set `APP_REDIRECT_URL` to your deployed payment callback URL
5. Run Alembic migrations or let your deployment workflow migrate before first use

## Demo Flow

1. Start backend
2. Start frontend
3. Open the app
4. Select a state and LGA
5. Search hospitals
6. Open the Medical Deserts tab
7. Click `View Analysis`
8. Test AI chat interaction

## Notes

- This project is built for demonstration speed and usability.
- SQLite is fine for local demo use.
- Some Hugging Face models depend on the providers enabled on your HF account.
- Interswitch is currently configured for test/demo workflow.
