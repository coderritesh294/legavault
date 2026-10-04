# LegaVault

Initial project foundation for the LegaVault secure legal document platform.

## Project layout

- `backend/`: FastAPI application and environment-based MySQL settings.
- `frontend/`: React application built with Vite and styled with Bootstrap.

The MySQL database `legavault_db` is expected to exist on `localhost:3306`. This foundation does not create tables or connect to the database.

## Backend setup

From the repository root, copy `backend/.env.example` to `backend/.env`, then set the MySQL username and password in that local file. Install and run the API:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend setup

In a separate terminal, install dependencies and start the development server:

```powershell
cd frontend
npm install
npm run dev
```