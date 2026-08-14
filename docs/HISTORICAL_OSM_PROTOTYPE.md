# Historical OSM Topology Prototype

## Scope and evidence meaning

This research-only prototype reconstructs the OSM power topology around
`DC-JHR-004` (PDG JH1) at `2023-05-22T23:59:59Z`. It does not change the
canonical current-state grid files or the DuckDB schema.

Historical presence is labelled `OSM_MAPPED_AS_OF_CUTOFF`. It proves only that
the feature was publicly represented in OSM at the cutoff. It does not prove
physical existence, commissioning, ownership, or available grid capacity.
Likewise, `NOT_MAPPED_IN_OSM_AT_CUTOFF` is not evidence of physical absence.
All calculated distances are `DERIVED`.

## Reproducible method

Run from the repository root:

```powershell
python src/prototype_historical_osm_grid.py
```

The script uses the PDG coordinate `1.69142, 103.41441`, creates an
approximately 30 km envelope in `EPSG:3375`, and submits this ohsome request:

```text
GET https://api.ohsome.org/v1/elements/bbox
bboxes=103.14454647,1.41989581,103.68418662,1.96292189
time=2023-05-22T23:59:59Z
filter=power in (line, cable, substation)
properties=tags,metadata
clipGeometry=false
timeout=600
```

The response supplies the object ID, object version, tags, edit metadata, and
geometry bounding box at the cutoff. The public ohsome
`/v1/elements/geometry` route returned HTTP 403 during the prototype. Exact
geometry is therefore reconstructed only for possible nearest features using
the versioned OSM API object and the node versions valid at the cutoff. Bounding
box lower bounds ensure the search stops only after no unresolved object can be
closer. Missing voltage is never inferred.

The current comparison comes from the local Geofabrik regional PBF, whose
header timestamp was `2026-08-13T20:21:01Z`, and the canonical current line and
substation Parquets. Metric distances use `EPSG:3375`. Change detection uses
stable OSM primitive IDs; Osmium's synthetic `area/...` representations are
excluded to avoid counting closed ways twice.

## Generated outputs

All generated artifacts are under the ignored directory
`data/processed/research/historical_osm_pdg/`:

- `ohsome_snapshot_bbox.geojson`: raw historical inventory response.
- `historical_power_feature_bboxes.geojson`: normalized historical inventory.
- `osm_api_exact_candidates.json` and
  `historical_distance_candidates.geojson`: exact nearest-candidate evidence.
- `current_bbox.osm.pbf`, `current_power_features.osm.pbf`, and
  `current_power_features.geojson`: disposable current comparison subset.
- `pdg_historical_current_distances.csv`: proposed one-row derived structure.
- `historical_current_change_detection.csv` and `prototype_summary.json`:
  stable-ID comparison and full run provenance.

Do not commit these outputs. Retain the script and this methodology note.

## Limitations and scaling decision

The filter covers the requested `power=line`, `power=cable`, and
`power=substation` records; it does not yet include objects whose only primary
tag is `power=construction`. OSM edit time is not construction time. Object-ID
appearance, disappearance, or tag changes may reflect mapping activity rather
than physical work. The exact resolver supports nodes and ways; it deliberately
fails if a relation becomes a nearest candidate rather than approximating it.

The method is adequate for a small, cached historical-project batch. It is not
yet suitable for high-volume parallel extraction because public API latency and
rate limits make repeated node-history requests fragile. Scale sequentially,
cache raw responses, and retain bounded retries. Reconsider an operated OSHDB
service or local history extract only if the public API becomes the measured
bottleneck; a full-history planet download is not justified by this pilot.

Sources: [ohsome elements extraction](https://docs.ohsome.org/ohsome-api/v1/endpoints.html),
[ohsome filter syntax](https://docs.ohsome.org/ohsome-api/v1/filter.html),
[ohsome time parameter](https://docs.ohsome.org/ohsome-api/development/time.html),
[OSM API v0.6](https://wiki.openstreetmap.org/wiki/API_v0.6), and
[OpenStreetMap copyright and attribution](https://www.openstreetmap.org/copyright).
