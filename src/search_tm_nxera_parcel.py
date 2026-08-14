import json

import geopandas as gpd
import pandas as pd
import requests
import truststore

from config import PROCESSED_DIR


truststore.inject_into_ssl()


# ============================================================
# OFFICIAL PLANMALAYSIA JOHOR ZONING SERVICE
# ============================================================

ZONING_URL = (
    "https://scharms.planmalaysia.gov.my/"
    "arcgis/rest/services/iPLAN/"
    "GTzoning_01/MapServer/0/query"
)


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_GEOJSON = (
    PROCESSED_DIR /
    "tm_nxera_full_zoning_search.geojson"
)

OUTPUT_CSV = (
    PROCESSED_DIR /
    "tm_nxera_full_zoning_search.csv"
)


# ============================================================
# DOCUMENTED LAND AREA
# ============================================================

# Singtel disclosure:
# 168,959 square metres
TARGET_AREA_HA = 16.8959

MIN_AREA_HA = 10.0
MAX_AREA_HA = 25.0


# ============================================================
# TM NXERA SEARCH AREA
# ============================================================
#
# Based on the cluster established from:
#
# Eco Botanic
# Eko Galleria
# University of Reading Malaysia
# EduCity
# Dataran Iskandar Puteri
# Jalan Kampung Lalang
#
# This is intentionally a reasonably wide envelope.
# ============================================================

WEST = 103.608
SOUTH = 1.423
EAST = 103.627
NORTH = 1.448


def download_full_zoning():

    print()
    print(
        "Querying full PLANMalaysia zoning layer..."
    )

    # ArcGIS envelope format:
    #
    # xmin,ymin,xmax,ymax

    geometry = (
        f"{WEST},"
        f"{SOUTH},"
        f"{EAST},"
        f"{NORTH}"
    )

    params = {

        "where":
            "1=1",

        "geometry":
            geometry,

        "geometryType":
            "esriGeometryEnvelope",

        "inSR":
            "4326",

        "spatialRel":
            "esriSpatialRelIntersects",

        "outFields":
            (
                "OBJECTID,"
                "gunatanah1,"
                "kod_gtn,"
                "tahun_data,"
                "lot_upi,"
                "luas_hekta,"
                "nama_ranca,"
                "negeri_nam,"
                "daerah_nam,"
                "mukim_name,"
                "seksyen_na,"
                "pbt_name"
            ),

        "returnGeometry":
            "true",

        "outSR":
            "4326",

        "f":
            "geojson",
    }

    response = requests.get(
        ZONING_URL,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    payload = response.json()

    if "error" in payload:

        print()
        print(
            "ARCGIS ERROR:"
        )

        print(
            json.dumps(
                payload["error"],
                indent=2,
            )
        )

        raise RuntimeError(
            "PLANMalaysia zoning query failed."
        )

    features = payload.get(
        "features",
        []
    )

    if not features:

        raise RuntimeError(
            "PLANMalaysia returned no zoning "
            "features in the search area."
        )

    zoning = (
        gpd.GeoDataFrame
        .from_features(
            features,
            crs="EPSG:4326",
        )
    )

    return zoning


def main():

    print("=" * 70)
    print(
        "POWERSTACK — TM NXERA FULL ZONING SEARCH"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Download ALL zoning classes in search area
    # --------------------------------------------------------

    zoning = (
        download_full_zoning()
    )

    print()
    print(
        f"Full zoning polygons returned: "
        f"{len(zoning):,}"
    )

    print(
        f"CRS: {zoning.crs}"
    )

    # --------------------------------------------------------
    # 2. Calculate area using projected CRS
    # --------------------------------------------------------

    projected = (
        zoning
        .to_crs(
            "EPSG:3375"
        )
        .copy()
    )

    projected[
        "calculated_area_ha"
    ] = (
        projected
        .geometry
        .area
        /
        10_000
    )

    projected[
        "area_difference_ha"
    ] = (
        projected[
            "calculated_area_ha"
        ]
        -
        TARGET_AREA_HA
    ).abs()

    # --------------------------------------------------------
    # 3. Representative coordinates
    # --------------------------------------------------------

    representative = (
        projected
        .geometry
        .representative_point()
        .to_crs(
            "EPSG:4326"
        )
    )

    projected[
        "candidate_lat"
    ] = (
        representative.y
    )

    projected[
        "candidate_lon"
    ] = (
        representative.x
    )

    # --------------------------------------------------------
    # 4. Show ALL zoning categories
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "ALL ZONING CATEGORIES IN SEARCH AREA"
    )
    print("=" * 70)

    print()

    print(
        projected[
            "gunatanah1"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # --------------------------------------------------------
    # 5. Particularly interesting categories
    # --------------------------------------------------------

    interesting_categories = [
        "Komersial",
        "Pembangunan Bercampur",
        "Industri",
        "Infrastruktur dan Utiliti",
        "Tanah Kosong",
    ]

    print()
    print("=" * 70)
    print(
        "POTENTIALLY RELEVANT ZONING CLASSES"
    )
    print("=" * 70)

    relevant = (
        projected[
            projected[
                "gunatanah1"
            ]
            .isin(
                interesting_categories
            )
        ]
        .copy()
    )

    print()

    print(
        relevant[
            "gunatanah1"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # --------------------------------------------------------
    # 6. 10–25 hectare candidate polygons
    # --------------------------------------------------------

    candidates = (
        projected[
            (
                projected[
                    "calculated_area_ha"
                ]
                >= MIN_AREA_HA
            )
            &
            (
                projected[
                    "calculated_area_ha"
                ]
                <= MAX_AREA_HA
            )
        ]
        .copy()
    )

    candidates = (
        candidates
        .sort_values(
            "area_difference_ha"
        )
    )

    display_columns = [
        column
        for column in [
            "OBJECTID",
            "gunatanah1",
            "kod_gtn",
            "tahun_data",
            "lot_upi",
            "luas_hekta",
            "calculated_area_ha",
            "area_difference_ha",
            "nama_ranca",
            "daerah_nam",
            "mukim_name",
            "pbt_name",
            "candidate_lat",
            "candidate_lon",
        ]
        if column in projected.columns
    ]

    print()
    print("=" * 70)
    print(
        "10–25 HA ZONING POLYGONS"
    )
    print("=" * 70)

    print()

    if candidates.empty:

        print(
            "NO 10–25 HA ZONING POLYGONS FOUND"
        )

    else:

        print(
            candidates[
                display_columns
            ]
            .head(50)
            .to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # 7. Closest zoning polygon areas
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "CLOSEST POLYGON AREAS TO 16.8959 HA"
    )
    print("=" * 70)

    print()

    closest = (
        projected
        .sort_values(
            "area_difference_ha"
        )
        .head(30)
    )

    print(
        closest[
            display_columns
        ]
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 8. Save full result
    # --------------------------------------------------------

    zoning.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    csv_output = (
        projected
        .drop(
            columns="geometry"
        )
    )

    csv_output.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print()
    print(
        f"Saved full search GeoJSON:"
    )

    print(
        OUTPUT_GEOJSON
    )

    print()

    print(
        f"Saved full search CSV:"
    )

    print(
        OUTPUT_CSV
    )

    print()
    print("=" * 70)
    print(
        "TM NXERA FULL ZONING SEARCH COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()