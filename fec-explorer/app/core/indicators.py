from collections import defaultdict


def _commence_par(compte: str, *prefixes: str) -> bool:
    return any(compte.startswith(p) for p in prefixes)


def calculate_indicators(rows: list) -> list:
    """
    Calcule les indicateurs financiers clés par SIRET à partir des lignes
    retournées par parse_multiple_fec.

    Règles de signe (convention FEC créditeur = produit) :
      - ca             : comptes 70        → solde × -1
      - charges        : comptes 6         → solde
      - produits       : comptes 7 hors 791 → solde × -1
      - tresorerie     : comptes 5         → solde
      - emprunt        : comptes 16        → solde
      - masse_salariale: comptes 64        → solde
      - assurance      : comptes 616       → solde
      - deplacement    : comptes 625       → solde
      - loyer          : comptes 613       → solde
      - cfe            : comptes 63511     → solde
      - tns            : comptes 644       → solde
      - publicite      : comptes 623       → solde
      - honoraires     : comptes 6226      → solde
      - banque         : comptes 627       → solde
      - compte_791     : comptes 791       → solde × -1
      - prestation     : "presta" si 706 présent et 707 absent
      - multitva       : "multitva" si plusieurs comptes 4457* distincts
      - resultat       : produits - charges + compte_791

    Retourne :
      [{"siret": str, "ca": float, "charges": float, "produits": float,
        "tresorerie": float, "emprunt": float, "masse_salariale": float,
        "assurance": float, "deplacement": float, "loyer": float,
        "cfe": float, "tns": float, "publicite": float, "honoraires": float,
        "banque": float, "compte_791": float,
        "prestation": str|None, "multitva": str|None,
        "resultat": float}, ...]
    """
    acc = defaultdict(lambda: {
        "ca":              0.0,
        "charges":         0.0,
        "produits":        0.0,
        "tresorerie":      0.0,
        "emprunt":         0.0,
        "masse_salariale": 0.0,
        "assurance":       0.0,
        "deplacement":     0.0,
        "loyer":           0.0,
        "cfe":             0.0,
        "tns":             0.0,
        "publicite":       0.0,
        "honoraires":      0.0,
        "banque":          0.0,
        "compte_791":      0.0,
    })

    # Indicateurs qualitatifs — ensembles de comptes rencontrés par SIRET
    comptes_706  = defaultdict(bool)   # True si au moins un compte 706
    comptes_707  = defaultdict(bool)   # True si au moins un compte 707
    comptes_4457 = defaultdict(set)    # ensemble des comptes 4457*

    for r in rows:
        siret  = r["siret"]
        compte = r["compte"]
        solde  = r["solde"]

        # ── Produits ──────────────────────────────────────────────────────────

        if _commence_par(compte, "70"):
            acc[siret]["ca"] += solde * -1

        # 791 isolé avant le bloc 7 générique
        if _commence_par(compte, "791"):
            acc[siret]["compte_791"] += solde * -1
        elif _commence_par(compte, "7"):
            acc[siret]["produits"] += solde * -1

        # Marqueurs prestation
        if _commence_par(compte, "706"):
            comptes_706[siret] = True
        if _commence_par(compte, "707"):
            comptes_707[siret] = True

        # ── Charges ───────────────────────────────────────────────────────────

        if _commence_par(compte, "6"):
            acc[siret]["charges"] += solde

            if _commence_par(compte, "64"):
                acc[siret]["masse_salariale"] += solde
                if _commence_par(compte, "644"):
                    acc[siret]["tns"] += solde

            elif _commence_par(compte, "616"):
                acc[siret]["assurance"] += solde

            elif _commence_par(compte, "625"):
                acc[siret]["deplacement"] += solde

            elif _commence_par(compte, "613"):
                acc[siret]["loyer"] += solde

            elif _commence_par(compte, "63511"):
                acc[siret]["cfe"] += solde

            elif _commence_par(compte, "623"):
                acc[siret]["publicite"] += solde

            elif _commence_par(compte, "6226"):
                acc[siret]["honoraires"] += solde

            elif _commence_par(compte, "627"):
                acc[siret]["banque"] += solde

        # ── Bilan ─────────────────────────────────────────────────────────────

        if _commence_par(compte, "5"):
            acc[siret]["tresorerie"] += solde

        if _commence_par(compte, "16"):
            acc[siret]["emprunt"] += solde

        # ── TVA multi-taux ────────────────────────────────────────────────────

        if _commence_par(compte, "4457"):
            comptes_4457[siret].add(compte)

    # ── Mise en forme finale ──────────────────────────────────────────────────
    resultat = []
    for siret, vals in sorted(acc.items()):
        c791 = vals["compte_791"]
        resultat.append({
            "siret":           siret,
            "ca":              round(vals["ca"],              2),
            "charges":         round(vals["charges"],         2),
            "produits":        round(vals["produits"],        2),
            "tresorerie":      round(vals["tresorerie"],      2),
            "emprunt":         round(vals["emprunt"],         2),
            "masse_salariale": round(vals["masse_salariale"], 2),
            "assurance":       round(vals["assurance"],       2),
            "deplacement":     round(vals["deplacement"],     2),
            "loyer":           round(vals["loyer"],           2),
            "cfe":             round(vals["cfe"],             2),
            "tns":             round(vals["tns"],             2),
            "publicite":       round(vals["publicite"],       2),
            "honoraires":      round(vals["honoraires"],      2),
            "banque":          round(vals["banque"],          2),
            "compte_791":      round(c791,                    2),
            "prestation":      "presta" if comptes_706[siret] and not comptes_707[siret] else None,
            "multitva":        "multitva" if len(comptes_4457[siret]) > 1 else None,
            "resultat":        round(vals["produits"] - vals["charges"] + c791, 2),
        })

    return resultat
