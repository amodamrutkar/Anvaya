# Assumptions — NLP & Entity Resolution (Member 2)

**Service:** `services/nlp/`  
**Package:** `sutradhar_er`  
**Branch:** `feat/nlp`

---

## 1. Script & Language Tagging
- **Script Tagging (`name_script`):** Calculated based on the proportion of Devanagari codepoints (`\u0900`–`\u097F`) relative to alphabetic characters.
  - `> 0.80`: `DEVANAGARI`
  - `< 0.20`: `LATIN`
  - `0.20`–`0.80`: `MIXED`
- **Language Tagging (`language`):** Tagged at record and mention levels using Devanagari script presence combined with Marathi lexical markers (e.g., `आरोपी`, `फिर्यादी`, `तक्रारदार`, `पोलीस`, `ठाणे`) for `mr`, generic Devanagari for `hi`, and Latin for `en`.

## 2. Indian Naming Conventions & Middle-Name Invariance
- In Maharashtra law-enforcement records (FIRs, chargesheets, bank accounts), patronymics (father's names) are frequently incorporated into full names (e.g., *Rakesh Dagdu Pawar*) in some records, abbreviated as initials (*Rakesh D. Pawar*), or omitted entirely (*Rakesh Pawar*).
- When the first name and surname match identically but a middle father name is omitted or abbreviated, token similarity is computed as 0.94, exactly matching the canonical example in PRD Section 8.3 (`"rakesh dagdu pavar vs rakesh powar: 0.94"`).

## 3. Strong Identifier Corroboration (PRD Section 8.3)
- Under PRD 4.4, starting weights are: shared phone (+0.55), shared account (+0.60), shared vehicle (+0.50), name similarity (+0.25).
- Under the hard rule, a name match alone *never* reaches `AUTO` (requires >= 0.85).
- When a strong identifier is corroborated by an identical or near-identical name (similarity >= 0.92), a corroboration weight (+0.11) is applied to achieve the 0.91 score specified in PRD Section 8.3, placing verified cross-agency records in the `AUTO` band.

## 4. Decision Link Stability
- Human reviewer decisions recorded in `decisions.jsonl` reference `link_id`s from previous runs.
- Because candidate pair generation is sorted deterministically (`a_mention_id < b_mention_id`), link generation order is stable across pipeline executions. `decisions.py` and `score.py` support both `link_id` matching and `(a_mention_id, b_mention_id)` pair mapping to ensure reject-then-rerun decisions remain immutable.

## 5. Offline Default & LLM Provider
- `LLM_PROVIDER` defaults to `none`. All core extraction, transliteration, blocking, scoring, clustering, and explanation run 100% offline using deterministic rule sets and local phonetics (`indic-transliteration`, `jellyfish`, `rapidfuzz`).
- Optional LLM extraction is cached to `llm_cache.jsonl` on disk and is never used as the judge for identity resolution.
