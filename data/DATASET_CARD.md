# Dataset Card: Sutradhar Synthetic Crime and Financial Intelligence Dataset

## 1. Overview & Purpose

The **Sutradhar Synthetic Dataset** is a purpose-built, multi-agency benchmark designed to evaluate cross-agency entity resolution, mule-account chain discovery, and community detection in law-enforcement intelligence scenarios.

### CRITICAL NOTICE: 100% SYNTHETIC DATA
> **NO REAL PERSONS, ORGANISATIONS, OR CRIMINAL CASES ARE REPRESENTED.**
> Every person name, father's name, phone number, bank account number, vehicle registration number, address, narrative, and agency case reference in this dataset has been generated algorithmically.
> Any similarity to actual persons (living or dead), actual bank accounts, actual phone numbers, or real incidents is purely coincidental.
>
> - **Phone numbers:** Fictitious 10-digit numbers generated under standard Indian numbering patterns (starting 6/7/8/9).
> - **Bank accounts:** 14-digit synthetic numbers with mock IFSC prefixes (e.g., `HDFC0XXXXX`, `SBIN0XXXXX`).
> - **Addresses:** Algorithmic combinations of synthetic police station jurisdictions and Maharashtra districts.
> - **FIR / Complaint references:** Synthetic numbering schemes prefixed by agency codes (`CASE-SPO-*`, `CASE-CYB-*`, `CASE-CEN-*`).

---

## 2. Dataset Architecture & Agency Partitioning

The dataset is partitioned into three independent agency silos matching real-world administrative boundaries:

| Agency Code | Agency Name | Record Types | Focus |
|---|---|---|---|
| `STATE_POLICE` | State Police (Maharashtra) | `FIR`, `CHARGESHEET` | Violent crime, urban extortion gang (Network B), local NDPS seizures |
| `MAHA_CYBER` | Maharashtra Cyber Crime | `COMPLAINT`, `accounts.jsonl`, `transactions.jsonl` | NCRP/1930 cyber fraud complaints, mule account layers (Network A), financial audit trail |
| `CENTRAL_AGENCY` | Central Narcotics / Investigation Agency | `SEIZURE_REPORT` | Interstate trafficking, commercial contraband seizures (Network C) |

In addition, an event stream is maintained at `data/kumbh/events.jsonl` containing simulated crowd management and watchlist alert events for high-density public event scenarios.

---

## 3. Planted Cast & Networks

The synthetic population includes three planted criminal networks and key cross-agency bridges:

1. **Network A — Cyber-fraud Mule Ring (MAHA_CYBER):**
   - **Recruiter:** Sachin Tukaram Kale (alias "Sachu")
   - **Controller:** Nitin Shankar Gaikwad
   - **Mule Structure:** 4-layer account transfer network with realistic pass-through latencies.
   - **Victims & Deceived Holders:** 8+ deceived account holders whose credentials were misappropriated, plus innocent complainants across 6+ Maharashtra districts.

2. **Network B — Urban Extortion Gang (STATE_POLICE):**
   - **Leader:** Anil Ramchandra Jadhav (alias "Boss") — intentionally insulated, appearing in minimal records.
   - **Operatives:** 5 active gang members across Mumbai Suburban, Thane, and Pune police stations.

3. **Network C — Interstate Drug Chain (CENTRAL_AGENCY + STATE_POLICE):**
   - **Financier:** Mahendra Arjun Rathore (based outside key operational hubs, funding logistics).
   - **Lab Operator:** Prakash Sadashiv Shinde.
   - **Couriers:** Inter-district couriers moving contraband through Nashik, Kolhapur, Aurangabad, and Solapur.

4. **Cross-Network Bridges:**
   - **Bridge 1: Rakesh Dagdu Pawar (alias "Raka")** — A pivotal broker who connects Network B to financial laundering in MAHA_CYBER and drug logistics in CENTRAL_AGENCY. He appears under at least 5 different surface renderings across all three agency silos.
   - **Bridge 2: Nitin Shankar Gaikwad** — Controls Network A mule operations while receiving and routing funds originating from Network C.

5. **Common-Name Collisions & Decoys:**
   - **30+ common-name collision groups:** Distinct individuals who share similar names and surnames (e.g., "Sachin Kale", "Vijay Shinde") but differ in father's name, age, district, or account details.
   - **10+ innocent look-alikes:** Honest citizens sharing bank branches or districts with ring members without criminal linkages.

---

## 4. Controlled Noise & Realistic Messiness

To benchmark entity resolution robustly across varying difficulty tiers, mentions are perturbed through calibrated noise operators:

| Version | Noise Level | Transliteration Variants | Script Mixing (Devanagari / Roman) | Initials / Honorifics | Typos & Age Drift |
|---|---|---|---|---|---|
| `v0` | Minimal | ~5% | ~5% | ~5% | ~2% |
| `v1` | Light | ~10% | ~8% | ~8-10% | ~5% |
| `v2` | Medium | ~30% | ~25% | ~20% | ~15% |
| `v3` | Heavy (Stress test) | ~50% | ~40% | ~35% | ~30% |

Every noisy mention is tagged with `difficulty_tags` in the answer key:
`['translit', 'alias', 'initials', 'missing_father', 'collision', 'old_phone', 'typo', 'script_mix']`.

---

## 5. Ground Truth & Dev / Holdout Split

- **Hidden Answer Key:** Stored locally in `data/truth/<version>/` (governed by repository protection rules; never committed).
  - `person_truth.jsonl`: True canonical persons and roles.
  - `mention_truth.jsonl`: Ground truth pointers from record mentions to canonical `person_id`.
  - `account_truth.jsonl`: Mule layer classification (`ORGANISER`, `DECEIVED`, `NEUTRAL`).
  - `networks_truth.json`: Network membership, leader IDs, and bridge IDs.
- **Development Split:** 20% of mentions (stratified by network and difficulty) are extracted to `data/dev/dev_labels.jsonl` for tuning and validation by NLP/Entity Resolution modules. The remaining 80% serves as the held-out evaluation key.

---

## 6. Fairness & Demographic Balance

### Principles
- **No Community Stereotyping:** Surnames, first names, and demographic backgrounds are assigned across roles using balanced synthetic sampling.
- **Role Independence:** Criminal leadership, operative, courier, deceived holder, and victim roles are distributed across different surnames without correlation to any real community, religion, or caste.
- **Automated Audit:** The `sutradhar_eval` evaluation harness executes an automated Chi-Square/correlation test on every generation to verify that role assignment is uncorrelated with surname clusters (`fairness.passed == true`).

---

## 7. How to Generate & Evaluate

### Generate Dataset
```bash
# Set PYTHONPATH to include data_gen
python -m sutradhar_data.generate --version v0 --seed 42 --out data/
python -m sutradhar_data.generate --version v1 --seed 42 --out data/
```

### Run Evaluation Harness
```bash
python -m sutradhar_eval.run --data data/v1 --truth data/truth/v1 --artifacts artifacts --out artifacts/metrics.json
```
