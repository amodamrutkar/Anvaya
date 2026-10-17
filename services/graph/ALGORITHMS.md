# Sutradhar Graph Analytics: Plain-Language Algorithm Reference

This document provides intuitive, plain-language explanations of the algorithms powering Sutradhar's network analytics and syndicate discovery engine, designed for non-technical judges, investigating officers, and prosecutors.

---

### 1. Heterogeneous Graph Construction & Evidentiary Link Weighting
Real-world intelligence does not consist of just "people knowing people"; it is a rich tapestry of suspects, burner phones, bank accounts, vehicles, crime scenes, and formal FIR filings. Sutradhar ingests raw records across distinct agency silos and builds a multi-modal graph where every single connection is categorized as **STRONG** (substantiated by formal records, shared banking credentials, or vehicle ownership) or **WEAK** (shared residential locality or general address). To prevent misleading circumstantial assumptions, weak links are given high traversal penalties and hidden from default views, ensuring that analysts always see legally defensible evidence.

---

### 2. Weighted Person Projection with the "Hub Guard"
To discover who operates with whom across disparate agency records, Sutradhar projects the multi-modal graph into a direct person-to-person network. Suspects receive heavy linkage weights when they appear as co-accused in the same case (1.0), share personal mobile devices (1.0), or transfer funds directly (0.7). Crucially, the **Hub Guard** prevents common false positives: high-density hubs—such as a crowded police station, a large bank branch, or a shared apartment complex—are automatically down-weighted or neutralized. As a result, honest citizens sharing a residential tower or bank branch are never mistakenly linked into a criminal gang.

---

### 3. Louvain Community Detection with Cohesion Metrics
Rather than forcing arbitrary clusters, Sutradhar applies the deterministic Louvain modularity algorithm to uncover natural syndicate boundaries. The algorithm identifies tightly knit clusters of suspects whose internal operational density far exceeds background interactions. Each discovered community is benchmarked using a formal **Cohesion Score** (measuring internal edge density), assigned a human-readable title based on its dominant crime classification, and mapped across a rolling 12-month activity timeline to prove sustained criminal enterprise.

---

### 4. Insulated Kingpin & Structural Role Detection
Traditional police systems rely on simple mention counts, which disproportionately target low-level foot soldiers who get arrested frequently while missing the mastermind. Sutradhar decouples prominence from arrest volume: it constructs a **Directed Command & Flow Graph** tracking financial transfers and operational dependencies. By executing directed PageRank on money flow sinks and computing insulation ratios (internal gang control divided by public arrest appearances), the system reliably flags the true **Kingpin Candidate**—even when they intentionally appear in only a single court filing. Concurrently, **Brokers** are uncovered using betweenness centrality, and **Recruiters** are flagged via financial fan-out.

---

### 5. Cross-Crime & Multi-Agency Bridge Discovery
Siloed law enforcement agencies often investigate different limbs of the same beast without knowing it: cyber police see a digital payment receiver, state police investigate an extortion enforcer, and central authorities seize narcotics from a vehicle. Sutradhar's **Bridge Detection Algorithm** scans all graph nodes (individuals, phone numbers, bank accounts, vehicles) that simultaneously intersect two or more independent crime classifications or distinct syndicates. This surfaces pivotal intermediaries (such as Rakesh Pawar) who broker funds between digital fraud rings and violent extortion syndicates.

---

### 6. Layered Mule Chain Tracing & Deceived Holder Separation
When cyber victims report fraudulent transactions via the 1930/NCRP portal, funds are dispersed across multiple bank accounts in minutes. Sutradhar identifies all Layer 1 victim-intake accounts and executes a **Breadth-First Search (BFS)** outward along transaction paths to trace money through Layers 2, 3, and 4. Critically, to protect innocent citizens whose accounts were compromised, the algorithm extracts behavioral features (transfer velocity, fan-out, and account tenure) to differentiate active **Organisers** (who sweep funds downstream instantly) from **Deceived Mule Holders** (victims with zero downstream transfers), categorizing ambiguous cases into an **Uncertain** investigative review band.

---

### 7. MCOCA-Readiness Dossier Synthesis with Evidence Gap Auditing
Preparing an organized crime prosecution docket under special statutes like the Maharashtra Control of Organised Crime Act (MCOCA) demands rigorous evidence meeting strict statutory prerequisites. Sutradhar synthesizes all linked cases, prior chargesheets, associate roles, financial transfers, and chronological timelines into a cohesive draft dossier. Uniquely, the system conducts an **Automated Evidence Gap Audit**, explicitly warning prosecutors of deficiencies—such as associates appearing in only one case, insufficient chargesheets within the lookback window, or lack of direct money trail—before formal court filing.

---

### 8. Evidence-Preserving Shortest Path & Neighborhood Queries
When field officers or analysts ask, *"How does Suspect A connect to Kingpin B?"*, standard shortest-path algorithms often take shortcuts through tenuous circumstantial links. Sutradhar implements a **Constrained Weighted Shortest Path** algorithm that assigns an extreme penalty (10x cost) to weak links, forcing the query to route exclusively through direct evidentiary bonds whenever possible. Every returned path itemizes the exact FIR numbers, bank transaction references, and timestamped seizure logs for every link traversed.
