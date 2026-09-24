"""Valores de configuración de la aplicación web CAPS VNZLA."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Configuración central de la aplicación.

    Los secretos, la conexión de base de datos y la tasa de cambio se cargan
    desde el entorno para mantener el proyecto portable y seguro.
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "caps-vnzla-dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'caps_vnzla.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CURRENCY_RATE_BS = float(os.getenv("CURRENCY_RATE_BS", "35.0"))
    SHIPPING_COST_USD = float(os.getenv("SHIPPING_COST_USD", "5.0"))
    WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "584122967035")
    ADMIN_DEFAULT_USERNAME = os.getenv("ADMIN_DEFAULT_USERNAME", "admin")
    ADMIN_DEFAULT_PASSWORD = os.getenv("ADMIN_DEFAULT_PASSWORD", "cambiar-esta-clave")
