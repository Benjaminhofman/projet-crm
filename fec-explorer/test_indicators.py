"""
Test manuel de la chaîne parse_multiple_fec → calculate_indicators.
Usage : python test_indicators.py [dossier_fec]
        (par défaut : exemples-fec/)
"""
import os
import sys

# Résolution des imports depuis la racine de fec-explorer
sys.path.insert(0, os.path.dirname(__file__))

from app.core.fec_parser import parse_multiple_fec
from app.core.indicators import calculate_indicators


def _fmt(val) -> str:
    """Formate un float avec séparateur de milliers et 2 décimales."""
    if val is None:
        return "-"
    return f"{val:>16,.2f}".replace(",", " ")


def affiche_tableau(indicateurs: list) -> None:
    col   = "{:<14} {:>16} {:>16} {:>16} {:>16}"
    sep   = "-" * 82

    print(sep)
    print(col.format("SIRET", "CA", "Charges", "Résultat", "Trésorerie"))
    print(sep)

    for ind in indicateurs:
        print(col.format(
            ind["siret"],
            _fmt(ind["ca"]),
            _fmt(ind["charges"]),
            _fmt(ind["resultat"]),
            _fmt(ind["tresorerie"]),
        ))

    print(sep)
    print(f"  {len(indicateurs)} entité(s) analysée(s)")


def affiche_detail(ind: dict) -> None:
    """Affiche tous les postes d'un indicateur pour inspection."""
    postes = [
        ("CA",              "ca"),
        ("Charges totales", "charges"),
        ("  Masse salariale","masse_salariale"),
        ("  TNS",           "tns"),
        ("  Loyer",         "loyer"),
        ("  Assurance",     "assurance"),
        ("  Déplacement",   "deplacement"),
        ("  CFE",           "cfe"),
        ("  Publicité",     "publicite"),
        ("  Honoraires",    "honoraires"),
        ("  Banque",        "banque"),
        ("Produits",        "produits"),
        ("  Reprises 791",  "compte_791"),
        ("Trésorerie",      "tresorerie"),
        ("Emprunt",         "emprunt"),
        ("Résultat",        "resultat"),
    ]
    print(f"\n  -- Détail SIRET {ind['siret']} --")
    for label, cle in postes:
        print(f"  {label:<22} {_fmt(ind[cle])}")
    flags = [v for v in (ind.get("prestation"), ind.get("multitva")) if v]
    if flags:
        print(f"  Flags : {', '.join(flags)}")


if __name__ == "__main__":
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "exemples-fec")

    if not os.path.isdir(dossier):
        print(f"Dossier introuvable : {dossier}")
        sys.exit(1)

    print(f"\nParsing du dossier : {os.path.abspath(dossier)}\n")

    rows        = parse_multiple_fec(dossier)
    indicateurs = calculate_indicators(rows)

    if not indicateurs:
        print("Aucun fichier FEC valide trouvé.")
        sys.exit(0)

    affiche_tableau(indicateurs)

    # Détail complet pour chaque entité
    for ind in indicateurs:
        affiche_detail(ind)

    print()
