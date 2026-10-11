"""Configure Metabase through its API: admin setup, then register the Parc & Assets database."""
import json
import os
import time
import urllib.request

MB = os.getenv("MB_URL", "http://localhost:3001")
EMAIL = os.getenv("MB_ADMIN_EMAIL", "admin@example.com")
PASSWORD = os.getenv("MB_ADMIN_PASSWORD", "Admin-Passw0rd!")
DB = {
    "host": os.getenv("PGHOST", "postgres"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "parc_assets"),
    "user": os.getenv("PGUSER", "parc"),
    "password": os.getenv("PGPASSWORD", "parc"),
}


def call(path, payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Metabase-Session"] = token
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(MB + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def wait_ready():
    for _ in range(60):
        try:
            if call("/api/health").get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(5)
    raise SystemExit("Metabase not ready")


def main():
    wait_ready()
    props = call("/api/session/properties")
    if props.get("setup-token"):
        token = call("/api/setup", {
            "token": props["setup-token"],
            "user": {"email": EMAIL, "password": PASSWORD, "first_name": "Admin", "last_name": "BI"},
            "prefs": {"site_name": "Parc & Assets", "allow_tracking": False},
        })["id"]
    else:
        token = call("/api/session", {"username": EMAIL, "password": PASSWORD})["id"]
    existing = call("/api/database", token=token)
    dbs = existing["data"] if isinstance(existing, dict) else existing
    if any(d["name"] == "Parc Assets" for d in dbs):
        print("Database already configured")
        return
    call("/api/database", {"name": "Parc Assets", "engine": "postgres", "details": DB, "is_full_sync": True}, token)
    print("Metabase database 'Parc Assets' created")


if __name__ == "__main__":
    main()
