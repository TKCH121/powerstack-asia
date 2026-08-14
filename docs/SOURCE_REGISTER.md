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

### Five-project Johor pilot

**Princeton Digital Group JH1**

- [PDG land-acquisition announcement, 22 May 2023](https://princetondg.com/newsroom/princeton-digital-group-acquires-land-from-jland-group-to-develop-a-150mw-data-centre-campus-in-malaysia/)
- [PDG construction and ESA announcement, 16 October 2023](https://princetondg.com/newsroom/princeton-digital-group-commences-superstructure-construction-of-150-mw-jh1-campus-2/)
- [TNB 1Q FY2024 briefing](https://www.tnb.com.my/assets/quarterly_results/Analyst_Briefing_1QFY2024.pdf), which records March 2024 commissioning at 132 kV
- [Official JH1 factsheet](https://princetondg.com/wp-content/uploads/2024/07/JH1_Factsheet_Updated.pdf) for the site coordinate and address
- [MIDA Phase One delivery report](https://www.mida.gov.my/mida-news/princeton-digital-delivers-phase-one-of-one-of-southeast-asias-largest-dcs-in-johor/)

**Bridge Data Centres MY07**

- [TNB 4Q FY2024 briefing](https://www.tnb.com.my/assets/quarterly_results/Analyst_Briefing_4QFY2024_Full_Deck_with_Appendix_FINAL.pdf) for the separate 400 MW ESA and 100 MW BESC/CRESS contract
- [TNB 2024 Sustainability Statement](https://www.tnb.com.my/assets/annual_report/TNB_IAR_2024_Sustainability_Statement.pdf) for the 400 MW agreement description
- [BDC MY07 water-reclamation disclosure](https://www.bridgedatacentres.com/bridge-data-centres-malaysias-first-data-centre-to-apply-effluent-water-and-cooling-technologies-at-johors-first-water-reclamation-plant/) for MY07 identity, Ulu Tiram locality, and qualified IT-load context

The two agreement quantities are not additive. No MY06 infrastructure fact is transferred to MY07.

**Digital Halo JHB1 / Nanda Digital**

- [Crescendo Bursa announcement, 12 July 2024](https://www.bursamalaysia.com/market_information/announcements/company_announcement/announcement_details?ann_id=3463785) for the Nanda Digital replacement SPA and project-vehicle relationship
- [Crescendo shareholder circular](https://crescendo.com.my/core-files/uploads/2024/08/CCB-Circular-Proposals-22-August-2024.pdf) for the exact land title and later detailed disclosure
- [Partners Group acquisition announcement, 13 May 2025](https://www.partnersgroup.com/en/news-and-views/press-releases/investment-news/detail?news_id=cec108f9-f5fe-445b-9f9b-2adcb7bbc95a) for later ownership and disclosed power/permit status
- [TNB 3Q FY2025 briefing](https://www.tnb.com.my/assets/quarterly_results/Analyst_Briefing_3QFY2025_Deck.pdf) for the post-boundary 150 MW ESA

**YTL Green Data Center Park / Sea Phase One**

- [YTL launch announcement, 21 April 2022](https://www.ytl.com/press-releases/ytl-green-data-center-park-launches-in-johor-the-first-integrated-data-center-park-powered-by-renewable-solar-energy-in-malaysia-2/)
- [MIDA groundbreaking announcement, 25 August 2022](https://www.mida.gov.my/media-release/ytl-data-centers-and-sea-break-ground-with-the-rm1-5bil-first-phase-of-the-500mw-ytl-green-data-center-park-in-johor/)
- [YTL Power Annual Report 2024](https://www.ytlpowerinternational.com/wp-content/uploads/ytles/sites/2/files/annual-report/YTLPI_AR2024.pdf) for the later Phase One operating outcome

The 500 MW campus and 72 MW first-phase figures are data-centre capacity. The 2022 launch supports project-enabled solar generation but does not state its generation capacity.

**STT Johor Campus / STT Johor 1**

- [Crescendo shareholder circular](https://crescendo.com.my/core-files/uploads/2024/08/CCB-Circular-Proposals-22-August-2024.pdf) for STT GDC Malaysia 2 legal-vehicle and land-sale history
- [STT Johor 1 factsheet dated 19 July 2024](https://assets.sttelemediagdc.com/sttgdc/global_en/public/2024-07/STT_Johor_1_Factsheet_v20240719.pdf) for the two designed 33 kV utility supplies
- [STT GDC groundbreaking announcement, 24 February 2025](https://www.sttelemediagdc.com/my-en/newsroom/stt-gdc-breaks-ground-high-performance-computing-data-centre-campus-johor-signs-mou-talent-development)

The factsheet establishes design and voltage, not ESA, supply MW, energisation, or whether the feeds were pre-existing or project-enabled.

## Current-state grid topology

**OpenStreetMap via Geofabrik regional extract**
`https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf`

The canonical ingestion route is Geofabrik plus local Osmium filtering. OSM is a public/crowdsourced topology source; map features are `VERIFIED` public-map records, while distances derived from them are `DERIVED`. Neither establishes utility-confirmed headroom.

## Historical OSM topology research

- [ohsome API documentation](https://docs.ohsome.org/ohsome-api/v1/endpoints.html)
- [OpenStreetMap API v0.6](https://wiki.openstreetmap.org/wiki/API_v0.6)
- [Historical extraction method and limitations](HISTORICAL_OSM_PROTOTYPE.md)

The cached extractor uses ohsome to identify normal and construction-tagged OSM
objects represented at the historical cutoff and the versioned OSM API to
reconstruct exact geometry for nearest-distance candidates. Label presence
`OSM_MAPPED_AS_OF_CUTOFF`, not `PRE_EXISTING_VERIFIED`; OSM history establishes
map state, not physical asset timing or grid capacity.

## Historical feature warning

Record infrastructure as `PRE_EXISTING_VERIFIED`, `PROJECT_ENABLED`, `POST_DECISION`, or `NOT_FOUND` where supported. In particular, the Yondr/Sedenak campus substation was project-enabled; its presence in today’s OSM cannot be used as an ex-ante predictor.
