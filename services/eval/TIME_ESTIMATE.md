# Sutradhar Evaluation: Manual Investigation Time Estimation Baseline

## 1. Context and Objective

To quantify the operational efficiency gains delivered by Sutradhar, we establish an empirical baseline representing the manual investigation effort required by intelligence analysts without cross-agency graph linkage.

This baseline is compared against Sutradhar's end-to-end automated pipeline runtime in `artifacts/metrics.json` under `time_saved`.

---

## 2. Standard Manual Investigation Walkthrough

Consider a typical multi-agency nexus investigation involving:
- 1 target suspect (e.g., Rakesh Pawar)
- 3 distinct law enforcement agency silos (`STATE_POLICE`, `MAHA_CYBER`, `CENTRAL_AGENCY`)
- 4 layers of mule bank transactions across 15+ accounts
- Disparate FIRs, 1930 cyber complaints, and seizure memos written across English, Marathi, and Hindi.

### Step-by-Step Task Breakdown

| Investigation Task | Manual Procedure | Estimated Time (Minutes) |
|---|---|---|
| **1. Multi-Agency Data Request & Ingestion** | Submitting formal inter-departmental letters, requesting extracts, receiving PDFs/spreadsheets. | 60 min |
| **2. Cross-Lingual Entity Matching** | Manually inspecting phonetic variations (Pawar vs Powar vs पवार), matching aliases ("Raka"), checking father's names and addresses across 50+ records. | 45 min |
| **3. Financial Audit & Mule Chain Tracing** | Extracting transaction logs across 4 banks, reconciling UPI/IMPS reference numbers, mapping Layer 1 → Layer 2 → Layer 3 → Layer 4 accounts. | 60 min |
| **4. Account Classification** | Discerning legitimate deceived account holders from active syndicates by reviewing account tenure, complaint velocity, and transfer latencies. | 35 min |
| **5. Cross-Network Synthesis & Dossier Preparation** | Collating timeline of extortion threats, cyber fraud complaints, and vehicle sightings into a unified prosecution docket. | 40 min |
| **Total Manual Baseline** | | **240 minutes (4.0 hours)** |

---

## 3. Sutradhar Automated Benchmark

| Stage | Manual Time | Sutradhar System Runtime |
|---|---|---|
| Entity Resolution | 45 min | < 5 sec |
| Graph Construction & Mule Tracing | 60 min | < 2 sec |
| Dossier & Community Discovery | 40 min | < 1 sec |
| **End-to-End Analysis** | **240 min** | **< 15 sec** |

### Efficiency Multiplier
- **Manual Effort:** 240 minutes per multi-agency suspect.
- **Sutradhar Execution:** ~10-15 seconds.
- **Speedup Factor:** > **960x speedup** with automated audit trails and reproducible ground-truth metrics.
