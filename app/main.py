"""Punto de entrada de FastAPI; los routers se incorporan por capacidad."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.reservations.router import router as reservations_router
from app.spaces.router import router as spaces_router
from app.users.router import router as users_router

app = FastAPI(title="Reservas de espacios académicos")
app.include_router(users_router)
app.include_router(spaces_router)
app.include_router(reservations_router)

WEB_DIRECTORY = Path(__file__).parent / "web" / "static"
app.mount("/assets", StaticFiles(directory=WEB_DIRECTORY), name="assets")


@app.get("/", include_in_schema=False)
def application_home() -> FileResponse:
    """Sirve la interfaz web; la documentación técnica se conserva en /docs."""
    return FileResponse(WEB_DIRECTORY / "index.html")
