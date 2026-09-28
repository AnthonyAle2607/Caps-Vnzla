"""Punto de entrada WSGI reconocido por Vercel para la aplicación Flask."""

from app import create_app

app = create_app()
