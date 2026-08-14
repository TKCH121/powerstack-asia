# Source Register

This register identifies source families. Preserve the exact URL, publication date, accessed date where relevant, and `fact_type` with every curated record.

## Planning and administrative geography

**PLANMalaysia iPLAN zoning**
`https://scharms.planmalaysia.gov.my/arcgis/rest/services/iPLAN/GTzoning_01/MapServer/0/query`

Used for Johor zoning geometry and source fields. District-boundary cleaning uses PLANMalaysia’s `SCHARMS/Mobil_DataAsas/MapServer/2` layer. These sources establish planning/map records, not power capacity.

## Power-system context and connection process

- [Single Buyer Malaysia demand](https://www.singlebuyer.com.my/market/market-data/demand)
- [Energy Commission MyEnergyStats](https://myenergystats.st.gov.my/dashboard)
- [TNB Electricity Supply Application Handbook](https://www.tnb.com.my/esah/supply-application/)

Use these for public context, process, and explicitly published facts only.

## Project and connection evidence

- [TNB / GDS announcement](https://www.tnb.com.my/announcements/tnb-gds-collaboration-signals-positive-growth-in-foreign-investment-for-dcm)
- [Yondr Johor announcement](https://www.yondrgroup.com/newsroom/press-release/yondr-group-powers-up-its-first-data-center-campus-in-malaysia-within-two-years-of-market-entry/)
- [TM Nxera supply announcement](https://www.tmnxera.com/news-insights/latest-from-tm-nxera/tm-nxera-secures-280mw-to-power-ai-ready-green-data-centre-campus-in-johor)

Manual CSV rows retain the specific source that supports each fact. A secured-supply statement is not evidence of spare capacity elsewhere.

## Current-state grid topology

**OpenStreetMap via Geofabrik regional extract**
`https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf`

The canonical ingestion route is Geofabrik plus local Osmium filtering. OSM is a public/crowdsourced topology source; map features are `VERIFIED` public-map records, while distances derived from them are `DERIVED`. Neither establishes utility-confirmed headroom.

## Historical feature warning

Record infrastructure as `PRE_EXISTING_VERIFIED`, `PROJECT_ENABLED`, `POST_DECISION`, or `NOT_FOUND` where supported. In particular, the Yondr/Sedenak campus substation was project-enabled; its presence in today’s OSM cannot be used as an ex-ante predictor.
