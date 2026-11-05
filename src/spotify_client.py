"""
Cliente mínimo para la Web API de Spotify.

Envuelve las peticiones HTTP para:
- añadir siempre el header `Authorization: Bearer <token>`,
- reintentar cuando Spotify responde 429 (demasiadas peticiones),
- convertir la respuesta JSON en diccionarios de Python.
"""

import time

import requests

from auth import get_access_token

BASE_URL = "https://api.spotify.com/v1"


def get(endpoint: str, params: dict | None = None, max_retries: int = 3) -> dict:
    """Hace un GET a la API de Spotify y devuelve el JSON como diccionario."""
    for _ in range(max_retries):
        headers = {"Authorization": f"Bearer {get_access_token()}"}
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params, timeout=15)

        if resp.status_code == 429:  # límite de peticiones: esperamos lo que indique Spotify
            wait = int(resp.headers.get("Retry-After", 5))
            print(f"Límite de peticiones alcanzado, esperando {wait} s...")
            time.sleep(wait)
            continue

        resp.raise_for_status()  # lanza error en 4xx/5xx
        return resp.json()

    raise RuntimeError(f"No se pudo completar GET {endpoint} tras {max_retries} intentos")


def post(endpoint: str, payload: dict) -> dict:
    """Hace un POST con cuerpo JSON (lo usaremos para crear playlists)."""
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    resp = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()
