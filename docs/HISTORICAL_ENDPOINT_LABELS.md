# Historical Endpoint Labels

`build_historical_endpoint_labels.py` derives endpoint labels from the local
DuckDB. The CSV is research output, not manual evidence:

```powershell
python src/build_historical_endpoint_labels.py --evaluation-date 2026-08-14
```

Output: `data/processed/research/historical_endpoint_labels.csv`.

## Label states

- `OBSERVED_POSITIVE`: a qualifying `VERIFIED` outcome is confidently within
  the horizon.
- `OBSERVED_NEGATIVE`: the horizon elapsed and explicit evidence establishes
  that the qualifying outcome did not occur within it.
- `RIGHT_CENSORED`: no positive is observed and the complete horizon has not
  elapsed.
- `UNLABELABLE`: the endpoint, timing, electrical threshold, or evidence of
  non-occurrence is insufficient.

Missing evidence is never converted to a negative label.

## Endpoint mappings

| Endpoint | Horizon | Qualifying verified records |
|---|---:|---|
| `ESA_WITHIN_12M` | 12 months | `ESA / SIGNED`; `ELECTRICITY_SUPPLY_AGREEMENT / AGREED` or `SIGNED` |
| `ESA_WITHIN_24M` | 24 months | Same ESA mapping |
| `UTILITY_COMMISSIONING_WITHIN_24M` | 24 months | `UTILITY_SUPPLY_COMMISSIONING / COMMISSIONED` |
| `FIRST_PHASE_OPERATION_WITHIN_24M` | 24 months | `PHASE_ONE_OPERATION / OPERATING`; project-level `PHASE_ONE_DELIVERY / DELIVERED` |
| `POWER_AGREEMENT_100MW_WITHIN_48M` | 48 months | A mapped ESA/electricity-supply agreement plus a typed, project-specific electrical measure meeting the threshold |

Equivalent `connection_events` terminology is used only when no semantic
milestone exists. `POWER_PARTNERSHIP` is not automatically an ESA. Substation
energisation is not automatically utility-supply commissioning. Groundbreaking,
topping-out, land acquisition, and IT handover alone do not qualify.

## Agreement-stage 100 MW rule

Only `ELECTRICAL_SUPPLY`, `MAXIMUM_DEMAND`, `CONTRACTED_CAPACITY`, or
`CONNECTION_CAPACITY` may establish the threshold. Automated positives require
`EXACT` or `GREATER_THAN` evidence at or above 100 MW. IT capacity and untyped
`connection_events.supply_mw` are excluded. BESC/CRESS alone is not currently a
qualifying power-agreement state.

`POWER_AGREEMENT_100MW_WITHIN_48M` is an agreement-stage outcome. It must not be
described as proof that at least 100 MW was commissioned, energised, or
delivered. Separate physical-delivery endpoints require evidence definitions
that have not yet been established.

## Date precision and negatives

`prediction_date` is time zero. `MONTH` and `YEAR` values remain intervals; the
script never supplies an assumed day. Outcomes that straddle a horizon are
`UNLABELABLE`. A shared recorded month/year at an event-based boundary is zero
elapsed periods.

The repository has no general structured evidence-review-complete field.
Therefore an elapsed horizon with no milestone remains `UNLABELABLE`. A verified
statement that a first phase *commenced operations* after the horizon can support
`OBSERVED_NEGATIVE`, because it explicitly dates the first-operation transition.

## Endpoint-specific training eligibility

The output separately records usable prediction boundaries, site geometry,
historical spatial output, prediction-time electrical targets, and label
usability. `TRAINING_READY_FOR_ENDPOINT` requires a usable observed label plus
site-quality geometry and historical spatial features. The 100 MW agreement
endpoint also requires a known electrical target at the prediction boundary. Otherwise an
observed label is `CALIBRATION_ONLY`; censored and unlabelable rows are
`NOT_READY`.
