import re

import geopandas as gpd
import pandas as pd

from config import PROCESSED_DIR


# ============================================================
# FILES
# ============================================================

ZONING_FILE = (
    PROCESSED_DIR /
    "johor_relevant_zoning.parquet"
)

GRID_FILE = (
    PROCESSED_DIR /
    "johor_hv_power_lines.parquet"
)

OUTPUT_PARQUET = (
    PROCESSED_DIR /
    "johor_industrial_grid_features.parquet"
)

OUTPUT_CSV = (
    PROCESSED_DIR /
    "johor_industrial_grid_features.csv"
)


# Working projected CRS for Peninsular Malaysia.
# Distances will therefore be measured in metres.
PROJECTED_CRS = "EPSG:3375"


# ============================================================
# VOLTAGE HELPERS
# ============================================================

def extract_voltages_kv(value):
    """
    Extract every stated OSM voltage from a voltage field.

    Examples:

        "132000"
            -> {132.0}

        "275000;132000"
            -> {275.0, 132.0}

        missing
            -> empty set

    We deliberately do not infer missing voltage.
    """

    if value is None:
        return set()

    try:
        if pd.isna(value):
            return set()
    except (TypeError, ValueError):
        pass

    numbers = re.findall(
        r"\d+",
        str(value),
    )

    if not numbers:
        return set()

    return {
        int(number) / 1000
        for number in numbers
    }


def has_voltage(value, target_kv):
    """
    Return True if the OSM voltage field explicitly
    contains the requested voltage.
    """

    return (
        target_kv
        in extract_voltages_kv(value)
    )


# ============================================================
# NEAREST-LINE CALCULATION
# ============================================================

def calculate_nearest_line(
    candidates,
    grid,
    target_kv,
):
    """
    Find the nearest grid line explicitly tagged with
    target_kv for every candidate industrial polygon.
    """

    print()
    print(
        f"Finding nearest {target_kv} kV line..."
    )

    voltage_mask = (
        grid["voltage"]
        .apply(
            lambda value:
            has_voltage(
                value,
                target_kv,
            )
        )
    )

    target_grid = (
        grid[
            voltage_mask
        ]
        .copy()
    )

    print(
        f"Eligible {target_kv} kV "
        f"features: {len(target_grid):,}"
    )

    if target_grid.empty:

        print(
            f"No {target_kv} kV lines available."
        )

        candidates[
            f"distance_{target_kv}kv_m"
        ] = None

        return candidates

    # ----------------------------------------------
    # Keep only useful grid attributes
    # ----------------------------------------------

    useful_grid_columns = [
        column
        for column in [
            "geometry",
            "name",
            "operator",
            "ref",
            "voltage",
            "power",
        ]
        if column in target_grid.columns
    ]

    target_grid = (
        target_grid[
            useful_grid_columns
        ]
        .copy()
    )

    # Create an internal ID for tracing the
    # nearest grid feature later.
    target_grid[
        "grid_feature_id"
    ] = (
        target_grid
        .index
        .astype(str)
    )

    # Rename fields before the join so we do not
    # collide with zoning columns.
    rename_map = {
        "name":
            f"nearest_{target_kv}kv_name",

        "operator":
            f"nearest_{target_kv}kv_operator",

        "ref":
            f"nearest_{target_kv}kv_ref",

        "voltage":
            f"nearest_{target_kv}kv_voltage_raw",

        "power":
            f"nearest_{target_kv}kv_power_type",

        "grid_feature_id":
            f"nearest_{target_kv}kv_feature_id",
    }

    target_grid = (
        target_grid
        .rename(
            columns=rename_map
        )
    )

    # ----------------------------------------------
    # Nearest-neighbour spatial join
    # ----------------------------------------------

    joined = gpd.sjoin_nearest(
        candidates[
            [
                "site_id",
                "geometry",
            ]
        ],
        target_grid,
        how="left",
        distance_col=(
            f"distance_{target_kv}kv_m"
        ),
    )

    # GeoPandas can return multiple rows when two
    # features are exactly equidistant.
    #
    # Keep one deterministic nearest result per site.
    joined = (
        joined
        .sort_values(
            [
                "site_id",
                f"distance_{target_kv}kv_m",
            ]
        )
        .drop_duplicates(
            subset="site_id",
            keep="first",
        )
    )

    # ----------------------------------------------
    # Prepare fields to merge back
    # ----------------------------------------------

    feature_columns = [
        "site_id",
        f"distance_{target_kv}kv_m",
    ]

    for original_name in rename_map.values():

        if original_name in joined.columns:
            feature_columns.append(
                original_name
            )

    nearest_features = (
        joined[
            feature_columns
        ]
        .copy()
    )

    result = (
        candidates
        .merge(
            nearest_features,
            on="site_id",
            how="left",
        )
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "POWERSTACK — INDUSTRIAL SITE GRID FEATURES"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Load datasets
    # --------------------------------------------------------

    if not ZONING_FILE.exists():

        raise FileNotFoundError(
            f"Missing zoning file: "
            f"{ZONING_FILE}"
        )

    if not GRID_FILE.exists():

        raise FileNotFoundError(
            f"Missing grid file: "
            f"{GRID_FILE}"
        )

    zoning = gpd.read_parquet(
        ZONING_FILE
    )

    grid = gpd.read_parquet(
        GRID_FILE
    )

    print()
    print(
        f"Loaded zoning polygons: "
        f"{len(zoning):,}"
    )

    print(
        f"Loaded HV grid features: "
        f"{len(grid):,}"
    )

    # --------------------------------------------------------
    # 2. Filter to INDUSTRIAL land only
    # --------------------------------------------------------

    industrial = (
        zoning[
            zoning[
                "gunatanah1"
            ]
            .astype(str)
            .str.strip()
            .eq("Industri")
        ]
        .copy()
    )

    print()
    print(
        f"Industrial polygons: "
        f"{len(industrial):,}"
    )

    if industrial.empty:

        raise RuntimeError(
            "No industrial zoning polygons found."
        )

    # --------------------------------------------------------
    # 3. Create stable PowerStack site IDs
    # --------------------------------------------------------

    if "OBJECTID" in industrial.columns:

        industrial[
            "site_id"
        ] = (
            "JHR-ZONE-"
            +
            industrial[
                "OBJECTID"
            ]
            .astype(str)
        )

    else:

        industrial = (
            industrial
            .reset_index(
                drop=True
            )
        )

        industrial[
            "site_id"
        ] = [
            f"JHR-ZONE-{i:06d}"
            for i in range(
                1,
                len(industrial) + 1,
            )
        ]

    # --------------------------------------------------------
    # 4. Reproject both datasets into metres
    # --------------------------------------------------------

    print()
    print(
        f"Projecting data to "
        f"{PROJECTED_CRS}..."
    )

    industrial = (
        industrial
        .to_crs(
            PROJECTED_CRS
        )
    )

    grid = (
        grid
        .to_crs(
            PROJECTED_CRS
        )
    )

    # --------------------------------------------------------
    # 5. Calculate polygon area ourselves
    # --------------------------------------------------------

    industrial[
        "calculated_area_ha"
    ] = (
        industrial
        .geometry
        .area
        /
        10_000
    )

    # --------------------------------------------------------
    # 6. Calculate nearest grid distances
    # --------------------------------------------------------

    for voltage_kv in [
        132,
        275,
        500,
    ]:

        industrial = (
            calculate_nearest_line(
                industrial,
                grid,
                voltage_kv,
            )
        )

    # --------------------------------------------------------
    # 7. Convert distances into kilometres
    # --------------------------------------------------------

    for voltage_kv in [
        132,
        275,
        500,
    ]:

        metres_column = (
            f"distance_{voltage_kv}kv_m"
        )

        km_column = (
            f"distance_{voltage_kv}kv_km"
        )

        if metres_column in industrial.columns:

            industrial[
                km_column
            ] = (
                industrial[
                    metres_column
                ]
                /
                1000
            )

    # --------------------------------------------------------
    # 8. Distance to nearest major transmission line
    # --------------------------------------------------------

    distance_columns = [
        "distance_132kv_km",
        "distance_275kv_km",
        "distance_500kv_km",
    ]

    industrial[
        "distance_nearest_hv_km"
    ] = (
        industrial[
            distance_columns
        ]
        .min(
            axis=1
        )
    )

    # --------------------------------------------------------
    # 9. Add simple proximity flags
    # --------------------------------------------------------

    industrial[
        "within_1km_275kv"
    ] = (
        industrial[
            "distance_275kv_km"
        ]
        <= 1
    )

    industrial[
        "within_5km_275kv"
    ] = (
        industrial[
            "distance_275kv_km"
        ]
        <= 5
    )

    industrial[
        "within_10km_275kv"
    ] = (
        industrial[
            "distance_275kv_km"
        ]
        <= 10
    )

    industrial[
        "within_5km_500kv"
    ] = (
        industrial[
            "distance_500kv_km"
        ]
        <= 5
    )

    # --------------------------------------------------------
    # 10. Evidence / model provenance
    # --------------------------------------------------------

    industrial[
        "grid_feature_source"
    ] = (
        "OpenStreetMap / "
        "Geofabrik regional extract"
    )

    industrial[
        "grid_proximity_fact_type"
    ] = "DERIVED"

    industrial[
        "grid_capacity_status"
    ] = "NOT_FOUND"

    # --------------------------------------------------------
    # 11. Save full GeoParquet
    # --------------------------------------------------------

    industrial.to_parquet(
        OUTPUT_PARQUET,
        index=False,
    )

    # --------------------------------------------------------
    # 12. Save human-readable CSV without geometry
    # --------------------------------------------------------

    csv_columns = [
        column
        for column in [
            "site_id",
            "gunatanah1",
            "daerah_nam",
            "mukim_name",
            "pbt_name",
            "lot_upi",
            "luas_hekta",
            "calculated_area_ha",
            "distance_132kv_km",
            "distance_275kv_km",
            "distance_500kv_km",
            "distance_nearest_hv_km",
            "within_1km_275kv",
            "within_5km_275kv",
            "within_10km_275kv",
            "within_5km_500kv",
            "nearest_132kv_name",
            "nearest_275kv_name",
            "nearest_500kv_name",
            "nearest_132kv_operator",
            "nearest_275kv_operator",
            "nearest_500kv_operator",
            "grid_capacity_status",
        ]
        if column in industrial.columns
    ]

    industrial[
        csv_columns
    ].to_csv(
        OUTPUT_CSV,
        index=False,
    )

    # --------------------------------------------------------
    # 13. Summary statistics
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SITE GRID FEATURE SUMMARY")
    print("=" * 70)

    print()
    print(
        f"Industrial candidate polygons: "
        f"{len(industrial):,}"
    )

    print()
    print("Median distance to grid:")

    for voltage_kv in [
        132,
        275,
        500,
    ]:

        column = (
            f"distance_{voltage_kv}kv_km"
        )

        median = (
            industrial[
                column
            ]
            .median()
        )

        print(
            f"  {voltage_kv} kV: "
            f"{median:.2f} km"
        )

    print()
    print("275 kV proximity:")

    print(
        f"  within 1 km: "
        f"{industrial['within_1km_275kv'].sum():,}"
    )

    print(
        f"  within 5 km: "
        f"{industrial['within_5km_275kv'].sum():,}"
    )

    print(
        f"  within 10 km: "
        f"{industrial['within_10km_275kv'].sum():,}"
    )

    print()
    print(
        "Largest industrial polygons "
        "within 5 km of mapped 275 kV:"
    )

    shortlist = (
        industrial[
            industrial[
                "within_5km_275kv"
            ]
        ]
        .sort_values(
            "calculated_area_ha",
            ascending=False,
        )
    )

    show_columns = [
        column
        for column in [
            "site_id",
            "daerah_nam",
            "mukim_name",
            "pbt_name",
            "calculated_area_ha",
            "distance_275kv_km",
        ]
        if column in shortlist.columns
    ]

    print(
        shortlist[
            show_columns
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    print()
    print(
        f"Saved GeoParquet:"
    )
    print(
        OUTPUT_PARQUET
    )

    print()
    print(
        f"Saved CSV:"
    )
    print(
        OUTPUT_CSV
    )

    print()
    print("=" * 70)
    print(
        "GRID FEATURE BUILD COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()