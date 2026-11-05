# Spotify Listening Stats

Pipeline de datos que extrae mi historial de escucha desde la **Spotify Web API** (OAuth 2.0), lo almacena en **PostgreSQL** y lo expone a través de una **API REST propia** construida con FastAPI.

> 🚧 Proyecto en construcción. Estado actual: **Fase 1 — autenticación y extracción**.

## Arquitectura

```
Spotify Web API ──(OAuth 2.0, JSON)──► Extracción en Python ──► PostgreSQL ──► API REST (FastAPI) ──► Dashboard
```

## Roadmap

- [x] **Fase 1:** Autenticación OAuth (Authorization Code) y extracción de reproducciones recientes
- [ ] **Fase 2:** Carga del historial completo exportado desde Spotify (JSON) a PostgreSQL
- [ ] **Fase 3:** Recolección incremental automática sin duplicados
- [ ] **Fase 4:** API REST propia con estadísticas calculadas en SQL
- [ ] **Fase 5:** Generación automática de playlists
- [ ] **Fase 6:** Dashboard, Docker y pruebas

## Instalación

1. Clona el repositorio y crea un entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Crea una app en el [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) y agrega como Redirect URI: `http://127.0.0.1:8888/callback`.
3. Copia `.env.example` como `.env` y llena tu Client ID y Client Secret.
4. Ejecuta:
   ```bash
   python src/fetch_recent.py
   ```
   La primera vez se abrirá el navegador para autorizar la app. Después, el token se renueva automáticamente.

## Estructura

```
spotify-stats/
├── src/
│   ├── auth.py            # Flujo OAuth 2.0 y renovación de tokens
│   ├── spotify_client.py  # Cliente HTTP (GET/POST, manejo de errores 429)
│   └── fetch_recent.py    # Extracción de reproducciones recientes
├── data/                  # Datos locales (no se suben al repo)
├── .env.example
└── requirements.txt
```

## Tecnologías

Python · requests · OAuth 2.0 · REST · JSON · PostgreSQL *(próximamente)* · FastAPI *(próximamente)*
