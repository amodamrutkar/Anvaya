"""
Record emitters for Sutradhar synthetic data.

Emits records per agency matching main PRD Section 8.2 exactly:
- STATE_POLICE: FIRs and chargesheets (extortion, dacoity, drug FIRs)
- MAHA_CYBER: COMPLAINT records, accounts.jsonl, transactions.jsonl
- CENTRAL_AGENCY: SEIZURE_REPORT, NDPS-style cases

Each record has form_fields, narrative (mr/hi/en/mixed), and a slot validator.
"""

import random
from datetime import datetime, timedelta

from .entities import PersonRecord, _gen_phone
from .lexicons import (
    CRIME_DESCRIPTIONS,
    CRIME_SECTIONS,
    NARRATIVE_TEMPLATES,
    POLICE_STATIONS,
    SEIZED_ITEMS,
)
from .noise import apply_noise


class SlotValidationError(Exception):
    """Raised when a form field value does not appear in the narrative."""


def validate_slots(form_fields: dict, narrative: str) -> list[str]:
    """
    Validate that every intended form field value appears in the narrative.

    In Indian police records:
    - Accused name must appear in the narrative.
    - Complainant name (if present) must appear in the narrative.

    Returns a list of missing slots. Empty list means all intended slots present.
    """
    missing = []

    # 1. Accused name must always appear in narrative
    for i, acc in enumerate(form_fields.get("accused", [])):
        if isinstance(acc, dict):
            name = acc.get("name")
            if name and name not in narrative:
                missing.append(f"accused[{i}].name={name}")

    # 2. Complainant name must appear in narrative if present
    comp = form_fields.get("complainant", {})
    if isinstance(comp, dict):
        comp_name = comp.get("name")
        if comp_name and comp_name not in narrative:
            missing.append(f"complainant.name={comp_name}")

    return missing


class RecordEmitter:
    """Generates records from true persons, applying noise per version."""

    def __init__(self, rng: random.Random, version: str = "v0"):
        self.rng = rng
        self.version = version
        self._record_counter = {"SPO": 0, "CYB": 0, "CEN": 0}
        self._case_counter = {"SPO": 0, "CYB": 0, "CEN": 0}
        self._mention_counter = 0
        self._txn_counter = 0

        self.all_records: list[dict] = []
        self.all_mentions_truth: list[dict] = []
        self.all_accounts: list[dict] = []
        self.all_transactions: list[dict] = []

    def _next_record_id(self, agency_code: str) -> str:
        self._record_counter[agency_code] += 1
        return f"R-{agency_code}-{self._record_counter[agency_code]:06d}"

    def _next_case_id(self, agency_code: str) -> str:
        self._case_counter[agency_code] += 1
        return f"CASE-{agency_code}-{self._case_counter[agency_code]:06d}"

    def _next_mention_id(self, record_id: str) -> str:
        self._mention_counter += 1
        return f"M-{record_id}-{self._mention_counter}"

    def _pick_language(self) -> str:
        return self.rng.choice(["mr", "hi", "en", "mixed"])

    def _gen_date(self, base_year: int = 2025) -> str:
        """Generate a random date string."""
        days_offset = self.rng.randint(0, 365 * 2)
        dt = datetime(base_year, 1, 1) + timedelta(days=days_offset)
        return dt.strftime("%Y-%m-%d")

    def _gen_narrative(self, template_key: str, slots: dict[str, str]) -> str:
        """Fill narrative template with slot values."""
        template = NARRATIVE_TEMPLATES.get(template_key)
        if template is None:
            # Fall back to English
            template = NARRATIVE_TEMPLATES.get(template_key.rsplit("_", 1)[0] + "_en", "")
        if not template:
            return ""

        # Fill with defaults for missing slots
        defaults = {
            "filed_date": slots.get("filed_date", "2025-01-01"),
            "complainant_name": slots.get("complainant_name", "Unknown"),
            "station": slots.get("station", "Synthetic Nagar PS"),
            "accused_name": slots.get("accused_name", "Unknown"),
            "accused_alias": slots.get("accused_alias", "N/A"),
            "accused_age": slots.get("accused_age", "30"),
            "accused_address": slots.get("accused_address", "Unknown"),
            "accused_phone": slots.get("accused_phone", "0000000000"),
            "crime_desc": slots.get("crime_desc", "committed an offence"),
            "vehicle": slots.get("vehicle", "N/A"),
            "account_no": slots.get("account_no", "N/A"),
            "bank": slots.get("bank", "N/A"),
            "amount": slots.get("amount", "0"),
            "seized_item": slots.get("seized_item", "contraband"),
        }
        try:
            return template.format(**defaults)
        except KeyError:
            return template

    def emit_state_police_fir(
        self,
        accused_person: PersonRecord,
        complainant_person: PersonRecord | None = None,
        crime_type: str = "EXTORTION",
    ) -> dict:
        """Emit an FIR/chargesheet for STATE_POLICE."""
        record_id = self._next_record_id("SPO")
        case_ref = self._next_case_id("SPO")
        filed_date = self._gen_date()
        lang = self._pick_language()
        station = self.rng.choice(POLICE_STATIONS)

        # Apply noise to accused
        accused_mention, diff_tags = apply_noise(accused_person, self.rng, self.version)
        mention_id = self._next_mention_id(record_id)

        # Complainant
        if complainant_person:
            comp_mention, _ = apply_noise(complainant_person, self.rng, self.version)
            comp_name = comp_mention["name_raw"]
            comp_phone = comp_mention["phones"][0] if comp_mention["phones"] else ""
        else:
            comp_name = f"Synthetic Complainant {self.rng.randint(1, 999)}"
            comp_phone = _gen_phone(self.rng)

        # Crime description
        crime_desc_map = CRIME_DESCRIPTIONS.get(crime_type, CRIME_DESCRIPTIONS["EXTORTION"])
        lang_key = lang if lang != "mixed" else "en"
        crime_desc = crime_desc_map.get(lang_key, crime_desc_map["en"])

        # Determine record type
        record_type = (
            self.rng.choice(["FIR", "CHARGESHEET"]) if crime_type != "NARCOTICS" else "FIR"
        )

        # Build form_fields
        acc_entry = {
            "name": accused_mention["name_raw"],
            "father_name": accused_mention["father_name_raw"],
            "age": accused_mention["age"],
            "address": accused_mention["address_raw"],
            "phone": accused_mention["phones"][0] if accused_mention["phones"] else "",
            "alias": accused_mention["aliases"][0] if accused_mention["aliases"] else "",
        }

        acct_list = []
        for ak in accused_mention["accounts"]:
            parts = ak.split(":")
            if len(parts) == 2:
                acct_list.append(
                    {
                        "bank": parts[0],
                        "account_no": parts[1],
                        "holder_name": accused_mention["name_raw"],
                    }
                )

        # Narrative slots
        slots = {
            "filed_date": filed_date,
            "complainant_name": comp_name,
            "station": station,
            "accused_name": accused_mention["name_raw"],
            "accused_alias": acc_entry["alias"] or "N/A",
            "accused_age": str(accused_mention["age"]),
            "accused_address": accused_mention["address_raw"] or "N/A",
            "accused_phone": acc_entry["phone"] or "N/A",
            "crime_desc": crime_desc,
            "vehicle": accused_mention["vehicles"][0] if accused_mention["vehicles"] else "N/A",
            "account_no": acct_list[0]["account_no"] if acct_list else "N/A",
            "bank": acct_list[0]["bank"] if acct_list else "N/A",
        }

        # Pick narrative template
        tmpl_key = "CHARGESHEET_en" if record_type == "CHARGESHEET" else f"FIR_{lang}"

        narrative = self._gen_narrative(tmpl_key, slots)

        form_fields = {
            "accused": [acc_entry],
            "complainant": {"name": comp_name, "phone": comp_phone},
            "victims": [],
            "accounts": acct_list,
            "phones": accused_mention["phones"],
            "vehicles": accused_mention["vehicles"],
        }

        record = {
            "record_id": record_id,
            "agency": "STATE_POLICE",
            "record_type": record_type,
            "crime_type": crime_type,
            "case_ref": case_ref,
            "district": accused_person.district,
            "station": station,
            "filed_date": filed_date,
            "language": lang,
            "sections": self.rng.sample(
                CRIME_SECTIONS.get(crime_type, ["BNS-308"]),
                k=min(2, len(CRIME_SECTIONS.get(crime_type, ["BNS-308"]))),
            ),
            "form_fields": form_fields,
            "narrative": narrative,
        }

        self.all_records.append(record)

        # Truth entry
        self.all_mentions_truth.append(
            {
                "mention_id": mention_id,
                "record_id": record_id,
                "person_id": accused_person.person_id,
                "role": "ACCUSED",
                "difficulty_tags": diff_tags,
            }
        )

        return record

    def emit_maha_cyber_complaint(
        self,
        suspect_person: PersonRecord,
        victim_person: PersonRecord | None = None,
        amount: int | None = None,
    ) -> dict:
        """Emit a COMPLAINT record for MAHA_CYBER (1930/NCRP-style)."""
        record_id = self._next_record_id("CYB")
        case_ref = self._next_case_id("CYB")
        filed_date = self._gen_date()
        lang = self._pick_language()
        station = self.rng.choice(POLICE_STATIONS)

        suspect_mention, diff_tags = apply_noise(suspect_person, self.rng, self.version)
        mention_id = self._next_mention_id(record_id)

        if victim_person:
            vic_mention, _ = apply_noise(victim_person, self.rng, self.version)
            comp_name = vic_mention["name_raw"]
            comp_phone = vic_mention["phones"][0] if vic_mention["phones"] else _gen_phone(self.rng)
        else:
            comp_name = f"Synthetic Victim {self.rng.randint(1, 999)}"
            comp_phone = _gen_phone(self.rng)

        if amount is None:
            amount = self.rng.choice([5000, 10000, 25000, 50000, 100000, 250000])

        acct_list = []
        for ak in suspect_mention["accounts"]:
            parts = ak.split(":")
            if len(parts) == 2:
                acct_list.append(
                    {
                        "bank": parts[0],
                        "account_no": parts[1],
                        "holder_name": suspect_mention["name_raw"],
                    }
                )

        slots = {
            "complainant_name": comp_name,
            "accused_name": suspect_mention["name_raw"],
            "accused_phone": suspect_mention["phones"][0] if suspect_mention["phones"] else "N/A",
            "amount": str(amount),
            "account_no": acct_list[0]["account_no"] if acct_list else "N/A",
            "bank": acct_list[0]["bank"] if acct_list else "N/A",
            "filed_date": filed_date,
            "station": station,
            "accused_alias": "N/A",
            "accused_age": str(suspect_mention["age"]),
            "accused_address": suspect_mention["address_raw"] or "N/A",
            "crime_desc": CRIME_DESCRIPTIONS["CYBER_FRAUD"].get(
                lang if lang != "mixed" else "en", ""
            ),
            "vehicle": "N/A",
        }

        tmpl_key = (
            f"COMPLAINT_{lang}" if f"COMPLAINT_{lang}" in NARRATIVE_TEMPLATES else "COMPLAINT_en"
        )
        narrative = self._gen_narrative(tmpl_key, slots)

        form_fields = {
            "accused": [
                {
                    "name": suspect_mention["name_raw"],
                    "father_name": suspect_mention["father_name_raw"],
                    "age": suspect_mention["age"],
                    "address": suspect_mention["address_raw"],
                    "phone": suspect_mention["phones"][0] if suspect_mention["phones"] else "",
                    "alias": "",
                }
            ],
            "complainant": {"name": comp_name, "phone": comp_phone},
            "victims": [{"name": comp_name, "phone": comp_phone}],
            "accounts": acct_list,
            "phones": suspect_mention["phones"],
            "vehicles": [],
        }

        record = {
            "record_id": record_id,
            "agency": "MAHA_CYBER",
            "record_type": "COMPLAINT",
            "crime_type": "CYBER_FRAUD",
            "case_ref": case_ref,
            "district": suspect_person.district,
            "station": station,
            "filed_date": filed_date,
            "language": lang,
            "sections": self.rng.sample(
                CRIME_SECTIONS["CYBER_FRAUD"],
                k=min(2, len(CRIME_SECTIONS["CYBER_FRAUD"])),
            ),
            "form_fields": form_fields,
            "narrative": narrative,
        }

        self.all_records.append(record)
        self.all_mentions_truth.append(
            {
                "mention_id": mention_id,
                "record_id": record_id,
                "person_id": suspect_person.person_id,
                "role": "SUSPECT",
                "difficulty_tags": diff_tags,
            }
        )

        # Add accounts to the account list
        for acct in suspect_person.accounts:
            acct_entry = {
                "account_key": acct["account_key"],
                "bank": acct["bank"],
                "ifsc": acct["ifsc"],
                "holder_name_raw": suspect_mention["name_raw"],
                "opened_date": self._gen_date(2020),
                "complaint_count": self.rng.randint(1, 50),
                "record_ids": [record_id],
            }
            self.all_accounts.append(acct_entry)

        return record

    def emit_central_agency_seizure(self, accused_person: PersonRecord) -> dict:
        """Emit a SEIZURE_REPORT for CENTRAL_AGENCY."""
        record_id = self._next_record_id("CEN")
        case_ref = self._next_case_id("CEN")
        filed_date = self._gen_date()
        lang = self.rng.choice(["mr", "en"])
        station = self.rng.choice(POLICE_STATIONS)

        accused_mention, diff_tags = apply_noise(accused_person, self.rng, self.version)
        mention_id = self._next_mention_id(record_id)

        seized_items_lang = SEIZED_ITEMS.get(lang, SEIZED_ITEMS["en"])
        seized_item = self.rng.choice(seized_items_lang)

        slots = {
            "filed_date": filed_date,
            "station": station,
            "accused_name": accused_mention["name_raw"],
            "seized_item": seized_item,
            "vehicle": accused_mention["vehicles"][0] if accused_mention["vehicles"] else "N/A",
            "accused_phone": accused_mention["phones"][0] if accused_mention["phones"] else "N/A",
            "accused_address": accused_mention["address_raw"] or "N/A",
        }

        tmpl_key = f"SEIZURE_{lang}" if f"SEIZURE_{lang}" in NARRATIVE_TEMPLATES else "SEIZURE_en"
        narrative = self._gen_narrative(tmpl_key, slots)

        form_fields = {
            "accused": [
                {
                    "name": accused_mention["name_raw"],
                    "father_name": accused_mention["father_name_raw"],
                    "age": accused_mention["age"],
                    "address": accused_mention["address_raw"],
                    "phone": accused_mention["phones"][0] if accused_mention["phones"] else "",
                    "alias": accused_mention["aliases"][0] if accused_mention["aliases"] else "",
                }
            ],
            "complainant": {},
            "victims": [],
            "accounts": [],
            "phones": accused_mention["phones"],
            "vehicles": accused_mention["vehicles"],
        }

        record = {
            "record_id": record_id,
            "agency": "CENTRAL_AGENCY",
            "record_type": "SEIZURE_REPORT",
            "crime_type": "NARCOTICS",
            "case_ref": case_ref,
            "district": accused_person.district,
            "station": station,
            "filed_date": filed_date,
            "language": lang,
            "sections": self.rng.sample(
                CRIME_SECTIONS["NARCOTICS"],
                k=min(2, len(CRIME_SECTIONS["NARCOTICS"])),
            ),
            "form_fields": form_fields,
            "narrative": narrative,
        }

        self.all_records.append(record)
        self.all_mentions_truth.append(
            {
                "mention_id": mention_id,
                "record_id": record_id,
                "person_id": accused_person.person_id,
                "role": "ACCUSED",
                "difficulty_tags": diff_tags,
            }
        )

        return record

    def emit_transactions(
        self, accounts: list[dict], num_txns: int = 5, base_amount: int = 100000
    ) -> list[dict]:
        """Emit synthetic transactions between accounts."""
        txns = []
        for _ in range(num_txns):
            if len(accounts) < 2:
                break
            src, dst = self.rng.sample(accounts, 2)
            self._txn_counter += 1
            amt = self.rng.randint(1000, base_amount)
            ts_base = datetime(2025, 6, 1) + timedelta(
                days=self.rng.randint(0, 180),
                minutes=self.rng.randint(0, 1440),
            )
            txn = {
                "txn_id": f"TXN-{self._txn_counter:06d}",
                "from_account": src["account_key"],
                "to_account": dst["account_key"],
                "amount": amt,
                "ts": ts_base.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "channel": self.rng.choice(["UPI", "NEFT", "IMPS", "RTGS"]),
            }
            txns.append(txn)
            self.all_transactions.append(txn)
        return txns
