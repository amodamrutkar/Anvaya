"""
sutradhar_api/adapters/banking.py
Simulated Core Banking / Financial Intelligence Unit (FIU) Adapter.

Normalizes raw bank transaction extracts and account records into:
- CanonicalTransaction (canonical_transaction.schema.json)
- CanonicalAccount (canonical_account.schema.json)
All operations are simulated; no live banking gateways or real credentials exist.
"""

from __future__ import annotations

import re
from typing import Any

from sutradhar_api.adapters.base import (
    AdapterMappingError,
    BaseAdapter,
)


class BankingFiuAdapter(BaseAdapter):
    """Adapter for simulated Core Banking System (CBS) and payment switch transaction feeds."""

    adapter_id = "BankingFiuAdapter"
    source_system = "CORE_BANKING_CBS"
    agency = "MAHA_CYBER"
    target_schema = "canonical_transaction.schema.json"

    def adapt(self, raw_payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Transform raw CBS transaction payload to CanonicalTransaction contract."""
        raw_ref = raw_payload.get("cbs_reference") or raw_payload.get("txn_ref") or raw_payload.get("source_txn_id")
        if not raw_ref:
            raise AdapterMappingError("Missing required transaction reference: 'cbs_reference'")

        # Remitter / From Account
        from_acc = raw_payload.get("from_account")
        if not from_acc:
            remitter_bank = raw_payload.get("remitter_bank_code") or raw_payload.get("remitter_bank")
            remitter_num = raw_payload.get("remitter_acc") or raw_payload.get("remitter_account")
            if remitter_bank and remitter_num:
                from_acc = f"{remitter_bank}:{remitter_num}"
        if not from_acc:
            raise AdapterMappingError("Missing required remitter account information: 'from_account' or remitter bank/acc")

        # Beneficiary / To Account
        to_acc = raw_payload.get("to_account")
        if not to_acc:
            bene_bank = raw_payload.get("beneficiary_bank_code") or raw_payload.get("beneficiary_bank")
            bene_num = raw_payload.get("beneficiary_acc") or raw_payload.get("beneficiary_account")
            if bene_bank and bene_num:
                to_acc = f"{bene_bank}:{bene_num}"
        if not to_acc:
            raise AdapterMappingError("Missing required beneficiary account information: 'to_account' or beneficiary bank/acc")

        # Amount
        raw_amount = raw_payload.get("amount") or raw_payload.get("txn_amount_inr") or raw_payload.get("txn_amount")
        if raw_amount is None:
            raise AdapterMappingError("Missing required transaction amount: 'amount' or 'txn_amount_inr'")
        try:
            amount = float(raw_amount)
            if amount < 0:
                raise ValueError("Negative amount")
        except (ValueError, TypeError) as err:
            raise AdapterMappingError(f"Invalid transaction amount '{raw_amount}': {err}")

        # Canonical Txn ID
        override_tid = kwargs.get("txn_id") or raw_payload.get("txn_id")
        if override_tid:
            canonical_tid = override_tid
        else:
            num_match = re.search(r"\d+", str(raw_ref))
            num_val = int(num_match.group(0)) if num_match else 1
            canonical_tid = f"TXN-BNK-{num_val:07d}"

        # Timestamp
        ts = raw_payload.get("settlement_time_utc") or raw_payload.get("timestamp") or raw_payload.get("ts")
        if not ts:
            raise AdapterMappingError("Missing required transaction timestamp: 'settlement_time_utc' or 'timestamp'")

        # Type / Channel
        txn_type = raw_payload.get("payment_mode") or raw_payload.get("type") or raw_payload.get("channel") or "IMPS"

        ingestion_metadata = self.build_ingestion_metadata(
            source_record_id=str(raw_ref),
            raw_payload=raw_payload,
            trace_id=kwargs.get("trace_id") or raw_payload.get("trace_id"),
            batch_id=kwargs.get("batch_id") or raw_payload.get("batch_id"),
            provenance={
                "cbs_ref": str(raw_ref),
                "utr": raw_payload.get("utr", ""),
                "payment_mode": txn_type,
            },
        )

        return {
            "txn_id": canonical_tid,
            "source_txn_id": str(raw_ref),
            "from_account": str(from_acc),
            "to_account": str(to_acc),
            "amount": amount,
            "currency": raw_payload.get("currency", "INR"),
            "timestamp": str(ts),
            "type": txn_type,
            "utr_number": raw_payload.get("utr") or raw_payload.get("rrn"),
            "source_system": self.source_system,
            "status": "SUCCESS" if str(raw_payload.get("core_status", "PROCESSED")).upper() in ["PROCESSED", "SUCCESS"] else "PENDING",
            "ingestion_metadata": ingestion_metadata,
        }

    def adapt_account(self, raw_account: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Transform raw CBS account info into validated CanonicalAccount contract."""
        bank = raw_account.get("bank_code") or raw_account.get("bank")
        num = raw_account.get("account_number") or raw_account.get("acc_num")
        holder = raw_account.get("customer_name") or raw_account.get("holder_name_raw")

        if not bank or not num or not holder:
            raise AdapterMappingError("Missing required CBS account fields (bank, account_number, customer_name)")

        ak = f"{bank}:{num}"
        ingestion_metadata = self.build_ingestion_metadata(
            source_record_id=ak,
            raw_payload=raw_account,
            trace_id=kwargs.get("trace_id"),
            batch_id=kwargs.get("batch_id"),
            provenance={"cbs_customer_id": raw_account.get("cif_number", "")},
        )

        canonical_acct = {
            "account_key": ak,
            "source_account_id": str(num),
            "bank": str(bank),
            "ifsc": raw_account.get("ifsc"),
            "holder_name_raw": str(holder),
            "opened_date": str(raw_account.get("account_open_date"))[:10] if raw_account.get("account_open_date") else None,
            "complaint_count": int(raw_account.get("reported_complaint_count", 0)),
            "account_type": raw_account.get("account_type", "SAVINGS"),
            "masked_account": f"XXXX-XXXX-{str(num)[-4:]}" if len(str(num)) >= 4 else None,
            "currency": raw_account.get("currency", "INR"),
            "status": raw_account.get("status", "ACTIVE"),
            "record_ids": raw_account.get("record_ids", []),
            "ingestion_metadata": ingestion_metadata,
        }
        self.validate(canonical_acct, schema_name="canonical_account.schema.json")
        return canonical_acct
