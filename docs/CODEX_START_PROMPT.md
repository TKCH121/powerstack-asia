# Codex Start Prompt

Use this prompt when starting a new PowerStack Asia repository session.

Work only on the currently checked-out branch. Do not switch, merge, push, or
modify files until the requested task and repository state have been inspected.

PowerStack is an evidence-first Power & Digital Infrastructure Intelligence
system for Southeast Asia, starting with Johor. Its first commercial product is
an analyst-led Power Pathway Assessment, not a self-serve SaaS platform.

Read, in order:

1. `AGENTS.md`
2. `README.md`
3. `docs/PRODUCT_MEMO.md`
4. `docs/INVESTMENT_MEMO.md`
5. `docs/METHODOLOGY_OVERVIEW.md`
6. `docs/MARKET_INTELLIGENCE_MODEL.md`
7. `docs/PROJECT_SPEC.md`
8. `docs/DATA_DICTIONARY.md`
9. `docs/HISTORICAL_ENDPOINT_LABELS.md`
10. `docs/HISTORICAL_OSM_PROTOTYPE.md`
11. `docs/SOURCE_REGISTER.md`
12. `docs/CODEX_HANDOFF.md`

Then inspect `git status`, recent history, the relevant source files, and any
manual evidence files in scope.

Preserve `VERIFIED`, `DERIVED`, `INFERRED`, and `NOT_FOUND`. Never invent
coordinates, dates, MW, available grid capacity, or evidence of absence. Keep IT
capacity separate from electrical measures. Do not let later agreements,
project-enabled infrastructure, or current OSM assets leak into historical
prediction features. Do not add ML, scoring weights, arbitrary proximity rules,
or a duplicate source of truth.

The intended next implementation step, when explicitly requested, is
Intelligence Core v0.1. Before adding any new event or evidence tables, define
canonical event identity and how the new layer references or crosswalks existing
`connection_events`, `grid_asset_events`, and Power Pathway milestones.
