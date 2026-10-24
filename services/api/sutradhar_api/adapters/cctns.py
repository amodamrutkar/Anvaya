"""
sutradhar_api/adapters/cctns.py
Simulated CCTNS (Crime and Criminal Tracking Network & Systems) Adapter.

Maps simulated CCTNS-style police FIR/complaint payloads into the canonical SourceRecord contract.
All operations are simulated; no live connection or credentials are used.
"""

from __future__ import annotations

import re
from typing import Any

from sutradhar_api.adapters.base import (
    AdapterMappingError,
    BaseAdapter,
)


class CctnsFirAdapter(BaseAdapter):
    """Adapter for simulated CCTNS state police FIR extracts."""

    adapter_id = "CctnsFirAdapter"
    source_system = "CCTNS_MH"
    agency = "STATE_POLICE"
    target_schema = "source_record.schema.json"

    def adapt(self, raw_payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """
        Transform simulated CCTNS payload to canonical SourceRecord.
        
        Expected raw fields:
        - fir_num or fir_number (str)
        - district_name (str)
        - date_of_registration (YYYY-MM-DD)
        Optional raw fields:
        - police_station, acts_sections, major_head, complainant_info,
          accused_persons, alleged_bank_accounts, brief_facts, canonical_record_id, case_ref
        """
        fir_num = raw_payload.get("fir_num") or raw_payload.get("fir_number")
        if not fir_num:
            raise AdapterMappingError("Missing required CCTNS field: 'fir_num' or 'fir_number'")

        district = raw_payload.get("district_name") or raw_payload.get("district")
        if not district:
            raise AdapterMappingError("Missing required CCTNS field: 'district_name'")

        filed_date = raw_payload.get("date_of_registration") or raw_payload.get("filed_date")
        if not filed_date:
            raise AdapterMappingError("Missing required CCTNS field: 'date_of_registration'")

        # Derive a canonical Sutradhar record_id (e.g. R-STP-000042)
        override_rid = kwargs.get("canonical_record_id") or raw_payload.get("canonical_record_id")
        if override_rid:
            canonical_rid = override_rid
        else:
            num_match = re.search(r"\d+", str(fir_num))
            num_val = int(num_match.group(0)) if num_match else 1
            canonical_rid = f"R-STP-{num_val:06d}"

        # Derive case_ref (CASE-STP-XXXXXX)
        override_case = kwargs.get("case_ref") or raw_payload.get("case_ref")
        if override_case:
            case_ref = override_case
        else:
            num_match = re.search(r"\d+", str(fir_num))
            num_val = int(num_match.group(0)) if num_match else 1
            case_ref = f"CASE-STP-{num_val:06d}"

        # Crime type normalization
        crime_raw = str(raw_payload.get("major_head") or raw_payload.get("crime_type") or "CYBER_FRAUD").upper()
        if "CYBER" in crime_raw or "FRAUD" in crime_raw or "IT" in crime_raw:
            crime_type = "CYBER_FRAUD"
        elif "EXTORT" in crime_raw:
            crime_type = "EXTORTION"
        elif "NARC" in crime_raw or "NDPS" in crime_raw:
            crime_type = "NARCOTICS"
        elif "MISS" in crime_raw:
            crime_type = "MISSING_PERSON"
        else:
            crime_type = "CYBER_FRAUD"

        # Accused form fields
        accused_list: list[dict[str, Any]] = []
        phones: list[str] = []
        vehicles: list[str] = []
        for acc in raw_payload.get("accused_persons", []):
            name = acc.get("full_name") or acc.get("name") or "Unknown"
            father = acc.get("relative_name") or acc.get("father_name") or ""
            age = acc.get("approx_age") or acc.get("age")
            phone = acc.get("contact_number") or acc.get("phone") or ""
            address = acc.get("permanent_address") or acc.get("address") or ""
            alias = acc.get("alias_name") or acc.get("alias") or ""
            accused_list.append({
                "name": name,
                "father_name": father,
                "age": int(age) if age is not None else None,
                "address": address,
                "phone": phone,
                "alias": alias,
            })
            if phone:
                phones.append(phone)

        # Complainant
        comp_raw = raw_payload.get("complainant_info") or raw_payload.get("complainant")
        complainant: dict[str, Any] | None = None
        if isinstance(comp_raw, dict) and (comp_raw.get("full_name") or comp_raw.get("name")):
            complainant = {
                "name": comp_raw.get("full_name") or comp_raw.get("name"),
                "phone": comp_raw.get("mobile") or comp_raw.get("contact_number") or comp_raw.get("phone", ""),
            }

        # Accounts
        accounts: list[dict[str, Any]] = []
        for acct in raw_payload.get("alleged_bank_accounts", raw_payload.get("accounts", [])):
            bank = acct.get("bank_name") or acct.get("bank") or "BANK"
            num = acct.get("account_no") or acct.get("account_number") or ""
            if num:
                accounts.append({"bank": bank, "account_no": num})

        # Vehicles
        for veh in raw_payload.get("vehicles", []):
            if isinstance(veh, str) and veh:
                vehicles.append(veh)

        # Form fields
        form_fields = {
            "accused": accused_list,
            "complainant": complainant,
            "victims": raw_payload.get("victims", []),
            "accounts": accounts,
            "phones": list(dict.fromkeys(phones)),
            "vehicles": list(dict.fromkeys(vehicles)),
        }

        # Sections
        sections = raw_payload.get("acts_sections") or raw_payload.get("sections") or []

        # Ingestion Metadata
        source_rec_id = f"{raw_payload.get('cctns_state_code', 'MH')}-{district}-{fir_num}"
        ingestion_metadata = self.build_ingestion_metadata(
            source_record_id=source_rec_id,
            raw_payload=raw_payload,
            trace_id=kwargs.get("trace_id") or raw_payload.get("trace_id"),
            batch_id=kwargs.get("batch_id") or raw_payload.get("batch_id"),
            provenance={
                "source_fir_number": fir_num,
                "police_station": raw_payload.get("police_station", ""),
                "state_code": raw_payload.get("cctns_state_code", "MH"),
            },
        )

        canonical_record = {
            "record_id": canonical_rid,
            "agency": self.agency,
            "record_type": raw_payload.get("record_type", "FIR"),
            "crime_type": crime_type,
            "case_ref": case_ref,
            "district": district,
            "station": raw_payload.get("police_station", ""),
            "filed_date": str(filed_date)[:10],
            "language": raw_payload.get("language", "en"),
            "sections": sections,
            "form_fields": form_fields,
            "narrative": raw_payload.get("brief_facts") or raw_payload.get("narrative", ""),
            "ingestion_metadata": ingestion_metadata,
        }
        return canonical_record
