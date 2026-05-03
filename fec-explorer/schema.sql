-- Généré par check_fields.py — corrigé manuellement
-- 128 colonnes : champs Airtable (encodage normalisé) + indicateurs FEC calculés

CREATE TABLE IF NOT EXISTS clients (

    -- ── Identifiant ──────────────────────────────────────────────────────────
    siret                              TEXT         PRIMARY KEY NOT NULL,

    -- ── Informations client ───────────────────────────────────────────────────
    nom_client                         TEXT,
    contact                            TEXT,
    e_mail                             TEXT,
    tel                                TEXT,
    structure                          TEXT,
    collaborateur                       TEXT,
    assistant                          TEXT,
    code_client                        TEXT,
    annee                              TEXT,        -- "année" (encodage corrigé)
    date_entree                        DATE,        -- "date entrée"
    date_de_cloture                    DATE,
    date_situation                     DATE,
    date_tbb                           DATE,
    mode_d_entree                      TEXT,        -- "mode d'entrée"
    eval                               TEXT,
    commentaires                       TEXT,
    previsionnel                       TEXT,
    achat_revente                      TEXT,
    activite_r                         TEXT,        -- activité (texte libre)
    code_naf_r                         TEXT,        -- code NAF (texte)
    code_impot_gouv                    TEXT,
    code_urssaf                        TEXT,
    prel_cfe                           TEXT,
    -- ── Missions & suivi ─────────────────────────────────────────────────────
    patrimoniale                       TEXT,
    placement                          TEXT,
    prevoyance                         TEXT,
    prevoyance_s                       TEXT,
    suivi_mission_patrimoniale         TEXT,
    suivi_mission_placement            TEXT,
    suivi_mission_prevoyance           TEXT,
    suivi_mission_retraite             NUMERIC,

    -- ── Indicateurs booléens / obligations fiscales ───────────────────────────
    liasse                             BOOLEAN,
    edi_liasse                         BOOLEAN,
    "2067_liasse"                      BOOLEAN,     -- déclaration 2067
    "2069_rci_liasse"                  BOOLEAN,     -- déclaration 2069 RCI
    ca12                               BOOLEAN,
    "is"                               BOOLEAN,     -- IS (mot réservé SQL → guillemets)
    impot_sur_le_revenu                BOOLEAN,
    cvae                               BOOLEAN,
    tvs                                BOOLEAN,
    situation                          BOOLEAN,
    tbb                                BOOLEAN,
    realisation_situ                   BOOLEAN,
    realisation_tbb                    BOOLEAN,
    juridique                          BOOLEAN,
    juridique_exceptionnel             BOOLEAN,
    prepa_pv_ag                        BOOLEAN,
    exo_entre_nouvelle                 BOOLEAN,
    cotisation_fonciere_entreprise     BOOLEAN,     -- "Cotisation foncière entreprise"
    dividendes_2561                    BOOLEAN,
    dividendes_2777                    BOOLEAN,

    -- ── Échéances fiscales (montants) ─────────────────────────────────────────
    mai_is                             NUMERIC,
    juin_is                            NUMERIC,
    mars_is                            NUMERIC,
    septembre_is                       NUMERIC,
    decembre_is                        NUMERIC,     -- "décembre IS"
    mai_ca12                           NUMERIC,
    juillet_ca12                       NUMERIC,
    decembre_ca12                      NUMERIC,
    mai_cvae                           NUMERIC,
    mai_ir                             NUMERIC,
    janvier_tvs                        NUMERIC,
    mai_tvs                            NUMERIC,
    date_2777_dividendes               DATE,
    anniversaire                       DATE,
    dividendes                         NUMERIC,

    -- ── Honoraires & temps ────────────────────────────────────────────────────
    honoraires_cpta                    NUMERIC,
    temps_passe                        NUMERIC,     -- "temps passé"

    -- ── Compte de résultat (FEC → Airtable avec suffixe R) ────────────────────
    ca_r                               NUMERIC,     -- ca
    charge_r                           NUMERIC,     -- charges totales
    produit_r                          NUMERIC,     -- produits totaux
    m_salariale_r                      NUMERIC,     -- masse salariale
    assurance_r                        NUMERIC,
    deplacement_r                      NUMERIC,
    loyer_r                            NUMERIC,
    cfe_r                              NUMERIC,
    publicite_r                        NUMERIC,
    honoraires_r                       NUMERIC,
    banque_r                           NUMERIC,
    emprunt_r                          NUMERIC,
    tresorerie_r                       NUMERIC,
    resultat_r                         NUMERIC,

    -- ── Charges détaillées ────────────────────────────────────────────────────
    achats_marchandises                NUMERIC,
    achats_matieres                    NUMERIC,
    achats_non_stockes                 NUMERIC,
    sous_traitance                     NUMERIC,
    entretien_reparation               NUMERIC,
    personnel_exterieur                NUMERIC,
    frais_telecom                      NUMERIC,
    impots_taxes                       NUMERIC,
    dotations_amortissements           NUMERIC,
    impot_societes                     NUMERIC,
    charges_financieres                NUMERIC,
    charges_exceptionnelles            NUMERIC,
    tns                                NUMERIC,

    -- ── Produits détaillés ────────────────────────────────────────────────────
    produits_financiers                NUMERIC,
    produits_exceptionnels             NUMERIC,
    compte_791                         NUMERIC,

    -- ── Bilan actif ───────────────────────────────────────────────────────────
    placements                         NUMERIC,
    clients                            NUMERIC,
    stocks                             NUMERIC,
    materiel_transport                 NUMERIC,
    materiel_informatique              NUMERIC,
    mobilier                           NUMERIC,
    fond_commerce                      NUMERIC,
    constructions                      NUMERIC,

    -- ── Bilan passif ──────────────────────────────────────────────────────────
    fournisseurs                       NUMERIC,
    capital                            NUMERIC,
    reserves                           NUMERIC,
    report_a_nouveau                   NUMERIC,
    compte_exploitant                  NUMERIC,
    compte_courant_associe             NUMERIC,

    -- ── Soldes intermédiaires de gestion ──────────────────────────────────────
    marge_brute                        NUMERIC,
    valeur_ajoutee                     NUMERIC,
    ebe                                NUMERIC,
    rex                                NUMERIC,
    resultat_financier                 NUMERIC,
    resultat_exceptionnel              NUMERIC,
    caf                                NUMERIC,
    variation_stocks                   NUMERIC,

    -- ── Ratios financiers ─────────────────────────────────────────────────────
    productivite                       NUMERIC,
    capacite_remboursement             NUMERIC,
    liquidite_generale                 NUMERIC,
    delai_client                       NUMERIC,
    ratio_endettement                  NUMERIC,

    -- ── Indicateurs FEC calculés (absents d'Airtable) ────────────────────────
    prestation                         TEXT,
    multitva                           TEXT

);
