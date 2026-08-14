"""Compatibility entry point for the Step 38 PDG prototype command.

Normal use should call ``build_historical_osm_features.py``. This wrapper keeps
the previously documented command working while using the hardened extractor.
"""

from build_historical_osm_features import main


if __name__ == "__main__":
    main()
