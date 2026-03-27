"""
FastAPI entry point for the RepoLens backend.
Exposes endpoints consumed by the Chrome extension.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router

app = FastAPI(title="RepoLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
