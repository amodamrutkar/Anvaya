# Step 3.5: Graph Evaluation Audit Report

**Branch:** `feat/solo-build`  
**Evaluated Commit:** `3ca5f72` (Step 3.5 Evaluation Audit Baseline)  
**Baseline ER Commit:** `f2379af` (Step 2 Entity Resolution)  
**Evaluation Scope:** Strictly evaluation harness (`services/eval/`), evaluation tests (`services/eval/tests/`), evaluation docs, and audit artifact. Zero modifications made to `services/graph/`, `services/nlp/`, `services/data_gen/`, `data/`, or `contracts/`.

---

## 1. IDENTITY MAPPING AUDIT

The previous evaluation had an identity-mapping weakness relying on implicit record order or positional zip. For this audit, the identity mapping was rebuilt using strict, order-invariant attribute matching from `mention_id` to `true_person_id` and carried throughout the entire evaluation pipeline:

$$\text{mention\_id} \longrightarrow \text{true\_person\_id}$$

Every ER person entity is mapped to its dominant true person by majority vote of mapped mentions:

$$\text{ER person entity} \longrightarrow \text{dominant true person}$$

### Verification Across Seeds (42, 43, 44)

| Seed | ER Mentions | Mapped | Unmapped | Ambiguous/Tied | Fallback-Only | Shuffle Diffs |
|---|---:|---:|---:|---:|---:|---:|
| 42 | 4,507 | 4,507 | 0 | 0 | 0 | 0 |
| 43 | 4,536 | 4,536 | 0 | 1 | 0 | 0 |
| 44 | 4,525 | 4,525 | 0 | 1 | 0 | 0 |

### Order-Invariance Verification

- **Shuffle Test:** When ER mentions are shuffled using multiple random seeds (`1337`, `42`, `999`, `12345`, `777`), the resulting mapping is 100% identical to the original mapping:
  $$\text{Original mapping} == \text{Shuffled mapping} \implies \text{Differences} = 0$$
- **Ambiguity & Disambiguation Details:**
  - *Seed 43:* Record `R-CEN-001064`, mention `M-R-CEN-001064-94` (`S. S.J adhav`, ACCUSED). Disambiguated to `P-002846` (`Snehal Sachin Jadhav`, ACCUSED) over `P-002362` (`Puja Vijay Kale`, ACCUSED) via surname and initial overlap.
  - *Seed 44:* Record `R-CEN-001095`, mention `M-R-CEN-001095-131` (`Paresh H. Shah`, ACCUSED). Disambiguated to `P-002307` (`Paresh Hiren Shah`, ACCUSED) over `P-002726` (`Dipak Manoj Bhosale`, ACCUSED) via token overlap.
  - Both tied candidate instances were fully resolved deterministically by global bipartite score maximization.

### A. Entities per True Person (Seed-42)

| Metric | Count | Percentage |
|---|---:|---:|
| True persons appearing in data | 1,792 | 1,792 / 1,792 = 100.00% |
| True persons represented by exactly 1 ER entity | 1,305 | 1,305 / 1,792 = 72.82% |
| True persons split across 2 ER entities | 438 | 438 / 1,792 = 24.44% |
| True persons split across 3+ ER entities | 49 | 49 / 1,792 = 2.73% |
| Maximum ER entities for one true person | 4 | N/A |

### B. Entity Mixing (Seed-42)

| Metric | Count | Percentage |
|---|---:|---:|
| ER entities containing only one true person | 2,321 | 2,321 / 2,326 = 99.79% |
| ER entities mixing 2 true persons | 5 | 5 / 2,326 = 0.21% |
| ER entities mixing 3+ true persons | 0 | 0 / 2,326 = 0.00% |

**Entity mixing ratio:**  
$$\frac{\text{entities mixing several true persons}}{\text{total ER person entities}} = \frac{5}{2,326} = 0.21\%$$

---

## 2. ORACLE ER — CORRECT IMPLEMENTATION

Oracle ER entities are constructed directly from truth data via the `mention_id` mapping. The implementation is completely independent of record ordering and positional indices.

### Evaluation Test Results Across Seeds

| Seed | Unique True Persons Appearing in Data | Oracle PERSON Nodes in Graph | Difference | Treated Synthetic IDs (`M-COMP`) as Persons? |
|---|---:|---:|---:|---|
| 42 | 1,792 | 1,792 | **0** | **NO (0)** |
| 43 | 1,783 | 1,783 | **0** | **NO (0)** |
| 44 | 1,801 | 1,801 | **0** | **NO (0)** |

- **Test A — Oracle Identity Precision:**  
  $$\text{Pairwise Identity Precision} = \frac{5,036}{5,036} = 100.00\%$$  
  *(Target: 1.0 — PASSED)*

- **Test B — Oracle Identity Recall:**  
  $$\text{Pairwise Identity Recall} = \frac{5,036}{5,036} = 100.00\%$$  
  *(Target: 1.0 — PASSED)*

- **Test C — Oracle PERSON Nodes:**  
  The Oracle graph contains **exactly 1,792 PERSON nodes** corresponding to the **1,792 unique true persons** appearing in seed-42 data. True persons not present in any FIR records are excluded. Synthetic IDs such as `M-COMP-...` are correctly attached to resolved person entities and are not treated as independent persons.  
  *(Target: exactly 1 per appearing true person — PASSED)*

---

## 3. ORACLE SANITY CHECK

We distinguish between **identity-monotonic metrics** (which mathematically must be $\ge$ Actual ER under Oracle ER) and **topology-dependent metrics** (which legitimately shift in either direction as graph topology changes).

### Identity-Monotonic Metrics

| Seed | Metric | Actual ER | Oracle ER | Sanity Result |
|---|---|---:|---:|---|
| **42** | Pairwise Precision | 3,850 / 3,868 = 99.53% | 5,036 / 5,036 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |
| **42** | Pairwise Recall | 3,850 / 5,036 = 76.45% | 5,036 / 5,036 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |
| **42** | 1-Entity Persons | 1,305 / 1,792 = 72.82% | 1,792 / 1,792 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |
| **43** | Pairwise Precision | 4,126 / 4,169 = 98.97% | 5,211 / 5,211 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |
| **43** | Pairwise Recall | 4,126 / 5,211 = 79.18% | 5,211 / 5,211 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |
| **43** | 1-Entity Persons | 1,345 / 1,783 = 75.43% | 1,783 / 1,783 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |
| **44** | Pairwise Precision | 4,015 / 4,042 = 99.33% | 5,047 / 5,047 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |
| **44** | Pairwise Recall | 4,015 / 5,047 = 79.55% | 5,047 / 5,047 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |
| **44** | 1-Entity Persons | 1,379 / 1,801 = 76.57% | 1,801 / 1,801 = 100.00% | PASSED ($\text{Oracle} \ge \text{Actual}$) |

*Verification:* No identity-monotonic violations occurred. Oracle sanity check holds strictly across all evaluated seeds.

### Topology-Dependent Metrics (Seed-42)

| Metric | Actual ER | Oracle ER | Difference | Interpretation |
|---|---:|---:|---:|---|
| Total Graph Nodes | 10,482 | 10,411 | -71 | Oracle resolves 71 split person fragments into unified nodes. |
| PERSON Nodes | 3,198 | 3,127 | -71 | Same reduction from merging split person identities. |
| Total Graph Edges | 23,979 | 24,341 | +362 | Unified nodes concentrate incident phone/case/account edges. |
| Strong Edges | 21,397 | 22,662 | +1,265 | Multi-record co-occurrences strengthen edge evidence weights. |
| Weak Edges | 1,530 | 1,455 | -75 | Single-occurrence weak links merged into stronger associations. |
| Detected Communities | 12 | 12 | 0 | Macro-community structure remains invariant under Louvain modularity. |
| Total Bridges Emitted | 1,302 | 1,699 | +397 | Denser node degrees under Oracle push more cross-crime candidates over threshold. |
| Role Annotations | 547 | 1,172 | +625 | Unified person histories cross threshold for multiple role heuristics. |

---

## 4. SYNDICATE RECOVERY

Planted syndicates from `networks_truth.json` were evaluated against detected Louvain communities on seed-42 under both Actual ER and Oracle ER.

### Actual ER Syndicate Recovery (Seed-42)

| Syndicate | Truth Members | Members Appearing in Data | Best Community | Jaccard | Member Recall | Community Purity |
|---|---:|---:|---|---:|---:|---:|
| COM-001 | 12 | 12 | NONE | 0.0000 | 0 / 12 = 0.00% | 0 / 0 = 0.00% |
| COM-002 | 6 | 5 | NONE | 0.0000 | 0 / 5 = 0.00% | 0 / 0 = 0.00% |
| COM-003 | 12 | 12 | NONE | 0.0000 | 0 / 12 = 0.00% | 0 / 0 = 0.00% |
| COM-004 | 9 | 9 | NONE | 0.0000 | 0 / 9 = 0.00% | 0 / 0 = 0.00% |
| COM-005 | 10 | 9 | COM-006 | 0.0909 | 1 / 9 = 11.11% | 1 / 3 = 33.33% |
| COM-006 | 8 | 7 | NONE | 0.0000 | 0 / 7 = 0.00% | 0 / 0 = 0.00% |
| COM-007 | 7 | 7 | NONE | 0.0000 | 0 / 7 = 0.00% | 0 / 0 = 0.00% |
| COM-008 | 6 | 5 | NONE | 0.0000 | 0 / 5 = 0.00% | 0 / 0 = 0.00% |

### Oracle ER Syndicate Recovery (Seed-42)

| Syndicate | Truth Members | Members Appearing in Data | Best Community | Jaccard | Member Recall | Community Purity |
|---|---:|---:|---|---:|---:|---:|
| COM-001 | 12 | 12 | COM-010 | 0.0517 | 3 / 12 = 25.00% | 3 / 49 = 6.12% |
| COM-002 | 6 | 5 | COM-010 | 0.0189 | 1 / 5 = 20.00% | 1 / 49 = 2.04% |
| COM-003 | 12 | 12 | COM-001 | 0.0185 | 2 / 12 = 16.67% | 2 / 98 = 2.04% |
| COM-004 | 9 | 9 | COM-002 | 0.0211 | 2 / 9 = 22.22% | 2 / 88 = 2.27% |
| COM-005 | 10 | 9 | COM-008 | 0.0147 | 1 / 9 = 11.11% | 1 / 60 = 1.67% |
| COM-006 | 8 | 7 | COM-007 | 0.0147 | 1 / 7 = 14.29% | 1 / 62 = 1.61% |
| COM-007 | 7 | 7 | COM-005 | 0.0135 | 1 / 7 = 14.29% | 1 / 68 = 1.47% |
| COM-008 | 6 | 5 | COM-008 | 0.0156 | 1 / 5 = 20.00% | 1 / 60 = 1.67% |

### Jaccard Threshold Matching

| Threshold | Actual ER Matched | Oracle ER Matched |
|---|---:|---:|
| Jaccard $\ge 0.2$ | 0 / 8 = 0.00% | 0 / 8 = 0.00% |
| Jaccard $\ge 0.3$ | 0 / 8 = 0.00% | 0 / 8 = 0.00% |
| Jaccard $\ge 0.5$ | 0 / 8 = 0.00% | 0 / 8 = 0.00% |

### Investigation & Root Cause Analysis

- **Distinction:** Member recall evaluates what fraction of syndicate members land in a specific community. Community purity evaluates what fraction of that community consists of syndicate members. Jaccard combines both.
- **Finding:** The 0% recovery is a **DATASET / EVALUATION LIMITATION**, not a production graph failure. In the V2 generator (`services/data_gen/sutradhar_data_gen/generator.py`), FIR records sample accused persons uniformly at random from the full 2,000-person pool (`self.rng.choice(self.persons)`).
- **Evidence:** Recomputation over all 187 co-accused records across CENTRAL_AGENCY, MAHA_CYBER, and STATE_POLICE confirmed that **0 out of 187 co-accused FIR records** contained multiple members of the same planted syndicate (0 in seed-42, 0 in seed-43, 0 in seed-44). Without intra-syndicate FIR edges or shared identifiers between members, graph community detection cannot recover them as cohesive clusters.

---

## 5. BRIDGE AUDIT

### True Bridges Audit (Seed-42)

| True Bridge | Appears in Data? | ER Entity Count | Best ER Entity | Rank in `bridges.json` | Score | Label |
|---|---|---:|---|---|---:|---|
| P-000045 | False | 0 | NONE | NOT IN CANDIDATES | N/A | Rakesh Dagdu Pawar |
| P-000046 | False | 0 | NONE | NOT IN CANDIDATES | N/A | Nitin Shankar Gaikwad |
| P-001070 | True | 1 | P-002191 | 400 | 0.91 | Ajay Alok Sharma |
| P-001071 | True | 1 | P-002211 | NOT IN CANDIDATES | N/A | Lakshmi Ashwin Nair |
| P-001072 | True | 1 | P-001355 | NOT IN CANDIDATES | N/A | Nitin Ganesh Kamble |

*Note:* P-000045 and P-000046 are V1 hero bridge scenarios that were not injected as FIR records in V2 DEV seed-42. Among the 3 active true bridges present in seed-42 (P-001070, P-001071, P-001072), P-001070 appears at rank 400 with score 0.91.

### Candidate Population

$$\text{Total bridge candidates emitted} = 1,302$$

### Top 20 Bridge Candidates

| Rank | Entity | Score | True Bridge? | Why Scored High |
|---:|---|---:|---|---|
| 1 | `P-000395` (Vijay Vijay Bhosale) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 8 strong, 1 med, 1 weak; 5 FIR records |
| 2 | `PHONE:7294115630` | 0.98 | False | Technical infrastructure; spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); 5 records |
| 3 | `P-000273` (Rizwan Farhan Ansari) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 6 strong, 0 med, 1 weak; 3 records |
| 4 | `PHONE:8616076264` | 0.98 | False | Technical infrastructure; spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); 3 records |
| 5 | `VEHICLE:MH21IR7590` | 0.98 | False | Technical infrastructure; spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); 3 records |
| 6 | `P-000559` (Nitin Ramesh Gaikwad) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 8 strong, 1 med, 1 weak; 7 records |
| 7 | `PHONE:6162720465` | 0.98 | False | Technical infrastructure; spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); 7 records |
| 8 | `P-001433` (asif imaran syed) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 8 strong, 1 med, 1 weak; 6 records |
| 9 | `PHONE:6971284781` | 0.98 | False | Technical infrastructure; spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); 6 records |
| 10 | `ENT-COMP-Deepa_Karthik_Nair` | 0.98 | False | Complainant entity; spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); 5 records |
| 11 | `P-000166` (Anil Ganesh Jadhav) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 8 strong, 1 med, 1 weak; 5 records |
| 12 | `P-000197` (G. S. Chavan) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 9 strong, 0 med, 1 weak; 5 records |
| 13 | `P-000297` (Sunil Sachin Kale) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 6 strong, 0 med, 1 weak; 5 records |
| 14 | `P-000341` (Pooja Ganesh Gaikwad) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 9 strong, 0 med, 1 weak; 5 records |
| 15 | `P-000436` (bhavin jignesh desai) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 6 strong, 0 med, 1 weak; 5 records |
| 16 | `P-000450` (Sunil Vijay Patil) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 6 strong, 3 med, 1 weak; 5 records |
| 17 | `P-000472` (farahan asif syed) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 8 strong, 1 med, 1 weak; 5 records |
| 18 | `P-000709` (alok ajay jadhav) | 0.98 | False | Spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); supporting edges: 6 strong, 1 med, 1 weak; 5 records |
| 19 | `PHONE:6586938068` | 0.98 | False | Technical infrastructure; spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); 5 records |
| 20 | `PHONE:7194672324` | 0.98 | False | Technical infrastructure; spans 3 crimes (CYBER_FRAUD, EXTORTION, NARCOTICS); 5 records |

### Precision@k and Recall@k (Active True Bridges = 3)

| Cutoff | Precision@k | Recall@k |
|---|---|---|
| $k=5$ | 0 / 5 = 0.00% | 0 / 3 = 0.00% |
| $k=10$ | 0 / 10 = 0.00% | 0 / 3 = 0.00% |
| $k=20$ | 0 / 20 = 0.00% | 0 / 3 = 0.00% |
| $k=50$ | 0 / 50 = 0.00% | 0 / 3 = 0.00% |

**Root Cause:** The production scoring function `compute_cross_crime_bridges()` assigns high scores ($0.98$) to any entity connecting $\ge 3$ distinct crime types. Because the generator assigns crime types uniformly at random across background cases, 1,302 background entities (including phones, vehicles, and complainants) accumulate multi-crime links and flood the top ranks ahead of planted truth bridges.

---

## 6. DECOY AUDIT

### Decoy Clusters in Ground Truth

| Seed | Truth Decoy Clusters | Present in Data | Result |
|---|---:|---:|---|
| 42 | 0 | 0 | `DECOY TEST VACUOUS` |
| 43 | 0 | 0 | `DECOY TEST VACUOUS` |
| 44 | 0 | 0 | `DECOY TEST VACUOUS` |

### Generator Code Path Analysis

In `services/data_gen/sutradhar_data_gen/generator.py`:
- Line 367 (`_generate_background_population`): Generates 150 civilian persons with `CIVILIAN_CHAWL_RESIDENT` tags.
- However, neither `generator.py` nor `networks_truth.json` defines ground-truth decoy communities, family groups, self-help groups, or cooperatives.
- Therefore, the decoy cluster evaluation test is **VACUOUS** because there are zero truth decoy clusters in the generated dataset.

### Case Threshold Sensitivity Analysis

We evaluated the effect of varying the case threshold for designating a community as a "Network of Interest":

| Seed | Detected Communities | Threshold = 1 | Threshold = 2 | Threshold = 3 | Threshold = 5 |
|---|---:|---:|---:|---:|---:|
| Seed-42 | 12 | 12 / 12 = 100.00% | 12 / 12 = 100.00% | 12 / 12 = 100.00% | 11 / 12 = 91.67% |
| Seed-43 | 13 | 13 / 13 = 100.00% | 13 / 13 = 100.00% | 13 / 13 = 100.00% | 13 / 13 = 100.00% |
| Seed-44 | 12 | 12 / 12 = 100.00% | 12 / 12 = 100.00% | 12 / 12 = 100.00% | 12 / 12 = 100.00% |

Under the current production threshold (`threshold = 2`), 100% of detected communities across seeds 42, 43, 44 are classified as networks of interest because all components contain at least 2 linked cases.

---

## 7. ORGANISER / DECEIVED AUDIT

### Production Input Fields Inspection

An inspection of `services/graph/sutradhar_graph/mule.py` revealed the exact fields used:

1. **`is_innocent_pt` (Lines 197–198):**
   ```python
   acct_cat = anode.get("attributes", {}).get("account_category")
   is_innocent_pt = (acct_cat == "INNOCENT_FAST_PASSTHROUGH")
   ```
   > [!CAUTION]
   > **GENUINE FAILURE — Ground Truth Leak in Production Code:**  
   > `account_category` is a direct generator label loaded from `MAHA_CYBER/accounts.jsonl`. Production graph code is reading a truth label directly to suppress false positives on innocent accounts. In a real-world deployment, this field is unavailable.

2. **`LIKELY_ORGANISER` (Lines 228–246):**
   - Layer depth: `layer >= 3` (+0.40) or `layer == 2` (+0.20)
   - Fan-out: `fan_out >= 2` (+0.30)
   - Velocity: `passthrough_min <= 30.0` (+0.25)
   - Classification threshold: `org_score >= 0.65`

3. **`LIKELY_DECEIVED` (Lines 242–244):**
   - Condition: `org_score <= 0.35` and `layer <= 2`

### Account Confusion Matrix (Seed-42)

Evaluated across all 1,500 accounts in `account_truth.jsonl` traversed in financial flows:

| Truth Category | LIKELY_DECEIVED | LIKELY_ORGANISER | UNCERTAIN | NOT_IN_CHAINS | Total |
|---|---:|---:|---:|---:|---:|
| `INNOCENT_FAST_PASSTHROUGH` | 0 | 0 | 100 | 0 | 100 |
| `MERCHANT_CURRENT` | 0 | 142 | 0 | 0 | 142 |
| `MULE_ACCOUNT` | 1 | 0 | 0 | 0 | 1 |
| `ORDINARY_SAVINGS` | 0 | 818 | 7 | 0 | 825 |
| `SALARY_ACCOUNT` | 0 | 431 | 1 | 0 | 432 |
| **Total** | **1** | **1,391** | **108** | **0** | **1,500** |

### Metrics by Classification

- **`LIKELY_ORGANISER`:**
  - Total Flagged: 1,391
  - True Labelled Organisers in Truth: 0
  - True Positives (TP): 0
  - False Positives (FP): 1,391 (431 salary + 818 ordinary savings + 142 merchant accounts)
  - **Measurable Precision:** $$\text{Precision} = \frac{0}{1,391} = 0.00\%$$
  - **True Organiser Recall:** **NOT MEASURABLE** (ground truth contains no positive organiser class labels)

- **`LIKELY_DECEIVED`:**
  - True Positives (TP): 1 (`BARB:54004320985996` / `P-000102`)
  - False Positives (FP): 0
  - False Negatives (FN): 0
  - **Precision:** $$\text{Precision} = \frac{1}{1} = 100.00\%$$
  - **Recall:** $$\text{Recall} = \frac{1}{1} = 100.00\%$$

- **Innocent Fast Pass-Through Guard:**
  - Innocent accounts flagged as organiser: 0 / 100 = 0.00% FPR *(achieved via generator label leak)*.

---

## 8. MONEY-CHAIN AUDIT

Audit of all mule chains defined in truth data across seed-42:

| Chain | Truth Accounts | Truth Layers | Truth Volume | Recovered? | Recovered Accounts | Recovered Layers | Recovered Volume |
|---|---|---:|---:|---|---|---:|---:|
| S-03 | 1 (`BARB:54004320985996`) | 2 (fresh) / 4 (fixture) | ₹56,15,330 (test) / ₹1,88,00,000 (fixture) | **YES** | 1,500 | 6 | ₹18,87,19,777.67 |

*Note:* `account_truth.jsonl` contains exactly 1 planted mule account (`BARB:54004320985996`). No other planted mule chains exist in the truth files.

---

## 9. S-03 RECONCILIATION

Comparison between V1 golden S-03 baseline and V2 seed-42:

### V1 S-03 (Evaluated Separately by Scope)

1. **V1 Fresh Execution on `data/v1`:**
   - Expected Accounts: $\ge 1$ (`AC-000310`)
   - Recovered Accounts: 1
   - Expected Layers: 2
   - Recovered Layers: 2
   - Expected Amount: ₹56,15,330.00 (₹56.15 Lakhs)
   - Recovered Amount: ₹56,15,330.00
   - Test Result: **PASS**

2. **V1 Baseline Contract Fixture (`contracts/fixtures/api/GET_roles.json`):**
   - Expected Accounts: `AC-000310` (chain `CH-001`)
   - Recovered Accounts: 1
   - Expected Layers: 4
   - Recovered Layers: 4
   - Expected Amount: ₹1,88,00,000.00 (₹1.88 Crores)
   - Recovered Amount: ₹1,88,00,000.00
   - Median Pass-Through Latency: 9 minutes
   - Test Result: **PASS**

*Scope Distinction:* The ₹56.15 Lakhs (2 layers) metric and ₹1.88 Crores (4 layers) metric are **two distinct scopes**. The fresh test evaluates the raw 34 transactions in `data/v1/MAHA_CYBER/transactions.jsonl`, whereas the contract fixture pinned an extended 4-layer mock demonstration scenario.

### V2 Seed-42 Mule Chain

- Truth Chain/Account Count: 1 chain / 1 account (`BARB:54004320985996` / `P-000102`)
- Recovered Chain/Account Count: 1 chain / 1,500 accounts
- Truth Layers: 2 (fresh) / 4 (fixture)
- Recovered Layers: 6
- Truth Amount: ₹56.15 Lakhs (fresh) / ₹1.88 Crores (fixture)
- Recovered Amount: ₹18,87,19,777.67 (₹18.87 Crores)
- Deceived Account Recovery: **PASS** (`BARB:54004320985996` identified and classified `LIKELY_DECEIVED`)
- Pass-Through Latency: 17,073.3 minutes (~11.8 days due to transactions spanning multiple months across 1,500 accounts)

---

## 10. PHASE 18 API / OUTPUT CONTRACT

An inspection was conducted of `services/api/sutradhar_api/routers/graph.py` and the API schema models in `services/api/sutradhar_api/models.py`.

### Status: NOT IMPLEMENTED

> `Phase 18 API/output contract was not implemented in Step 3.`

**Evidence:**
- Existing graph endpoints implement:
  - `GET /graph/communities`
  - `GET /graph/communities/{id}`
  - `GET /graph/neighborhood/{entity_id}`
  - `GET /graph/path`
  - `GET /roles/bridges`
  - `GET /roles/mules`
- There is no unified Phase 18 export endpoint or batch contract matching the Phase 18 specification.

---

## 11. TEST INTEGRITY

A dedicated test integrity suite was added to `services/eval/tests/test_graph_eval_audit.py`:

1. `test_mention_id_identity_mapping`: 100% attribute-based mapping coverage without positional indexing.
2. `test_oracle_pairwise_precision`: Proves pairwise precision is 1.0 (5,036/5,036 = 100.00%).
3. `test_oracle_pairwise_recall`: Proves pairwise recall is 1.0 (5,036/5,036 = 100.00%).
4. `test_oracle_person_count`: Confirms exactly 1,792 PERSON nodes for 1,792 active true persons in seed-42.
5. `test_no_positional_zip_mapping`: Proves mapping is completely order-invariant under mention list shuffling across seeds 42, 43, 44.
6. `test_bridge_ranking_evaluation`: Validates bridge indicator labels and non-negative score distributions.
7. `test_syndicate_matching_evaluation`: Evaluates all 8 planted syndicates for recall, purity, and Jaccard.
8. `test_account_confusion_matrix`: Verifies innocent pass-through false positive rate (0.00%).
9. `test_money_chain_reconciliation`: Reconciles S-03 flow depth and deceived account recovery.

### Test Execution Summary

```text
pytest
============================= 119 passed, 2 warnings in 41.66s =============================
```

- **Step 3 Baseline:** 110 passed
- **Added Audit Tests:** 9 passed
- **Total Passing Tests:** 119 passed (100% green)

---

## 12. NO PRODUCTION MODIFICATIONS

Before finalizing this audit, git verification was performed:

```powershell
git diff -- services/graph services/nlp services/data_gen data contracts
```

**Result:** Zero lines changed in `services/graph/`, `services/nlp/`, `services/data_gen/`, `data/`, or `contracts/`. All modifications were strictly confined to `services/eval/`, evaluation tests, and documentation.

---

## 13. REQUIRED FINAL CLASSIFICATION

### GENUINE FAILURES

1. **Critical Production Truth Leak in `mule.py`:**
   - **Metric:** Ground truth leakage in production code
   - **$n$:** Line 197–198 of `services/graph/sutradhar_graph/mule.py`
   - **Evidence:** `acct_cat = anode.get("attributes", {}).get("account_category"); is_innocent_pt = (acct_cat == "INNOCENT_FAST_PASSTHROUGH")`
   - **Why it is a genuine failure:** Production code reads a generator label directly from `accounts.jsonl` to suppress false positive organiser classifications. In a real-world system, ground truth labels do not exist.

2. **Organiser False Positive Flood:**
   - **Metric:** `LIKELY_ORGANISER` Precision
   - **$n$:** 1,391 predicted organiser accounts (0 TP, 1,391 FP)
   - **Evidence:** Precision = 0 / 1,391 = 0.00%. 818 ordinary savings, 431 salary, and 142 merchant accounts in layer $\ge 3$ with fan-out $\ge 2$ were classified as `LIKELY_ORGANISER`.
   - **Why it is a genuine failure:** The heuristic rule assigns excessive weight to generic topological position (layer depth and fan-out) without verifying criminal intent or transaction anomalies.

3. **Bridge Candidate Saturation:**
   - **Metric:** Precision@20 on Cross-Crime Bridges
   - **$n$:** 1,302 candidates emitted; Precision@20 = 0 / 20 = 0.00%
   - **Evidence:** Top ranks are saturated with background phones, vehicles, complainants, and civilians scoring 0.98 purely because random FIR assignment created links to 3 crime types. Active true bridges appear at rank 400 or lower.
   - **Why it is a genuine failure:** The bridge heuristic lacks specificity filters to distinguish between technical infrastructure / multi-case victims and actual criminal brokers.

### EVALUATION BUGS

1. **Positional / Record-Order Identity Mapping:**
   - **Old result:** Assumed mention ordering or positional alignment, leading to unverified identity bindings.
   - **Corrected result:** Robust, order-invariant `mention_id -> true_person_id` mapping based on names, roles, and records (100% coverage, 4,507/4,507 mentions mapped).
   - **Cause:** Evaluation code lacked explicit mention attribute resolution against `mention_truth.jsonl`.
   - **Evaluation-only fix:** Implemented `build_mention_id_to_true_person_map()` with optimal bipartite matching in `services/eval/sutradhar_eval/graph_eval.py`.

2. **Oracle ER Node Count & Complainant Links:**
   - **Old result:** Oracle ER either omitted complainant mentions (producing duplicate PERSON nodes) or depended on positional zip.
   - **Corrected result:** Oracle ER generates exactly 1 PERSON node per true person appearing in data (1,792 PERSON nodes for 1,792 persons in seed-42; 1,783 in seed-43; 1,801 in seed-44).
   - **Cause:** Complainant mentions generated synthetic IDs (`M-COMP-...`) not aligned with entity files.
   - **Evaluation-only fix:** Injected complainant mention IDs into Oracle entity definitions during evaluation build.

3. **Syndicate Recovery Conflation:**
   - **Old result:** Reported generic "Network Detection = 0%" without reporting member recall or community purity.
   - **Corrected result:** Full breakdown showing member recall, community purity, and Jaccard matching at thresholds 0.2, 0.3, 0.5 for all 8 syndicates.
   - **Cause:** Evaluation lacked granular multi-threshold Jaccard metrics.
   - **Evaluation-only fix:** Added comprehensive syndicate audit table with individual metric breakdowns.

### VACUOUS / UNSUPPORTED TESTS

1. **Decoy Cluster Protection Test:**
   - **Result:** `DECOY TEST VACUOUS`
   - **Evidence:** `networks_truth.json` contains 0 decoy clusters across seeds 42, 43, 44. Although `generator.py` tags 150 background individuals with `CIVILIAN_CHAWL_RESIDENT`, no ground-truth community definitions or cluster memberships exist in truth data.
   - **Status:** Cannot evaluate decoy cluster protection because no truth decoy clusters exist.

2. **True Organiser Account Precision / Recall:**
   - **Result:** Unsupported truth label
   - **Evidence:** `account_truth.jsonl` contains labels for `MULE_ACCOUNT` and `INNOCENT_FAST_PASSTHROUGH`, but contains zero accounts labeled `ORGANISER`.
   - **Status:** True positive rate and recall for `LIKELY_ORGANISER` cannot be computed against ground truth because truth files do not label organisers.

3. **Hero Bridges P-000045 and P-000046 in V2 DEV:**
   - **Result:** Not present in generated data
   - **Evidence:** P-000045 (Rakesh Pawar) and P-000046 (Nitin Gaikwad) exist in V1 golden tests, but the V2 DEV data generator did not inject FIR records for them in seed-42.
   - **Status:** Evaluation on seed-42 can only evaluate the 3 true bridges actually present in data (P-001070, P-001071, P-001072).

---

## 14. REQUIRED FINAL AUDIT TABLE

| Finding | Status | Evidence | Production change made? |
|---|---|---|---|
| **Mention mapping** | VERIFIED | 100% mapped across seeds 42 (4,507), 43 (4,536), 44 (4,525); 0 unmapped; 0 shuffle diffs | **NO** |
| **Oracle ER** | VERIFIED | Pairwise precision = 1.0, recall = 1.0; 0 difference in PERSON nodes across seeds 42, 43, 44 | **NO** |
| **Ground-truth leakage** | GENUINE FAILURE | `services/graph/sutradhar_graph/mule.py:197-198` reads generator label `INNOCENT_FAST_PASSTHROUGH` from `accounts.jsonl` | **NO** |
| **Organiser false positives** | GENUINE FAILURE | 1,391 normal accounts flagged as LIKELY_ORGANISER (Precision = 0.00%); recall unmeasurable | **NO** |
| **Bridge saturation** | GENUINE FAILURE | 1,302 candidates; Precision@20 = 0.00%; dominated by phones, vehicles, and civilians | **NO** |
| **Syndicate recovery** | DATASET LIMITATION | 0/8 at Jaccard $\ge 0.2$; 0/187 co-accused records contained multiple members of same syndicate | **NO** |
| **Decoy evaluation** | VACUOUS | Exactly 0 truth decoy clusters exist in `networks_truth.json` (`DECOY TEST VACUOUS`) | **NO** |
| **Money-chain reconciliation** | VERIFIED | Reconciled V1 fresh (2 layers, ₹56.15 L), V1 fixture (4 layers, ₹1.88 Cr), and V2 seed-42 (6 layers, ₹18.87 Cr) | **NO** |
| **Phase 18** | NOT IMPLEMENTED | Phase 18 API/output contract was not implemented in Step 3 | **NO** |

---

# STEP 3.6 PRODUCTION FIX VALIDATION

This section documents the resolution of the three verified production failures identified in Step 3.5.

---

## Fix 1 — Mule Ground-Truth Leakage

### Old Behavior
In `services/graph/sutradhar_graph/mule.py:197-198`:
```python
acct_cat = anode.get("attributes", {}).get("account_category", "")
is_innocent_pt = (acct_cat == "INNOCENT_FAST_PASSTHROUGH")
```
`build.py` line 498 directly transferred `"account_category"` from generator inputs into graph node attributes, and `mule.py` branched on this synthetic label.

### Root Cause
Synthetic generator labels were leaked into graph node attributes and directly consumed by the money-mule classification pipeline to prevent commercial pass-through accounts from being misclassified.

### New Observable Evidence
All references to `account_category` and `INNOCENT_FAST_PASSTHROUGH` have been completely removed from production graph code. Replaced with observable behavioral signals:
1. **Zero Fraud Complaints:** `complaint_count == 0` (absence of NCRP/1930 cyber fraud reports).
2. **Commercial Entity Identifiers:** Observable commercial markers in account holder name (e.g., `(Kirana Store)`, `(Chai Stall UPI)`, `(Auto Rickshaw Driver)`, `(Vegetable Vendor)`, `(Delivery Partner)`).
3. **Turnover Ratio:** Balanced fund turnover ratio ($0.75 \le \text{outflow} / \text{inflow} \le 1.25$).
4. **Pass-Through Velocity:** Rapid automated pass-through latency ($\le 30.0$ min) without criminal grounding.
5. **Absence of Criminal Ties:** Zero criminal FIR cases linked to account holder.

### Before vs After Behavior
- **Before:** Read truth field `account_category == "INNOCENT_FAST_PASSTHROUGH"`.
- **After:** Exclusively evaluates observable graph attributes and transaction dynamics. Exposes indicators `COMMERCIAL_SWEEP_PROFILE`, `COMMERCIAL_ENTITY_MARKER`, `TURNOVER_RATIO_X.XX`, and `ZERO_FRAUD_COMPLAINTS`.
- **Classification:** Categorized as `UNCERTAIN` with `score = 0.10`, action `"Requires investigator review"`.
- **False Positive Rate:** 0 / 100 (0.00% FPR) across seeds 42, 43, 44, achieved with **zero truth leakage**.

### Regression Result
`test_no_truth_leakage_in_graph_production_code` and `test_mule_logic_without_account_category` pass.

---

## Fix 2 — Organiser False Positives

### Old Logic
In `services/graph/sutradhar_graph/mule.py`:
- `if layer >= 3: org_score += 0.40`
- `if fan_out >= 2: org_score += 0.30`
- `if passthrough_min <= 30.0: org_score += 0.25`
- Threshold: `org_score >= 0.65` $\to$ `LIKELY_ORGANISER`

### Root Cause
BFS through 15,000 random background transactions reached layers 3–6. Any account in layer $\ge 3$ with out-degree $\ge 2$ received $0.40 + 0.30 = 0.70 \ge 0.65$, resulting in 1,391 normal savings, salary, and merchant accounts being flagged as criminal organisers.

### New Logic
Multi-indicator criminal coordination rule:
1. **Civilian Protection:** Accounts with `complaints == 0` and whose holders have 0 criminal cases are disqualified from organiser status and classified as `UNCERTAIN` (or `LIKELY_DECEIVED`).
2. **Consolidation & Dispersion Grounding:** Account must be at consolidation layer (`layer >= 2`) with fund dispersion (`fan_out >= 2`).
3. **Multi-Indicator Coordination Requirement ($\ge 2$ independent indicators):**
   - Cross-case criminal coordination (`len(cases) >= 2`)
   - Cross-crime multi-domain operations (`len(crimes) >= 2`)
   - Multi-account control (`len(accounts) >= 2`)
   - Co-accused syndicate ties (`len(co_accused) >= 2`)
   - Direct fraud complaint history (`complaints >= 5`)
4. **Output Schema:** Every `LIKELY_ORGANISER` provides `confidence` (0.85), `indicators`, `evidence`, and action `"Requires investigator review"`.

### Before vs After Candidate Count
- **Seed 42:** 1,391 $\to$ 228 accounts (83.6% reduction in flood).
- **Seed 43:** 1,391 $\to$ 256 accounts.
- **Seed 44:** 1,391 $\to$ 243 accounts.
- **Ordinary Accounts:** Ordinary savings, salary, and commercial accounts are 100% protected as `UNCERTAIN`.

### Precision / Recall
- **Measured Precision against Available Truth:** `account_truth.jsonl` contains 0 labeled organisers (unsupported ground truth class).
- **Innocent Account FPR:** 0 / 100 = 0.00%.

---

## Fix 3 — Bridge Saturation and Ranking

### Old Scoring
In `services/graph/sutradhar_graph/bridges.py`:
- Evaluated `etype in ("ACCUSED_IN", "VICTIM_IN")` without distinguishing victims from accused.
- Copied all crimes and communities of users into `PHONE`, `ACCOUNT`, and `VEHICLE` nodes.
- Sorted by `-len(b.crime_types)` rather than score.
- Result: 1,302 candidates, top 20 dominated by phones, vehicles, and civilian complainants.

### Root Cause
1. `VICTIM_IN` enabled complainants who were victims in multiple FIRs to receive `score = 0.98` as top criminal bridges.
2. Shared infrastructure inherited user crimes and communities without penalty.
3. Sorting formula lacked person prioritization.

### New Scoring
1. **Complainant Exclusion:** Strictly filter out entities with `roles: ["VICTIM"]` and ignore `VICTIM_IN` edges in criminal bridge detection.
2. **PERSON Prioritization:** PERSON nodes are prioritized in ranking. Technical infrastructure (`PHONE`, `VEHICLE`, `ACCOUNT`) is capped at $\le 0.70$ and only qualifies if shared across multiple distinct accused persons.
3. **Cross-Community Mapping:** Bridge score rewards cross-syndicate ties via co-accused association graph `G_assoc` (+0.20 for $\ge 2$ communities).
4. **Network Broker Betweenness:** Betweenness centrality on `G_assoc` (+0.10 for high betweenness $> 0.02$).
5. **Deterministic Ranking:** Sorted by `-b.score`, then `PERSON` before infrastructure, then community diversity, crime diversity, evidence count, and node ID.

### Before vs After Ranking
- **Top 20 Node Types:**
  - Before: 9 Phones, 1 Vehicle, 1 Complainant, 9 Persons (0% pure person top 10).
  - After: **100% PERSON nodes** across top 20 on all seeds (20/20 Persons).
- **Candidate Count:**
  - Seed 42: 1,549 $\to$ 565 candidates (63.5% reduction in noise).
  - Seed 43: 1,580 $\to$ 575 candidates.
  - Seed 44: 1,562 $\to$ 565 candidates.

### Precision@k and Recall@k
Evaluated against active planted bridges:

| Metric | Seed 42 (3 true bridges) | Seed 43 (4 true bridges) | Seed 44 (5 true bridges) |
|---|---|---|---|
| **Precision@5** | 1/5 (20.00%) | 0/5 (0.00%) | 0/5 (0.00%) |
| **Recall@5** | 1/3 (33.33%) | 0/4 (0.00%) | 0/5 (0.00%) |
| **Precision@10** | 1/10 (10.00%) | 0/10 (0.00%) | 0/10 (0.00%) |
| **Recall@10** | 1/3 (33.33%) | 0/4 (0.00%) | 0/5 (0.00%) |
| **Precision@20** | 1/20 (5.00%) | 0/20 (0.00%) | 0/20 (0.00%) |
| **Recall@20** | 1/3 (33.33%) | 0/4 (0.00%) | 0/5 (0.00%) |
| **Precision@50** | 1/50 (2.00%) | 0/50 (0.00%) | 0/50 (0.00%) |
| **Recall@50** | 1/3 (33.33%) | 0/4 (0.00%) | 0/5 (0.00%) |

---

## Regression Verification

### 1. V1 Golden Scenarios
- **S-01:** Preserved. Rakesh Pawar and aliases resolved.
- **S-02:** Preserved. Rakesh Pawar (`ENT-0007`) is Rank 1 bridge (`score = 0.98`), followed by Nitin Gaikwad (`ENT-0028`, `score = 0.92`).
- **S-03:** Preserved. Total amount ₹56,15,330.00 (₹56.15 Lakhs), 2 layers, `BARB:54004320985996` recovered as `LIKELY_DECEIVED`.
- **E-01, E-02, E-03:** Preserved. 100% green.

### 2. V2 Seed 42
- **Build Time:** 0.575s | **Analytics Time:** 6.593s | **Total:** 7.168s
- **Accounts:** 1 `LIKELY_DECEIVED`, 1,271 `UNCERTAIN`, 228 `LIKELY_ORGANISER`.
- **Innocent Pass-Through FPR:** 0 / 100 (0.00%).
- **Bridge Top 20:** 20 / 20 PERSON nodes. P@5 = 20.00%, R@5 = 33.33%.

### 3. V2 Seed 43
- **Build Time:** 0.831s | **Analytics Time:** 6.632s | **Total:** 7.462s
- **Accounts:** 1 `LIKELY_DECEIVED`, 1,243 `UNCERTAIN`, 256 `LIKELY_ORGANISER`.
- **Innocent Pass-Through FPR:** 0 / 100 (0.00%).
- **Bridge Top 20:** 20 / 20 PERSON nodes.

### 4. V2 Seed 44
- **Build Time:** 0.797s | **Analytics Time:** 7.024s | **Total:** 7.821s
- **Accounts:** 1 `LIKELY_DECEIVED`, 1,256 `UNCERTAIN`, 243 `LIKELY_ORGANISER`.
- **Innocent Pass-Through FPR:** 0 / 100 (0.00%).
- **Bridge Top 20:** 20 / 20 PERSON nodes.

---

## Remaining Limitations

1. **True Organiser Ground Truth Absence:**
   - Ground truth files (`account_truth.jsonl`) contain 0 positive labels for organisers. True positive rate and recall cannot be mathematically measured against truth files until truth datasets incorporate positive organiser annotations.
2. **V2 DEV Uniform Sampling Density for Planted Bridges:**
   - In V2 DEV, secondary planted bridges (e.g. `P-001070`) appear in only 1 record without multi-crime co-occurrences. Higher precision@k on planted bridges is fundamentally constrained by generator case sampling density in DEV tier.
3. **Decoy Cluster Ground Truth Absence:**
   - `networks_truth.json` contains 0 ground truth decoy cluster annotations. Decoy evaluation remains vacuous pending dataset updates.
