# Graph & Network Analytics (Member 3) Assumptions

This document records minimal architectural assumptions for `services/graph` (`sutradhar_graph`) in accordance with `REPO-SETUP.md` and PRD 3.

## 1. Input Handling & ER Fallback
- When `artifacts/er/{entities,links,mentions}.jsonl` exists and is populated, `sutradhar_graph` ingests entity clusters directly.
- When `artifacts/er` is not yet available (e.g. early development or running standalone on `data/dev/` or `data/v1/`), `sutradhar_graph` loads records from agency silos (`STATE_POLICE`, `MAHA_CYBER`, `CENTRAL_AGENCY`) and groups mentions by exact phone or name matching as a provisional baseline to ensure complete offline independence without reading `data/truth/`.

## 2. Hub-Guard Thresholds
- High-degree nodes such as common police stations (e.g., "Synthetic Nagar PS"), common bank branches, or shared residential localities (e.g., "Bandra PS") can artificially inflate graph density.
- Any non-person identifier node with degree exceeding `degree_threshold = 15` (or shared address nodes) is down-weighted to weight `0.05` (or excluded from direct person projection) to prevent false community mergers.

## 3. MCOCA Legal Parameters Verification Flag
- All statutory thresholds in `dossier_rules.yaml` (such as 10-year lookback, minimum of 2 prior chargesheets, gang size >= 2) are tagged with `verified: false` to emphasize that they are synthetic evaluation guidelines for hackathon demonstration rather than formal legal counsel.
- All exported dossiers state: `"Draft to support officer judgement. Synthetic data."`

## 4. Mule Account Scoring Bands
- Risk scores are normalized between `0.0` and `1.0`:
  - `score >= 0.70`: `LIKELY_ORGANISER`
  - `score <= 0.35`: `LIKELY_DECEIVED`
  - `0.35 < score < 0.70`: `UNCERTAIN`
- Every score assignment provides human-readable reasons citing observable structural features (fan-out, pass-through latency, layer depth, account tenure).
