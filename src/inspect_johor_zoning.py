from pathlib import Path

import geopandas as gpd
import pandas as pd

from config import RAW_DIR, PROCESSED_DIR


INPUT_FILE = RAW_DIR / "johor_relevant_zoning.geojson"

OUTPUT_PARQUET = (
    PROCESSED_DIR / "johor_relevant_zoning.parquet"
)

OUTPUT_SUMMARY = (
    PROCESSED_DIR / "johor_zoning_summary.csv"
)


def main():

    print("=" * 70)
    print("POWERSTACK — JOHOR ZONING INSPECTION")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Check the downloaded file exists
    # --------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find: {INPUT_FILE}"
        )

    print()
    print(f"Reading: {INPUT_FILE}")

    # --------------------------------------------------
    # 2. Load GeoJSON
    # --------------------------------------------------

    gdf = gpd.read_file(INPUT_FILE)

    print()
    print("DATASET OVERVIEW")
    print("-" * 70)

    print(f"Rows: {len(gdf):,}")
    print(f"Columns: {len(gdf.columns)}")
    print(f"CRS: {gdf.crs}")

    print()
    print("Columns:")
    for column in gdf.columns:
        print(f"  - {column}")

    # --------------------------------------------------
    # 3. Check geometry
    # --------------------------------------------------

    missing_geometry = gdf.geometry.isna().sum()

    invalid_geometry = (
        (~gdf.geometry.is_valid)
        .fillna(False)
        .sum()
    )

    print()
    print("GEOMETRY CHECK")
    print("-" * 70)

    print(
        f"Missing geometry: {missing_geometry:,}"
    )

    print(
        f"Invalid geometry: {invalid_geometry:,}"
    )

    # --------------------------------------------------
    # 4. Inspect zoning categories
    # --------------------------------------------------

    print()
    print("LAND-USE CATEGORIES")
    print("-" * 70)

    if "gunatanah1" in gdf.columns:

        category_counts = (
            gdf["gunatanah1"]
            .value_counts(dropna=False)
        )

        print(category_counts)

    # --------------------------------------------------
    # 5. Inspect districts
    # --------------------------------------------------

    print()
    print("DISTRICTS")
    print("-" * 70)

    if "daerah_nam" in gdf.columns:

        district_counts = (
            gdf["daerah_nam"]
            .value_counts(dropna=False)
        )

        print(district_counts)

    # --------------------------------------------------
    # 6. Inspect mukims
    # --------------------------------------------------

    print()
    print("TOP 20 MUKIMS")
    print("-" * 70)

    if "mukim_name" in gdf.columns:

        mukim_counts = (
            gdf["mukim_name"]
            .value_counts(dropna=False)
            .head(20)
        )

        print(mukim_counts)

    # --------------------------------------------------
    # 7. Basic cleaning
    # --------------------------------------------------

    print()
    print("CLEANING")
    print("-" * 70)

    before = len(gdf)

    # Remove records without geometry
    gdf = gdf[
        gdf.geometry.notna()
    ].copy()

    # Repair invalid polygon geometry
    invalid_mask = ~gdf.geometry.is_valid

    if invalid_mask.any():

        print(
            f"Repairing "
            f"{invalid_mask.sum():,} invalid geometries..."
        )

        gdf.loc[
            invalid_mask,
            "geometry"
        ] = (
            gdf.loc[
                invalid_mask,
                "geometry"
            ]
            .buffer(0)
        )

    after = len(gdf)

    print(
        f"Rows before cleaning: {before:,}"
    )

    print(
        f"Rows after cleaning: {after:,}"
    )

    # --------------------------------------------------
    # 8. Add PowerStack internal fields
    # --------------------------------------------------

    gdf["powerstack_source"] = (
        "PLANMalaysia iPLAN"
    )

    gdf["fact_type"] = "VERIFIED"

    gdf["country"] = "Malaysia"

    gdf["state"] = "Johor"

    # --------------------------------------------------
    # 9. Save clean geospatial file
    # --------------------------------------------------

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    gdf.to_parquet(
        OUTPUT_PARQUET,
        index=False,
    )

    print()
    print(
        f"Saved cleaned zoning data to:"
    )

    print(
        OUTPUT_PARQUET
    )

    # --------------------------------------------------
    # 10. Create simple summary table
    # --------------------------------------------------

    summary = (
        gdf.groupby(
            [
                "gunatanah1",
                "daerah_nam",
            ],
            dropna=False,
        )
        .size()
        .reset_index(
            name="polygon_count"
        )
        .sort_values(
            "polygon_count",
            ascending=False,
        )
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    print()
    print(
        f"Saved summary to:"
    )

    print(
        OUTPUT_SUMMARY
    )

    # --------------------------------------------------
    # 11. Show sample records
    # --------------------------------------------------

    print()
    print("SAMPLE RECORDS")
    print("-" * 70)

    display_columns = [
        column
        for column in [
            "gunatanah1",
            "daerah_nam",
            "mukim_name",
            "pbt_name",
            "luas_hekta",
            "tahun_data",
        ]
        if column in gdf.columns
    ]

    print(
        gdf[
            display_columns
        ]
        .head(10)
        .to_string(index=False)
    )

    print()
    print("=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()