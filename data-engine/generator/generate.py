"""Generate synthetic "Parc & Assets" data and load it into the PostgreSQL `raw` schema."""
import os
import random

import pandas as pd
from faker import Faker
from sqlalchemy import create_engine, inspect, text

SEED = int(os.getenv("SEED", "42"))
N_USERS = int(os.getenv("N_USERS", "200"))
N_ASSETS = int(os.getenv("N_ASSETS", "300"))
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://parc:parc@localhost:5432/parc_assets"
)

HARDWARE = [
    ("Dell Latitude 5440", "Laptop", "Dell", 1150),
    ("Apple MacBook Pro 14", "Laptop", "Apple", 2300),
    ("HP EliteBook 840", "Laptop", "HP", 1300),
    ("Lenovo ThinkPad T14", "Laptop", "Lenovo", 1200),
    ("Dell U2723QE", "Monitor", "Dell", 650),
    ("Apple iPhone 15", "Smartphone", "Apple", 950),
    ("Samsung Galaxy S23", "Smartphone", "Samsung", 800),
    ("Dell OptiPlex 7010", "Desktop", "Dell", 900),
]
SOFTWARE = [
    ("Microsoft 365", 12.5),
    ("Adobe Creative Cloud", 60.0),
    ("Slack", 8.0),
    ("Jira", 7.5),
    ("Visual Studio", 45.0),
    ("Zoom", 13.0),
]
DEPARTMENTS = ["IT", "Finance", "RH", "Ventes", "Marketing", "Support", "R&D"]
STATUSES = ["in_use", "in_stock", "in_repair", "retired"]


def build_frames(fake: Faker):
    users = pd.DataFrame(
        {
            "user_id": range(1, N_USERS + 1),
            "full_name": [fake.name() for _ in range(N_USERS)],
            "email": [fake.unique.email() for _ in range(N_USERS)],
            "department": [random.choice(DEPARTMENTS) for _ in range(N_USERS)],
            "city": [fake.city() for _ in range(N_USERS)],
        }
    )
    models = pd.DataFrame(
        [
            {"model_id": i, "model_name": n, "category": c, "manufacturer": m, "unit_price": p}
            for i, (n, c, m, p) in enumerate(HARDWARE, start=1)
        ]
    )
    assets = []
    for i in range(1, N_ASSETS + 1):
        purchase = fake.date_between(start_date="-6y", end_date="today")
        status = random.choices(STATUSES, weights=[70, 15, 5, 10])[0]
        assets.append(
            {
                "asset_id": i,
                "serial_number": fake.unique.bothify("SN-########").upper(),
                "model_id": random.randint(1, len(HARDWARE)),
                "user_id": random.randint(1, N_USERS) if status in ("in_use", "in_repair") else None,
                "status": status,
                "purchase_date": purchase,
                "warranty_end_date": purchase.replace(year=purchase.year + 3)
                if purchase.month != 2 or purchase.day != 29
                else purchase.replace(year=purchase.year + 3, day=28),
            }
        )
    assets = pd.DataFrame(assets)
    installs = []
    iid = 1
    for a in assets[assets.status == "in_use"].itertuples():
        for name, cost in random.sample(SOFTWARE, k=random.randint(1, 3)):
            installs.append(
                {
                    "installation_id": iid,
                    "asset_id": a.asset_id,
                    "software_name": name,
                    "monthly_license_cost": cost,
                    "installed_at": fake.date_between(start_date=a.purchase_date, end_date="today"),
                }
            )
            iid += 1
    return users, models, assets, pd.DataFrame(installs)


def main():
    random.seed(SEED)
    Faker.seed(SEED)
    fake = Faker("fr_FR")
    users, models, assets, installs = build_frames(fake)
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        inspector = inspect(conn)
        for name, df in [
            ("dim_users", users),
            ("dim_hardware_models", models),
            ("fact_assets", assets),
            ("fact_software_installations", installs),
        ]:
            if inspector.has_table(name, schema="raw"):
                conn.execute(text(f'TRUNCATE TABLE raw."{name}" CASCADE'))
                df.to_sql(name, conn, schema="raw", if_exists="append", index=False)
            else:
                df.to_sql(name, conn, schema="raw", if_exists="replace", index=False)
            print(f"raw.{name}: {len(df)} rows")


if __name__ == "__main__":
    main()
