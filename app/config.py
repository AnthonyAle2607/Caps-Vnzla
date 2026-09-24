"""Configuration values for the CAPS VNZLA web application."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Central application configuration.

    Secrets, database connection and currency settings are loaded from the
    environment to keep the project portable and secure.
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "caps-vnzla-dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'caps_vnzla.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CURRENCY_RATE_BS = float(os.getenv("CURRENCY_RATE_BS", "35.0"))
