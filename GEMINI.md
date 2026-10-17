# Platform Samples Dashboards — Mémoire & Directives Projet

Ce document sert de référence technique et de mémoire pérenne pour l'architecture, les conventions et le fonctionnement de la plateforme.

---

## 1. Vue d'Ensemble & Objectifs

La plateforme **Platform Samples Dashboards** est un benchmark technique et métier de restitution décisionnelle comparant **Grafana**, **Metabase** et **Power BI** sur la gestion d'un parc informatique d'entreprise (*Parc & Assets*).

Elle implémente une **Modern Data Stack (MDS)** conteneurisée :
1. **Génération de données brutes** : `data-engine/generator` (Python, SQLAlchemy, Faker).
2. **Entrepôt de données** : PostgreSQL 15 (base `parc_assets`).
3. **Modélisation & Transformations** : `data-engine/dbt-parc-assets` (dbt-core, dbt-postgres).
4. **Restitutions BI** :
   - **Grafana 10.4.2** (port 3000) : Supervision opérationnelle, métriques matérielles et alertes.
   - **Metabase v0.49.7** (port 3001) : Exploration libre, requêtes self-service et reporting.
   - **Power BI / Fabric** : Modélisation sémantique as Code (TMDL).
5. **Portail Web Vitrine** : `site-vitrine` (port 4321, Astro, Tailwind CSS, React).

---

## 2. Règles d'Architecture & Schémas PostgreSQL

### 2.1. Schémas de Données
- `raw` : Schéma hébergeant les tables brutes générées par `generate.py` (`dim_users`, `dim_hardware_models`, `fact_assets`, `fact_software_installations`).
- `staging` : Schéma hébergeant les vues nettoyées dbt (`stg_assets`, `stg_hardware_models`, `stg_software_installations`, `stg_users`).
- `marts` : Schéma hébergeant les tables/vues décisionnelles dbt :
  - `mart_assets_overview` : Vue consolidée des équipements, utilisateurs, affectations, prix et garanties.
  - `mart_software_licenses` : Vue consolidée des logiciels, postes équipés et coûts mensuels/annuels.

### 2.2. Règle Critique dbt (Nommage des Schémas)
> [!IMPORTANT]
> Par défaut, dbt Postgres préfixe les schémas personnalisés avec le schéma cible de connexion (`public_marts`).
> La macro **`data-engine/dbt-parc-assets/macros/generate_schema_name.sql`** surcharge ce comportement pour garantir la création directe dans `marts` et `staging`.
> **Ne jamais supprimer cette macro**, sous peine de casser toutes les requêtes Grafana et Metabase.

---

## 3. Configuration & Restitution des Outils BI

### 3.1. Grafana
- **Fichier de configuration** : `infrastructure/grafana-provisioning/dashboards/parc-assets.json`.
- **Organisation en 3 Thématiques (Rows repliables)** :
  1. `🖥️ Thématique 1 : Parc & Assets (Matériel & Postes)` : Total actifs, postes en service, réserve, hors garantie, graphiques de répartition par statut, catégorie et constructeur.
  2. `💳 Thématique 2 : Licences & Coûts (FinOps & Abonnements)` : Coûts mensuels et annuels, volume d'installations, budget par logiciel, valorisation par pôle et tableau complet des licences.
  3. `🛡️ Thématique 3 : Supervision SI (Santé, Disponibilité & Obsolescence)` : Jauge de disponibilité %, pannes/réparations, obsolescence critique et cartographie par site/ville.
- **Variables dynamiques en en-tête** : `$department` et `$status`.
- **Accès iframe** : `http://localhost:3000/d/parc-assets?kiosk&theme=light` (authentification anonyme activée).

### 3.2. Metabase
- **Script d'initialisation** : `infrastructure/metabase-init/init_metabase.py`.
- **Persistance** : Volume Docker `metabase_data` attaché à `metabase-db`.
- **Automatisations au démarrage** :
  - Détection fiable du setup (`has-user-setup`).
  - Enregistrement de la base PostgreSQL `Parc Assets` (moteur postgres, host `postgres`, db `parc_assets`).
  - Synchronisation des métadonnées (schémas `marts`, `staging`, `raw`).
  - Activation globale du partage public (`enable-public-sharing`).
  - Provisioning de 4 cartes analytiques et du dashboard d'accueil *"Parc & Assets — Vue d'ensemble SI"*.
  - Génération d'un lien public (`/public/dashboard/:uuid`) persisté dans `site-vitrine/src/metabase_config.json`.
- **Intégration vitrine** : L'iframe charge le dashboard public sans authentification requise.

---

## 4. Identifiants & Ports d'Accès

| Service | Port Externe | Identifiants par Défaut | Usage |
|---|---|---|---|
| **PostgreSQL** | `5432` | User: `parc` / Pwd: `parc` / DB: `parc_assets` | Entrepôt de données MDS |
| **Grafana** | `3000` | User: `admin` / Pwd: `admin` | Dashboards opérationnels & kiosk |
| **Metabase** | `3001` | User: `admin@example.com` / Pwd: `Admin-Passw0rd!` | Self-Service BI & Dashboard public |
| **Site Vitrine** | `4321` | Accès libre | Portail d'intégration Astro |

---

## 5. Commandes de Routine

```bash
# Démarrage complet de la stack Docker
cd infrastructure
docker compose up -d --build

# Exécution des transformations et tests dbt
docker compose run --rm dbt-runner

# Réinitialisation / reconfiguration Metabase
docker compose run --rm metabase-init

# Lancement local du site vitrine Astro
cd site-vitrine
npm run dev
```

