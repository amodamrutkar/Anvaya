# Datasheet for Dataset: Sutradhar Synthetic Law & Order Financial Intelligence

Following the framework proposed by Gebru et al. (*Datasheets for Datasets*), this document provides a structured specification of the Sutradhar synthetic benchmark dataset.

---

## 1. Motivation

- **For what purpose was the dataset created?**  
  The Sutradhar dataset was created to benchmark entity resolution (ER), cross-crime syndicate discovery, money mule ring isolation, federated cross-agency query privacy, and crowd surveillance alerts in law-enforcement and financial intelligence contexts.
- **Who created the dataset?**  
  Antigravity / Sutradhar core team.
- **Who funded the creation of the dataset?**  
  Internal synthetic intelligence benchmark research.

---

## 2. Composition & Scaling Tiers

All data is **100% synthetic and fabricated**. No real-world criminal records, PII, bank accounts, or surveillance events are present.

### Scaling Tiers

| Tier | Unique Persons | Records | Mentions | Bank Accounts | Transactions | Kumbh Events | Syndicates / Bridges |
|---|---|---|---|---|---|---|---|
| **v1 Baseline** | 445 | 153 | 200 | 45 | 150 | 53 | 3 planted (A, B, C) / 2 bridges |
| **v2 Dev** | ~2,000 | ~2,400 | ~5,000 | ~1,500 | ~15,000 | ~300 | 8 syndicates / 5 bridges |
| **v2 Full** | ~10,000 | ~12,000 | ~25,000 | ~7,500 | ~75,000 | ~1,500 | 25 syndicates / 15 bridges |
| **v2 Stress** | ~40,000 | ~50,000 | ~100,000 | ~30,000 | ~300,000 | ~5,000 | 60 syndicates / 40 bridges |

### Deterministic Seeded Generation Output Paths

- Benchmark input data: `data/v2/<tier>/seed-<seed>/`
  - `STATE_POLICE/records.jsonl`: State Police FIRs and chargesheets.
  - `MAHA_CYBER/records.jsonl`: Cyber crime complaints.
  - `MAHA_CYBER/accounts.jsonl`: Bank accounts.
  - `MAHA_CYBER/transactions.jsonl`: Financial transaction stream.
  - `CENTRAL_AGENCY/records.jsonl`: Narcotics and contraband seizure reports.
  - `kumbh/events.jsonl`: High-density public festival surveillance stream.
- Ground truth answer keys (evaluation only, never used by production services): `data/truth/v2/<tier>/seed-<seed>/`
  - `person_truth.jsonl`: Canonical persons, demographic pool, true roles, and pseudo-Aadhaars.
  - `mention_truth.jsonl`: True person cluster mappings, difficulty tiers, and noise tags.
  - `account_truth.jsonl`: True mule layer, classification (ORGANISER / LIKELY_DECEIVED / INNOCENT_FAST_PASSTHROUGH), and complaint history.
  - `networks_truth.json`: True syndicate memberships and cross-crime bridge operative links.
  - `mcoca_truth.json`: Configurable MCOCA statute eligibility rule test cases and edge cases.

---

## 3. Schema Contracts & Data Fields

All generated datasets adhere to the strict JSON schemas in `contracts/schemas/`:
1. `source_record.schema.json`: Validates all source records (`R-[A-Z]{3}-\\d{6}`).
2. `kumbh_event.schema.json`: Validates simulated events (`KUMBH-EVT-\\d{4}`).
3. `mention.schema.json`: Validates extracted mentions (`M-R-[A-Z]{3}-\\d{6}-\\d+`).

### Documented Schema Extensions in v2 Ground Truth
- `person_truth.jsonl`:
  - `pseudo_aadhaar` (optional array of strings): Synthetic 12-digit identity strings designed to fail Verhoeff checksum.
  - `pool` (string): Demographic origin pool (`marathi`, `hindi`, `gujarati`, `marwari`, `muslim`, `south_indian`).
- `account_truth.jsonl`:
  - `category` (string): Account type (`MULE_ACCOUNT`, `INNOCENT_FAST_PASSTHROUGH`, `ORDINARY`).

---

## 4. Safety, Ethics & Privacy Precautionary Controls

### Phone Number Disclaimer
> **CRITICAL WARNING:** Phone numbers are randomly generated 10-digit numbers matching Indian telecommunication numbering patterns (prefixes 6, 7, 8, 9). Because these numbers are randomly synthesized, **they may coincide with real, active subscriber numbers**. 
> **THESE NUMBERS MUST NEVER BE CALLED, MESSAGED, OR CONTACTED UNDER ANY CIRCUMSTANCES.** Any claim that synthetic numbers are guaranteed non-routable has been explicitly removed.

### Synthetic Pseudo-Aadhaar Numbers
All synthetic pseudo-Aadhaar numbers generated in the dataset are mathematically corrupted such that they **strictly FAIL the Verhoeff checksum algorithm** used by UIDAI. Consequently, no generated pseudo-Aadhaar can ever be a valid, issued Aadhaar number.

### Real-World Figure Denylist
The generator enforces an automated screening denylist covering prominent national and state-level political figures, judicial personalities, and notorious underworld figures. Any sampled combination matching a denylisted entity is automatically discarded during generation.

### Demographic Fairness & Anti-Bias Audit
The synthetic population reflects Maharashtra's urban and regional demographic composition:
- Marathi: ~55%
- Hindi: ~20%
- Gujarati: ~10%
- Marwari: ~5%
- Muslim: ~5%
- South Indian: ~5%

The generator algorithmically ensures demographic fairness: **no single community or surname group is disproportionately criminalized**. Criminal syndicate membership rates across all demographic pools are evenly balanced (2.0% – 5.0%), and civilians form >95% of each demographic group.

---

## 5. Maintenance & Reproducibility

The dataset generator is deterministic. Given the same `--version`, `--tier`, and `--seed`, the generated output files and ground-truth answer keys are strictly byte-identical.
All v1 baseline artifacts (`data/v1/` and `data/kumbh/events.jsonl`) remain strictly byte-identical and pinned by SHA-256 checksums.
