from fastapi import FastAPI

from app.auth import router as auth_router
from app.database import get_db_connection


app = FastAPI(
    title="LegaVault API",
    version="0.1.0",
)


app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "LegaVault API is running"
    }


@app.get("/health/database")
def database_health():
    connection = None

    try:
        connection = get_db_connection()

        return {
            "status": "success",
            "database": "connected",
        }

    except Exception as exc:
        return {
            "status": "error",
            "database": "connection failed",
            "detail": str(exc),
        }

    finally:
        if connection is not None and connection.is_connected():
            connection.close()