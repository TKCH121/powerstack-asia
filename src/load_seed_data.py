import duckdb
import pandas as pd
from config import DB_PATH, MANUAL_DIR

def replace_from_csv(con, table_name: str, csv_name: str):
    path = MANUAL_DIR / csv_name
    df = pd.read_csv(path)
    con.register("seed_df", df)
    con.execute(f"DELETE FROM {table_name}")
    con.execute(
    f"INSERT INTO {table_name} BY NAME SELECT * FROM seed_df"
    )
    con.unregister("seed_df")
    print(f"Loaded {len(df)} rows into {table_name}")

def main():
    con = duckdb.connect(str(DB_PATH))
    replace_from_csv(con, "dc_projects", "dc_projects_seed.csv")
    replace_from_csv(con, "connection_events", "connection_events_seed.csv")
    print("\nProjects:")
    print(con.execute("SELECT * FROM dc_projects").fetchdf())
    print("\nConnection events:")
    print(con.execute("SELECT * FROM connection_events ORDER BY event_date").fetchdf())
    con.close()

if __name__ == "__main__":
    main()
