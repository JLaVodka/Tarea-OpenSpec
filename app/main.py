"""Punto de entrada de FastAPI; los routers se incorporan por capacidad."""

from fastapi import FastAPI

from app.spaces.router import router as spaces_router
from app.users.router import router as users_router

app = FastAPI(title="Reservas de espacios académicos")
app.include_router(users_router)
app.include_router(spaces_router)
