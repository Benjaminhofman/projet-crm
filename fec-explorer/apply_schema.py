"""
apply_schema.py
Exécute schema.sql sur PostgreSQL pour créer la table clients.

Usage :
    DATABASE_URL=postgresql://user:password@host:5432/dbname python apply_schema.py
"""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("Erreur : psycopg2 non installé. Lance : pip install psycopg2-binary")
    sys.exit(1)

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Erreur : variable d'environnement DATABASE_URL non définie.")
        print("Exemple : DATABASE_URL=postgresql://user:password@localhost:5432/crm python apply_schema.py")
        sys.exit(1)

    if not os.path.exists(SCHEMA_PATH):
        print(f"Erreur : fichier schema.sql introuvable à {SCHEMA_PATH}")
        sys.exit(1)

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        sql = f.read()

    conn = None
    try:
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("Table créée avec succès.")
    except psycopg2.Error as e:
        print(f"Erreur PostgreSQL : {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
