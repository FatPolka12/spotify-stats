"""
Prueba de la Fase 1: consulta tu perfil y tus últimas reproducciones,
las muestra en pantalla y guarda la respuesta JSON cruda en data/raw/.

Uso:  python src/fetch_recent.py
"""

import json
from datetime import datetime
from pathlib import Path

from spotify_client import get

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main():
    me = get("/me")
    print(f"Conectado como: {me.get('display_name')} ({me.get('id')})\n")

    # Spotify devuelve como máximo 50 reproducciones recientes por petición
    recent = get("/me/player/recently-played", params={"limit": 50})

    print("Últimas reproducciones:")
    for item in recent["items"][:10]:
        track = item["track"]
        artists = ", ".join(a["name"] for a in track["artists"])
        print(f"  {item['played_at']}  |  {track['name']} — {artists}")
    print(f"  ... ({len(recent['items'])} en total)\n")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / f"recently_played_{datetime.now():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(recent, indent=2, ensure_ascii=False))
    print(f"Respuesta JSON guardada en {out}")


if __name__ == "__main__":
    main()
