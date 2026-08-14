"""Build conservative historical OSM grid features for one project.

Run without arguments for the PDG JH1 regression case. Supply explicit
arguments when another project has a supported coordinate and cutoff.
"""

from __future__ import annotations

import argparse
import json
import sys

from historical_osm_grid import ExtractionConfig, run_historical_osm_extraction


PDG_LOCATION_SOURCE = (
    "https://princetondg.com/wp-content/uploads/2024/07/"
    "JH1_Factsheet_Updated.pdf"
)


def parse_args(argv=None):
    """Parse one project's evidence-backed spatial inputs."""
    argument_list = sys.argv[1:] if argv is None else list(argv)
    parser = argparse.ArgumentParser(
        description="Build one historical OSM grid-feature observation."
    )
    parser.add_argument("--project-id", default="DC-JHR-004")
    parser.add_argument("--information-cutoff-date", default="2023-05-22")
    parser.add_argument(
        "--snapshot-timestamp",
        default="2023-05-22T23:59:59Z",
    )
    parser.add_argument("--latitude", type=float, default=1.69142)
    parser.add_argument("--longitude", type=float, default=103.41441)
    parser.add_argument("--site-geometry-source", default=PDG_LOCATION_SOURCE)
    parser.add_argument("--site-geometry-quality", default="SITE_COORDINATE")
    parser.add_argument("--search-radius-km", type=float, default=30.0)
    args = parser.parse_args(argument_list)
    supplied_flags = {
        value.split("=", 1)[0]
        for value in argument_list
        if value.startswith("--")
    }
    if args.project_id != "DC-JHR-004":
        required = {
            "--information-cutoff-date",
            "--snapshot-timestamp",
            "--latitude",
            "--longitude",
            "--site-geometry-source",
            "--site-geometry-quality",
        }
        missing = sorted(required - supplied_flags)
        if missing:
            parser.error(
                "A non-PDG project requires explicit evidence-backed inputs: "
                + ", ".join(missing)
            )
    if args.search_radius_km <= 0:
        parser.error("--search-radius-km must be positive")
    if not -90 <= args.latitude <= 90 or not -180 <= args.longitude <= 180:
        parser.error("latitude or longitude is outside its valid range")
    return args


def main(argv=None):
    """Run the extraction and print a compact reproducibility report."""
    args = parse_args(argv)
    config = ExtractionConfig(
        project_id=args.project_id,
        information_cutoff_date=args.information_cutoff_date,
        snapshot_timestamp=args.snapshot_timestamp,
        latitude=args.latitude,
        longitude=args.longitude,
        site_geometry_source=args.site_geometry_source,
        site_geometry_quality=args.site_geometry_quality,
        search_radius_m=round(args.search_radius_km * 1000),
    )
    result = run_historical_osm_extraction(config)
    print(
        json.dumps(
            {
                "project_id": config.project_id,
                "snapshot_timestamp": config.snapshot_timestamp,
                "feature_file": str(result.feature_file),
                "summary_file": str(result.summary_file),
                "request_stats": result.summary["request_stats"],
                "inventory_counts": result.summary["inventory_counts"],
                "historical_distances_km": result.summary[
                    "historical_distances_km"
                ],
                "geometry_resolution_failures": result.summary[
                    "geometry_resolution_failures"
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
