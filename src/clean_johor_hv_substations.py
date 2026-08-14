import hashlib
import re

import geopandas as gpd
import pandas as pd
import requests
import truststore

from config import PROCESSED_DIR


truststore.inject_into_ssl()


# ============================================================
# FILES
# ============================================================

ZONING_FILE = (
    PROCESSED_DIR /
    "johor_relevant_zoning.parquet"
)

SUBSTATION_FILE = (
    PROCESSED_DIR /
    "johor_substations.parquet"
)

OUTPUT_FILE = (
    PROCESSED_DIR /
    "johor_hv_substations_clean.parquet"
)

OUTPUT_CSV = (
    PROCESSED_DIR /
    "johor_hv_substations_clean.csv"
)


# Official PLANMalaysia district boundary layer
DISTRICT_URL = (
    "https://scharms.planmalaysia.gov.my/"
    "arcgis/rest/services/SCHARMS/"
    "Mobil_DataAsas/MapServer/2/query"
)

JOHOR_DISTRICTS = {
    "batu pahat",
    "johor bahru",
    "kluang",
    "kota tinggi",
    "kulai",
    "mersing",
    "muar",
    "pontian",
    "segamat",
    "tangkak",
}

# ============================================================
# HELPERS
# ============================================================

def normalize_text(value):

    if pd.isna(value):
        return ""

    return (
        str(value)
        .strip()
        .lower()
    )


def geometry_hash(geometry):

    if geometry is None:
        return None

    return hashlib.sha256(
        geometry.normalize().wkb
    ).hexdigest()


def normalize_operator(value):

    text = normalize_text(value)

    if text in {
        "tnb",
        "tenaga nasional",
        "tenaga nasional berhad",
    }:

        return "Tenaga Nasional Berhad"

    if not text:
        return None

    return str(value).strip()


# ============================================================
# DOWNLOAD OFFICIAL DISTRICT BOUNDARIES
# ============================================================

def get_johor_boundary():

    print()
    print(
        "Downloading official PLANMalaysia "
        "district boundaries..."
    )

    params = {
        "where": "1=1",
        "outFields": (
            "kod_negeri,"
            "kod_daerah,"
            "nama_daera"
        ),
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }

    response = requests.get(
        DISTRICT_URL,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    payload = response.json()

    if "error" in payload:
        raise RuntimeError(
            payload["error"]
        )

    districts = (
        gpd.GeoDataFrame
        .from_features(
            payload["features"],
            crs="EPSG:4326",
        )
    )

    print(
        f"PLANMalaysia district polygons "
        f"downloaded: {len(districts):,}"
    )

    districts[
        "_district_normalized"
    ] = (
        districts[
            "nama_daera"
        ]
        .apply(
            normalize_text
        )
    )

    johor_districts = (
        districts[
            districts[
                "_district_normalized"
            ]
            .isin(
                JOHOR_DISTRICTS
            )
        ]
        .copy()
    )

    matched_names = set(
        johor_districts[
            "_district_normalized"
        ]
    )

    missing = (
        JOHOR_DISTRICTS -
        matched_names
    )

    print()
    print("Matched Johor districts:")

    for name in sorted(
        johor_districts[
            "nama_daera"
        ]
        .dropna()
        .unique()
    ):
        print(
            f"  - {name}"
        )

    print()
    print(
        f"Johor district polygons matched: "
        f"{len(johor_districts)}"
    )

    # Hard safety check.
    # Do not silently build an incomplete Johor boundary.
    if missing:

        print()
        print(
            "ERROR — missing expected Johor districts:"
        )

        for name in sorted(missing):
            print(
                f"  - {name}"
            )

        raise RuntimeError(
            "Incomplete Johor district boundary."
        )

    if len(johor_districts) != 10:

        raise RuntimeError(
            f"Expected 10 Johor district polygons, "
            f"received {len(johor_districts)}."
        )

    johor_boundary = (
        johor_districts
        .geometry
        .union_all()
    )

    return johor_boundary


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "POWERSTACK — CLEAN JOHOR HV SUBSTATIONS"
    )
    print("=" * 70)

    zoning = gpd.read_parquet(
        ZONING_FILE
    )

    substations = gpd.read_parquet(
        SUBSTATION_FILE
    )

    print()
    print(
        f"Input mapped substations: "
        f"{len(substations):,}"
    )

    print(
        f"Input CRS: "
        f"{substations.crs}"
    )

    # --------------------------------------------------------
    # 1. Official Johor boundary
    # --------------------------------------------------------

    johor_boundary = (
        get_johor_boundary()
    )

    if substations.crs is None:

        raise RuntimeError(
            "Substation CRS is missing."
        )

    if (
        substations.crs
        .to_epsg()
        != 4326
    ):

        substations = (
            substations
            .to_crs(
                "EPSG:4326"
            )
        )

    # --------------------------------------------------------
    # 2. Spatially restrict to Johor
    # --------------------------------------------------------

    # Representative point works for:
    # Point
    # Polygon
    # MultiPolygon
    # LineString
    #
    # We use this only for administrative inclusion,
    # not for final distance calculations.

    representative_points = (
        substations
        .geometry
        .representative_point()
    )

    johor_mask = (
        representative_points
        .within(
            johor_boundary
        )
    )

    johor = (
        substations[
            johor_mask
        ]
        .copy()
    )

    print()
    print(
        f"Features spatially inside Johor: "
        f"{len(johor):,}"
    )

    print(
        f"Features excluded outside Johor: "
        f"{len(substations) - len(johor):,}"
    )

    # --------------------------------------------------------
    # 3. Remove non-canonical LineString representation
    # --------------------------------------------------------

    print()
    print(
        "Geometry types before cleaning:"
    )

    print(
        johor.geometry
        .geom_type
        .value_counts()
        .to_string()
    )

    canonical_geometry_types = {
        "Point",
        "Polygon",
        "MultiPolygon",
    }

    canonical = (
        johor[
            johor.geometry
            .geom_type
            .isin(
                canonical_geometry_types
            )
        ]
        .copy()
    )

    print()
    print(
        f"Canonical point/area features: "
        f"{len(canonical):,}"
    )

    # --------------------------------------------------------
    # 4. Keep explicit HV substations
    # --------------------------------------------------------

    hv = (
        canonical[
            canonical[
                "max_voltage_kv"
            ] >= 100
        ]
        .copy()
    )

    print(
        f"Explicit >=100 kV features: "
        f"{len(hv):,}"
    )

    # --------------------------------------------------------
    # 5. Exact geometry deduplication
    # --------------------------------------------------------

    hv[
        "geometry_hash"
    ] = (
        hv.geometry
        .apply(
            geometry_hash
        )
    )

    hv[
        "exact_geometry_duplicate_count"
    ] = (
        hv.groupby(
            "geometry_hash"
        )[
            "geometry_hash"
        ]
        .transform("size")
    )

    before_dedupe = len(hv)

    hv = (
        hv
        .sort_values(
            [
                "geometry_hash",
                "name",
            ],
            na_position="last",
        )
        .drop_duplicates(
            subset="geometry_hash",
            keep="first",
        )
        .copy()
    )

    print()
    print(
        f"Exact duplicate geometries removed: "
        f"{before_dedupe - len(hv):,}"
    )

    # --------------------------------------------------------
    # 6. Operator normalization
    # --------------------------------------------------------

    hv[
        "operator_normalized"
    ] = (
        hv[
            "operator"
        ]
        .apply(
            normalize_operator
        )
    )

    # --------------------------------------------------------
    # 7. Useful evidence flags
    # --------------------------------------------------------

    hv[
        "mapped_transmission_substation"
    ] = (
        hv[
            "substation"
        ]
        .astype(str)
        .str.lower()
        .eq(
            "transmission"
        )
    )

    hv[
        "pmu_name_signal"
    ] = (
        hv[
            "name"
        ]
        .fillna("")
        .str.contains(
            "Pencawang Masuk Utama",
            case=False,
            regex=False,
        )
    )

    # IMPORTANT:
    # pmu_name_signal is only based on the mapped name.
    # It is not independent TNB verification.

    hv[
        "pmu_verification_status"
    ] = "NOT_INDEPENDENTLY_VERIFIED"

    hv[
        "capacity_status"
    ] = "NOT_FOUND"

    hv[
        "cleanup_fact_type"
    ] = "DERIVED"

    # --------------------------------------------------------
    # 8. Save
    # --------------------------------------------------------

    hv.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    csv_columns = [
        column
        for column in hv.columns
        if column != "geometry"
    ]

    hv[
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
        "CLEAN JOHOR HV SUBSTATION SUMMARY"
    )
    print("=" * 70)

    print()
    print(
        f"Canonical Johor HV substations: "
        f"{len(hv):,}"
    )

    print()
    print(
        "Maximum-voltage distribution:"
    )

    print(
        hv[
            "max_voltage_kv"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print(
        "Transmission classification:"
    )

    print(
        hv[
            "mapped_transmission_substation"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print()
    print(
        "Operator normalized:"
    )

    print(
        hv[
            "operator_normalized"
        ]
        .value_counts(
            dropna=False
        )
        .head(20)
        .to_string()
    )

    print()
    print(
        "PMU name signal:"
    )

    print(
        hv[
            "pmu_name_signal"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "NAMED JOHOR HV SUBSTATIONS"
    )
    print("-" * 70)

    columns = [
        column
        for column in [
            "name",
            "operator_normalized",
            "substation",
            "voltage",
            "max_voltage_kv",
            "ref",
            "pmu_name_signal",
        ]
        if column in hv.columns
    ]

    print(
        hv[
            columns
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
        .to_string(
            index=False
        )
    )

    print()
    print(
        f"Saved:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print("=" * 70)
    print(
        "SUBSTATION CLEANING COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()