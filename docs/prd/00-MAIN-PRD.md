# MAIN PRD: Sutradhar (Prototype v0.1)

**Kumbathon | Sector: Law and Order | Sub-theme: Organized Crime and Cross-Agency Intelligence Integration**
**Status:** Build phase. **Team:** 5 members, 5 branches. **All data is synthetic.**

> This is the single source of truth. Every member also has a personal PRD (`01` to `05`) that goes deeper on their own part. **If a member PRD and this document disagree, this document wins.** Contract changes (Section 8, 9) must be made on `main` by pull request and announced to all five members.

---

## 0. How the PRD system works

| Doc | File | Who reads it |
|---|---|---|
| Main PRD | `docs/prd/00-MAIN-PRD.md` | Everyone |
| Member 1: Data and Synthetic Dataset | `docs/prd/01-data-synthetic.md` | Member 1 (+ everyone reads main) |
| Member 2: NLP and Entity Resolution | `docs/prd/02-nlp-entity-resolution.md` | Member 2 |
| Member 3: Graph and Analytics | `docs/prd/03-graph-analytics.md` | Member 3 |
| Member 4: Backend, Security, Audit | `docs/prd/04-backend-security-audit.md` | Member 4 |
| Member 5: Frontend and Storytelling | `docs/prd/05-frontend-storytelling.md` | Member 5 |

Each member PRD ends with an **Antigravity prompt**. The member pastes it into Antigravity; the agent reads the main PRD and the member PRD from the repo, then builds only that member's part.

---

## 1. Product summary

**Problem.** Maharashtra already has CCTNS, MahaCrimeOS AI, Maharashtra Cyber (Operation 1930, NCRP) and NATGRID access. What is missing is a layer that connects scattered records across police stations, districts, agencies and crime types, and shows whole criminal networks. Gangs look like unrelated petty cases; mule-account tracing stops at the first layer; MCOCA case-building is manual; cross-agency sharing is slow and unaudited; mega-events like Kumbh 2027 have no organized-crime early warning.

**Solution.** Sutradhar is a Syndicate Intelligence Layer that sits on top of existing systems (it does not replace them). It:

1. Resolves the same person, phone, account or vehicle across messy Marathi, Hindi and English records, with a visible reason for every link.
2. Builds a network graph that reveals gangs, brokers, kingpins and cross-crime bridges.
3. Traces money-mule chains beyond layer 1 and separates likely deceived account holders from organisers.
4. Drafts an explainable MCOCA-readiness dossier for the approving officer.
5. Lets agencies query each other without sharing raw data (match / no-match / maybe), with a hash-chained, tamper-evident audit log.
6. Offers a Kumbh mode: simulated early-warning alerts that a human officer must confirm.

### 1.1 Goals (prototype)

- One end-to-end story that runs **offline from one command** and takes five minutes to demo.
- Real, honest accuracy numbers measured against a hidden answer key.
- Trust features visible in the UI: confidence, reasons, review queue, human confirmation, audit log.

### 1.2 Non-goals

- No real personal data, no real integration with CCTNS, MahaCrimeOS, NATGRID or Maharashtra Cyber. Connectors are **simulated and labelled**.
- No automatic arrests, accusations or enforcement actions. The system proposes; officers decide.
- No predictive policing of the general population. Works only on case-linked records.
- No real facial recognition. Kumbh mode uses synthetic identifiers only.
- Not a legal-advice tool. Legal parameters are configurable and flagged unverified (Section 10.6).

### 1.3 Unverified items (do not state as fact in the pitch)

- Official Kumbathon problem statement and judging criteria have not been seen. Tie to Kumbh 2027 is inferred from the event name.
- Case figures come from news reports and need re-checking against originals.
- MCOCA prerequisites (e.g. a ten-year chargesheet look-back) and the exact DPDP Act wording need legal confirmation.
- Gaps "field officers lack NATGRID access" and "no organized-crime layer in the Kumbh plan" are inferences.

---

## 2. Users

| Persona | Needs in the first 10 seconds | Main screens |
|---|---|---|
| Crime branch analyst | See the network, who links to whom, and why | Search, entity profile, network, money trail |
| Senior approving officer (Joint CP level) | A clear, sourced dossier with evidence gaps | Dossier |
| Station inspector / field officer | A quick yes/no answer from another agency | Federated query |
| Agency liaison | Incoming queries to my agency, with purpose | Agency inbox |
| Auditor | Proof nothing was altered | Audit log + verify |
| Kumbh control-room operator | Short alert, reason, confirm / dismiss | Kumbh mode |

---

## 3. Feature list and priorities

P0 = must work in the demo. P1 = should. P2 = only if time remains.

| ID | Feature | Priority | Owner |
|---|---|---|---|
| F1 | Synthetic dataset v1/v2/v3 with three planted networks, bridges, noise, answer key | P0 | M1 |
| F2 | Extraction of mentions from form fields and narrative (mr/hi/en) | P0 | M2 |
| F3 | Entity resolution with confidence bands and explanations | P0 | M2 |
| F4 | Review queue with confirm / reject, and one-click unlink | P0 | M2 + M4 + M5 |
| F5 | Knowledge graph, communities, strong/weak edges | P0 | M3 |
| F6 | Role detection: broker, kingpin candidate, recruiter, controller | P0 | M3 |
| F7 | Mule-chain tracing beyond layer 1, deceived vs organiser | P0 | M3 |
| F8 | Cross-crime bridge detection | P0 | M3 |
| F9 | MCOCA-readiness dossier (draft, sourced) | P0 | M3 + M5 |
| F10 | Federated query (match / no-match / maybe) with purpose and roles | P0 | M4 |
| F11 | Hash-chained audit log with verify | P0 | M4 |
| F12 | Kumbh mode: simulated feed, alerts, human confirm | P0 (thin) | M1 + M4 + M5 |
| F13 | Marathi and English UI toggle | P1 | M5 |
| F14 | Path query ("how is A connected to B") | P1 | M3 + M5 |
| F15 | Guided demo mode (step-by-step overlay) | P1 | M5 |
| F16 | Metrics dashboard (precision, recall, etc.) | P1 | M1 (eval) + M5 |
| F17 | Natural-language search in Marathi/English | P2 | M2 + M5 |
| F18 | Victim-support view for deceived account holders | P2 | M3 + M5 |

---

## 4. Demo story and hero cast

All names below are **invented**; any resemblance to real people is coincidental. Cast roles must be assigned independent of any religion, caste or community (fairness rule, Section 10.5).

### 4.1 Five-minute storyline

| # | Step | Time | What the judge sees |
|---|---|---|---|
| 1 | Hook | 30s | Three FIRs in three districts that look unrelated |
| 2 | Resolve | 60s | Two spellings (Devanagari and Roman) plus a shared phone become one person, with reasons and a confidence score |
| 3 | Network | 90s | Graph reveals the extortion gang; broker highlighted; the same phone also appears in a fraud case and a drug case |
| 4 | Mule chain | 60s | Money traced beyond layer 1 to the recruiter; most account holders shown as likely deceived, with reasons |
| 5 | Dossier | 45s | One click produces a draft MCOCA-readiness dossier with sources and evidence gaps |
| 6 | Sharing and audit | 30s | Second agency asks a purpose-tagged question, gets MATCH, audit entry appears, chain verifies |
| 7 | Kumbh mode | 30s | Simulated alert in a Nashik zone; officer confirms |
| 8 | Close | 15s | Real metrics from the answer key |

### 4.2 Planted networks (reference cast)

**Network A: Cyber-fraud mule ring (MAHA_CYBER)**
- Recruiter: Sachin Kale (alias "Sachu"). Controller: Nitin Gaikwad.
- 60 rented mule accounts: 8 deceived holders (single account, small payment, no other cases), the rest organiser-linked or neutral.
- Victims across 6 districts; complaints in 1930/NCRP-style records; layered transfers (layers 1 to 4).

**Network B: Urban extortion gang (STATE_POLICE)**
- Leader: Anil Jadhav (rarely appears directly; appears as "boss" in a few narratives, controls transfers).
- 6 members across 3 police stations in Mumbai suburban, Thane and Pune, with spelling variants.
- **Bridge 1: Rakesh Dagdu Pawar** (broker). Appears as राकेश दगडू पवार, Rakesh D. Pawar, Rakesh Powar, "Raka". His phone appears in the extortion FIR, as the number used to contact victims in a fraud complaint, and as a contact in a drug seizure.

**Network C: Interstate drug chain (CENTRAL_AGENCY + STATE_POLICE)**
- Financier: Mahendra Rathore (outside Maharashtra). Lab operator: Prakash Shinde (Pune). 4 couriers.
- Records split between a central agency seizure report and state police FIRs.
- **Bridge 2: Nitin Gaikwad** appears in A (controller) and as an account holder receiving funds in C.

**Decoys.** At least 30 common-name collision groups, including two other "Rakesh Pawar" (different father names / districts). At least 10 innocent account holders who look suspicious.

### 4.3 Kumbh scenario (Nashik, synthetic)

Zones: Ramkund, Panchavati, Tapovan, Trimbakeshwar, Godavari Ghats. Planted events: **E1** an associate of the extortion gang (watchlist entity) is flagged in Ramkund; **E2** a pilgrim-targeted scam pattern (fake booking links, 14 complaints in two hours) matched to Network A accounts; **E3** a missing-person flag with no gang link (control case; must NOT raise an organized-crime alert).

---

## 5. Architecture and frozen tech choices

```
data/ (M1) ──► services/nlp (M2) ──► services/graph (M3) ──► artifacts/ ──► services/api (M4) ──► apps/web (M5)
   │                  │                      │                                   ▲
   └─► data/truth ──► services/eval (M1) ──► artifacts/metrics.json ─────────────┘
                (truth read ONLY by eval)
```

The parts talk through **files in `artifacts/`** (Section 8) and the **HTTP API** (Section 9). This is what lets five people build in parallel: everyone codes against the same fixtures in `contracts/fixtures/` until real output exists.

| Layer | Choice (frozen; change only by main-PRD pull request) |
|---|---|
| Python | 3.11 |
| Data gen | Python, Faker (en_IN) + custom Marathi/Hindi lists, seeded, pandas optional |
| NLP / ER | rapidfuzz, jellyfish, indic-transliteration, custom Marathi surname lexicon, pure-Python rules scorer; optional LLM for extraction only |
| Graph | networkx (Louvain via `networkx.algorithms.community`) |
| Backend | FastAPI, pydantic v2, uvicorn, SQLite (stdlib), pytest |
| Frontend | React 18, Vite, TypeScript, Tailwind, Cytoscape.js (fcose layout), Recharts |
| Packaging | Docker Compose, Makefile; **no network calls at demo time** |
| LLM | `LLM_PROVIDER=none` by default (offline); `anthropic` or `gemini` optional; results cached to disk |

Ports: API `8000`, web `5173` (dev) / `8080` (compose).

---

## 6. Repository layout and ownership

```
sutradhar/
├─ docs/prd/                 00..05 PRDs                      (all read; owner edits own)
├─ docs/pitch/               script, deck outline, Q&A        (M5)
├─ contracts/                schemas, openapi.json, fixtures  (M4 owns; changes via main PR)
│   ├─ schemas/*.schema.json
│   └─ fixtures/             tiny hand-made example of EVERY artifact and API response
├─ data/                     generated datasets               (M1)
│   ├─ v1/ v2/ v3/           per-version, per-agency folders
│   ├─ dev/                  small labelled dev set (NLP may read)
│   ├─ truth/                HOLD-OUT answer key (eval only)
│   └─ kumbh/events.jsonl
├─ services/
│   ├─ data_gen/             python package sutradhar_data    (M1)
│   ├─ eval/                 python package sutradhar_eval    (M1)
│   ├─ nlp/                  python package sutradhar_er      (M2)
│   ├─ graph/                python package sutradhar_graph   (M3)
│   └─ api/                  python package sutradhar_api     (M4)
├─ apps/web/                 React app                        (M5)
├─ artifacts/                generated outputs, gitignored    (nobody commits)
├─ scripts/check_no_truth_leak.sh                              (M4)
├─ Makefile, docker-compose.yml, README.md, CODEOWNERS, .gitignore   (M4)
```

**Ownership rule: you only edit files inside your own folders.** If you need something changed elsewhere, open an issue or ping the owner. Each service has its own `requirements.txt` / `package.json` so nobody edits a shared dependency file. Root files belong to M4.

**Answer-key rule.** `data/truth/` may be read only by `services/eval/` and `services/data_gen/`. `scripts/check_no_truth_leak.sh` greps `services/nlp`, `services/graph`, `services/api` and `apps/web` for the string `data/truth` and fails the build if found. NLP may tune on `data/dev/` only.

---

## 7. Git workflow

- Branches: `main` (protected, always runnable) and one branch per member: `feat/data`, `feat/nlp`, `feat/graph`, `feat/backend`, `feat/frontend`. Optional short-lived `integration` branch for merges.
- **Day 0 (M0):** Member 4 runs the scaffold prompt (Appendix A) and pushes to `main`. Everyone then creates their branch from that commit.
- Commit small and often, message format: `<area>: <what>` e.g. `er: add marathi surname lexicon`.
- Sync daily: `git fetch origin && git rebase origin/main` (or merge) so conflicts stay small.
- **Integration merges** at the end of M1, M2, M3, M4:
  1. Create `integration` from `main`.
  2. Merge in this order: `feat/data` → `feat/nlp` → `feat/graph` → `feat/backend` → `feat/frontend`.
  3. Resolve conflicts together on a call. Because folders are owned, real conflicts should only occur in `contracts/`, `README.md`, `Makefile`.
  4. Run `make pipeline && make test && make demo-check` (Section 12). Fix what breaks.
  5. Merge `integration` into `main`, and every member rebases onto the new `main`.
- Contract changes: separate PR into `main` touching only `contracts/` and Section 8/9 of this PRD, with a one-line announcement in the team chat. Others rebase within the day.
- Never commit `artifacts/`, `.env`, node_modules, or anything under `data/truth/` outside M1's branch.

---

## 8. Data contracts (file artifacts)

Format: JSONL (one JSON object per line) unless `.json`. All timestamps ISO-8601 UTC. UTF-8 everywhere. Strings in Marathi/Hindi are stored as Devanagari, never escaped.

### 8.1 IDs and enums

| Thing | Format | Example |
|---|---|---|
| Record | `R-<AGENCY3>-<6 digits>` | `R-SPO-000123` |
| Mention | `M-<record_id>-<n>` | `M-R-SPO-000123-2` |
| Entity | `P-` person, `PH-` phone, `AC-` account, `VH-` vehicle, `AD-` address + 6 digits | `P-000045` |
| Case | `CASE-<AGENCY3>-<6 digits>` | `CASE-SPO-000031` |
| Link / Community / Dossier / Alert / Query | `L-`, `COM-`, `DOS-`, `ALR-`, `Q-` + digits | `COM-002` |

Agencies: `STATE_POLICE` (SPO), `MAHA_CYBER` (CYB), `CENTRAL_AGENCY` (CEN).
Record types: `FIR`, `CHARGESHEET`, `COMPLAINT`, `SEIZURE_REPORT`.
Crime types: `CYBER_FRAUD`, `EXTORTION`, `NARCOTICS`, `MISSING_PERSON`.
Roles in a record: `ACCUSED`, `SUSPECT`, `VICTIM`, `COMPLAINANT`, `WITNESS`, `ACCOUNT_HOLDER`.

Normalisation: phone = 10 digits, no `+91` (regex `^[6-9]\d{9}$`); account key = `<BANKCODE>:<digits>`; IFSC `^[A-Z]{4}0[A-Z0-9]{6}$`; vehicle = uppercase no spaces, e.g. `MH15AB1234`.

### 8.2 Source records (M1 writes; M2 reads)

`data/<version>/<agency>/records.jsonl`

```json
{
  "record_id": "R-SPO-000123",
  "agency": "STATE_POLICE",
  "record_type": "FIR",
  "crime_type": "EXTORTION",
  "case_ref": "CASE-SPO-000031",
  "district": "Thane",
  "station": "Synthetic Nagar PS",
  "filed_date": "2025-11-04",
  "language": "mr",
  "sections": ["BNS-308"],
  "form_fields": {
    "accused": [{"name": "राकेश दगडू पवार", "father_name": "दगडू", "age": 34,
                 "address": "कळवा, ठाणे", "phone": "9000012345", "alias": "राका"}],
    "complainant": {"name": "...", "phone": "..."},
    "victims": [],
    "accounts": [{"bank": "HDFC", "account_no": "50100012345678", "holder_name": "..."}],
    "phones": ["9000012345"],
    "vehicles": ["MH05AB1234"]
  },
  "narrative": "मराठी / हिंदी / English FIR-style text ..."
}
```

Also `data/<version>/MAHA_CYBER/accounts.jsonl` (`account_key, bank, ifsc, holder_name_raw, opened_date, complaint_count, record_ids[]`) and `transactions.jsonl` (`txn_id, from_account, to_account, amount, ts, channel`).

`data/dev/`: same shapes plus `dev_labels.jsonl` (`mention_id → person_id`) for about 20% of mentions. The other 80% is held out in `data/truth/`.

### 8.3 Mentions, entities, links (M2 writes `artifacts/er/`; M3 and M4 read)

`mentions.jsonl`
```json
{"mention_id":"M-R-SPO-000123-1","record_id":"R-SPO-000123","agency":"STATE_POLICE",
 "role":"ACCUSED","name_raw":"राकेश दगडू पवार","name_norm":"rakesh dagdu pavar",
 "name_script":"DEVANAGARI","father_name_raw":"दगडू","father_name_norm":"dagdu","age":34,
 "address_raw":"कळवा, ठाणे","district":"Thane","phones":["9000012345"],"accounts":[],
 "vehicles":[],"aliases":["राका"],"extraction_method":"FORM","extraction_confidence":0.99}
```
`extraction_method` is `FORM`, `REGEX` or `LLM`.

`entities.jsonl`
```json
{"entity_id":"P-000045","entity_type":"PERSON","canonical_name":"Rakesh Dagdu Pawar",
 "name_variants":["राकेश दगडू पवार","Rakesh D. Pawar","Rakesh Powar"],
 "identifiers":{"phones":["PH-000007"],"accounts":[],"vehicles":[]},
 "mention_ids":["M-R-SPO-000123-1","M-R-CYB-000456-3"],
 "record_ids":["R-SPO-000123","R-CYB-000456"],"agencies":["STATE_POLICE","MAHA_CYBER"],
 "districts":["Thane","Pune"],"min_link_confidence":0.88,"status":"ACTIVE"}
```
Phone, account, vehicle and address entities are created **deterministically** from normalised values. Only PERSON entities use fuzzy matching.

`links.jsonl` (pairwise decisions between PERSON mentions)
```json
{"link_id":"L-000812","a_mention_id":"M-R-SPO-000123-1","b_mention_id":"M-R-CYB-000456-3",
 "score":0.91,"band":"AUTO",
 "reasons":[{"clue":"SHARED_PHONE","direction":"FOR","weight":0.55,"detail":"both list 9000012345"},
            {"clue":"NAME_SIMILARITY","direction":"FOR","weight":0.25,"detail":"rakesh dagdu pavar vs rakesh powar: 0.94"},
            {"clue":"FATHER_NAME_MISMATCH","direction":"AGAINST","weight":-0.0,"detail":"father missing in one record"}],
 "explanation_text":"Same phone number and a near-identical name; father's name absent in one record.",
 "explanation_source":"TEMPLATE","status":"ACTIVE","decided_by":null,"decided_at":null,"decision_reason":null}
```
`band` is `AUTO` (score >= 0.85), `REVIEW` (0.60 to 0.85), `SEPARATE` (< 0.60, stored only for the hard negatives M2 chooses to keep). `status`: `ACTIVE`, `PENDING_REVIEW`, `UNLINKED`.

`decisions.jsonl` is written by the backend at `artifacts/decisions/decisions.jsonl`: `{link_id, decision: CONFIRM|REJECT|UNLINK, reason, actor, ts}`. M2 re-reads it on every run: CONFIRM = must-link, REJECT/UNLINK = cannot-link.

### 8.4 Graph artifacts (M3 writes `artifacts/graph/`; M4 and M5 read)

`graph.json`
```json
{"nodes":[{"id":"P-000045","type":"PERSON","label":"Rakesh Dagdu Pawar",
           "props":{"districts":["Thane","Pune"]},"agencies":["STATE_POLICE","MAHA_CYBER"],
           "crime_types":["EXTORTION","CYBER_FRAUD","NARCOTICS"]}],
 "edges":[{"edge_id":"E-000100","source":"P-000045","target":"PH-000007","type":"USES",
           "strength":"STRONG","evidence":["R-SPO-000123"],"confidence":0.97,"weight":null}]}
```
Node types: `PERSON, PHONE, ACCOUNT, VEHICLE, ADDRESS, CASE, PLACE`.
Edge types: `USES, OWNS, ACCUSED_IN, VICTIM_IN, TRANSFERRED_TO, RECRUITED, CO_ACCUSED_WITH, SEEN_AT, LIVES_AT`.
`strength`: `STRONG` = directly documented in a record or a shared identifier; `WEAK` = shared address, co-location, name-only. `weight` is the amount for `TRANSFERRED_TO`.

`communities.json`
```json
[{"community_id":"COM-002","label":"Extortion gang (suspected)","member_ids":["P-000045"],
  "size":9,"crime_types":["EXTORTION","CYBER_FRAUD","NARCOTICS"],
  "districts":["Thane","Pune","Mumbai Suburban"],"agencies":["STATE_POLICE","MAHA_CYBER","CENTRAL_AGENCY"],
  "cohesion":0.71,"first_activity":"2023-02-10","last_activity":"2026-08-01","case_ids":["CASE-SPO-000031"]}]
```

`roles.json`
```json
[{"entity_id":"P-000045","community_id":"COM-002","role":"BROKER","score":0.82,
  "reasons":[{"signal":"BRIDGES_COMMUNITIES","value":3,"text":"Connects 3 groups"}],
  "evidence_record_ids":["R-SPO-000123"]}]
```
Roles: `BROKER, KINGPIN_CANDIDATE, RECRUITER, CONTROLLER, LIKELY_ORGANISER, LIKELY_DECEIVED_HOLDER`. A score is 0 to 1 and **every role must carry at least one reason and one evidence record.**

`mule_chains.json`
```json
[{"chain_id":"CH-001","community_id":"COM-001","total_amount":18800000,"victims_count":140,
  "max_depth":4,"layer1_only_accounts":12,
  "accounts":[{"account_id":"AC-000310","layer":2,"inflow":1500000,"outflow":1490000,
               "median_pass_through_minutes":9,"complaint_count":210,
               "classification":"LIKELY_DECEIVED","score":0.78,
               "reasons":[{"signal":"SINGLE_ACCOUNT_HOLDER","text":"Holder linked to only this account"}]}],
  "recruiter_candidates":["P-000101"],"controller_candidates":["P-000102"],
  "edges":[{"from":"AC-000300","to":"AC-000310","amount":900000,"ts":"2026-03-01T10:00:00Z"}]}]
```
Classification: `LIKELY_DECEIVED`, `LIKELY_ORGANISER`, `UNCERTAIN`. Uncertain is a valid and honest answer.

`bridges.json`
```json
[{"entity_id":"PH-000007","entity_type":"PHONE","communities":["COM-001","COM-002","COM-003"],
  "crime_types":["CYBER_FRAUD","EXTORTION","NARCOTICS"],"linked_person":"P-000045",
  "evidence_record_ids":["R-SPO-000123","R-CYB-000456","R-CEN-000009"]}]
```

`dossiers/DOS-<n>.json`
```json
{"dossier_id":"DOS-001","community_id":"COM-002","generated_at":"2026-10-20T10:00:00Z",
 "status":"DRAFT","summary":"...","legal_params":{"lookback_years":10,"verified":false},
 "sections":{"linked_cases":[{"case_id":"...","text":"...","source_record_ids":["..."]}],
   "prior_chargesheets":[],"associates":[{"entity_id":"...","role":"...","source_record_ids":[]}],
   "financial_links":[],"timeline":[{"date":"2024-03-01","event":"...","source_record_ids":[]}],
   "evidence_gaps":[{"text":"Member P-000050 appears in only one case","severity":"MEDIUM"}]},
 "disclaimer":"Draft to support officer judgement. Synthetic data."}
```
**Every statement in a dossier has `source_record_ids`.** Evidence gaps are required, not optional.

### 8.5 Backend-owned objects

Audit entry (hash chain):
```json
{"seq":57,"ts":"2026-10-20T10:01:02Z","actor":"analyst1","role":"ANALYST","action":"FEDERATED_QUERY",
 "purpose":"INVESTIGATION","case_ref":"CASE-SPO-000031","summary":"PHONE query by STATE_POLICE: MATCH",
 "prev_hash":"ab12...","hash":"9f3c..."}
```
`hash = sha256(prev_hash + canonical_json(entry without hash))`. Genesis `prev_hash` is 64 zeros.

Kumbh event (M1 writes `data/kumbh/events.jsonl`): `{event_id, ts, zone, event_type: WATCHLIST_SIGHTING|SCAM_PATTERN|MISSING_PERSON, subject_token, related_ids[], details}`. `subject_token` is a synthetic token that maps to an entity id or to nothing.

Metrics (M1 eval writes `artifacts/metrics.json`):
```json
{"dataset_version":"v2","er":{"auto_precision":0.99,"auto_recall":0.82,"overall_recall":0.91,
   "by_difficulty":{"easy":{"precision":0.99,"recall":0.97},"hard":{"precision":0.97,"recall":0.74}},
   "wrong_merge_rate":0.004,"review_share":0.12},
 "network":{"planted":3,"recovered":3,"kingpin_rank":2,"bridges_found":2,"bridges_planted":2},
 "mule":{"max_depth":4,"layer1_baseline_depth":1,"recruiter_detected":true,"deceived_precision":0.85},
 "time_saved":{"manual_minutes_estimate":240,"system_seconds":12}}
```

---

## 9. API contract (M4 builds; M5 consumes)

Base `http://localhost:8000`. Auth for the demo: header `X-Demo-User: <user_id>` (users are seeded). Errors: `{"error":{"code":"FORBIDDEN","message":"..."}}`. M4 exports `contracts/openapi.json` on every change. **Until the real API exists, `contracts/fixtures/` holds an example response for every endpoint.**

| Method and path | Purpose | Notes |
|---|---|---|
| `GET /health` | Liveness + `dataset_version` + `simulated: true` | |
| `GET /me` | Current demo user, role, agency | |
| `GET /entities/search?q=&type=` | Search persons / phones / accounts | Matches name variants in both scripts |
| `GET /entities/{id}` | Entity profile: variants, records, agencies, links | |
| `GET /entities/{id}/links` | Links with reasons and bands | |
| `GET /review-queue` | Links with band REVIEW and status PENDING_REVIEW | |
| `POST /review-queue/{link_id}/decision` | `{decision: CONFIRM or REJECT, reason}` | Reason required; audited |
| `POST /links/{link_id}/unlink` | `{reason}` | One click; audited |
| `GET /graph/communities` | List of communities | |
| `GET /graph/communities/{id}` | Nodes and edges of one community + roles | |
| `GET /graph/entity/{id}/neighborhood?hops=2` | Local subgraph | |
| `GET /graph/path?from=&to=` | Shortest path with evidence per edge | F14 |
| `GET /roles?community_id=` | Role list | |
| `GET /mule/chains?community_id=` | Chain with layers and classifications | |
| `GET /bridges` | Cross-crime bridges | |
| `POST /dossier/generate` | `{community_id}` → dossier JSON | Audited |
| `GET /dossier/{id}` | Read dossier | |
| `POST /dossier/{id}/export` | `{confirm: true}`; only `APPROVING_OFFICER` | Returns a printable JSON/HTML; audited |
| `POST /federated/query` | See below | Never returns raw records |
| `GET /agency/{agency}/inbox` | Queries received by that agency | Liaison role |
| `GET /audit?limit=&offset=` | Audit entries | `AUDITOR` |
| `GET /audit/verify` | `{valid, entries, head_hash, broken_at}` | |
| `POST /audit/dev/tamper` | Dev-only toggle that corrupts one entry for the demo | Disabled unless `DEMO_TAMPER=1` |
| `GET /kumbh/zones` | Zone list with state | |
| `GET /kumbh/alerts` | Current alerts | |
| `POST /kumbh/simulate/next` | Plays the next event from the feed | |
| `POST /kumbh/alerts/{id}/confirm` | `{action: CONFIRM or DISMISS, reason}` | Audited |
| `GET /metrics` | Contents of `artifacts/metrics.json` | |
| `GET /connectors/status` | Lists simulated connectors, each with `simulated: true` | |

**Federated query**
Request:
```json
{"querying_agency":"STATE_POLICE","identifier_type":"PHONE","identifier_value":"9000012345",
 "purpose":"INVESTIGATION","case_ref":"CASE-SPO-000031"}
```
Response (never any record content):
```json
{"query_id":"Q-000031","result":"MATCH","confidence":0.97,"reason_code":"OPEN_CASE_MATCH",
 "reason_text":"Identifier appears in an open case held by another agency.",
 "owning_agency_notified":true,"audit_seq":58}
```
`result`: `MATCH`, `NO_MATCH`, `MAYBE`. `purpose`: `INVESTIGATION`, `ALERT_VERIFICATION`, `AUDIT`. `identifier_type`: `PHONE`, `ACCOUNT`, `VEHICLE`, `PERSON_NAME_FATHER` (the last may return `MAYBE`).

---

## 10. Cross-cutting requirements

### 10.1 Roles and permissions (demo users, seeded)

| Role | Can do |
|---|---|
| `ANALYST` | Search, graph, mule chains, review decisions, generate dossier, federated query |
| `INSPECTOR` | Federated query, entity profile (limited), no graph export |
| `APPROVING_OFFICER` | Everything an analyst can, plus dossier export and Kumbh confirm |
| `LIAISON` | See own agency inbox, answer queries |
| `AUDITOR` | Audit log and verify only (read-only) |

### 10.2 Human-in-the-loop (always logged)
Review decisions, unlinks, dossier export, and Kumbh alert confirmation all require a **named user and a typed reason or confirm click**. The system never acts on its own.

### 10.3 Explainability
Every link, role, chain classification and dossier statement carries reasons and source record ids. Nothing is shown as a bare score.

### 10.4 Synthetic labelling
A persistent banner "SYNTHETIC DATA | SIMULATED CONNECTORS" in the UI. `simulated: true` in `/health` and `/connectors/status`. `data/DATASET_CARD.md` explains how the data was generated.

### 10.5 Fairness and ethics
- A wrong merge is worse than a missed merge. Name-only matches never auto-link.
- Cast roles are assigned independent of community; the generator must not correlate surname community with crime role (M1 checks and reports this).
- No feature may use religion, caste or community as a signal.
- Report the false-positive (wrong-merge) rate and the share of links sent to human review.
- Deceived holders are shown as such; "UNCERTAIN" is allowed.

### 10.6 Legal parameters
MCOCA-related parameters (e.g. look-back years, number of chargesheets) live in `services/graph/dossier_rules.yaml` with `verified: false`. The UI shows "legal parameters unverified" until a person with a legal source flips the flag. The pitch must not state them as fact before that.

### 10.7 Offline and determinism
No runtime network calls. Every generator and pipeline takes a `--seed`. `make demo` must start from a clean machine with Docker and no internet.

### 10.8 Language
Marathi (Devanagari), Hindi and English in data. UI: English plus Marathi labels (toggle is P1). Bundle a Devanagari font locally.

---

## 11. Commands (Makefile at root, owned by M4)

| Command | Does |
|---|---|
| `make data VERSION=v2 SEED=42` | `python -m sutradhar_data.generate --version v2 --seed 42 --out data/` |
| `make er` | `python -m sutradhar_er.run --data data/$(VERSION) --out artifacts/er` |
| `make graph` | `python -m sutradhar_graph.run --data data/$(VERSION) --er artifacts/er --out artifacts/graph` |
| `make eval` | `python -m sutradhar_eval.run --data data/$(VERSION) --truth data/truth/$(VERSION) --artifacts artifacts --out artifacts/metrics.json` |
| `make pipeline` | `data` → `er` → `graph` → `eval` |
| `make api` / `make web` | Run backend / frontend in dev |
| `make test` | pytest for every service + web unit tests + `check_no_truth_leak.sh` |
| `make demo` | `docker compose up` with prebuilt artifacts |
| `make demo-check` | Scripted smoke test of the full demo path via the API |

---

## 12. Milestones and merge gates

| Milestone | Everyone delivers | Gate (must pass before merge to `main`) |
|---|---|---|
| **M0 Scaffold** | M4 pushes scaffold, schemas, fixtures. Everyone branches. | Repo clones, `make test` runs (empty), fixtures validate against schemas |
| **M1 Walking skeleton** | M1: v0 data (30 to 60 records, 3 networks sketched, dev set). M2: baseline extractor + exact-identifier ER. M3: graph + communities on M2 output. M4: API serving fixtures with roles + audit chain. M5: screens 1 to 3 on fixtures. | `make pipeline` runs on v0; API returns fixture-shaped responses; UI shows search + network from fixtures |
| **M2 Real v1** | M1: v1 clean-ish data + eval. M2: name matching, bands, explanations. M3: roles, bridges. M4: real endpoints, review queue, federated query. M5: all main screens on live API. | Hero path works: 3 FIRs → one person → network → bridge |
| **M3 Hard and complete** | M1: v2 noisy data, hard cases. M2: tuned on dev set, held-out report. M3: mule chains + dossier. M4: audit verify, mock connectors, tamper demo. M5: money trail, dossier, audit screens. | Dossier generates with sources; audit verifies; mule chain shows depth > 1 |
| **M4 Kumbh and polish** | M1: Kumbh feed + v3 hard. M4: Kumbh alerts + confirm. M5: Kumbh screen, guided demo, Marathi labels. Metrics on dashboard. | Full 5-minute demo runs offline; metrics real; no truth leak |
| **M5 Freeze** | Rehearsal x2 each, backup video, bug freeze, deck final | `make demo-check` green on a clean clone; backup video recorded |

Reserve at least 25% of total time for M4 and M5.

---

## 13. Success criteria and metric targets

Targets are goals, not claims. Report whatever the held-out evaluation actually gives.

| Area | Target |
|---|---|
| ER: AUTO-band precision | >= 0.97 (wrong-merge rate <= 1%) |
| ER: overall recall (AUTO + confirmed REVIEW) | >= 0.85; hard cases >= 0.70 |
| Review share | 5 to 20% of links |
| Networks recovered | 3 of 3 planted; true leader in top 3 kingpin candidates |
| Bridges found | 2 of 2 |
| Mule tracing | Depth >= 3 vs layer-1 baseline of 1; recruiter detected; deceived-holder precision >= 0.80 |
| Dossier | Generated in under 15 seconds; 100% of statements have source ids |
| Audit | `verify` passes; tamper demo detected |
| Performance | Search < 500 ms; community fetch < 1 s on v2 |
| Demo | Runs offline from `make demo`; whole path under 5 minutes |

---

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Scope too big | P0 first; Kumbh stays thin; P2 only after M4 |
| Data too clean or too random | v1 → v2 → v3 ladder; M1 and M2 review hard cases together |
| Answer-key leakage inflates results | Folder rule + `check_no_truth_leak.sh` + dev/holdout split |
| Wrongful linking | Bands, review queue, unlink, reported wrong-merge rate |
| Integration breaks late | Fixtures from day 0; integration merges at each milestone |
| LLM errors or no internet | `LLM_PROVIDER=none` default; validators; cached outputs |
| Overclaiming | Simulated labels everywhere; unverified list in 1.3 |
| Demo failure | Offline compose, rehearsal, backup video |

---

## 15. Open decisions (owners fill in)

| Decision | Owner | Default if undecided |
|---|---|---|
| Live demo vs recorded vs both | M5 + team | Both |
| Plain tamper-evident log vs blockchain | M4 + team | Hash chain only; mention blockchain only as the audit ledger idea |
| Privacy-preserving matching stretch (hashed identifiers) | M4 | Salted-hash compare; full PSI is a stretch |
| Language toggle | M5 | Bilingual labels now, toggle in M4 |
| Exact portal requirements | Anyone | Update Section 1.3 once verified |

---

## Appendix A: Scaffold prompt for Antigravity (Member 4 runs this once, on `main`)

```
You are setting up the repository scaffold for the project "Sutradhar". Read docs/prd/00-MAIN-PRD.md fully first (put the PRD files from the zip into docs/prd/ if they are not there yet). Do NOT implement features. Create only the scaffold, then commit to main.

Create:
1. The folder layout in Section 6 with a README.md in each service folder explaining its owner and purpose.
2. contracts/schemas/*.schema.json (JSON Schema draft 2020-12) for: source_record, account, transaction, mention, entity, link, decision, graph, community, role, mule_chain, bridge, dossier, audit_entry, federated_query_request, federated_query_response, kumbh_event, kumbh_alert, metrics. Derive them exactly from Section 8 and 9.
3. contracts/fixtures/: a tiny hand-made, valid example file for every artifact in Section 8 and a JSON response for every endpoint in Section 9, using the Rakesh Pawar bridge story from Section 4. A script scripts/validate_fixtures.py must validate fixtures against the schemas.
4. Minimal python packages sutradhar_data, sutradhar_er, sutradhar_graph, sutradhar_eval, sutradhar_api, each with __init__.py, a __main__/run module that accepts the CLI arguments in Section 11 and currently copies the matching fixtures into the output folder, plus a requirements.txt and one placeholder pytest.
5. apps/web: Vite + React + TypeScript + Tailwind skeleton that renders "Sutradhar" and the SYNTHETIC DATA banner.
6. Makefile with the commands in Section 11, docker-compose.yml (api, web), .gitignore (artifacts/, .env, node_modules, data/truth must NOT be ignored in feat/data but never read by others), CODEOWNERS mapping folders to the five roles, and scripts/check_no_truth_leak.sh.
7. Branch protection notes in README.md and the git workflow from Section 7.

Rules: Python 3.11, no network calls at runtime, no real data. When done, run make test and fix failures, then give me a summary and the exact git commands to push main and create the five feature branches.
```

## Appendix B: Glossary

- **CCTNS:** national police records network. **MahaCrimeOS AI:** Maharashtra police AI copilot. **NCRP / 1930:** national cybercrime reporting portal and helpline. **NATGRID:** national intelligence data-access grid. **MCOCA:** Maharashtra Control of Organised Crime Act, 1999. **BNS:** Bharatiya Nyaya Sanhita, 2023.
- **Mule account:** a bank account used to pass fraud proceeds. **Layer 1:** the first accounts that receive victim money.
- **Blocking:** grouping likely candidates before comparing, to avoid comparing everything with everything.
- **Broker:** someone who connects groups. **Kingpin candidate:** someone others depend on, even if rarely named in cases.
- **Hash chain:** each log entry includes the hash of the previous one, so any edit breaks the chain.
