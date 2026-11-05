"""
ETL de reproducciones recientes:
  Extract   -> GET /me/player/recently-played (solo lo posterior a la última carga)
  Transform -> separa el JSON anidado en artistas, álbumes, canciones y reproducciones
  Load      -> inserta en PostgreSQL sin duplicados (ON CONFLICT DO NOTHING)

Cada ejecución queda registrada en la tabla ingestion_runs.

Uso:  python src/load_recent.py
"""

from db import connect
from spotify_client import get

SOURCE = "api_recently_played"


def save_item(cur, item: dict, run_id: int) -> int:
    """Guarda una reproducción y sus entidades relacionadas. Devuelve 1 si era nueva, 0 si no."""
    track = item["track"]
    if not track or not track.get("id"):
        return 0  # archivos locales o elementos sin ID de Spotify: se omiten

    album = track["album"]
    cur.execute(
        """
        INSERT INTO albums (album_id, name, album_type, release_date)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (album_id) DO NOTHING
        """,
        (album["id"], album["name"], album.get("album_type"), album.get("release_date")),
    )

    cur.execute(
        """
        INSERT INTO tracks (track_id, name, album_id, duration_ms, explicit)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (track_id) DO NOTHING
        """,
        (track["id"], track["name"], album["id"], track.get("duration_ms"), track.get("explicit")),
    )

    for position, artist in enumerate(track["artists"]):
        cur.execute(
            "INSERT INTO artists (artist_id, name) VALUES (%s, %s) ON CONFLICT (artist_id) DO NOTHING",
            (artist["id"], artist["name"]),
        )
        cur.execute(
            """
            INSERT INTO track_artists (track_id, artist_id, position)
            VALUES (%s, %s, %s)
            ON CONFLICT (track_id, artist_id) DO NOTHING
            """,
            (track["id"], artist["id"], position),
        )

    context = item.get("context") or {}
    cur.execute(
        """
        INSERT INTO plays (played_at, track_id, context_type, source, run_id)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (played_at) DO NOTHING
        """,
        (item["played_at"], track["id"], context.get("type"), SOURCE, run_id),
    )
    return cur.rowcount  # 1 si se insertó, 0 si ya existía


def main():
    with connect() as conn:
        # 1. Abrimos un registro de ejecución
        run_id = conn.execute(
            "INSERT INTO ingestion_runs (source) VALUES (%s) RETURNING run_id", (SOURCE,)
        ).fetchone()[0]
        conn.commit()

        try:
            # 2. Carga incremental: solo pedimos lo posterior a la última reproducción guardada
            last = conn.execute(
                "SELECT max(played_at) FROM plays WHERE source = %s", (SOURCE,)
            ).fetchone()[0]
            params = {"limit": 50}
            if last is not None:
                params["after"] = int(last.timestamp() * 1000)  # Spotify espera milisegundos Unix

            items = get("/me/player/recently-played", params=params)["items"]

            # 3. Transformar y cargar
            with conn.cursor() as cur:
                inserted = sum(save_item(cur, item, run_id) for item in items)

            conn.execute(
                """
                UPDATE ingestion_runs
                SET finished_at = now(), status = 'ok', rows_fetched = %s, rows_inserted = %s
                WHERE run_id = %s
                """,
                (len(items), inserted, run_id),
            )
            conn.commit()
            print(f"Ejecución #{run_id}: {len(items)} reproducciones recibidas, {inserted} nuevas guardadas.")

        except Exception as exc:
            conn.rollback()  # deshace los datos a medias de esta ejecución
            conn.execute(
                """
                UPDATE ingestion_runs
                SET finished_at = now(), status = 'error', error_message = %s
                WHERE run_id = %s
                """,
                (str(exc), run_id),
            )
            conn.commit()
            raise


if __name__ == "__main__":
    main()
