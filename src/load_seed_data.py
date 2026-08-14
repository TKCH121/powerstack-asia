import duckdb
import pandas as pd

from config import DB_PATH, MANUAL_DIR
from powerstack_utils import EVIDENCE_FACT_TYPES


def replace_from_csv(con, table_name: str, csv_name: str):
    path = MANUAL_DIR / csv_name
    df = pd.read_csv(path)

    if "fact_type" not in df.columns:
        raise ValueError(f"{csv_name} is missing fact_type.")

    invalid_fact_types = set(df["fact_type"].dropna()) - EVIDENCE_FACT_TYPES
    if invalid_fact_types:
        raise ValueError(
            f"{csv_name} has invalid fact_type values: "
            f"{sorted(invalid_fact_types)}"
        )

    con.register("seed_df", df)
    con.execute(f"DELETE FROM {table_name}")
    con.execute(f"INSERT INTO {table_name} BY NAME SELECT * FROM seed_df")
    con.unregister("seed_df")
    print(f"Loaded {len(df)} rows into {table_name}")


def main():
    con = duckdb.connect(str(DB_PATH))
    replace_from_csv(con, "dc_projects", "dc_projects_seed.csv")
    replace_from_csv(con, "connection_events", "connection_events_seed.csv")
    replace_from_csv(con, "dc_project_locations", "dc_project_locations_seed.csv")
    replace_from_csv(con, "grid_asset_events", "grid_asset_events_seed.csv")

    print("\nProjects:")
    print(con.execute("SELECT * FROM dc_projects").fetchdf())
    print("\nConnection events:")
    print(con.execute("SELECT * FROM connection_events ORDER BY event_date").fetchdf())
    print("\nProject locations:")
    print(con.execute("SELECT * FROM dc_project_locations").fetchdf())
    print("\nGrid asset events:")
    print(con.execute("SELECT * FROM grid_asset_events ORDER BY event_date").fetchdf())
    con.close()

if __name__ == "__main__":
    main()
