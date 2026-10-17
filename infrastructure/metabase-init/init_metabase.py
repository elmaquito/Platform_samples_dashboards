"""Configure Metabase through its API: admin setup, register Parc & Assets, and provision public dashboard."""
import json
import os
import time
import urllib.request
import urllib.error

MB = os.getenv("MB_URL", "http://localhost:3001")
EMAIL = os.getenv("MB_ADMIN_EMAIL", "admin@example.com")
PASSWORD = os.getenv("MB_ADMIN_PASSWORD", "Admin-Passw0rd!")
DB = {
    "host": os.getenv("PGHOST", "postgres"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "parc_assets"),
    "user": os.getenv("PGUSER", "parc"),
    "password": os.getenv("PGPASSWORD", "parc"),
    "ssl": False,
}


def call(path, payload=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Metabase-Session"] = token
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(MB + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def wait_ready():
    print(f"Waiting for Metabase at {MB}...")
    for i in range(60):
        try:
            if call("/api/health").get("status") == "ok":
                print("Metabase is healthy and ready.")
                return
        except Exception:
            pass
        time.sleep(3)
    raise SystemExit("Metabase not ready after 3 minutes")


def get_token():
    props = call("/api/session/properties")
    has_user = props.get("has-user-setup", False)
    
    if not has_user:
        setup_token = props.get("setup-token")
        if not setup_token:
            raise RuntimeError("Metabase has no user and no setup token found.")
        print("Initial setup: creating admin user...")
        res = call("/api/setup", {
            "token": setup_token,
            "user": {
                "email": EMAIL,
                "password": PASSWORD,
                "first_name": "Admin",
                "last_name": "BI",
            },
            "prefs": {
                "site_name": "Parc & Assets",
                "allow_tracking": False,
            },
        }, method="POST")
        token = res.get("id")
        print("Admin user created successfully.")
        return token

    # Already setup: authenticate
    print("Metabase already set up. Logging in...")
    try:
        res = call("/api/session", {"username": EMAIL, "password": PASSWORD}, method="POST")
        return res["id"]
    except urllib.error.HTTPError as e:
        print(f"Standard admin login failed ({e.code}). Checking fallback session...")
        # Check if environment provides an explicit session or token
        fallback_session = os.getenv("MB_SESSION_TOKEN")
        if fallback_session:
            return fallback_session
        raise


def register_database(token):
    existing = call("/api/database", token=token)
    dbs = existing["data"] if isinstance(existing, dict) else existing
    for d in dbs:
        if d.get("name") == "Parc Assets":
            print(f"Database 'Parc Assets' already registered (id={d['id']}).")
            return d["id"]

    print("Registering PostgreSQL database 'Parc Assets'...")
    res = call("/api/database", {
        "name": "Parc Assets",
        "engine": "postgres",
        "details": DB,
        "is_full_sync": True,
    }, token=token, method="POST")
    db_id = res["id"]
    print(f"Database 'Parc Assets' registered successfully with ID: {db_id}")
    return db_id


def wait_metadata_sync(db_id, token):
    print("Waiting for tables synchronization in Metabase...")
    for _ in range(30):
        try:
            meta = call(f"/api/database/{db_id}/metadata", token=token)
            tables = meta.get("tables", [])
            marts_tables = [t for t in tables if t.get("schema") == "marts"]
            if len(marts_tables) >= 2:
                print(f"Metadata sync complete: {len(tables)} tables indexed (including marts).")
                return
        except Exception:
            pass
        time.sleep(2)
    print("Metadata sync timeout (proceeding anyway).")


def enable_public_sharing(token):
    try:
        call("/api/setting/enable-public-sharing", {"value": True}, token=token, method="PUT")
        print("Public sharing enabled in Metabase settings.")
    except Exception as e:
        print(f"Notice: public sharing setting update returned: {e}")


def provision_thematic_dashboard(db_id, token):
    existing_dashboards = call("/api/dashboard", token=token)
    d_list = existing_dashboards if isinstance(existing_dashboards, list) else existing_dashboards.get("data", [])
    for d in d_list:
        if d.get("name") == "Parc & Assets — Vue d'ensemble SI":
            print(f"Dashboard already exists (id={d['id']}).")
            dash_id = d["id"]
            link_info = call(f"/api/dashboard/{dash_id}/public_link", {}, token=token, method="POST")
            uuid = link_info.get("uuid")
            return dash_id, uuid

    print("Creating thematic cards for the dashboard...")
    cards = [
        {
            "name": "Total Actifs Informatiques",
            "description": "Thématique 1 : Volume total des équipements inventoriés",
            "dataset_query": {
                "type": "native",
                "native": {"query": "SELECT count(*) AS total_actifs FROM marts.mart_assets_overview"},
                "database": db_id,
            },
            "display": "scalar",
            "visualization_settings": {},
        },
        {
            "name": "Répartition par Statut",
            "description": "Thématique 1 : Proportion des postes en service, stock, réparation et retirés",
            "dataset_query": {
                "type": "native",
                "native": {"query": "SELECT status AS \"Statut\", count(*) AS \"Quantité\" FROM marts.mart_assets_overview GROUP BY status ORDER BY 2 DESC"},
                "database": db_id,
            },
            "display": "pie",
            "visualization_settings": {},
        },
        {
            "name": "Budget Annuel des Licences Logicielles",
            "description": "Thématique 2 : Coûts mensuels et annuels par solution logicielle",
            "dataset_query": {
                "type": "native",
                "native": {"query": "SELECT software_name AS \"Logiciel\", installations AS \"Installations\", monthly_cost AS \"Coût/mois (€)\", yearly_cost AS \"Coût/an (€)\" FROM marts.mart_software_licenses ORDER BY yearly_cost DESC"},
                "database": db_id,
            },
            "display": "table",
            "visualization_settings": {},
        },
        {
            "name": "Supervision : Équipements Hors Garantie en Service",
            "description": "Thématique 3 : Matériel actif nécessitant un renouvellement",
            "dataset_query": {
                "type": "native",
                "native": {"query": "SELECT serial_number AS \"N° Série\", model_name AS \"Modèle\", category AS \"Catégorie\", coalesce(user_name, 'Non attribué') AS \"Utilisateur\", coalesce(department, 'N/A') AS \"Pôle\", warranty_end_date AS \"Fin Garantie\" FROM marts.mart_assets_overview WHERE is_out_of_warranty AND status = 'in_use' ORDER BY warranty_end_date ASC LIMIT 25"},
                "database": db_id,
            },
            "display": "table",
            "visualization_settings": {},
        },
    ]

    card_ids = []
    for c in cards:
        res = call("/api/card", c, token=token, method="POST")
        card_ids.append(res["id"])
        print(f"Created card '{c['name']}' (id={res['id']})")

    print("Creating main dashboard...")
    dash = call("/api/dashboard", {
        "name": "Parc & Assets — Vue d'ensemble SI",
        "description": "Supervision unifiée du matériel, des licences logicielles et de l'obsolescence.",
    }, token=token, method="POST")
    dash_id = dash["id"]

    dash_cards = [
        {"id": -1, "card_id": card_ids[0], "row": 0, "col": 0, "size_x": 6, "size_y": 4, "parameter_mappings": [], "visualization_settings": {}},
        {"id": -2, "card_id": card_ids[1], "row": 0, "col": 6, "size_x": 6, "size_y": 4, "parameter_mappings": [], "visualization_settings": {}},
        {"id": -3, "card_id": card_ids[2], "row": 4, "col": 0, "size_x": 12, "size_y": 6, "parameter_mappings": [], "visualization_settings": {}},
        {"id": -4, "card_id": card_ids[3], "row": 10, "col": 0, "size_x": 12, "size_y": 6, "parameter_mappings": [], "visualization_settings": {}},
    ]
    call(f"/api/dashboard/{dash_id}/cards", {"cards": dash_cards}, token=token, method="PUT")
    print(f"Cards linked to dashboard {dash_id}.")

    link_info = call(f"/api/dashboard/{dash_id}/public_link", {}, token=token, method="POST")
    uuid = link_info.get("uuid")
    print(f"Public dashboard link generated: {uuid}")
    return dash_id, uuid


def save_config(uuid):
    host_mb = os.getenv("HOST_MB_URL", "http://localhost:3001")
    info = {
        "uuid": uuid,
        "public_url": f"{host_mb}/public/dashboard/{uuid}",
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    # 1. Write local in init directory
    try:
        with open("public_dashboard.json", "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)
        print(f"Wrote public_dashboard.json with URL: {info['public_url']}")
    except Exception as e:
        print(f"Could not write local config: {e}")

    # 2. Write in site-vitrine if mounted/accessible
    for rel_path in ["../../site-vitrine/src/metabase_config.json", "/site-vitrine/src/metabase_config.json"]:
        try:
            full_p = os.path.abspath(os.path.join(os.path.dirname(__file__), rel_path))
            if os.path.exists(os.path.dirname(full_p)):
                with open(full_p, "w", encoding="utf-8") as f:
                    json.dump(info, f, indent=2)
                print(f"Updated site-vitrine config: {full_p}")
                break
        except Exception:
            pass


def main():
    wait_ready()
    token = get_token()
    db_id = register_database(token)
    wait_metadata_sync(db_id, token)
    enable_public_sharing(token)
    dash_id, uuid = provision_thematic_dashboard(db_id, token)
    save_config(uuid)
    print("\nMetabase initialization completed successfully!")
    print(f"Public URL: {MB}/public/dashboard/{uuid}")
    print(f"Admin login: {EMAIL} / {PASSWORD}")


if __name__ == "__main__":
    main()
