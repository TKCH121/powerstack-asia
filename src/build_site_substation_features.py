import geopandas as gpd
import pandas as pd

from config import PROCESSED_DIR
from powerstack_utils import (
    PROJECTED_CRS,
    geometry_hash,
    has_voltage,
    nearest_feature_join,
)


# ============================================================
# FILES
# ============================================================

SITE_FILE = (
    PROCESSED_DIR /
    "johor_industrial_grid_features_clean.parquet"
)

SUBSTATION_FILE = (
    PROCESSED_DIR /
    "johor_hv_substations_clean.parquet"
)

OUTPUT_PARQUET = (
    PROCESSED_DIR /
    "johor_powerstack_site_features_v01.parquet"
)

OUTPUT_CSV = (
    PROCESSED_DIR /
    "johor_powerstack_site_features_v01.csv"
)


def make_substation_id(
    geometry
):
    """
    Create a stable internal identifier from geometry.
    """

    return "JHR-SS-" + geometry_hash(geometry)[:12].upper()


# ============================================================
# NEAREST SUBSTATION FUNCTION
# ============================================================

def add_nearest_substation(
    sites,
    substations,
    mask,
    label,
):

    target = (
        substations[
            mask
        ]
        .copy()
    )

    print()
    print(
        f"Finding nearest {label}..."
    )

    print(
        f"Eligible substations: "
        f"{len(target):,}"
    )

    distance_m = (
        f"distance_{label}_m"
    )

    distance_km = (
        f"distance_{label}_km"
    )

    if target.empty:

        sites[
            distance_m
        ] = None

        sites[
            distance_km
        ] = None

        return sites

    # --------------------------------------------------------
    # Keep relevant substation attributes
    # --------------------------------------------------------

    attributes = [
        column
        for column in [
            "substation_id",
            "name",
            "operator_normalized",
            "substation",
            "voltage",
            "max_voltage_kv",
            "ref",
            "pmu_name_signal",
            "mapped_transmission_substation",
            "geometry",
        ]
        if column in target.columns
    ]

    target = (
        target[
            attributes
        ]
        .copy()
    )

    rename_map = {
        "substation_id":
            f"nearest_{label}_id",

        "name":
            f"nearest_{label}_name",

        "operator_normalized":
            f"nearest_{label}_operator",

        "substation":
            f"nearest_{label}_type",

        "voltage":
            f"nearest_{label}_voltage_raw",

        "max_voltage_kv":
            f"nearest_{label}_max_voltage_kv",

        "ref":
            f"nearest_{label}_ref",

        "pmu_name_signal":
            f"nearest_{label}_pmu_name_signal",

        "mapped_transmission_substation":
            f"nearest_{label}_transmission_signal",
    }

    target = target.rename(
        columns=rename_map
    )

    # --------------------------------------------------------
    # Nearest-neighbour join
    # --------------------------------------------------------

    joined = nearest_feature_join(
        sites[
            [
                "site_id",
                "geometry",
            ]
        ],
        target,
        candidate_id="site_id",
        distance_column=distance_m,
        tie_break_columns=(f"nearest_{label}_id",),
    )

    result_columns = [
        "site_id",
        distance_m,
    ]

    for renamed in rename_map.values():

        if renamed in joined.columns:

            result_columns.append(
                renamed
            )

    nearest = (
        joined[
            result_columns
        ]
        .copy()
    )

    result = (
        sites
        .merge(
            nearest,
            on="site_id",
            how="left",
        )
    )

    result = gpd.GeoDataFrame(
        result,
        geometry="geometry",
        crs=sites.crs,
    )

    result[
        distance_km
    ] = (
        result[
            distance_m
        ]
        /
        1000
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "POWERSTACK — SITE SUBSTATION FEATURES"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Load clean datasets
    # --------------------------------------------------------

    sites = gpd.read_parquet(
        SITE_FILE
    )

    substations = gpd.read_parquet(
        SUBSTATION_FILE
    )

    print()
    print(
        f"Canonical industrial sites: "
        f"{len(sites):,}"
    )

    print(
        f"Canonical Johor HV substations: "
        f"{len(substations):,}"
    )

    # --------------------------------------------------------
    # 2. Reproject into metres
    # --------------------------------------------------------

    sites = sites.to_crs(
        PROJECTED_CRS
    )

    substations = substations.to_crs(
        PROJECTED_CRS
    )

    # --------------------------------------------------------
    # 3. Stable internal substation IDs
    # --------------------------------------------------------

    substations[
        "substation_id"
    ] = (
        substations.geometry
        .apply(
            make_substation_id
        )
    )

    # --------------------------------------------------------
    # 4. Nearest ANY mapped HV substation
    # --------------------------------------------------------

    sites = add_nearest_substation(
        sites,
        substations,
        pd.Series(
            True,
            index=substations.index,
        ),
        "hv_substation",
    )

    # --------------------------------------------------------
    # 5. Nearest mapped transmission substation
    # --------------------------------------------------------

    transmission_mask = (
        substations[
            "mapped_transmission_substation"
        ]
        .fillna(False)
    )

    sites = add_nearest_substation(
        sites,
        substations,
        transmission_mask,
        "transmission_substation",
    )

    # --------------------------------------------------------
    # 6. Nearest explicitly tagged voltage levels
    # --------------------------------------------------------

    for voltage_kv in [
        132,
        275,
        500,
    ]:

        voltage_mask = (
            substations[
                "voltage"
            ]
            .apply(
                lambda value:
                has_voltage(
                    value,
                    voltage_kv,
                )
            )
        )

        sites = add_nearest_substation(
            sites,
            substations,
            voltage_mask,
            f"{voltage_kv}kv_substation",
        )

    # --------------------------------------------------------
    # 7. Evidence classification
    # --------------------------------------------------------

    sites[
        "substation_proximity_fact_type"
    ] = "DERIVED"

    sites[
        "substation_source"
    ] = (
        "OpenStreetMap / "
        "Geofabrik regional extract"
    )

    sites[
        "substation_capacity_status"
    ] = "NOT_FOUND"

    # --------------------------------------------------------
    # 8. Save
    # --------------------------------------------------------

    sites.to_parquet(
        OUTPUT_PARQUET,
        index=False,
    )

    csv_columns = [
        column
        for column in sites.columns
        if column != "geometry"
    ]

    sites[
        csv_columns
    ].to_csv(
        OUTPUT_CSV,
        index=False,
    )

    # --------------------------------------------------------
    # 9. Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "SUBSTATION PROXIMITY SUMMARY"
    )
    print("=" * 70)

    print()
    print(
        f"Industrial sites analysed: "
        f"{len(sites):,}"
    )

    print()
    print(
        "Median distance to mapped substations:"
    )

    summary_columns = {
        "Any HV":
            "distance_hv_substation_km",

        "Transmission":
            "distance_transmission_substation_km",

        "132 kV":
            "distance_132kv_substation_km",

        "275 kV":
            "distance_275kv_substation_km",

        "500 kV":
            "distance_500kv_substation_km",
    }

    for label, column in (
        summary_columns.items()
    ):

        median = (
            sites[
                column
            ]
            .median()
        )

        print(
            f"  {label}: "
            f"{median:.2f} km"
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
        "SUBSTATION FEATURE BUILD COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
