"""
postgres_sync.py
Synchronise les indicateurs FEC calculés vers PostgreSQL (table clients).

Usage :
    DATABASE_URL=postgresql://user:pass@host:5432/db python postgres_sync.py
"""
import logging
import os
import re

try:
    import psycopg2
except ImportError as exc:
    raise ImportError("psycopg2 non installé. Lance : pip install psycopg2-binary") from exc


# Correspondances manuelles pour les clés dont le nom PostgreSQL ne peut pas
# être déduit automatiquement (direct ou + "_r").
MANUAL_OVERRIDES: dict = {
    "masse_salariale": "m_salariale_r",
}

_RE_DIGIT       = re.compile(r"^\d")
_RE_NEEDS_QUOTE = re.compile(r"[^a-z0-9_]")
_RESERVED = {"is", "order", "table", "user", "type", "end", "start", "check", "index"}


def _qi(col: str) -> str:
    """Guillemets doubles si le nom n'est pas un identifiant SQL simple."""
    if _RE_DIGIT.match(col) or col in _RESERVED or _RE_NEEDS_QUOTE.search(col):
        return f'"{col}"'
    return col


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise EnvironmentError("Variable d'environnement DATABASE_URL non définie.")
    return url


def _fetch_pg_columns(cur) -> set:
    """Retourne l'ensemble des colonnes de la table clients via information_schema."""
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'clients' ORDER BY column_name"
    )
    return {row[0] for row in cur.fetchall()}


def _resolve_mapping(pg_cols: set, indicator_keys: list) -> tuple:
    """
    Construit {py_key: pg_col} en cherchant pour chaque clé indicateur :
      1. MANUAL_OVERRIDES  (nom non déductible automatiquement)
      2. Colonne directe   (py_key dans pg_cols)
      3. Suffixe _r        (py_key + "_r" dans pg_cols)

    Retourne (mapping, non_trouvés).
    """
    mapping   = {}
    unmatched = []

    for key in indicator_keys:
        if key == "siret":
            continue
        if key in MANUAL_OVERRIDES and MANUAL_OVERRIDES[key] in pg_cols:
            mapping[key] = MANUAL_OVERRIDES[key]
        elif key in pg_cols:
            mapping[key] = key
        elif (key + "_r") in pg_cols:
            mapping[key] = key + "_r"
        else:
            unmatched.append(key)

    return mapping, unmatched


def _build_upsert(siret: str, pg_row: dict) -> tuple:
    """Construit la requête UPSERT et la liste de valeurs pour une ligne."""
    cols   = ["siret"] + list(pg_row.keys())
    vals   = [siret]   + list(pg_row.values())
    q_cols = [_qi(c) for c in cols]

    update_parts = [
        f"{_qi(c)} = EXCLUDED.{_qi(c)}"
        for c in cols if c != "siret"
    ]
    on_conflict = f"DO UPDATE SET {', '.join(update_parts)}" if update_parts else "DO NOTHING"

    sql = (
        f"INSERT INTO clients ({', '.join(q_cols)}) "
        f"VALUES ({', '.join(['%s'] * len(cols))}) "
        f"ON CONFLICT (siret) {on_conflict}"
    )
    return sql, vals


def sync_all(indicateurs: list) -> dict:
    """
    Synchronise une liste d'indicateurs FEC vers PostgreSQL.

    - Récupère dynamiquement les colonnes réelles de la table clients.
    - Construit le mapping automatiquement (direct ou suffixe _r).
    - Affiche les indicateurs sans colonne correspondante.
    - N'upserte que les colonnes qui existent réellement.

    Retourne :
        {"updated": int, "errors": int}
    """
    database_url = _get_database_url()
    updated = 0
    errors  = 0

    conn = None
    try:
        conn = psycopg2.connect(database_url)
        cur  = conn.cursor()

        # ── 1. Colonnes réelles PostgreSQL ────────────────────────────────────
        pg_cols = _fetch_pg_columns(cur)
        logging.info("sync_all : %d colonne(s) trouvée(s) dans clients.", len(pg_cols))

        # ── 2. Mapping dynamique (calculé une fois sur le premier indicateur) ─
        mapping = {}
        if indicateurs:
            mapping, unmatched = _resolve_mapping(pg_cols, list(indicateurs[0].keys()))
            if unmatched:
                msg = ", ".join(unmatched)
                logging.warning("sync_all : %d indicateur(s) sans colonne PostgreSQL : %s", len(unmatched), msg)
                print(f"Indicateurs sans colonne PostgreSQL ({len(unmatched)}) : {msg}")

        if not mapping:
            logging.error("sync_all : aucune correspondance trouvée — abandon.")
            return {"updated": 0, "errors": 0}

        # ── 3. UPSERT ─────────────────────────────────────────────────────────
        for ind in indicateurs:
            siret = str(ind.get("siret", "")).strip()
            if not siret:
                logging.warning("sync_all : indicateur sans SIRET — ignoré.")
                continue

            pg_row = {
                pg_col: ind[py_key]
                for py_key, pg_col in mapping.items()
                if py_key in ind and ind[py_key] is not None
            }

            if not pg_row:
                logging.warning("sync_all : SIRET %s — aucune valeur à synchroniser.", siret)
                continue

            sql, vals = _build_upsert(siret, pg_row)

            try:
                cur.execute(sql, vals)
                updated += 1
            except psycopg2.Error as e:
                conn.rollback()
                logging.error("sync_all : SIRET %s — %s", siret, e)
                errors += 1
                cur = conn.cursor()

        conn.commit()

    except psycopg2.OperationalError as e:
        logging.error("sync_all : connexion PostgreSQL impossible — %s", e)
        raise
    finally:
        if conn:
            conn.close()

    logging.info("sync_all terminé : %d mis à jour, %d erreurs.", updated, errors)
    return {"updated": updated, "errors": errors}
