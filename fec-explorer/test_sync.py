import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.fec_parser    import parse_multiple_fec
from app.core.indicators    import calculate_indicators
from app.core.postgres_sync import sync_all

dossier = os.path.join(os.path.dirname(__file__), "exemples-fec")

print(f"Parsing : {os.path.abspath(dossier)}")
rows        = parse_multiple_fec(dossier)
indicateurs = calculate_indicators(rows)
print(f"{len(indicateurs)} indicateur(s) calculé(s)\n")

if indicateurs:
    print("Clés du premier indicateur :")
    for cle in indicateurs[0].keys():
        print(f"  {cle}")
    print()

print("Synchronisation PostgreSQL...")
res = sync_all(indicateurs)

print(f"\n{res['updated']} client(s) mis à jour, {res['errors']} erreur(s)")
