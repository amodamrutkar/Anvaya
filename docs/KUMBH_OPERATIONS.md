# Kumbh Operations Intelligence Layer

## 1. Purpose

The **Kumbh Operations Intelligence Layer** provides an event-specific situational intelligence correlation engine for mega-event security operations during Kumbh Mela (Nashik / Trimbakeshwar 2027).

It connects live operational event streams (surveillance sightings, financial scams, crowd anomalies, infrastructure reports, missing pilgrim incidents) with the existing Sutradhar Knowledge Graph, Network Intelligence, and Financial Flow tracking layers.

### Critical Safety Mandate

> [!IMPORTANT]
> Kumbh Operations is an **INTELLIGENCE CORRELATION** layer, NOT an autonomous policing, targeting, or accusation system.

The system adheres strictly to the following non-negotiable safety rules:
- **Never declare guilt:** The system never declares any individual guilty or automatically accuses anyone.
- **Attendance is not evidence:** Presence at Kumbh or attendance at religious rituals is never converted into criminal evidence or suspicious classification.
- **Proximity is not involvement:** Proximity to an incident zone (e.g. Ramkund, Panchavati) does not imply or infer criminal involvement.
- **Human investigator review:** Every generated intelligence item requires human review (`action = "Requires investigator review"`).
- **Zero ground-truth leakage:** Operates purely on observable graph evidence without relying on synthetic generator labels, planted scenario tags, or evaluation truth tables.

---

## 2. Taxonomy of Intelligence Categories

To prevent conflation between raw facts and analytical inferences, Sutradhar enforces four distinct operational categories:

| Category | Definition | Example in System |
| :--- | :--- | :--- |
| **OBSERVATION** | An objective, verifiable event report recorded at a specific time and location by an agency or sensor. | Sighting of token `TOK-SYNTH-0140` at Ramkund bathing ghat on 2027-01-13 13:00 UTC. |
| **ASSOCIATION** | A factual, deterministic link between an observation and a known graph node or infrastructure. | Matched phone `9820011111` or registered vehicle `MH-15-AB-1234` in the graph. |
| **INTELLIGENCE SIGNAL** | An explainable indicator derived from correlated context (e.g., cross-case activity, multi-layer mule account). | `KNOWN_CASE_ASSOCIATION`, `CROSS_CASE_ACTIVITY`, `ACCOUNT_ASSOCIATION`. |
| **INVESTIGATOR INTERPRETATION** | The human decision, contextual assessment, and legal judgment exercised by an authorized officer. | Officer confirms alert, initiates inquiry, or dismisses false alarm with mandatory rationale. |

---

## 3. Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                Agency Records & Feeds                  │
       │   (State Police CCTNS, MahaCyber 1930, Central Agency)  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │               NLP & Entity Resolution (ER)             │
       │        (Bilingual Normalization, Blocking, Fusion)     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │            Heterogeneous Knowledge Graph               │
       │    (Persons, Cases, Phones, Accounts, Vehicles, Nodes) │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                 Network Intelligence                   │
       │    (Communities, Bridge Detection, Mule Chain Tracing) │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
 ┌────────────────────────────────────────────────────────────────────┐
 │              KUMBH OPERATIONS INTELLIGENCE LAYER                   │
 │                                                                    │
 │  ┌──────────────────────┐  ┌────────────────────────────────────┐  │
 │  │ Event Ingestion      │  │ Deterministic Correlation Engine   │  │
 │  │ - Event Model        │  │ - Direct Identity (Person/Phone)   │  │
 │  │ - Zone Normalization │  │ - Case & Network Context           │  │
 │  │ - ISO Time Parsing   │  │ - Financial Chain Matching         │  │
 │  └──────────┬───────────┘  └─────────────────┬──────────────────┘  │
 │             │                                │                     │
 │             ▼                                ▼                     │
 │  ┌──────────────────────┐  ┌────────────────────────────────────┐  │
 │  │ Temporal / Spatial   │  │ Multi-Factor Incident Clustering   │  │
 │  │ - Immediate (±1h)    │  │ - Shared Infrastructure            │  │
 │  │ - Short (±6h)        │  │ - Shared Entities                  │  │
 │  │ - Extended (±24h)    │  │ - Spatio-Temporal Bursts           │  │
 │  └──────────────────────┘  └─────────────────┬──────────────────┘  │
 │                                              │                     │
 └──────────────────────────────────────────────┼─────────────────────┘
                                                │
                                                ▼
       ┌────────────────────────────────────────────────────────┐
       │               Investigator Review Portfolio            │
       │    - Signals, Evidence, Provenance, Hierarchy Tier     │
       │    - Action: "Requires investigator review"            │
       └────────────────────────────────────────────────────────┘
```

---

## 4. Event Intelligence Model (`KumbhEventModel`)

Each ingested operational event is validated according to schema:

```json
{
  "event_id": "KUMBH-EVT-0001",
  "event_type": "WATCHLIST_SIGHTING",
  "ts": "2027-01-16T16:15:00Z",
  "zone": "Ramkund",
  "subject_token": "TOK-EXTORT-ASSOC-001",
  "related_ids": ["P-000001"],
  "source_agency": "KUMBH_SURVEILLANCE",
  "confidence": 0.92,
  "details": {
    "description": "Subject matching watchlist entity observed near Ramkund."
  },
  "provenance": {
    "source": "Kumbh Operations Feed",
    "event_id": "KUMBH-EVT-0001",
    "zone": "Ramkund",
    "timestamp": "2027-01-16T16:15:00Z"
  },
  "coordinates": null
}
```

### Supported Zones
- `Ramkund` (Primary sacred bathing ghat)
- `Panchavati` (Commercial temple sector)
- `Tapovan` (Transit, camp accommodation sector)
- `Trimbakeshwar` (Jyotirlinga temple sector)
- `Godavari Ghats` (Riverbank crowd corridors)

---

## 5. Correlation Rules

The engine performs deterministic multi-dimensional correlation:

1. **Direct Identity Correlation:**
   - Person identifier matching (`P-XXXXXX` / `ENT-XXXX`).
   - Phone identifier matching (`PHONE:XXXXXXXXXX`).
   - Account identifier matching (`ACCOUNT:AC-XXXXXX` / `AC-XXXXXX`).
   - Vehicle registration plate matching (`VEH-XXXX-XXXXXX`).
2. **Case Association Correlation:**
   - Evaluates whether matched entities have prior or active FIRs/chargesheets (`ACCUSED_IN`, `VICTIM_IN`).
   - Surfaces crime types (`EXTORTION`, `CYBER_FRAUD`, `NARCOTICS`, etc.) and filing agencies.
3. **Network & Community Correlation:**
   - Maps entities to detected Louvain communities.
   - Flags whether the community is marked as a Network of Interest (`is_network_of_interest`).
   - Surfaces bridge operative status and broker roles.
4. **Financial Chain Correlation:**
   - Traces if referenced accounts appear in 4-layer mule pipelines (`MuleChainModel`).
   - Surfaces whether account is classified as `LIKELY_ORGANISER`, `LIKELY_DECEIVED`, or `UNCERTAIN`.

---

## 6. Temporal Rules (`TemporalConfig`)

Timestamps are parsed into UTC datetime representations. Configurable windows:

| Window Name | Duration | Operational Justification |
| :--- | :--- | :--- |
| **Immediate** | `±3,600s` (1 hour) | Immediate incident response, rapid scam surges (e.g. 14 fake dharamshala booking complaints in 120m), or co-incident scene sightings. |
| **Short** | `±21,600s` (6 hours) | Operational shift window (e.g. morning Aarti crowd wave, evening snan shift). |
| **Extended** | `±86,400s` (24 hours) | Diurnal pattern tracking capturing movements and repeated sightings across a full day. |

A temporal match is evidence of temporal proximity only, never proof of common criminal purpose.

---

## 7. Spatial Rules & Limitations (`SpatialConfig`)

### Spatial Modeling
- When GPS coordinates (`latitude`, `longitude`) are supplied, Haversine great-circle distance is computed against `max_distance_km` (default `2.0 km`).
- **Limitation & Fallback:** In live police and surveillance feeds, exact GPS coordinates are often unavailable or restricted. In such cases, the system **NEVER** fabricates or hallucinates coordinates. Instead, it relies on explicit zone boundaries (`Ramkund`, `Panchavati`, `Tapovan`, `Trimbakeshwar`, `Godavari Ghats`).
- Spatial proximity alone is strictly categorized as `WEAK` evidence.

---

## 8. Incident Clustering (`KumbhClusterModel`)

The clustering algorithm groups related incidents deterministically without machine-learning hallucinations:

1. **Shared Infrastructure Clusters:**
   - Multiple events referencing the same financial account, phone number, or vehicle.
   - *Example:* Fake booking scam complaints across different sectors directing funds to the same mule account (`AC-000310`).
2. **Shared Entity Clusters:**
   - Multiple events referencing the same individual identifier across different zones or dates.
3. **Spatio-Temporal Bursts:**
   - $\ge 3$ events occurring in the same zone within the immediate temporal window ($\le 1\text{ hour}$).
   - Highlights crowd anomalies, coordinated fraud waves, or flash points for crowd management.

Every cluster exposes:
`cluster_id`, `cluster_type`, `member_events`, `shared_evidence`, `confidence`, `provenance`, `explanation`, and `action = "Requires investigator review"`.

---

## 9. Evidence Hierarchy & Provenance

Evidence is strictly stratified:

```text
┌────────────────────────────────────────────────────────┐
│  STRONG TIER                                           │
│  - Statutory chargesheets and FIR filings (ACCUSED_IN) │
│  - Primary banking KYC and transaction audit records   │
│  - High-confidence deterministic identity linkages     │
├────────────────────────────────────────────────────────┤
│  MEDIUM TIER                                           │
│  - Multi-hop community membership                      │
│  - Verified co-occurrence across multiple case records │
│  - ER review band linkage                              │
├────────────────────────────────────────────────────────┤
│  WEAK TIER                                             │
│  - Spatial proximity / zone co-presence                │
│  - Loose temporal co-occurrence without shared infra   │
│  - Unverified bystander observation                    │
└────────────────────────────────────────────────────────┘
```

> [!WARNING]
> WEAK tier evidence (such as being present in the same zone) can **NEVER** override, dilute, or artificially inflate STRONG tier evidence.

---

## 10. Investigator Review Object (`InvestigatorReviewObject`)

All generated intelligence items conform to:

```json
{
  "intelligence_id": "INTEL-KUMBH-EVT-0001-P-000001",
  "type": "EVENT_ENTITY_CORRELATION",
  "subject": "P-000001",
  "related_event": "KUMBH-EVT-0001",
  "confidence": 0.92,
  "signals": [
    {
      "signal_type": "KNOWN_ENTITY_MATCH",
      "description": "Entity P-000001 (Rakesh Pawar) matches identifier in Kumbh event KUMBH-EVT-0001.",
      "evidence": ["Event KUMBH-EVT-0001 references P-000001"],
      "provenance": {"source": "Kumbh Operations Feed", "event_id": "KUMBH-EVT-0001"},
      "confidence": 0.92,
      "action": "Requires investigator review"
    },
    {
      "signal_type": "KNOWN_CASE_ASSOCIATION",
      "description": "Entity P-000001 is already linked to statutory case(s): CASE-SPO-000031.",
      "evidence": ["Case filing(s): CASE-SPO-000031"],
      "provenance": {"cases": ["CASE-SPO-000031"], "crime_types": ["EXTORTION"]},
      "confidence": 0.90,
      "action": "Requires investigator review"
    }
  ],
  "evidence": [
    "Direct identifier match: P-000001 observed at Ramkund.",
    "Statutory case link: P-000001 associated with CASE-SPO-000031."
  ],
  "provenance": [
    {"source": "CASE_RECORD", "case_ref": "CASE-SPO-000031", "agency": "STATE_POLICE"}
  ],
  "evidence_tier": "STRONG",
  "network_context": {
    "entity_id": "P-000001",
    "cases": ["CASE-SPO-000031"],
    "crime_types": ["EXTORTION"],
    "communities": ["COM-001"],
    "is_network_of_interest": true,
    "roles": ["BROKER"],
    "is_bridge_candidate": true,
    "bridge_score": 0.82,
    "evidence_tier": "STRONG",
    "action": "Requires investigator review"
  },
  "explanation": "Sutradhar intelligence correlation for Kumbh event KUMBH-EVT-0001 at zone Ramkund: Subject P-000001 (Rakesh Pawar) was surfaced based on deterministic graph matching. Existing intelligence reflects 1 statutory cases, 1 community networks, and 0 financial flow linkages. Presence at Kumbh is not criminal evidence by itself. Action requires investigator review.",
  "action": "Requires investigator review"
}
```

---

## 11. False-Positive Protections (Safety Regression Matrix)

| Test Case | Scenario | Expected Behavior | Verification Status |
| :--- | :--- | :--- | :--- |
| **Case 1** | Civilian merely attending Kumbh | Classified as `CIVILIAN_OPERATIONAL_OBSERVATION`. Zero criminal signals. Zero threat labels. Evidence tier = `WEAK`. | **PASS** |
| **Case 2** | Civilian located near incident zone | Spatial association only. Proximity is not proof of involvement. Zero criminal accusations. | **PASS** |
| **Case 3** | Person already linked to case at Kumbh | Existing case context surfaced with complete provenance. No automatic guilt. `action = "Requires investigator review"`. | **PASS** |
| **Case 4** | Vehicle seen near multiple events | Produces `VEHICLE_ASSOCIATION` only with `WEAK` tier. Does not infer criminal conspiracy. | **PASS** |
| **Case 5** | Known network member at Kumbh | Network context (`COM-001`, `BROKER`) surfaced. No automatic accusation. | **PASS** |
| **Case 6** | Unrelated people at same event | No artificial syndicate or co-accused link generated between them. | **PASS** |
| **Case 7** | Weak spatial vs strong direct evidence | Hierarchy preserved: Statutory case = `STRONG`, spatial proximity = `WEAK`. Weak evidence cannot override strong evidence. | **PASS** |

---

## 12. Performance Metrics

Benchmarked on V2 Dev Tier (~300 Kumbh events, ~2,000 entities, ~5,000 edges):

- **Event Ingestion:** `< 0.05 seconds`
- **Graph Correlation:** `< 0.85 seconds`
- **Multi-Factor Clustering:** `< 0.15 seconds`
- **Total Pipeline Execution:** `< 1.20 seconds` (well below the 5.0-second SLA)
- **Time Complexity:** $O(E + V)$ indexed hash lookups, avoiding all $O(N^2)$ candidate explosions.

---

## 13. Testing & Verification Summary

The Step 4 test suite comprises **17 targeted tests** in `services/graph/tests/test_kumbh_ops.py` alongside the existing 123 baseline tests, bringing the total suite to **140 passing tests**:

- `test_case1_civilian_attending_kumbh_no_criminal_classification`
- `test_case2_civilian_near_incident_spatial_association_only`
- `test_case3_person_connected_to_case_surfaced_with_provenance`
- `test_case4_vehicle_near_multiple_events_vehicle_association_only`
- `test_case5_known_network_member_network_context_surfaced`
- `test_case6_unrelated_attendees_at_same_event_no_artificial_syndicate`
- `test_case7_evidence_hierarchy_preserved_weak_spatial_vs_strong_direct`
- `test_direct_entity_correlation_dimensions`
- `test_temporal_correlation_windows`
- `test_spatial_correlation_and_coordinate_limitation`
- `test_incident_clustering_shared_infra_and_spatio_temporal`
- `test_provenance_and_tiers`
- `test_truth_leak_audit_in_kumbh_ops`
- `test_determinism_kumbh_operations`
- `test_v2_multiseed_kumbh_regression[seed-42]`
- `test_v2_multiseed_kumbh_regression[seed-43]`
- `test_v2_multiseed_kumbh_regression[seed-44]`
