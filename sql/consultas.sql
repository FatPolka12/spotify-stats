-- Consultas de ejemplo para explorar tus datos.
-- Ejecútalas con:  psql spotify_stats -f sql/consultas.sql
-- o copia una sola en psql.

-- 1. ¿Cuántas reproducciones hay en total y desde cuándo?
SELECT count(*)                                              AS reproducciones,
       min(played_at AT TIME ZONE 'America/Mexico_City')     AS primera,
       max(played_at AT TIME ZONE 'America/Mexico_City')     AS ultima
FROM plays;

-- 2. Artistas más escuchados (solo artista principal de cada canción)
SELECT ar.name AS artista, count(*) AS reproducciones
FROM plays p
JOIN track_artists ta ON ta.track_id = p.track_id AND ta.position = 0
JOIN artists ar       ON ar.artist_id = ta.artist_id
GROUP BY ar.name
ORDER BY reproducciones DESC
LIMIT 10;

-- 3. Canciones más repetidas
SELECT t.name AS cancion, count(*) AS veces
FROM plays p
JOIN tracks t ON t.track_id = p.track_id
GROUP BY t.name
ORDER BY veces DESC
LIMIT 10;

-- 4. ¿A qué hora escuchas más música? (convertido de UTC a hora de Guadalajara)
SELECT extract(hour FROM played_at AT TIME ZONE 'America/Mexico_City') AS hora_local,
       count(*) AS reproducciones
FROM plays
GROUP BY hora_local
ORDER BY hora_local;

-- 5. Historial de ejecuciones del pipeline
SELECT run_id, source, status, rows_fetched, rows_inserted,
       started_at AT TIME ZONE 'America/Mexico_City' AS inicio
FROM ingestion_runs
ORDER BY run_id DESC
LIMIT 10;
