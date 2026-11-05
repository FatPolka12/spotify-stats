-- Esquema de la base de datos spotify_stats
-- Se puede ejecutar varias veces sin error gracias a IF NOT EXISTS.

-- Registro de cada ejecución del proceso de carga (auditoría del pipeline)
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id         SERIAL PRIMARY KEY,
    source         TEXT        NOT NULL,             -- de dónde vienen los datos
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ,
    status         TEXT        NOT NULL DEFAULT 'running',  -- running | ok | error
    rows_fetched   INTEGER,
    rows_inserted  INTEGER,
    error_message  TEXT
);

CREATE TABLE IF NOT EXISTS artists (
    artist_id  TEXT PRIMARY KEY,   -- ID de Spotify
    name       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS albums (
    album_id      TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    album_type    TEXT,            -- album | single | compilation
    release_date  TEXT             -- Spotify la da como '2019', '2019-05' o '2019-05-17'
);

CREATE TABLE IF NOT EXISTS tracks (
    track_id     TEXT PRIMARY KEY,
    name         TEXT    NOT NULL,
    album_id     TEXT    REFERENCES albums(album_id),
    duration_ms  INTEGER,
    explicit     BOOLEAN
);

-- Relación muchos a muchos: una canción puede tener varios artistas
CREATE TABLE IF NOT EXISTS track_artists (
    track_id   TEXT     NOT NULL REFERENCES tracks(track_id),
    artist_id  TEXT     NOT NULL REFERENCES artists(artist_id),
    position   SMALLINT NOT NULL,  -- 0 = artista principal
    PRIMARY KEY (track_id, artist_id)
);

-- Cada fila es una reproducción. El instante exacto la identifica de forma única:
-- la misma canción puede escucharse varias veces, pero no dos veces en el mismo instante.
CREATE TABLE IF NOT EXISTS plays (
    played_at     TIMESTAMPTZ PRIMARY KEY,           -- se guarda en UTC
    track_id      TEXT    NOT NULL REFERENCES tracks(track_id),
    ms_played     INTEGER,                           -- solo viene en el historial exportado
    context_type  TEXT,                              -- playlist | album | artist | null
    source        TEXT    NOT NULL,
    run_id        INTEGER REFERENCES ingestion_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_plays_track_id ON plays (track_id);
CREATE INDEX IF NOT EXISTS idx_track_artists_artist_id ON track_artists (artist_id);
