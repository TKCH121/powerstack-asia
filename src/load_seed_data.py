import duckdb
import pandas as pd

from config import DB_PATH, MANUAL_DIR
from powerstack_utils import EVIDENCE_FACT_TYPES


POWER_MEASURE_TYPES = {
    "ELECTRICAL_SUPPLY",
    "MAXIMUM_DEMAND",
    "CONTRACTED_CAPACITY",
    "CONNECTION_CAPACITY",
    "NOT_FOUND",
}

POWER_MW_QUALIFIERS = {
    "EXACT",
    "APPROXIMATE",
    "GREATER_THAN",
    "LESS_THAN",
    "NOT_FOUND",
}


def validate_power_pathways(df):
    for column in [
        "target_power_measure_type",
        "ultimate_power_measure_type",
    ]:
        invalid = set(df[column].dropna()) - POWER_MEASURE_TYPES
        if invalid:
            raise ValueError(
                f"power_pathways_seed.csv has invalid {column} values: "
                f"{sorted(invalid)}"
            )

    for column in [
        "target_power_mw_qualifier",
        "ultimate_power_mw_qualifier",
    ]:
        invalid = set(df[column].dropna()) - POWER_MW_QUALIFIERS
        if invalid:
            raise ValueError(
                f"power_pathways_seed.csv has invalid {column} values: "
                f"{sorted(invalid)}"
            )

    for prefix in ["target", "ultimate"]:
        mw_column = f"{prefix}_power_mw"
        type_column = f"{prefix}_power_measure_type"
        qualifier_column = f"{prefix}_power_mw_qualifier"

        missing_mw = df[mw_column].isna()
        invalid_missing = (
            missing_mw
            &
            (
                (df[type_column] != "NOT_FOUND")
                |
                (df[qualifier_column] != "NOT_FOUND")
            )
        )
        invalid_present = (
            ~missing_mw
            &
            (
                (df[type_column] == "NOT_FOUND")
                |
                (df[qualifier_column] == "NOT_FOUND")
            )
        )

        if invalid_missing.any() or invalid_present.any():
            raise ValueError(
                f"power_pathways_seed.csv has inconsistent {prefix} power "
                "MW, measure type, or qualifier values."
            )

    cutoff_date_present = df["information_cutoff_date"].notna()
    cutoff_precision_present = (
        df["information_cutoff_date_precision"].notna()
    )

    if not cutoff_date_present.equals(cutoff_precision_present):
        raise ValueError(
            "power_pathways_seed.csv must provide information cutoff date "
            "and precision together."
        )


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

    if table_name == "power_pathways":
        validate_power_pathways(df)

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
    replace_from_csv(con, "power_pathways", "power_pathways_seed.csv")
    replace_from_csv(
        con,
        "power_pathway_components",
        "power_pathway_components_seed.csv",
    )
    replace_from_csv(
        con,
        "power_pathway_milestones",
        "power_pathway_milestones_seed.csv",
    )

    print("\nProjects:")
    print(con.execute("SELECT * FROM dc_projects").fetchdf())
    print("\nConnection events:")
    print(con.execute("SELECT * FROM connection_events ORDER BY event_date").fetchdf())
    print("\nProject locations:")
    print(con.execute("SELECT * FROM dc_project_locations").fetchdf())
    print("\nGrid asset events:")
    print(con.execute("SELECT * FROM grid_asset_events ORDER BY event_date").fetchdf())
    print("\nPower pathways:")
    print(con.execute("SELECT * FROM power_pathways ORDER BY pathway_id").fetchdf())
    print("\nPower pathway components:")
    print(
        con.execute(
            "SELECT * FROM power_pathway_components ORDER BY component_id"
        ).fetchdf()
    )
    print("\nPower pathway milestones:")
    print(
        con.execute(
            "SELECT * FROM power_pathway_milestones ORDER BY milestone_id"
        ).fetchdf()
    )
    con.close()

if __name__ == "__main__":
    main()
