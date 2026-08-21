"""
app.py
======
Application entry point for the CrimeSense backend.

Builds a FastAPI application, registers the crime routes, and adds CORS
so a web frontend can call the API.  Run with:

    uvicorn backend.app:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db, routes


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="CrimeSense API",
        version="1.0.0",
        description="Crime incident, hotspot, locality and proximity API "
                    "for the CrimeSense backend.",
    )

    # CORS: allow the frontend (any origin during development) to call the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes.router)

    @app.get("/", tags=["service"])
    def root():
        return {
            "service": "CrimeSense API",
            "docs": "/docs",
            "database": str(db.DB_PATH),
            "total_crimes": db.total_rows(),
        }

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()