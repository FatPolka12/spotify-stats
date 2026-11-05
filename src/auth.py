"""
Autenticación con Spotify mediante el flujo "Authorization Code" de OAuth 2.0.

Flujo:
1. Abrimos en el navegador la página de autorización de Spotify.
2. El usuario acepta y Spotify redirige a nuestro servidor local con un `code`.
3. Intercambiamos ese `code` por un access token y un refresh token (POST /api/token).
4. Guardamos los tokens en disco. Cuando el access token expira (~1 hora),
   usamos el refresh token para pedir uno nuevo sin volver a abrir el navegador.
"""

import base64
import json
import os
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
TOKEN_FILE = Path(__file__).resolve().parent.parent / ".tokens.json"

# Permisos (scopes) que pedimos al usuario
SCOPES = " ".join([
    "user-read-recently-played",   # historial reciente
    "user-top-read",               # artistas y canciones más escuchados
    "playlist-read-private",       # leer playlists privadas
    "playlist-modify-private",     # crear/editar playlists privadas
    "playlist-modify-public",      # crear/editar playlists públicas
])


def _basic_auth_header() -> dict:
    """Header 'Authorization: Basic <base64(client_id:client_secret)>' que pide Spotify."""
    creds = f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    return {"Authorization": "Basic " + base64.b64encode(creds).decode()}


def _save_tokens(data: dict) -> dict:
    """Guarda los tokens con su hora de expiración absoluta."""
    data["expires_at"] = int(time.time()) + data["expires_in"] - 60  # margen de 1 min
    TOKEN_FILE.write_text(json.dumps(data, indent=2))
    return data


def _wait_for_code(expected_state: str) -> str:
    """Levanta un servidor HTTP local y espera a que Spotify redirija con el `code`."""
    parsed = urlparse(REDIRECT_URI)
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            result["code"] = query.get("code", [None])[0]
            result["state"] = query.get("state", [None])[0]
            result["error"] = query.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("Autorización recibida. Ya puedes cerrar esta pestaña.".encode())

        def log_message(self, *args):  # silencia el log del servidor
            pass

    server = HTTPServer((parsed.hostname, parsed.port), Handler)
    server.handle_request()  # atiende una sola petición y termina
    server.server_close()

    if result.get("error"):
        raise RuntimeError(f"Spotify devolvió un error: {result['error']}")
    if result.get("state") != expected_state:
        raise RuntimeError("El parámetro 'state' no coincide (posible petición falsificada).")
    return result["code"]


def login() -> dict:
    """Ejecuta el flujo completo de autorización (solo se necesita la primera vez)."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError("Faltan SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET en el archivo .env")

    state = secrets.token_urlsafe(16)
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    print("Abriendo el navegador para autorizar la app...\nSi no se abre, visita:\n", url)
    webbrowser.open(url)

    code = _wait_for_code(state)

    # Intercambio del code por tokens: POST con datos de formulario
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI},
        headers=_basic_auth_header(),
        timeout=15,
    )
    resp.raise_for_status()
    print("Tokens obtenidos y guardados en .tokens.json")
    return _save_tokens(resp.json())


def refresh(tokens: dict) -> dict:
    """Pide un access token nuevo usando el refresh token."""
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]},
        headers=_basic_auth_header(),
        timeout=15,
    )
    resp.raise_for_status()
    new = resp.json()
    # Spotify no siempre devuelve un refresh token nuevo; si no viene, conservamos el anterior
    new.setdefault("refresh_token", tokens["refresh_token"])
    return _save_tokens(new)


def get_access_token() -> str:
    """Devuelve un access token válido: lo lee de disco, lo renueva o inicia el login."""
    if not TOKEN_FILE.exists():
        return login()["access_token"]
    tokens = json.loads(TOKEN_FILE.read_text())
    if time.time() >= tokens["expires_at"]:
        tokens = refresh(tokens)
    return tokens["access_token"]


if __name__ == "__main__":
    login()
