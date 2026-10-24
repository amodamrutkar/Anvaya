"""
sutradhar_api/adapters/mahacyber.py
Simulated Maharashtra Cyber / NCRP Portal Adapter.

Normalizes cyber fraud complaints and suspect mule accounts into canonical contracts:
- SourceRecord (source_record.schema.json)
- CanonicalAccount (canonical_account.schema.json)
All operations are simulated; no live external connections or credentials exist.
"""

from __future__ import annotations

import re
from typing import Any

from sutradhar_api.adapters.base import (
    AdapterMappingError,
    BaseAdapter,
)


class MahaCyberPortalAdapter(BaseAdapter):
    """Adapter for simulated Maharashtra Cyber NCRP portal incidents and suspect accounts."""

    adapter_id = "MahaCyberPortalAdapter"
    source_system = "MAHACYBER_NCRP"
    agency = "MAHA_CYBER"
    target_schema = "source_record.schema.json"

    def adapt(self, raw_payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Transform simulated NCRP cyber complaint payload into canonical SourceRecord."""
        ack_no = raw_payload.get("ncrp_acknowledgement_no") or raw_payload.get("incident_id")
        if not ack_no:
            raise AdapterMappingError(
                "Missing required field: 'ncrp_acknowledgement_no' or 'incident_id'"
            )

        district = raw_payload.get("reporting_district") or raw_payload.get("district")
        if not district:
            raise AdapterMappingError("Missing required field: 'reporting_district'")

        filed_date = raw_payload.get("incident_date") or raw_payload.get("filed_date")
        if not filed_date:
            raise AdapterMappingError("Missing required field: 'incident_date'")

        override_rid = kwargs.get("canonical_record_id") or raw_payload.get("canonical_record_id")
        if override_rid:
            canonical_rid = override_rid
        else:
            num_match = re.search(r"\d+", str(ack_no))
            num_val = int(num_match.group(0)) if num_match else 1
            canonical_rid = f"R-CYB-{num_val:06d}"

        override_case = kwargs.get("case_ref") or raw_payload.get("case_ref")
        if override_case:
            case_ref = override_case
        else:
            num_match = re.search(r"\d+", str(ack_no))
            num_val = int(num_match.group(0)) if num_match else 1
            case_ref = f"CASE-CYB-{num_val:06d}"

        accused_list: list[dict[str, Any]] = []
        phones: list[str] = []
        for susp in raw_payload.get("suspect_identifiers", []):
            name = susp.get("name") or susp.get("suspect_name") or "Unknown Suspect"
            phone = susp.get("phone") or susp.get("mobile") or ""
            accused_list.append(
                {
                    "name": name,
                    "father_name": susp.get("father_name", ""),
                    "age": susp.get("age"),
                    "address": susp.get("address", ""),
                    "phone": phone,
                    "alias": susp.get("alias", ""),
                }
            )
            if phone:
                phones.append(phone)

        # Complainant / Victim
        vic_raw = raw_payload.get("victim_details") or raw_payload.get("complainant")
        complainant: dict[str, Any] | None = None
        if isinstance(vic_raw, dict) and vic_raw.get("name"):
            complainant = {
                "name": vic_raw.get("name"),
                "phone": vic_raw.get("contact") or vic_raw.get("phone", ""),
            }

        # Accounts
        accounts: list[dict[str, Any]] = []
        for acct in raw_payload.get("suspect_accounts", []):
            bank = acct.get("bank_code") or acct.get("bank") or "BANK"
            num = acct.get("account_number") or acct.get("account_no") or ""
            if num:
                accounts.append({"bank": bank, "account_no": num})

        form_fields = {
            "accused": accused_list,
            "complainant": complainant,
            "victims": [complainant] if complainant else [],
            "accounts": accounts,
            "phones": list(dict.fromkeys(phones)),
            "vehicles": raw_payload.get("vehicles", []),
        }

        ingestion_metadata = self.build_ingestion_metadata(
            source_record_id=str(ack_no),
            raw_payload=raw_payload,
            trace_id=kwargs.get("trace_id") or raw_payload.get("trace_id"),
            batch_id=kwargs.get("batch_id") or raw_payload.get("batch_id"),
            provenance={
                "ncrp_ack": str(ack_no),
                "state_nodal": raw_payload.get("state_nodal", "Maharashtra Cyber"),
                "police_station": raw_payload.get("police_station", "Cyber PS"),
            },
        )

        return {
            "record_id": canonical_rid,
            "agency": self.agency,
            "record_type": raw_payload.get("record_type", "COMPLAINT"),
            "crime_type": "CYBER_FRAUD",
            "case_ref": case_ref,
            "district": district,
            "station": raw_payload.get("police_station", "BKC Cyber PS"),
            "filed_date": str(filed_date)[:10],
            "language": raw_payload.get("language", "en"),
            "sections": raw_payload.get("sections", ["IT Act 66D", "BNS 318"]),
            "form_fields": form_fields,
            "narrative": raw_payload.get("incident_summary") or raw_payload.get("narrative", ""),
            "ingestion_metadata": ingestion_metadata,
        }

    def adapt_account(self, raw_account: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Transform raw account dictionary into validated CanonicalAccount contract."""
        bank = raw_account.get("bank_code") or raw_account.get("bank")
        if not bank:
            raise AdapterMappingError("Missing required bank identifier in raw account payload")

        num = raw_account.get("account_number") or raw_account.get("account_no")
        if not num:
            raise AdapterMappingError("Missing required account number in raw account payload")

        holder = raw_account.get("holder_name") or raw_account.get("holder_name_raw")
        if not holder:
            raise AdapterMappingError("Missing required holder name in raw account payload")

        ak = f"{bank}:{num}"
        ingestion_metadata = self.build_ingestion_metadata(
            source_record_id=ak,
            raw_payload=raw_account,
            trace_id=kwargs.get("trace_id"),
            batch_id=kwargs.get("batch_id"),
            provenance={"source_bank": bank, "raw_account_no": num},
        )

        canonical_acct = {
            "account_key": ak,
            "source_account_id": str(num),
            "bank": bank,
            "ifsc": raw_account.get("ifsc"),
            "holder_name_raw": str(holder),
            "opened_date": str(raw_account.get("opened_date"))[:10]
            if raw_account.get("opened_date")
            else None,
            "complaint_count": int(
                raw_account.get("complaints_linked") or raw_account.get("complaint_count", 0)
            ),
            "account_category": raw_account.get("account_category"),
            "account_type": raw_account.get("account_type", "SAVINGS"),
            "masked_account": f"XXXX-XXXX-{str(num)[-4:]}" if len(str(num)) >= 4 else None,
            "currency": raw_account.get("currency", "INR"),
            "status": raw_account.get("status", "ACTIVE"),
            "record_ids": raw_account.get("record_ids", []),
            "ingestion_metadata": ingestion_metadata,
        }
        self.validate(canonical_acct, schema_name="canonical_account.schema.json")
        return canonical_acct
