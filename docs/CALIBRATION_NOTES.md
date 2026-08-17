# PowerStack Historical Calibration Notes

## Current status — 17 August 2026

The original v0.1 proximity exercise below is preserved as a historical result,
not as the present product definition. The repository now contains eight
historical Johor projects and a stricter agreement-stage endpoint,
`POWER_AGREEMENT_100MW_WITHIN_48M`. The current target-endpoint output contains
two verified observed positives, TM Nxera and Digital Halo/Nanda, no mature
observed negative, four right-censored observations, and two observations whose
endpoint is not labelable from the current evidence.

Neither positive is presently a complete supervised-training observation.
Digital Halo has an `AUTHORITATIVE_PROJECT_POLYGON`, a 2024-06-11
`POST_SITE_COMMITMENT` boundary, and a later quantified agreement outcome; its
historical grid snapshot has not been produced. TM Nxera has a 2024-06-15
`POST_SITE_COMMITMENT` boundary and a later 280 MW electricity-supply agreement,
but its official geometry remains a `BOUNDED_PARCEL`, not an accepted project
polygon or point.

Predictive calibration remains research-only. These cases do not support a
commercial probability claim, a score, or transfer to a different decision
context.

Historical cohort eligibility now uses the common decision contract
`POST_SITE_COMMITMENT + PRE_QUALIFYING_OR_EQUIVALENT_POWER_COMMITMENT`.
Construction and project-specific grid-work status at the boundary are research
state variables, not universal exclusion gates. Unknown status remains
`NOT_FOUND`. See `docs/HISTORICAL_ENDPOINT_LABELS.md` for the operational
contract and its documented implementation gap.

## Calibration v0.1

Positive controls:

- GDS Nusajaya Tech Park
- Yondr / Vantage Sedenak

At the time of this v0.1 exercise, TM Nxera was excluded because authoritative
project geometry had not been resolved. A later official boundary recovery is
classified only as `BOUNDED_PARCEL`, so it remains ineligible for Tier A point
features and Tier B parcel-bound features are still deferred.

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
