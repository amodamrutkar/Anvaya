# Privacy, Data Protection, and Legal Framing

> **LEGAL NOTICE & STATUS:**
> - **Synthetic Data Only:** All data in this repository and application is 100% synthetically generated. No actual personal data, Aadhaar details, phone numbers, or real criminal cases exist within Sutradhar.
> - **Legal Wording Status:** **[UNVERIFIED - PENDING STATUTORY COUNSEL REVIEW BEFORE PITCH]**. The legal references below represent a technical design alignment proposal under the Digital Personal Data Protection Act (DPDP Act), 2023, and require verification by qualified legal counsel.

---

## 1. Core Privacy Principles in Sutradhar

Sutradhar is designed from the ground up around four foundational data protection principles:

### 1.1 Purpose Limitation
- Every cross-agency and federated lookup requires a mandatory `purpose` enum (`INVESTIGATION`, `ALERT_VERIFICATION`, `AUDIT`).
- Queries cannot be executed for general curiosity or exploratory browsing.
- Each query must reference an active, valid case identifier (e.g., `CASE-MUM-2026-004512`) or an automated Kumbh incident ID.

### 1.2 Data Minimisation
- **Share answers, not data:** The federated query endpoint returns exclusively `MATCH`, `NO_MATCH`, or `MAYBE` along with a standardized reason code.
- It **never** returns raw records, names, suspect dossiers, or identifiers held by another agency.
- All identifier matching utilizes one-way salted HMAC-SHA256 digests. Raw phone numbers and account numbers are never transmitted across agency silos.

### 1.3 Security and Access Control
- **Role-Based Access Control (RBAC):** Strict operational segregation of duties (e.g., `INVESTIGATOR`, `ANALYST`, `APPROVING_OFFICER`, `AUDITOR`).
- **Cryptographic Audit Integrity:** Every query, view, review decision, dossier export, and tamper event is recorded in an append-only, SHA-256 hash-chained ledger.
- Export of suspect dossiers is restricted exclusively to `APPROVING_OFFICER` with explicit `confirm: true` gating.

### 1.4 Accountability & Auditability
- Independent `AUDITOR` role with real-time audit ledger inspection and mathematical verification (`GET /audit/verify`).
- Tamper detection ensures any retrospective modification of log entries immediately breaks the cryptographic hash chain and flags the exact corrupted sequence number.

---

## 2. Indian Statutory Framework (DPDP Act 2023 Alignment)

*(Marked unverified until statutory review)*

1. **Exemptions for Law Enforcement:** Section 17 of the Digital Personal Data Protection Act, 2023 provides exemptions for processing personal data in the interests of prevention, detection, investigation, or prosecution of any offence or the execution of any sentence or penal sanction.
2. **Proportionality and Safeguards:** Even where statutory exemptions apply, Sutradhar adheres to judicial standards of necessity, proportionality, and purpose limitation established under *K.S. Puttaswamy (Retd.) v. Union of India (2017)*.
3. **Audit Trail Mandate:** All processing operations maintain forensic-grade audit logs to prevent unauthorized access or abuse of power.
