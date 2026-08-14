"""Diagnostic current-state comparison, not an ex-ante historical model.

This script preserves the GDS and Yondr/Sedenak findings, including the
look-ahead-leakage warning. Its distances use a current OSM snapshot and must
not be treated as pre-decision predictors or a site pass/fail rule.
"""

import geopandas as gpd
import pandas as pd

from config import MANUAL_DIR, RAW_DIR, PROCESSED_DIR
from powerstack_utils import PROJECTED_CRS, has_voltage


# ============================================================
# DIRECTORIES / FILES
# ============================================================

PROJECT_FILE = (
    MANUAL_DIR /
    "dc_projects_seed.csv"
)

LOCATION_FILE = (
    MANUAL_DIR /
    "dc_project_locations_seed.csv"
)

NAMED_OSM_FILE = (
    RAW_DIR /
    "johor_named_features.geojson"
)

GRID_FILE = (
    PROCESSED_DIR /
    "johor_hv_power_lines.parquet"
)

SUBSTATION_FILE = (
    PROCESSED_DIR /
    "johor_hv_substations_clean.parquet"
)

CANDIDATE_FILE = (
    PROCESSED_DIR /
    "johor_powerstack_site_features_v01.parquet"
)

OUTPUT_FILE = (
    PROCESSED_DIR /
    "historical_project_grid_calibration_v01.csv"
)


# ============================================================
# HISTORICAL PROJECT GEOMETRY PROXIES
# ============================================================
#
# These are based on the OSM objects we already inspected.
#
# IMPORTANT:
# These are NOT claimed to be exact DC parcel boundaries.
# ============================================================

PROJECT_GEOMETRIES = {

    "DC-JHR-001": {

        "osm_name":
            "Nusajaya Tech Park",

        "osm_type":
            "way",

        "osm_id":
            "648730398",

        "geometry_type":
            "MultiPolygon",

        "geometry_precision":
            "PARK_PROXY",

        "geometry_fact_type":
            "DERIVED",
    },

    "DC-JHR-002": {

        "osm_name":
            "STePEast Data Hub",

        "osm_type":
            "way",

        "osm_id":
            "1544740076",

        "geometry_type":
            "MultiPolygon",

        "geometry_precision":
            "PARK_SECTION_PROXY",

        "geometry_fact_type":
            "INFERRED",
    },
}


# ============================================================
# HELPERS
# ============================================================

def nearest_feature(
    features,
    geometry,
):
    """
    Find the nearest feature to a geometry.

    Returns:

        distance_km
        nearest feature row
    """

    if features.empty:

        return None, None

    distances = (
        features.geometry
        .distance(
            geometry
        )
    )

    position = (
        distances
        .to_numpy()
        .argmin()
    )

    distance_m = (
        distances.iloc[
            position
        ]
    )

    nearest_row = (
        features.iloc[
            position
        ]
    )

    return (
        distance_m / 1000,
        nearest_row,
    )


def closeness_percentile(
    candidate_series,
    project_distance_km,
):
    """
    Return the percentage of candidate sites that
    are FARTHER from the asset than this project.

    Higher = better proximity.

    Example:

        90

    means the historical project is closer than
    approximately 90% of candidate sites.
    """

    if project_distance_km is None:

        return None

    values = (
        pd.to_numeric(
            candidate_series,
            errors="coerce",
        )
        .dropna()
    )

    if values.empty:

        return None

    percentile = (
        (
            values
            >= project_distance_km
        )
        .mean()
        *
        100
    )

    return percentile


def safe_value(
    row,
    column,
):

    if row is None:

        return None

    if column not in row.index:

        return None

    value = row[
        column
    ]

    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):

        pass

    return value


def select_project_geometry(
    osm,
    project_id,
    specification,
):
    """
    Select exactly the OSM MultiPolygon that we
    previously inspected manually.
    """

    if "@type" not in osm.columns:

        raise RuntimeError(
            "OSM file is missing @type."
        )

    if "@id" not in osm.columns:

        raise RuntimeError(
            "OSM file is missing @id."
        )

    osm_id = (
        osm[
            "@id"
        ]
        .astype(str)
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
    )

    mask = (

        osm[
            "@type"
        ]
        .astype(str)
        .eq(
            specification[
                "osm_type"
            ]
        )

        &

        osm_id.eq(
            specification[
                "osm_id"
            ]
        )

        &

        osm.geometry
        .geom_type
        .eq(
            specification[
                "geometry_type"
            ]
        )
    )

    matches = (
        osm[
            mask
        ]
        .copy()
    )

    if len(matches) != 1:

        raise RuntimeError(
            f"{project_id}: expected exactly "
            f"1 geometry, found {len(matches)}."
        )

    return matches.iloc[0]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "POWERSTACK — HISTORICAL PROJECT CALIBRATION"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Load project metadata
    # --------------------------------------------------------

    projects = pd.read_csv(
        PROJECT_FILE
    )

    locations = pd.read_csv(
        LOCATION_FILE
    )

    print()
    print(
        f"Historical projects loaded: "
        f"{len(projects):,}"
    )

    # --------------------------------------------------------
    # 2. Load geospatial datasets
    # --------------------------------------------------------

    print()
    print(
        "Loading OSM named geometries..."
    )

    osm = gpd.read_file(
        NAMED_OSM_FILE
    )

    grid = gpd.read_parquet(
        GRID_FILE
    )

    substations = gpd.read_parquet(
        SUBSTATION_FILE
    )

    candidates = gpd.read_parquet(
        CANDIDATE_FILE
    )

    print(
        f"Candidate industrial sites: "
        f"{len(candidates):,}"
    )

    print(
        f"HV grid features: "
        f"{len(grid):,}"
    )

    print(
        f"HV substations: "
        f"{len(substations):,}"
    )

    # --------------------------------------------------------
    # 3. Reproject into metres
    # --------------------------------------------------------

    osm = osm.to_crs(
        PROJECTED_CRS
    )

    grid = grid.to_crs(
        PROJECTED_CRS
    )

    substations = (
        substations
        .to_crs(
            PROJECTED_CRS
        )
    )

    candidates = (
        candidates
        .to_crs(
            PROJECTED_CRS
        )
    )

    # --------------------------------------------------------
    # 4. Pre-build voltage subsets
    # --------------------------------------------------------

    grid_by_voltage = {}

    substation_by_voltage = {}

    for voltage_kv in [
        132,
        275,
        500,
    ]:

        grid_by_voltage[
            voltage_kv
        ] = (
            grid[
                grid[
                    "voltage"
                ]
                .apply(
                    lambda value:
                    has_voltage(
                        value,
                        voltage_kv,
                    )
                )
            ]
            .copy()
        )

        substation_by_voltage[
            voltage_kv
        ] = (
            substations[
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
            ]
            .copy()
        )

    transmission_substations = (
        substations[
            substations[
                "mapped_transmission_substation"
            ]
            .fillna(False)
        ]
        .copy()
    )

    # --------------------------------------------------------
    # 5. Calibrate each usable historical project
    # --------------------------------------------------------

    output_rows = []

    for (
        project_id,
        specification,
    ) in (
        PROJECT_GEOMETRIES.items()
    ):

        print()
        print("=" * 70)

        project_record = (
            projects[
                projects[
                    "project_id"
                ]
                .eq(
                    project_id
                )
            ]
        )

        if project_record.empty:

            raise RuntimeError(
                f"Could not find {project_id} "
                f"in dc_projects_seed.csv."
            )

        project_record = (
            project_record.iloc[0]
        )

        location_record = (
            locations[
                locations[
                    "project_id"
                ]
                .eq(
                    project_id
                )
            ]
        )

        if not location_record.empty:

            location_record = (
                location_record.iloc[0]
            )

        else:

            location_record = None

        project_geometry_row = (
            select_project_geometry(
                osm,
                project_id,
                specification,
            )
        )

        project_geometry = (
            project_geometry_row.geometry
        )

        representative_point = (
            project_geometry
            .representative_point()
        )

        proxy_area_ha = (
            project_geometry.area
            /
            10_000
        )

        project_name = (
            project_record[
                "project_name"
            ]
        )

        print(
            f"{project_id} — "
            f"{project_name}"
        )

        print("=" * 70)

        print()
        print(
            f"Geometry proxy: "
            f"{specification['osm_name']}"
        )

        print(
            f"Precision: "
            f"{specification['geometry_precision']}"
        )

        print(
            f"Proxy geometry area: "
            f"{proxy_area_ha:.2f} ha"
        )

        result = {

            "project_id":
                project_id,

            "project_name":
                project_name,

            "operator_at_event":
                project_record[
                    "operator_at_event"
                ],

            "current_operator":
                project_record[
                    "current_operator"
                ],

            "announced_it_mw":
                project_record[
                    "announced_it_mw"
                ],

            "secured_supply_mw":
                project_record[
                    "secured_supply_mw"
                ],

            "geometry_proxy_name":
                specification[
                    "osm_name"
                ],

            "geometry_precision":
                specification[
                    "geometry_precision"
                ],

            "geometry_fact_type":
                specification[
                    "geometry_fact_type"
                ],

            "osm_type":
                specification[
                    "osm_type"
                ],

            "osm_id":
                specification[
                    "osm_id"
                ],

            "proxy_area_ha":
                proxy_area_ha,
        }

        # ====================================================
        # GRID LINE DISTANCES
        # ====================================================

        print()
        print(
            "GRID LINE PROXIMITY"
        )

        print("-" * 70)

        for voltage_kv in [
            132,
            275,
            500,
        ]:

            target_grid = (
                grid_by_voltage[
                    voltage_kv
                ]
            )

            edge_distance, edge_row = (
                nearest_feature(
                    target_grid,
                    project_geometry,
                )
            )

            point_distance, _ = (
                nearest_feature(
                    target_grid,
                    representative_point,
                )
            )

            candidate_column = (
                f"distance_{voltage_kv}kv_km"
            )

            percentile = (
                closeness_percentile(
                    candidates[
                        candidate_column
                    ],
                    edge_distance,
                )
            )

            result[
                f"distance_{voltage_kv}kv_line_edge_km"
            ] = edge_distance

            result[
                f"distance_{voltage_kv}kv_line_point_km"
            ] = point_distance

            result[
                f"proximity_percentile_{voltage_kv}kv_line"
            ] = percentile

            result[
                f"nearest_{voltage_kv}kv_line_name"
            ] = safe_value(
                edge_row,
                "name",
            )

            result[
                f"nearest_{voltage_kv}kv_line_voltage"
            ] = safe_value(
                edge_row,
                "voltage",
            )

            print(
                f"{voltage_kv} kV line:"
            )

            print(
                f"  polygon edge: "
                f"{edge_distance:.2f} km"
            )

            print(
                f"  representative point: "
                f"{point_distance:.2f} km"
            )

            print(
                f"  proximity percentile: "
                f"{percentile:.1f}"
            )

        # ====================================================
        # ANY HV SUBSTATION
        # ====================================================

        hv_edge_distance, hv_row = (
            nearest_feature(
                substations,
                project_geometry,
            )
        )

        hv_point_distance, _ = (
            nearest_feature(
                substations,
                representative_point,
            )
        )

        hv_percentile = (
            closeness_percentile(
                candidates[
                    "distance_hv_substation_km"
                ],
                hv_edge_distance,
            )
        )

        result[
            "distance_hv_substation_edge_km"
        ] = hv_edge_distance

        result[
            "distance_hv_substation_point_km"
        ] = hv_point_distance

        result[
            "proximity_percentile_hv_substation"
        ] = hv_percentile

        result[
            "nearest_hv_substation_name"
        ] = safe_value(
            hv_row,
            "name",
        )

        result[
            "nearest_hv_substation_voltage"
        ] = safe_value(
            hv_row,
            "voltage",
        )

        # ====================================================
        # TRANSMISSION SUBSTATION
        # ====================================================

        (
            transmission_edge_distance,
            transmission_row,
        ) = nearest_feature(
            transmission_substations,
            project_geometry,
        )

        (
            transmission_point_distance,
            _,
        ) = nearest_feature(
            transmission_substations,
            representative_point,
        )

        transmission_percentile = (
            closeness_percentile(
                candidates[
                    "distance_transmission_substation_km"
                ],
                transmission_edge_distance,
            )
        )

        result[
            "distance_transmission_substation_edge_km"
        ] = transmission_edge_distance

        result[
            "distance_transmission_substation_point_km"
        ] = transmission_point_distance

        result[
            "proximity_percentile_transmission_substation"
        ] = transmission_percentile

        result[
            "nearest_transmission_substation_name"
        ] = safe_value(
            transmission_row,
            "name",
        )

        # ====================================================
        # VOLTAGE-SPECIFIC SUBSTATIONS
        # ====================================================

        print()
        print(
            "SUBSTATION PROXIMITY"
        )

        print("-" * 70)

        for voltage_kv in [
            132,
            275,
            500,
        ]:

            target_substations = (
                substation_by_voltage[
                    voltage_kv
                ]
            )

            (
                edge_distance,
                edge_row,
            ) = nearest_feature(
                target_substations,
                project_geometry,
            )

            (
                point_distance,
                _,
            ) = nearest_feature(
                target_substations,
                representative_point,
            )

            candidate_column = (
                f"distance_{voltage_kv}kv_substation_km"
            )

            percentile = (
                closeness_percentile(
                    candidates[
                        candidate_column
                    ],
                    edge_distance,
                )
            )

            result[
                f"distance_{voltage_kv}kv_substation_edge_km"
            ] = edge_distance

            result[
                f"distance_{voltage_kv}kv_substation_point_km"
            ] = point_distance

            result[
                f"proximity_percentile_{voltage_kv}kv_substation"
            ] = percentile

            result[
                f"nearest_{voltage_kv}kv_substation_name"
            ] = safe_value(
                edge_row,
                "name",
            )

            result[
                f"nearest_{voltage_kv}kv_substation_voltage"
            ] = safe_value(
                edge_row,
                "voltage",
            )

            print(
                f"{voltage_kv} kV substation:"
            )

            print(
                f"  polygon edge: "
                f"{edge_distance:.2f} km"
            )

            print(
                f"  representative point: "
                f"{point_distance:.2f} km"
            )

            print(
                f"  proximity percentile: "
                f"{percentile:.1f}"
            )

            print(
                f"  nearest: "
                f"{safe_value(edge_row, 'name')}"
            )

        output_rows.append(
            result
        )

    # --------------------------------------------------------
    # 6. Save calibration results
    # --------------------------------------------------------

    output = pd.DataFrame(
        output_rows
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # 7. Compact comparison table
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "HISTORICAL CALIBRATION COMPARISON"
    )
    print("=" * 70)

    comparison_columns = [
        "project_id",
        "project_name",

        "distance_275kv_line_edge_km",
        "proximity_percentile_275kv_line",

        "distance_275kv_substation_edge_km",
        "proximity_percentile_275kv_substation",

        "distance_transmission_substation_edge_km",
        "proximity_percentile_transmission_substation",
    ]

    print()
    print(
        output[
            comparison_columns
        ]
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 8. TM Nxera reminder
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "TM NXERA STATUS"
    )
    print("=" * 70)

    print()
    print(
        "DC-JHR-003 was intentionally not calibrated."
    )

    print(
        "Its exact plot identity is verified, but an "
        "authoritative project geometry is still NOT_FOUND."
    )

    print(
        "No guessed city centroid was used."
    )

    print()
    print(
        f"Saved calibration table:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print("=" * 70)
    print(
        "HISTORICAL PROJECT CALIBRATION COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
