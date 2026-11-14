"""Read-only sanity checks before stamping an existing StudySync DB."""
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
if not url or make_url(url).get_backend_name() != "postgresql":
    raise SystemExit("A PostgreSQL DATABASE_URL is required")
engine = create_engine(url)
expected = {"users", "workspaces", "memberships", "modules", "tasks", "comments", "activities"}
with engine.connect() as conn:
    tables = set(inspect(conn).get_table_names())
    missing = expected - tables
    if missing:
        raise SystemExit("DO NOT STAMP: missing tables " + ", ".join(sorted(missing)))
    for table in sorted(expected):
        count = conn.execute(text(f'SELECT count(*) FROM "{table}"')).scalar_one()
        print(f"{table}: {count} rows")
print("Basic table presence checks passed. This does not establish full schema equivalence.")
print("Back up and compare schema/constraints before stamping an existing database.")
