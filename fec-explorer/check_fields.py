"""
check_fields.py
1. Compare colonnes PostgreSQL (table clients) vs schéma indicateurs FEC
2. Génère schema.sql — CREATE TABLE clients — avec toutes les colonnes attendues

Usage :
    DATABASE_URL=postgresql://user:pass@host:5432/db python check_fields.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

try:
    import psycopg2
except ImportError:
    print("Erreur : psycopg2 non installé. Lance : pip install psycopg2-binary")
    sys.exit(1)

from app.core.postgres_sync import FIELD_MAP_R

# ── Schéma FEC attendu (toutes les clés de calculate_indicators) ───────────────
SCHEMA_FEC = {
    "siret",
    "ca", "charges", "produits", "tresorerie", "emprunt", "masse_salariale",
    "assurance", "deplacement", "loyer", "cfe", "tns", "publicite",
    "honoraires", "banque",
    "compte_791", "produits_financiers", "produits_exceptionnels",
    "placements", "capital", "reserves", "report_a_nouveau",
    "compte_exploitant", "compte_courant_associe",
    "charges_financieres", "charges_exceptionnelles",
    "achats_non_stockes", "sous_traitance", "entretien_reparation",
    "personnel_exterieur", "frais_telecom", "impots_taxes",
    "dotations_amortissements", "impot_societes",
    "materiel_transport", "fond_commerce", "constructions",
    "materiel_informatique", "mobilier",
    "stocks", "clients", "fournisseurs",
    "achats_marchandises", "variation_stocks", "achats_matieres",
    "prestation", "multitva",
    "resultat", "marge_brute", "valeur_ajoutee", "ebe", "rex",
    "resultat_financier", "resultat_exceptionnel", "caf",
    "productivite", "capacite_remboursement", "liquidite_generale",
    "delai_client", "ratio_endettement",
}

# Colonnes brutes FEC (suffixe _r)
SCHEMA_R = set(FIELD_MAP_R.values())

# Ensemble complet des colonnes attendues
ALL_EXPECTED = SCHEMA_FEC | SCHEMA_R

# Colonnes dont le type SQL est TEXT (les autres sont NUMERIC)
TEXT_FIELDS = {"siret", "prestation", "multitva"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sql_type(col: str) -> str:
    if col in TEXT_FIELDS:
        return "TEXT"
    return "NUMERIC"


# ── PostgreSQL ────────────────────────────────────────────────────────────────

def fetch_postgres_columns() -> set:
    """Retourne les colonnes existantes dans la table clients via information_schema."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Erreur : variable d'environnement DATABASE_URL non définie.")
        sys.exit(1)

    try:
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'clients' ORDER BY column_name"
            )
            cols = {row[0] for row in cur.fetchall()}
        conn.close()
        return cols
    except psycopg2.Error as e:
        print(f"Erreur PostgreSQL : {e}")
        sys.exit(1)


# ── Génération SQL ────────────────────────────────────────────────────────────

def generate_sql(expected: set) -> str:
    """Construit le DDL CREATE TABLE clients à partir des colonnes attendues."""
    lines = []
    seen  = set()

    def add_col(col: str, sql_t: str, comment: str = ""):
        if col in seen:
            return
        seen.add(col)
        suffix = f"  -- {comment}" if comment else ""
        lines.append(f"    {col:<46}{sql_t}{suffix}")

    add_col("siret", "TEXT  PRIMARY KEY NOT NULL", "identifiant SIRET")

    for col in sorted(expected - {"siret"}):
        add_col(col, _sql_type(col))

    body = ",\n".join(lines)
    nb   = len(seen)
    return (
        "-- Généré automatiquement par check_fields.py\n"
        f"-- {nb} colonnes : indicateurs FEC calculés + valeurs brutes _r\n\n"
        "CREATE TABLE IF NOT EXISTS clients (\n"
        f"{body}\n"
        ");\n"
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Récupération des colonnes PostgreSQL (table clients)...\n")
    pg_cols = fetch_postgres_columns()

    extra   = sorted(pg_cols - ALL_EXPECTED - {"siret"})
    missing = sorted(ALL_EXPECTED - pg_cols)

    print(f"Colonnes PostgreSQL trouvées  : {len(pg_cols)}")
    print(f"Colonnes attendues (schéma)   : {len(ALL_EXPECTED)}\n")

    print("=" * 58)
    print(f"Dans PostgreSQL mais hors schéma ({len(extra)}) :")
    print("=" * 58)
    for n in (extra or ["(aucun)"]):
        print(f"  + {n}")

    print()
    print("=" * 58)
    print(f"Attendues mais absentes de PostgreSQL ({len(missing)}) :")
    print("=" * 58)
    for n in (missing or ["(aucun)"]):
        print(f"  - {n}")

    sql      = generate_sql(ALL_EXPECTED)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(sql)

    print(f"\nschema.sql sauvegardé : {len(ALL_EXPECTED) + 1} colonnes")
    print(f"  {out_path}")


if __name__ == "__main__":
    main()
