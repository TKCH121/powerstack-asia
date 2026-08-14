import json
import time

import truststore

truststore.inject_into_ssl()

import requests

from config import RAW_DIR


# Official PLANMalaysia iPLAN public Johor zoning layer
BASE_URL = (
    "https://scharms.planmalaysia.gov.my/arcgis/rest/services/"
    "iPLAN/GTzoning_01/MapServer/0/query"
)


# Start only with categories confirmed in this public layer.
LAND_USE_CLASSES = [
    "Industri",
    "Infrastruktur dan Utiliti",
]


OUT_FIELDS = (
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
)


def download_class(land_use: str):
    features = []
    offset = 0
    page_size = 2000

    while True:
        print(f"Requesting {land_use!r}, offset={offset} ...")

        params = {
            "where": f"gunatanah1='{land_use}'",
            "outFields": OUT_FIELDS,
            "returnGeometry": "true",
            "f": "geojson",
            "outSR": "4326",
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "orderByFields": "OBJECTID",
        }

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        payload = response.json()

        # ArcGIS sometimes returns HTTP 200 but places
        # the actual query failure inside the JSON body.
        if "error" in payload:
            print("\nARCGIS ERROR RESPONSE:")
            print(json.dumps(payload["error"], indent=2))
            raise RuntimeError(
                f"ArcGIS query failed for {land_use!r}"
            )

        if "features" not in payload:
            print("\nUNEXPECTED RESPONSE:")
            print(json.dumps(payload, indent=2)[:3000])
            raise RuntimeError(
                f"No 'features' field returned for {land_use!r}"
            )

        batch = payload["features"]

        print(f"Received {len(batch)} features")

        features.extend(batch)

        # If fewer than one full page came back,
        # we have reached the end.
        if len(batch) < page_size:
            break

        offset += page_size
        time.sleep(0.25)

    return features


def main():
    all_features = []

    for land_use in LAND_USE_CLASSES:
        features = download_class(land_use)
        all_features.extend(features)

    if not all_features:
        raise RuntimeError(
            "The API worked, but no zoning features were returned."
        )

    output = {
        "type": "FeatureCollection",
        "features": all_features,
    }

    out_path = RAW_DIR / "johor_relevant_zoning.geojson"

    out_path.write_text(
        json.dumps(output),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"Total features: {len(all_features):,}")
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()