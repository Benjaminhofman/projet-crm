import csv
import logging
import os
import re
import sys

# Pattern réglementaire DGFiP : 9 chiffres (SIREN) + FEC + 8 chiffres (date) + .txt
_PATTERN_FEC = re.compile(r"^(\d{9})FEC\d{8}\.txt$")


def parse_fec_file(file_path: str) -> dict:
    """
    Lit un fichier FEC (tabulé, ISO-8859-1) et retourne la balance par compte.

    Colonnes attendues (index 0-based) :
      4  → numéro de compte
      11 → montant débit
      12 → montant crédit

    Retourne :
      { compte: {"debit": float, "credit": float, "solde": float} }
    """
    soldes = {}

    with open(file_path, "r", encoding="ISO-8859-1") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # ignore l'en-tête

        for row_num, row in enumerate(reader, start=2):
            try:
                if len(row) < 13:
                    raise IndexError(
                        f"Ligne {row_num} : {len(row)} colonnes trouvées, 13 attendues"
                    )

                compte = row[4].strip()
                debit  = float(row[11].replace(",", ".")) if row[11].strip() else 0.0
                credit = float(row[12].replace(",", ".")) if row[12].strip() else 0.0

                if compte not in soldes:
                    soldes[compte] = {"debit": 0.0, "credit": 0.0, "solde": 0.0}

                soldes[compte]["debit"]  += debit
                soldes[compte]["credit"] += credit

            except IndexError as e:
                logging.warning("parse_fec_file – %s", e)
            except ValueError as e:
                logging.warning("parse_fec_file – conversion ligne %d : %s", row_num, e)

    # calcul du solde une seule fois après l'agrégation
    for compte, vals in soldes.items():
        vals["solde"] = round(vals["debit"] - vals["credit"], 2)
        vals["debit"]  = round(vals["debit"],  2)
        vals["credit"] = round(vals["credit"], 2)

    return soldes


def parse_multiple_fec(folder_path: str) -> list:
    """
    Scanne un dossier, parse chaque fichier FEC valide et retourne une liste
    de lignes de balance enrichies du SIRET.

    Retourne :
      [{"siret": str, "compte": str, "debit": float, "credit": float, "solde": float}, ...]
    """
    rows = []

    try:
        fichiers = os.listdir(folder_path)
    except OSError as e:
        logging.error("parse_multiple_fec – impossible de lire le dossier : %s", e)
        return rows

    for nom in sorted(fichiers):
        match = _PATTERN_FEC.match(nom)
        if not match:
            continue

        siret = match.group(1)
        chemin = os.path.join(folder_path, nom)

        try:
            balance = parse_fec_file(chemin)
        except Exception as e:
            logging.error("parse_multiple_fec – erreur sur %s : %s", nom, e)
            continue

        for compte, vals in sorted(balance.items()):
            rows.append({
                "siret":   siret,
                "compte":  compte,
                "debit":   vals["debit"],
                "credit":  vals["credit"],
                "solde":   vals["solde"],
            })

    return rows


# ---------------------------------------------------------------------------
# Utilitaire d'affichage commun
# ---------------------------------------------------------------------------

def _fmt(montant: float) -> str:
    return f"{montant:,.2f}".replace(",", " ")


def _affiche_balance_fichier(balance: dict) -> None:
    col = "{:<12} {:>18} {:>18} {:>18}"
    sep = "-" * 70
    print(sep)
    print(col.format("Compte", "Débit", "Crédit", "Solde"))
    print(sep)
    for compte, vals in sorted(balance.items()):
        print(col.format(compte, _fmt(vals["debit"]), _fmt(vals["credit"]), _fmt(vals["solde"])))
    print(sep)
    print(f"Total : {len(balance)} compte(s)")


def _affiche_balance_dossier(rows: list) -> None:
    col = "{:<14} {:<12} {:>18} {:>18} {:>18}"
    sep = "-" * 86
    print(sep)
    print(col.format("SIRET", "Compte", "Débit", "Crédit", "Solde"))
    print(sep)

    siret_courant = None
    nb_siret = 0
    for r in rows:
        if r["siret"] != siret_courant:
            if siret_courant is not None:
                print()  # ligne vide entre deux entités
            siret_courant = r["siret"]
            nb_siret += 1
        print(col.format(r["siret"], r["compte"], _fmt(r["debit"]), _fmt(r["credit"]), _fmt(r["solde"])))

    print(sep)
    print(f"Total : {len(rows)} ligne(s) — {nb_siret} entité(s)")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python fec_parser.py <fichier_fec | dossier_fec>")
        sys.exit(1)

    cible = sys.argv[1]

    if os.path.isdir(cible):
        lignes = parse_multiple_fec(cible)
        if not lignes:
            print("Aucun fichier FEC valide trouvé dans le dossier.")
            sys.exit(0)
        _affiche_balance_dossier(lignes)
    else:
        balance = parse_fec_file(cible)
        _affiche_balance_fichier(balance)
