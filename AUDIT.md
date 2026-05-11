# AUDIT TECHNIQUE — CRM Collaborateurs Comptables
> Date : 11/05/2026 — Analysé par Claude Code sur la branche `main`

---

## 1. Architecture

### Forces
- **Séparation backend/frontend nette** : FastAPI Python sert du HTML statique, sans framework JS côté client — facile à déployer et à comprendre.
- **Triggers PostgreSQL centralisés** : les 11 champs calculés (age, rendement, franchise_tva, etc.) sont maintenus en base, pas dans chaque page front — logique métier en un seul endroit.
- **`decl-engine.js` partagé** : 12 pages déclaratives (liasse, IS, CA12, CVAE…) partagent un seul moteur JS. Pattern DRY bien exécuté.
- **`_safe_fields()` + regex** : double protection SQL injection sur les endpoints CRUD (regex + `information_schema`).
- **UPSERT sur SIRET** : idempotence garantie pour les imports FEC et CSV.
- **`fec_parser.py` / `indicators.py` isolés** : le parsing FEC est découplé de l'API — testable indépendamment.

### Faiblesses
- **`main.py` monolithique** : 1 897 lignes, 30+ endpoints, logique CRUD + migrations + debug + FEC tout dans un seul fichier. Aucune séparation en routeurs ou modules.
- **Pas de pool de connexions** : `psycopg2.connect()` ouvre une connexion TCP complète à Render Frankfurt à chaque requête. Timeout possible sous charge, latence ajoutée.
- **Pas d'ORM, pas de couche d'abstraction** : les requêtes SQL sont des f-strings dispersées sur 1 900 lignes — aucune réutilisabilité.
- **`schema.sql` désynchronisé** : le fichier contient 135 colonnes originales, mais la production a au moins 15 colonnes supplémentaires ajoutées via `ALTER TABLE` dans les endpoints `/api/migrate/*`. La vraie structure ne peut être connue qu'en interrogeant `information_schema`.
- **Double emplacement des fichiers HTML** : les HTML existent à la racine du projet ET dans `fec-explorer/static/`. Le script `sync_html.py` maintient la cohérence manuellement, mais le risque de divergence est permanent.
- **Dossier `frontend/` avec `node_modules`** : présent dans le repo mais non utilisé en production — charge inutile dans git.
- **`@app.on_event("startup")` déprécié** : FastAPI recommande `lifespan` depuis la v0.93.

---

## 2. Dette technique

### Code mort
| Fichier | Statut |
|---------|--------|
| `airtable.py` (racine) | Airtable supprimé, fichier inutilisé |
| `migrate_airtable.py` | Inutilisé depuis migration PostgreSQL |
| `list_airtable_fields.py` | Inutilisé |
| `app/core/airtable_sync.py` (.pyc) | Module compilé sans source visible |
| `appsauvegard1e.py` (racine) | Doublon sauvegarde de `main.py` |
| `utilisateur1.py` (racine) | Rôle inconnu, non référencé |
| `app.py` (racine) | Doublon d'application Flask/FastAPI abandonné |
| `sauvegarde/` (55 fichiers HTML) | Archives dont 22 fichiers `-Copie.html` |
| `CLIENTSAUVEGARDE1.html`, `INDEXSAUVE2.html`, etc. (racine) | Sauvegardes manuelles non nettoyées |
| `fusionfec.db` (SQLite, racine) | Base SQLite abandonnée |

### Duplications
- **Logique `calc_rendement`** : dupliquée deux fois en PL/pgSQL (fonction `calc_rendement(siret)` + fonction `update_rendement_trigger()`) — ~100 lignes identiques. En cas de changement de seuil, les deux doivent être mises à jour simultanément.
- **`/api/migrate/rendement_trigger` vs `/api/migrate/install_trigger_rendement`** : deux endpoints qui installent le trigger rendement avec des noms différents (`update_rendement` vs `trg_rendement`). Le premier crée une fonction obsolète (`trigger_calc_rendement`) qui appelle `calc_rendement()` — moins performant.
- **Connexion DB répétée** : le pattern `conn = _get_db_conn(); try: … finally: conn.close()` est répété 30+ fois sans factorisation (pas de context manager).
- **`console.log` debug en production** (`decl-engine.js` lignes 136-137) : `console.log("filterField:", ...)` émis à chaque chargement de page déclarative.

### TODO non faits (mentionnés dans CLAUDE.md)
- `/api/migrate/install_all_triggers` — endpoint de réinstallation groupée des 11 triggers (non créé)
- `/api/debug/health` — endpoint de vérification de présence des 11 triggers (non créé)

### Incohérences de schéma
- `suivi_mission_retraite` est déclaré `NUMERIC` dans `schema.sql` mais migré en `TEXT` en production via `/api/migrate`. Idem pour `juridique_exceptionnel` (BOOLEAN → TEXT).
- La colonne `dividendes` stocke un montant numérique mais est utilisée comme flag booléen pour filtrer (`dividendes > 1`) dans le calendrier fiscal.

---

## 3. Sécurité

### Critique
- **Aucune authentification** : tous les endpoints sont publics — lecture, écriture, suppression et reconfiguration de schema sont accessibles sans token ni session. L'URL de production `https://projet-crm-m0o3.onrender.com` est connue et les routes documentées dans l'OpenAPI automatique (`/docs`).
- **`/api/migrate/*` exposés en production** : ces 20+ endpoints modifient le schéma de base de données (`ALTER TABLE`, `CREATE TRIGGER`, `DROP TRIGGER`). Un acteur malveillant peut les appeler librement.
- **`/api/debug/*` exposés** : retournent le code source des fonctions PostgreSQL (`pg_get_functiondef`), la structure de la base et des données clients brutes. Fuite d'information structurelle.
- **`CORS allow_origins=["*"]`** : n'importe quel site web peut faire des requêtes cross-origin vers l'API — exploitable avec une page piégée si un collaborateur est authentifié (CSRF élargi).
- **`/api/fec/upload` — path traversal** : le `folder_path` est fourni par le client et passé directement à `os.path.isdir()` puis à `parse_multiple_fec()`. Un attaquant sur le réseau peut pointer vers des répertoires arbitraires du serveur Render.

### Majeur
- **`print()` en production** (`update_client_field`) : affiche `siret`, `field`, `value` dans les logs Render — potentiellement visible dans les dashboards de log partagés.
- **Données réelles dans le dépôt** : `Base clients-table principale.csv`, `exemples-fec/*.txt` (4 fichiers avec SIREN réels) et `libelle_naf.csv` sont commitées dans git/GitHub public.
- **OpenAPI auto-généré** : FastAPI expose `/docs` (Swagger UI) et `/redoc` en production, listant tous les endpoints avec leurs paramètres — guide d'attaque involontaire.

### Mineur
- **`_BOOL_STRS` retourne `None` silencieusement** pour une valeur non reconnue dans un champ booléen — l'erreur de saisie utilisateur est ignorée sans feedback.

---

## 4. Performance

### Requêtes et I/O backend
- **`GET /api/clients` : SELECT \*** : retourne les 135+ colonnes pour tous les clients à chaque chargement de page. Avec 50 clients × 135 colonnes, le payload JSON peut dépasser 500 Ko à chaque requête.
- **Toutes les pages front chargent la table entière** : index, déclaratif, opportunités, rendement, commercial — chacune fait un `GET /api/clients` complet. 7 pages = 7 fois le même payload.
- **Pas de pagination** : ni côté API ni côté front. À 200 clients la table principale deviendra difficile à utiliser.
- **Connexion TCP par requête** : Render PostgreSQL est en EU-Frankfurt, la création de connexion ajoute 20-80 ms de latence à chaque appel. Un pool de 3-5 connexions réduirait cela à ~0 ms.
- **`_safe_fields()` : 1 requête `information_schema` par create/update** : peut être mis en cache.
- **`/api/update-airtable` : 5 requêtes `information_schema`** à chaque appel (1 pour le type du champ + 4 pour les colonnes `suivi_mission_*`), même si les colonnes sont déjà TEXT.
- **Import CSV : COMMIT par ligne** (`/api/clients/import`) : 100 lignes = 100 commits. Un seul commit final avec rollback global serait 10x plus rapide.

### Frontend
- **Rendu DOM non virtualisé** : toutes les lignes sont insérées dans le DOM simultanément via `DocumentFragment`. À 200+ clients, le rendu devient bloquant.
- **`console.log()` en production** (decl-engine.js) : émis à chaque load de page déclarative.
- **Pas de cache navigateur** : seul `index.html` a `Cache-Control: no-cache`. Les autres fichiers statiques (HTML, JS, CSS) bénéficient du cache par défaut de Render mais sans versioning — une mise à jour peut ne pas être prise en compte.
- **Rechargement complet à chaque action** : certaines pages rechargent tous les clients après une mise à jour de checkbox au lieu de mettre à jour uniquement la ligne concernée.

---

## 5. UX / Cohérence inter-pages

### Incohérences de navigation
- **index.html** : menu déroulant avec toutes les pages — expérience complète.
- **opportunites.html, client.html, rendement.html** : simple lien "⬅ Retour" vers index — pas de navigation vers les autres sections.
- **Résultat** : impossible de passer de `rendement.html` à `missions.html` sans repasser par l'index.

### Incohérences de style
- **CSS entièrement inline dans chaque HTML** : `index.html`, `client.html`, `opportunites.html` ont chacun plusieurs centaines de lignes de CSS dupliquées (`.header`, `table`, `th`, `tr:hover`, `.btn`…).
- **`decl-shared.css`** existe mais n'est partagé que par les pages déclaratives — les autres pages ignorent ce fichier.
- **`gestion-clients.html`** utilise `box-sizing: border-box` sur `*` (moderne) ; `opportunites.html` n'en a pas — comportements de layout différents.
- **`client.html`** : balise `<html>` sans `lang="fr"` — les autres pages l'ont.
- **`opportunites.html`** : pas de `<meta name="viewport">` — les autres pages l'ont.
- **Titre navigateur** : "CRM Clients" (index), "Détail client" (client), "Gestion Clients" (gestion-clients) — pas de préfixe cohérent type "CRM — …".

### Incohérences de feedback utilisateur
- **Pages déclaratives** : skeleton loader pendant le chargement — bonne expérience.
- **index.html** : skeleton loader présent.
- **opportunites.html, missions.html** : pas de skeleton loader — affichage vide puis pop brutal.
- **Feedback modification** : déclaratif colore la cellule (orange → vert/rouge). Index n'a pas ce feedback visuel pour les clics de filtres.

### Incohérences fonctionnelles
- **Filtre "rendement" disponible sur index.html** mais la page `rendement.html` ne permet pas de filtrer par collaborateur ou structure.
- **Tri** : index.html a tri côté client (rendement, CA, résultat). Les pages déclaratives n'ont pas de tri.
- **Export CSV** : disponible sur index et les pages déclaratives. Absent sur `opportunites.html` et `rendement.html`.
- **Lien depuis table → fiche client** : les pages déclaratives (via decl-engine.js) ont le lien. `opportunites.html` recharge la page via JS mais sans lien `<a href>` direct — clic droit/ouvrir dans un nouvel onglet impossible.

---

## 6. Top 10 améliorations — Impact × Effort

| # | Amélioration | Impact | Effort | Priorité |
|---|-------------|--------|--------|----------|
| **1** | **Authentification minimale** — Ajouter un token Bearer (variable d'environnement) vérifié par un middleware FastAPI sur tous les endpoints non-statiques. Bloque la lecture/modification de données clients et la réexécution des migrations en production. | ★★★★★ | Moyen (1 jour) | 🔴 Critique |
| **2** | **Pool de connexions PostgreSQL** — Remplacer `psycopg2.connect()` par `psycopg2.pool.ThreadedConnectionPool(3, 10)` initialisé au démarrage. Élimine 20-80 ms de latence par requête et les risques de timeout sous charge. | ★★★★★ | Faible (2h) | 🔴 Critique |
| **3** | **Restreindre `/api/migrate/*` et `/api/debug/*`** — Ajouter un header `X-Admin-Key` requis (ou désactiver en production via variable d'environnement). Ces routes modifient le schéma ou exposent des métadonnées sensibles. | ★★★★☆ | Faible (2h) | 🔴 Critique |
| **4** | **Pagination API + front** — Ajouter `GET /api/clients?limit=50&offset=0` côté backend. Côté front, un simple système "page suivante / précédente" suffit. Réduit le payload de 500 Ko à ~30 Ko et accélère les temps de chargement. | ★★★★☆ | Moyen (1 jour) | 🟠 Majeur |
| **5** | **Nettoyer le dépôt** — Supprimer `airtable.py`, `migrate_airtable.py`, `list_airtable_fields.py`, `appsauvegard1e.py`, `utilisateur1.py`, `app.py`, `fusionfec.db`, `sauvegarde/`, et les fichiers sauvegarde racine. Déplacer les exemples FEC et CSV hors du repo ou dans un `.gitignore`. | ★★★☆☆ | Faible (1h) | 🟠 Majeur |
| **6** | **Navigation cohérente** — Extraire le menu déroulant de `index.html` dans un composant HTML inclus (ou reproduit) sur toutes les pages. Toutes les pages doivent avoir accès au même menu de navigation. | ★★★★☆ | Faible (2h) | 🟠 Majeur |
| **7** | **Éclater `main.py` en modules FastAPI** — Créer `app/routes/clients.py`, `app/routes/migrate.py`, `app/routes/debug.py`, `app/routes/fec.py`. Utiliser `APIRouter` et les assembler dans `main.py`. Maintenabilité drastiquement améliorée. | ★★★☆☆ | Moyen (1 jour) | 🟡 Important |
| **8** | **Dédupliquer la logique rendement** — Supprimer `calc_rendement(siret)` et `rendement_trigger` (l'ancienne version). Garder uniquement `update_rendement_trigger()` qui travaille sur `NEW.*`. Créer un endpoint de recalcul forcé qui fait `UPDATE clients SET honoraires_cpta = honoraires_cpta` par batch. | ★★★☆☆ | Moyen (3h) | 🟡 Important |
| **9** | **CSS partagé** — Extraire les styles communs (header, table, boutons, skeleton) dans `decl-shared.css` et l'inclure sur toutes les pages. Éliminer ~60% des lignes CSS dupliquées. Garantit une cohérence visuelle en un seul point de modification. | ★★★☆☆ | Moyen (4h) | 🟡 Important |
| **10** | **Import CSV en batch** — Dans `/api/clients/import`, accumuler tous les UPSERTs et faire un seul `conn.commit()` en fin de boucle (avec rollback global si une ligne échoue). Ajouter un mode `ignore_errors=true` pour les imports tolérants. Gain de performance ×10 à 100 lignes. | ★★★☆☆ | Faible (1h) | 🟡 Important |

---

*Audit réalisé sur : `main.py` (1 897 lignes), `schema.sql`, `gestion-clients.html` (2 014 lignes), `index.html`, `decl-engine.js`, `opportunites.html`, `client.html`, `fec_parser.py`, `indicators.py`, `postgres_sync.py` et l'arborescence complète du projet.*
