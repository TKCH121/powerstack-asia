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

POWER_PATHWAY_COMPONENT_TYPES = {
    "EXISTING_GRID",
    "CONSUMER_LANDING_STATION",
    "SSU",
    "PMU",
    "SUBSTATION",
    "LINE",
    "CABLE",
    "UPSTREAM_REINFORCEMENT",
    "RIGHT_OF_WAY",
    "ONSITE_GENERATION",
}

POWER_PATHWAY_COMPONENT_CAPACITY_UNITS = {
    "MW",
    "MWac",
    "MWp",
    "MVA",
}


def validate_power_value_semantics(
    df,
    csv_name,
    power_column,
    measure_type_column,
    qualifier_column,
):
    invalid_types = set(df[measure_type_column].dropna()) - POWER_MEASURE_TYPES
    if invalid_types:
        raise ValueError(
            f"{csv_name} has invalid {measure_type_column} values: "
            f"{sorted(invalid_types)}"
        )

    invalid_qualifiers = (
        set(df[qualifier_column].dropna()) - POWER_MW_QUALIFIERS
    )
    if invalid_qualifiers:
        raise ValueError(
            f"{csv_name} has invalid {qualifier_column} values: "
            f"{sorted(invalid_qualifiers)}"
        )

    missing_power = df[power_column].isna()
    invalid_missing = (
        missing_power
        &
        (
            (df[measure_type_column] != "NOT_FOUND")
            |
            (df[qualifier_column] != "NOT_FOUND")
        )
    )
    invalid_present = (
        ~missing_power
        &
        (
            (df[measure_type_column] == "NOT_FOUND")
            |
            (df[qualifier_column] == "NOT_FOUND")
        )
    )

    if invalid_missing.any() or invalid_present.any():
        raise ValueError(
            f"{csv_name} has inconsistent {power_column}, "
            f"{measure_type_column}, or {qualifier_column} values."
        )


def validate_power_pathways(df):
    for prefix in ["target", "ultimate"]:
        validate_power_value_semantics(
            df,
            "power_pathways_seed.csv",
            f"{prefix}_power_mw",
            f"{prefix}_power_measure_type",
            f"{prefix}_power_mw_qualifier",
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


def validate_power_pathway_components(df):
    invalid_types = (
        set(df["component_type"].dropna())
        - POWER_PATHWAY_COMPONENT_TYPES
    )
    if invalid_types:
        raise ValueError(
            "power_pathway_components_seed.csv has invalid component_type "
            f"values: {sorted(invalid_types)}"
        )

    invalid_units = (
        set(df["capacity_unit"].dropna())
        - POWER_PATHWAY_COMPONENT_CAPACITY_UNITS
    )
    if invalid_units:
        raise ValueError(
            "power_pathway_components_seed.csv has invalid capacity_unit "
            f"values: {sorted(invalid_units)}"
        )

    capacity_present = df["capacity_value"].notna()
    unit_present = df["capacity_unit"].notna()
    if not capacity_present.equals(unit_present):
        raise ValueError(
            "power_pathway_components_seed.csv must provide capacity_value "
            "and capacity_unit together."
        )


def validate_power_pathway_milestones(df):
    validate_power_value_semantics(
        df,
        "power_pathway_milestones_seed.csv",
        "power_mw",
        "power_measure_type",
        "power_mw_qualifier",
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
    elif table_name == "power_pathway_components":
        validate_power_pathway_components(df)
    elif table_name == "power_pathway_milestones":
        validate_power_pathway_milestones(df)

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
