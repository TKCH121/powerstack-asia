import hashlib

import geopandas as gpd
import pandas as pd

from config import PROCESSED_DIR


INPUT_FILE = (
    PROCESSED_DIR /
    "johor_industrial_grid_features.parquet"
)

AUDIT_FILE = (
    PROCESSED_DIR /
    "industrial_duplicate_audit.csv"
)


def geometry_hash(geometry):
    """
    Create a stable identifier from the polygon geometry.

    Two polygons with identical geometry should therefore
    receive the same geometry_hash.
    """

    if geometry is None:
        return None

    return hashlib.sha256(
        geometry.normalize().wkb
    ).hexdigest()


def main():

    print("=" * 70)
    print("POWERSTACK — INDUSTRIAL SITE DUPLICATE AUDIT")
    print("=" * 70)

    sites = gpd.read_parquet(
        INPUT_FILE
    )

    print()
    print(
        f"Candidate records loaded: "
        f"{len(sites):,}"
    )

    # --------------------------------------------------
    # 1. Create geometry fingerprint
    # --------------------------------------------------

    sites[
        "geometry_hash"
    ] = (
        sites.geometry
        .apply(
            geometry_hash
        )
    )

    # --------------------------------------------------
    # 2. Count exact geometry duplicates
    # --------------------------------------------------

    sites[
        "geometry_duplicate_count"
    ] = (
        sites.groupby(
            "geometry_hash"
        )[
            "geometry_hash"
        ]
        .transform("size")
    )

    duplicates = (
        sites[
            sites[
                "geometry_duplicate_count"
            ] > 1
        ]
        .copy()
    )

    duplicate_groups = (
        duplicates[
            "geometry_hash"
        ]
        .nunique()
    )

    duplicate_rows = (
        len(duplicates)
    )

    unique_geometries = (
        sites[
            "geometry_hash"
        ]
        .nunique()
    )

    print()
    print("EXACT GEOMETRY DUPLICATES")
    print("-" * 70)

    print(
        f"Rows involved in duplicate groups: "
        f"{duplicate_rows:,}"
    )

    print(
        f"Duplicate geometry groups: "
        f"{duplicate_groups:,}"
    )

    print(
        f"Unique geometries: "
        f"{unique_geometries:,}"
    )

    print(
        f"Raw candidate rows: "
        f"{len(sites):,}"
    )

    # --------------------------------------------------
    # 3. Show duplicate examples
    # --------------------------------------------------

    display_columns = [
        column
        for column in [
            "site_id",
            "geometry_hash",
            "gunatanah1",
            "daerah_nam",
            "mukim_name",
            "pbt_name",
            "lot_upi",
            "tahun_data",
            "luas_hekta",
            "calculated_area_ha",
            "distance_275kv_km",
        ]
        if column in sites.columns
    ]

    duplicate_examples = (
        duplicates[
            display_columns
        ]
        .sort_values(
            [
                "geometry_hash",
                "site_id",
            ]
        )
    )

    duplicate_examples.to_csv(
        AUDIT_FILE,
        index=False,
    )

    print()
    print("FIRST DUPLICATE GROUPS")
    print("-" * 70)

    print(
        duplicate_examples
        .head(30)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------
    # 4. Check planning years
    # --------------------------------------------------

    if "tahun_data" in sites.columns:

        print()
        print("PLANNING DATA YEARS")
        print("-" * 70)

        print(
            sites[
                "tahun_data"
            ]
            .value_counts(
                dropna=False
            )
            .sort_index()
            .to_string()
        )

    print()
    print(
        f"Audit written to:"
    )

    print(
        AUDIT_FILE
    )

    print()
    print("=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()