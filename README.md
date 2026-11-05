# Spotify Listening Stats

Pipeline de datos que extrae mi historial de escucha desde la **Spotify Web API** (OAuth 2.0), lo almacena en **PostgreSQL** y lo expone a través de una **API REST propia** construida con FastAPI.

> 🚧 Proyecto en construcción. Estado actual: **Fase 2 — almacenamiento en PostgreSQL**.

## Arquitectura

```
Spotify Web API ──(OAuth 2.0, JSON)──► Extracción en Python ──► PostgreSQL ──► API REST (FastAPI) ──► Dashboard
```

## Roadmap

- [x] **Fase 1:** Autenticación OAuth (Authorization Code) y extracción de reproducciones recientes
- [x] **Fase 2:** Modelo relacional en PostgreSQL y ETL incremental sin duplicados
- [ ] **Fase 3:** Carga del historial completo exportado desde Spotify y ejecución automática programada
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
4. Crea la base de datos y las tablas:
   ```bash
   createdb spotify_stats
   python src/db.py
   ```
5. Carga tus reproducciones recientes:
   ```bash
   python src/load_recent.py
   ```
   La primera vez se abrirá el navegador para autorizar la app. Después, el token se renueva automáticamente y cada ejecución solo guarda las reproducciones nuevas.

## Estructura

```
spotify-stats/
├── src/
│   ├── auth.py            # Flujo OAuth 2.0 y renovación de tokens
│   ├── spotify_client.py  # Cliente HTTP (GET/POST, manejo de errores 429)
│   ├── fetch_recent.py    # Prueba de extracción (guarda el JSON crudo)
│   ├── db.py              # Conexión a PostgreSQL y creación del esquema
│   └── load_recent.py     # ETL incremental: API -> PostgreSQL
├── sql/
│   ├── schema.sql         # Modelo relacional
│   └── consultas.sql      # Consultas de análisis de ejemplo
├── data/                  # Datos locales (no se suben al repo)
├── .env.example
└── requirements.txt
```

## Modelo de datos

```
artists ──< track_artists >── tracks >── albums
                                │
                              plays ──> ingestion_runs
```

- `plays` usa el instante de reproducción (`played_at`, en UTC) como llave primaria: así la misma canción puede repetirse, pero ninguna reproducción se guarda dos veces.
- `ingestion_runs` registra cada ejecución del pipeline (filas recibidas, insertadas y errores).

## Tecnologías

Python · requests · OAuth 2.0 · REST · JSON · PostgreSQL · psycopg · FastAPI *(próximamente)*
