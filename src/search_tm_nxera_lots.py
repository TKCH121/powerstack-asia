"""Diagnostic cadastral-lot search; never treat candidates as verified parcels."""

import json

import geopandas as gpd
import pandas as pd
import requests
import truststore

from config import PROCESSED_DIR


truststore.inject_into_ssl()


# ============================================================
# OFFICIAL PLANMALAYSIA JOHOR LOT LAYER
# ============================================================

LOT_URL = (
    "https://scharms.planmalaysia.gov.my/"
    "arcgis/rest/services/iPLAN/"
    "LOT_01/MapServer/0/query"
)


# ============================================================
# EXISTING POWERSTACK FILES
# ============================================================

ZONING_SEARCH_FILE = (
    PROCESSED_DIR /
    "tm_nxera_full_zoning_search.geojson"
)


# ============================================================
# OUTPUT FILES
# ============================================================

OUTPUT_GEOJSON = (
    PROCESSED_DIR /
    "tm_nxera_lot_search.geojson"
)

OUTPUT_CSV = (
    PROCESSED_DIR /
    "tm_nxera_lot_search.csv"
)


# ============================================================
# DOCUMENTED TM NXERA LAND AREA
# ============================================================

# Singtel filing:
#
# 168,959 square metres
# = 16.8959 hectares

TARGET_AREA_HA = 16.8959


# ============================================================
# IMPORTANT ZONING CANDIDATE
# ============================================================

# From our previous full-zoning search:
#
# Komersial
# 15.6969 ha
# Pulai
# representative point:
# 1.430112, 103.614717

TARGET_ZONING_OBJECTID = 1374519


# ============================================================
# SEARCH AREA
# ============================================================

# Keep the same broader search envelope.
#
# We deliberately do not restrict the lot query to
# only the zoning polygon yet.

WEST = 103.608
SOUTH = 1.423
EAST = 103.627
NORTH = 1.448


# ============================================================
# DOWNLOAD LOT DATA
# ============================================================

def download_lots():

    print()
    print(
        "Querying official PLANMalaysia Johor lot layer..."
    )

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
                "NEGERI,"
                "DAERAH,"
                "MUKIM,"
                "SEKSYEN,"
                "LOT,"
                "UPI,"
                "KELUASAN"
            ),

        "returnGeometry":
            "true",

        "outSR":
            "4326",

        "f":
            "geojson",
    }

    response = requests.get(
        LOT_URL,
        params=params,
        timeout=180,
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
            "PLANMalaysia lot query failed."
        )

    features = payload.get(
        "features",
        []
    )

    if not features:

        raise RuntimeError(
            "No cadastral lots returned "
            "inside the search area."
        )

    lots = (
        gpd.GeoDataFrame
        .from_features(
            features,
            crs="EPSG:4326",
        )
    )

    return lots


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "POWERSTACK — TM NXERA CADASTRAL LOT SEARCH"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Download lots
    # --------------------------------------------------------

    lots = download_lots()

    print()
    print(
        f"Cadastral lots returned: "
        f"{len(lots):,}"
    )

    print(
        f"CRS: {lots.crs}"
    )

    # --------------------------------------------------------
    # 2. Calculate actual geometry area ourselves
    # --------------------------------------------------------

    lots_projected = (
        lots
        .to_crs(
            "EPSG:3375"
        )
        .copy()
    )

    lots_projected[
        "calculated_area_ha"
    ] = (
        lots_projected
        .geometry
        .area
        /
        10_000
    )

    lots_projected[
        "area_difference_ha"
    ] = (
        lots_projected[
            "calculated_area_ha"
        ]
        -
        TARGET_AREA_HA
    ).abs()

    lots_projected[
        "area_difference_pct"
    ] = (
        lots_projected[
            "area_difference_ha"
        ]
        /
        TARGET_AREA_HA
        *
        100
    )

    # --------------------------------------------------------
    # 3. Representative coordinates
    # --------------------------------------------------------

    reps = (
        lots_projected
        .geometry
        .representative_point()
        .to_crs(
            "EPSG:4326"
        )
    )

    lots_projected[
        "candidate_lat"
    ] = reps.y

    lots_projected[
        "candidate_lon"
    ] = reps.x

    # --------------------------------------------------------
    # 4. Load our strong commercial zoning candidate
    # --------------------------------------------------------

    if not ZONING_SEARCH_FILE.exists():

        raise FileNotFoundError(
            f"Missing zoning search file: "
            f"{ZONING_SEARCH_FILE}"
        )

    zoning = gpd.read_file(
        ZONING_SEARCH_FILE
    )

    zoning_target = (
        zoning[
            pd.to_numeric(
                zoning[
                    "OBJECTID"
                ],
                errors="coerce",
            )
            ==
            TARGET_ZONING_OBJECTID
        ]
        .copy()
    )

    if zoning_target.empty:

        raise RuntimeError(
            f"Could not find zoning OBJECTID "
            f"{TARGET_ZONING_OBJECTID}."
        )

    print()
    print(
        "Loaded target commercial zoning polygon:"
    )

    print(
        f"  OBJECTID: "
        f"{TARGET_ZONING_OBJECTID}"
    )

    print(
        f"  zoning: "
        f"{zoning_target.iloc[0]['gunatanah1']}"
    )

    # --------------------------------------------------------
    # 5. Project zoning polygon into metres
    # --------------------------------------------------------

    zoning_target = (
        zoning_target
        .to_crs(
            "EPSG:3375"
        )
    )

    target_geometry = (
        zoning_target
        .geometry
        .iloc[0]
    )

    # --------------------------------------------------------
    # 6. Calculate each lot's overlap with zoning candidate
    # --------------------------------------------------------

    lots_projected[
        "intersection_area_ha"
    ] = (
        lots_projected
        .geometry
        .intersection(
            target_geometry
        )
        .area
        /
        10_000
    )

    lots_projected[
        "overlap_pct_of_lot"
    ] = (
        lots_projected[
            "intersection_area_ha"
        ]
        /
        lots_projected[
            "calculated_area_ha"
        ]
        *
        100
    )

    lots_projected[
        "intersects_target_zoning"
    ] = (
        lots_projected[
            "intersection_area_ha"
        ]
        >
        0
    )

    # Distance from lot geometry to commercial
    # zoning polygon.
    #
    # If they intersect, this is zero.

    lots_projected[
        "distance_to_target_zoning_m"
    ] = (
        lots_projected
        .geometry
        .distance(
            target_geometry
        )
    )

    # --------------------------------------------------------
    # 7. Show lots closest to documented 16.8959 ha
    # --------------------------------------------------------

    display_columns = [
        column
        for column in [
            "OBJECTID",
            "LOT",
            "UPI",
            "NEGERI",
            "DAERAH",
            "MUKIM",
            "SEKSYEN",
            "KELUASAN",
            "calculated_area_ha",
            "area_difference_ha",
            "area_difference_pct",
            "intersection_area_ha",
            "overlap_pct_of_lot",
            "intersects_target_zoning",
            "distance_to_target_zoning_m",
            "candidate_lat",
            "candidate_lon",
        ]
        if column in lots_projected.columns
    ]

    print()
    print("=" * 70)
    print(
        "LOTS CLOSEST TO DOCUMENTED 16.8959 HA"
    )
    print("=" * 70)

    print()

    closest_area = (
        lots_projected
        .sort_values(
            "area_difference_ha"
        )
        .head(30)
    )

    print(
        closest_area[
            display_columns
        ]
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 8. Lots overlapping the commercial zoning polygon
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "LOTS OVERLAPPING COMMERCIAL ZONING CANDIDATE"
    )
    print("=" * 70)

    print()

    overlapping = (
        lots_projected[
            lots_projected[
                "intersects_target_zoning"
            ]
        ]
        .copy()
    )

    overlapping = (
        overlapping
        .sort_values(
            [
                "intersection_area_ha",
                "area_difference_ha",
            ],
            ascending=[
                False,
                True,
            ],
        )
    )

    if overlapping.empty:

        print(
            "NO CADASTRAL LOTS OVERLAP "
            "THE TARGET ZONING POLYGON"
        )

    else:

        print(
            overlapping[
                display_columns
            ]
            .head(50)
            .to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # 9. Serious candidate lots
    # --------------------------------------------------------

    # This is exploratory only.
    #
    # A lot enters this screen if:
    #
    # - calculated area is 12–22 ha, OR
    # - it materially overlaps our commercial polygon.
    #
    # We are NOT declaring any result the Nxera parcel.

    serious = (
        lots_projected[
            (
                (
                    lots_projected[
                        "calculated_area_ha"
                    ]
                    >= 12
                )
                &
                (
                    lots_projected[
                        "calculated_area_ha"
                    ]
                    <= 22
                )
            )
            |
            (
                lots_projected[
                    "overlap_pct_of_lot"
                ]
                >= 50
            )
        ]
        .copy()
    )

    serious[
        "candidate_score"
    ] = (

        # Smaller area error is better.
        (
            1
            /
            (
                1
                +
                serious[
                    "area_difference_ha"
                ]
            )
        )

        +

        # Strong zoning overlap is useful.
        (
            serious[
                "overlap_pct_of_lot"
            ]
            /
            100
        )
    )

    serious = (
        serious
        .sort_values(
            "candidate_score",
            ascending=False,
        )
    )

    print()
    print("=" * 70)
    print(
        "SERIOUS TM NXERA LOT CANDIDATES"
    )
    print("=" * 70)

    print()

    serious_columns = (
        display_columns
        +
        [
            "candidate_score"
        ]
    )

    print(
        serious[
            serious_columns
        ]
        .head(30)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 10. Save everything
    # --------------------------------------------------------

    output_geo = (
        lots_projected
        .to_crs(
            "EPSG:4326"
        )
    )

    output_geo.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    (
        lots_projected
        .drop(
            columns="geometry"
        )
        .to_csv(
            OUTPUT_CSV,
            index=False,
        )
    )

    print()
    print(
        f"Saved lot GeoJSON:"
    )

    print(
        OUTPUT_GEOJSON
    )

    print()

    print(
        f"Saved lot CSV:"
    )

    print(
        OUTPUT_CSV
    )

    print()
    print("=" * 70)
    print(
        "TM NXERA CADASTRAL LOT SEARCH COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
