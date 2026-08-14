# PowerStack Historical Calibration Notes

## Calibration v0.1

Positive controls:

- GDS Nusajaya Tech Park
- Yondr / Vantage Sedenak

TM Nxera is excluded until authoritative project geometry is resolved.

## Result 1 — 275 kV line proximity

GDS:
- Current mapped 275 kV line distance: 1.47 km
- Candidate-universe proximity percentile: 95.4

Yondr / Sedenak:
- Current mapped 275 kV line distance: 0.00 km
- Candidate-universe proximity percentile: 100.0

Interpretation:

275 kV line proximity remains a candidate PowerStack feature.

Evidence strength is currently weak because the calibration sample contains only two positive controls.

## Result 2 — Hard 5 km 275 kV substation rule rejected

GDS:
- Current mapped 275 kV substation distance: 10.07 km
- Proximity percentile: 94.3
- Existing hard rule would reject GDS.

Conclusion:

Do not require a candidate site to be within 5 km of a 275 kV substation.

Relative proximity is more informative than the current arbitrary 5 km threshold.

## Result 3 — Look-ahead bias at Sedenak

Yondr / Sedenak currently has effectively zero distance to mapped 275 kV infrastructure and PMU Sedenak.

However, project evidence shows that the campus high-voltage solution was developed as part of the project's power pathway.

Therefore today's mapped infrastructure cannot automatically be used as an input when asking whether the project could have been identified before its power solution was secured.

Historical calibration must use only information available at or before the chosen prediction date.

## Result 4 — Current-state and historical models must differ

Current site screening may use present grid topology.

Historical model training must use date-aware infrastructure features.

Required evidence categories:

- PRE_EXISTING_VERIFIED
- PROJECT_ENABLED
- POST_DECISION
- NOT_FOUND

## Current hypothesis status

Keep for testing:
- Distance / percentile to 275 kV line
- Distance / percentile to 275 kV substation
- Proximity to 132 kV infrastructure

Reject as hard rule:
- 275 kV substation <= 5 km

Not yet validated:
- Transmission-substation proximity
- 500 kV proximity
- Any weighted Power Pathway Score