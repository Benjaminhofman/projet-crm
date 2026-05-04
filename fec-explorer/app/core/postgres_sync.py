"""
postgres_sync.py
Synchronise les indicateurs FEC calculés vers PostgreSQL (table clients).
Remplace airtable_sync.py pour la cible PostgreSQL.

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


# Correspondance clé Python (indicateurs) → colonne PostgreSQL avec suffixe _r.
# Miroir de FIELD_MAPPING dans airtable_sync.py, limité aux champs bruts FEC
# (ceux dont le nom Airtable se terminait par " R").
FIELD_MAP_R: dict = {
    "ca":             "ca_r",
    "assurance":      "assurance_r",
    "deplacement":    "deplacement_r",
    "loyer":          "loyer_r",
    "cfe":            "cfe_r",
    "publicite":      "publicite_r",
    "honoraires":     "honoraires_r",
    "banque":         "banque_r",
    "emprunt":        "emprunt_r",
    "masse_salariale":"masse_salariale_r",
    "produits":       "produits_r",
    "charges":        "charges_r",
    "tresorerie":     "tresorerie_r",
    "resultat":       "resultat_r",
}

_RE_DIGIT = re.compile(r"^\d")
_RESERVED = {"is", "order", "table", "user", "type", "end", "start", "check", "index"}


def _qi(col: str) -> str:
    """Guillemets doubles si le nom commence par un chiffre ou est un mot réservé SQL."""
    if _RE_DIGIT.match(col) or col in _RESERVED:
        return f'"{col}"'
    return col


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise EnvironmentError("Variable d'environnement DATABASE_URL non définie.")
    return url


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

    Seules les colonnes avec suffixe _r (valeurs brutes FEC) sont écrites.
    Les champs None ou absents de l'indicateur sont ignorés.

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

        for ind in indicateurs:
            siret = str(ind.get("siret", "")).strip()
            if not siret:
                logging.warning("sync_all : indicateur sans SIRET — ignoré.")
                continue

            # Colonnes _r présentes et non-None dans cet indicateur
            pg_row = {
                pg_col: ind[py_key]
                for py_key, pg_col in FIELD_MAP_R.items()
                if py_key in ind and ind[py_key] is not None
            }

            if not pg_row:
                logging.warning("sync_all : SIRET %s — aucune colonne _r à synchroniser.", siret)
                continue

            sql, vals = _build_upsert(siret, pg_row)

            try:
                cur.execute(sql, vals)
                updated += 1
            except psycopg2.Error as e:
                conn.rollback()
                logging.error("sync_all : SIRET %s — %s", siret, e)
                errors += 1
                cur = conn.cursor()  # réouvre après rollback

        conn.commit()

    except psycopg2.OperationalError as e:
        logging.error("sync_all : connexion PostgreSQL impossible — %s", e)
        raise
    finally:
        if conn:
            conn.close()

    logging.info("sync_all terminé : %d mis à jour, %d erreurs.", updated, errors)
    return {"updated": updated, "errors": errors}
