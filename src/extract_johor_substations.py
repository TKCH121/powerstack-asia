import shutil

import geopandas as gpd
import pandas as pd

from config import RAW_DIR, PROCESSED_DIR
from powerstack_utils import (
    PUBLIC_MAP_SOURCE_TYPE,
    has_voltage,
    max_voltage_kv,
    run_command,
)


# ============================================================
# FILES
# ============================================================

JOHOR_PBF = (
    RAW_DIR /
    "johor_bbox.osm.pbf"
)

SUBSTATION_PBF = (
    RAW_DIR /
    "johor_substations.osm.pbf"
)

SUBSTATION_GEOJSON = (
    RAW_DIR /
    "johor_substations.geojson"
)

ALL_OUTPUT = (
    PROCESSED_DIR /
    "johor_substations.parquet"
)

HV_OUTPUT = (
    PROCESSED_DIR /
    "johor_hv_substations.parquet"
)


# ============================================================
# HELPERS
# ============================================================

# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "POWERSTACK — JOHOR SUBSTATION EXTRACTION"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Check input files/tools
    # --------------------------------------------------------

    if not JOHOR_PBF.exists():

        raise FileNotFoundError(
            f"Missing Johor PBF: {JOHOR_PBF}"
        )

    osmium_path = shutil.which(
        "osmium"
    )

    if osmium_path is None:

        raise RuntimeError(
            "Osmium not found in the active environment."
        )

    print()
    print(
        f"Using Osmium: {osmium_path}"
    )

    # --------------------------------------------------------
    # 2. Extract operating + construction substations
    # --------------------------------------------------------

    print()
    print(
        "Filtering mapped substations..."
    )

    run_command(
        [
            "osmium",
            "tags-filter",
            str(JOHOR_PBF),

            # Any OSM object type:
            # node, way or relation.
            "power=substation",

            # Future / construction substations
            "construction:power=substation",

            "-o",
            str(SUBSTATION_PBF),
            "-O",
        ]
    )

    # Osmium's tags-filter accepts expressions without an
    # object prefix, which means all node/way/relation types
    # are matched.

    # --------------------------------------------------------
    # 3. Export to GIS geometry
    # --------------------------------------------------------

    print()
    print(
        "Converting substations to GeoJSON..."
    )

    run_command(
        [
            "osmium",
            "export",
            str(SUBSTATION_PBF),
            "-o",
            str(SUBSTATION_GEOJSON),
            "-O",
        ]
    )

    # --------------------------------------------------------
    # 4. Load into GeoPandas
    # --------------------------------------------------------

    print()
    print(
        "Loading substations into GeoPandas..."
    )

    substations = gpd.read_file(
        SUBSTATION_GEOJSON
    )

    print()
    print(
        f"Mapped substation features: "
        f"{len(substations):,}"
    )

    print(
        f"CRS: {substations.crs}"
    )

    print()
    print("Available columns:")

    for column in substations.columns:

        print(
            f"  - {column}"
        )

    # --------------------------------------------------------
    # 5. Ensure important fields exist
    # --------------------------------------------------------

    expected_fields = [
        "power",
        "construction:power",
        "substation",
        "voltage",
        "name",
        "operator",
        "ref",
        "location",
    ]

    for field in expected_fields:

        if field not in substations.columns:

            substations[
                field
            ] = None

    # --------------------------------------------------------
    # 6. Voltage features
    # --------------------------------------------------------

    substations[
        "max_voltage_kv"
    ] = (
        substations[
            "voltage"
        ]
        .apply(
            max_voltage_kv
        )
    )

    for voltage_kv in [
        132,
        275,
        500,
    ]:

        substations[
            f"has_{voltage_kv}kv"
        ] = (
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

    # --------------------------------------------------------
    # 7. Operating/construction status
    # --------------------------------------------------------

    substations[
        "powerstack_status"
    ] = "OPERATING_OR_MAPPED"

    construction_mask = (
        substations[
            "construction:power"
        ]
        .eq(
            "substation"
        )
    )

    substations.loc[
        construction_mask,
        "powerstack_status"
    ] = "UNDER_CONSTRUCTION"

    # --------------------------------------------------------
    # 8. Evidence classification
    # --------------------------------------------------------

    substations[
        "powerstack_source"
    ] = (
        "OpenStreetMap / "
        "Geofabrik regional extract"
    )

    substations[
        "fact_type"
    ] = "VERIFIED"

    substations["source_type"] = PUBLIC_MAP_SOURCE_TYPE

    # We explicitly do not claim PMU status unless
    # independently supported.
    substations[
        "tnb_pmu_status"
    ] = "NOT_VERIFIED"

    substations[
        "available_capacity_mw"
    ] = None

    substations[
        "capacity_status"
    ] = "NOT_FOUND"

    # --------------------------------------------------------
    # 9. Save ALL mapped substations
    # --------------------------------------------------------

    substations.to_parquet(
        ALL_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------
    # 10. Confirmed mapped HV subset
    # --------------------------------------------------------

    hv = (
        substations[
            substations[
                "max_voltage_kv"
            ] >= 100
        ]
        .copy()
    )

    hv.to_parquet(
        HV_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------
    # 11. Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "SUBSTATION SUMMARY"
    )
    print("=" * 70)

    print()
    print(
        f"All mapped substations: "
        f"{len(substations):,}"
    )

    print(
        f"Mapped >=100 kV substations: "
        f"{len(hv):,}"
    )

    print()
    print(
        "Voltage-data completeness:"
    )

    known_voltage = (
        substations[
            "max_voltage_kv"
        ]
        .notna()
        .sum()
    )

    unknown_voltage = (
        substations[
            "max_voltage_kv"
        ]
        .isna()
        .sum()
    )

    print(
        f"  voltage known: "
        f"{known_voltage:,}"
    )

    print(
        f"  voltage NOT_FOUND: "
        f"{unknown_voltage:,}"
    )

    print()
    print(
        "HV maximum-voltage distribution:"
    )

    if not hv.empty:

        print(
            hv[
                "max_voltage_kv"
            ]
            .value_counts()
            .sort_index()
            .to_string()
        )

    else:

        print(
            "NO >=100 kV SUBSTATIONS FOUND"
        )

    print()
    print(
        "Explicit voltage tags:"
    )

    for voltage_kv in [
        132,
        275,
        500,
    ]:

        count = (
            substations[
                f"has_{voltage_kv}kv"
            ]
            .sum()
        )

        print(
            f"  contains {voltage_kv} kV: "
            f"{count:,}"
        )

    print()
    print(
        "Substation-type distribution:"
    )

    print(
        substations[
            "substation"
        ]
        .value_counts(
            dropna=False
        )
        .head(20)
        .to_string()
    )

    print()
    print(
        "Operator distribution:"
    )

    print(
        substations[
            "operator"
        ]
        .value_counts(
            dropna=False
        )
        .head(20)
        .to_string()
    )

    print()
    print(
        "Geometry types:"
    )

    print(
        substations.geometry
        .geom_type
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Construction status:"
    )

    print(
        substations[
            "powerstack_status"
        ]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------------
    # 12. Show named HV substations
    # --------------------------------------------------------

    print()
    print(
        "NAMED HIGH-VOLTAGE SUBSTATIONS"
    )
    print("-" * 70)

    display_columns = [
        column
        for column in [
            "name",
            "operator",
            "substation",
            "voltage",
            "max_voltage_kv",
            "ref",
            "powerstack_status",
        ]
        if column in hv.columns
    ]

    if not hv.empty:

        named_hv = (
            hv[
                display_columns
            ]
            .sort_values(
                [
                    "max_voltage_kv",
                    "name",
                ],
                ascending=[
                    False,
                    True,
                ],
                na_position="last",
            )
        )

        print(
            named_hv
            .head(50)
            .to_string(
                index=False
            )
        )

    print()
    print(
        f"Saved all substations:"
    )
    print(
        ALL_OUTPUT
    )

    print()
    print(
        f"Saved HV substations:"
    )
    print(
        HV_OUTPUT
    )

    print()
    print("=" * 70)
    print(
        "SUBSTATION EXTRACTION COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
