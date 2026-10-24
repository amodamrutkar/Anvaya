"""
tests/test_canonical_contracts.py
Verification suite for Step 7A Canonical Data Contracts & Adapter Boundary.

Validates:
1. Valid canonical source record passes
2. Invalid source record fails
3. Valid account passes
4. Invalid account fails
5. Valid transaction passes
6. Invalid transaction fails
7. Valid ingestion metadata passes
8. Invalid ingestion metadata fails
9. Each simulated adapter converts its fixture correctly
10. Adapter output validates against appropriate canonical schema
11. Malformed external payloads fail cleanly
12. Missing required fields in external payloads fail cleanly
13. Backward-compatibility of existing V1 and V2 dataset records
14. Minimal integration with existing simulated connectors
"""

import copy
import json
from pathlib import Path

import pytest

from sutradhar_api.adapters import (
    AdapterMappingError,
    AdapterValidationError,
    BankingFiuAdapter,
    CctnsFirAdapter,
    KumbhOperationsAdapter,
    MahaCyberPortalAdapter,
)
from sutradhar_api.adapters.base import _get_schema_validator
from sutradhar_api.connectors import (
    SimulatedCCTNS,
    SimulatedMahaCrimeOS,
    SimulatedMahaCyber,
)

FIXTURES_DIR = Path(__file__).parent.parent / "contracts" / "fixtures" / "canonical"
DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> dict:
    fpath = FIXTURES_DIR / filename
    assert fpath.exists(), f"Fixture file missing: {fpath}"
    return json.loads(fpath.read_text(encoding="utf-8"))


# ── Test 1 & 2: Canonical Source Record ─────────────────────────────────────


def test_1_valid_canonical_source_record_passes():
    """1. Valid canonical source record passes schema validation."""
    data = _load_json("source_record.json")
    validator = _get_schema_validator("source_record.schema.json")
    validator.validate(data)  # Raises if invalid


def test_2_invalid_source_record_fails():
    """2. Invalid source record fails schema validation."""
    data = _load_json("source_record.json")
    validator = _get_schema_validator("source_record.schema.json")

    # A: Missing required field
    bad_data = copy.deepcopy(data)
    del bad_data["crime_type"]
    errors = list(validator.iter_errors(bad_data))
    assert len(errors) > 0, "Missing required field 'crime_type' should fail validation"

    # B: Invalid record_id pattern
    bad_data_2 = copy.deepcopy(data)
    bad_data_2["record_id"] = "INVALID-ID-123"
    errors_2 = list(validator.iter_errors(bad_data_2))
    assert len(errors_2) > 0, "Invalid record_id format should fail pattern validation"

    # C: Invalid agency enum
    bad_data_3 = copy.deepcopy(data)
    bad_data_3["agency"] = "UNREGISTERED_AGENCY"
    errors_3 = list(validator.iter_errors(bad_data_3))
    assert len(errors_3) > 0, "Unrecognized agency should fail enum validation"


# ── Test 3 & 4: Canonical Account ───────────────────────────────────────────


def test_3_valid_canonical_account_passes():
    """3. Valid canonical account passes schema validation."""
    data = _load_json("canonical_account.json")
    validator = _get_schema_validator("canonical_account.schema.json")
    validator.validate(data)


def test_4_invalid_account_fails():
    """4. Invalid account fails schema validation."""
    data = _load_json("canonical_account.json")
    validator = _get_schema_validator("canonical_account.schema.json")

    # A: Missing bank identifier
    bad_acct = copy.deepcopy(data)
    del bad_acct["bank"]
    errors = list(validator.iter_errors(bad_acct))
    assert len(errors) > 0, "Missing 'bank' should fail validation"

    # B: Malformed account_key
    bad_acct_2 = copy.deepcopy(data)
    bad_acct_2["account_key"] = "bad_key_without_colon"
    errors_2 = list(validator.iter_errors(bad_acct_2))
    assert len(errors_2) > 0, "Malformed account_key pattern should fail"

    # C: Invalid negative complaint count
    bad_acct_3 = copy.deepcopy(data)
    bad_acct_3["complaint_count"] = -5
    errors_3 = list(validator.iter_errors(bad_acct_3))
    assert len(errors_3) > 0, "Negative complaint_count should fail minimum check"


# ── Test 5 & 6: Canonical Transaction ───────────────────────────────────────


def test_5_valid_canonical_transaction_passes():
    """5. Valid canonical transaction passes schema validation."""
    data = _load_json("canonical_transaction.json")
    validator = _get_schema_validator("canonical_transaction.schema.json")
    validator.validate(data)


def test_6_invalid_transaction_fails():
    """6. Invalid transaction fails schema validation."""
    data = _load_json("canonical_transaction.json")
    validator = _get_schema_validator("canonical_transaction.schema.json")

    # A: Missing destination account
    bad_txn = copy.deepcopy(data)
    del bad_txn["to_account"]
    errors = list(validator.iter_errors(bad_txn))
    assert len(errors) > 0, "Missing 'to_account' should fail validation"

    # B: Negative amount
    bad_txn_2 = copy.deepcopy(data)
    bad_txn_2["amount"] = -100.0
    errors_2 = list(validator.iter_errors(bad_txn_2))
    assert len(errors_2) > 0, "Negative amount should fail minimum check"

    # C: Empty txn_id
    bad_txn_3 = copy.deepcopy(data)
    bad_txn_3["txn_id"] = ""
    errors_3 = list(validator.iter_errors(bad_txn_3))
    assert len(errors_3) > 0, "Empty txn_id should fail minLength check"


# ── Test 7 & 8: Ingestion Metadata ──────────────────────────────────────────


def test_7_valid_ingestion_metadata_passes():
    """7. Valid ingestion metadata passes schema validation."""
    data = _load_json("ingestion_metadata.json")
    validator = _get_schema_validator("ingestion_metadata.schema.json")
    validator.validate(data)


def test_8_invalid_ingestion_metadata_fails():
    """8. Invalid ingestion metadata fails schema validation."""
    data = _load_json("ingestion_metadata.json")
    validator = _get_schema_validator("ingestion_metadata.schema.json")

    # A: Missing adapter_id
    bad_meta = copy.deepcopy(data)
    del bad_meta["adapter_id"]
    errors = list(validator.iter_errors(bad_meta))
    assert len(errors) > 0, "Missing required adapter_id should fail validation"

    # B: Invalid semantic version pattern
    bad_meta_2 = copy.deepcopy(data)
    bad_meta_2["schema_version"] = "v2"
    errors_2 = list(validator.iter_errors(bad_meta_2))
    assert len(errors_2) > 0, "Bad schema_version format should fail pattern check"

    # C: Bad SHA-256 hash length
    bad_meta_3 = copy.deepcopy(data)
    bad_meta_3["payload_sha256"] = "abc123not64hex"
    errors_3 = list(validator.iter_errors(bad_meta_3))
    assert len(errors_3) > 0, "Malformed payload_sha256 should fail pattern check"


# ── Test 9 & 10: Adapter Conversion & Canonical Schema Validation ───────────


def test_9_and_10_cctns_adapter_conversion_and_validation():
    """9 & 10. CctnsFirAdapter converts raw CCTNS fixture and output validates."""
    raw = _load_json("raw_cctns_fir.json")
    adapter = CctnsFirAdapter()

    canonical = adapter.process(raw)

    assert canonical["agency"] == "STATE_POLICE"
    assert canonical["record_type"] == "FIR"
    assert canonical["crime_type"] == "CYBER_FRAUD"
    assert canonical["district"] == "Pune City"
    assert canonical["station"] == "Bundgarden"
    assert canonical["filed_date"] == "2026-02-14"
    assert len(canonical["form_fields"]["accused"]) == 1
    assert canonical["form_fields"]["accused"][0]["name"] == "Rakesh Powar"
    assert canonical["form_fields"]["accused"][0]["alias"] == "Rocky"
    assert canonical["ingestion_metadata"]["source_system"] == "CCTNS_MH"
    assert canonical["ingestion_metadata"]["simulated"] is True
    assert len(canonical["ingestion_metadata"]["payload_sha256"]) == 64


def test_9_and_10_mahacyber_adapter_conversion_and_validation():
    """9 & 10. MahaCyberPortalAdapter converts raw incident fixture and output validates."""
    raw = _load_json("raw_mahacyber_incident.json")
    adapter = MahaCyberPortalAdapter()

    canonical = adapter.process(raw)

    assert canonical["agency"] == "MAHA_CYBER"
    assert canonical["record_type"] == "COMPLAINT"
    assert canonical["crime_type"] == "CYBER_FRAUD"
    assert canonical["district"] == "Mumbai Cyber"
    assert canonical["ingestion_metadata"]["source_system"] == "MAHACYBER_NCRP"
    assert canonical["ingestion_metadata"]["simulated"] is True

    # Also test account extraction
    raw_acct = raw["suspect_accounts"][0]
    canonical_acct = adapter.adapt_account(raw_acct)
    assert canonical_acct["account_key"] == "AXIS:73306261209770"
    assert canonical_acct["bank"] == "AXIS"
    assert canonical_acct["holder_name_raw"] == "Daksha Bhavin Shah"
    assert canonical_acct["masked_account"] == "XXXX-XXXX-9770"
    assert canonical_acct["ingestion_metadata"]["simulated"] is True


def test_9_and_10_banking_adapter_conversion_and_validation():
    """9 & 10. BankingFiuAdapter converts raw CBS transaction and output validates."""
    raw = _load_json("raw_banking_transaction.json")
    adapter = BankingFiuAdapter()

    canonical = adapter.process(raw)

    assert canonical["from_account"] == "SBIN:68166060251503"
    assert canonical["to_account"] == "KKBK:96100167283599"
    assert canonical["amount"] == 1204.07
    assert canonical["type"] == "UPI_P2P"
    assert canonical["utr_number"] == "SBI00918237192"
    assert canonical["status"] == "SUCCESS"
    assert canonical["ingestion_metadata"]["source_system"] == "CORE_BANKING_CBS"
    assert canonical["ingestion_metadata"]["simulated"] is True


def test_9_and_10_kumbh_adapter_conversion_and_validation():
    """9 & 10. KumbhOperationsAdapter converts raw sensor alert and output validates."""
    raw = _load_json("raw_kumbh_observation.json")
    adapter = KumbhOperationsAdapter()

    canonical = adapter.process(raw)

    assert canonical["zone"] == "Ramkund"
    assert canonical["event_type"] == "WATCHLIST_SIGHTING"
    assert canonical["subject_token"] == "ENT-0004"
    assert "PH-9890123456" in canonical["related_ids"]
    assert canonical["ingestion_metadata"]["source_system"] == "KUMBH_SURVEILLANCE"
    assert canonical["ingestion_metadata"]["simulated"] is True


# ── Test 11 & 12: Error Handling on Malformed / Missing Inputs ──────────────


def test_11_malformed_external_payloads_fail_cleanly():
    """11. Malformed external payloads fail cleanly with descriptive exceptions."""
    adapter = BankingFiuAdapter()

    # Negative amount in CBS payload
    bad_cbs = {
        "cbs_reference": "CBS-ERR-001",
        "remitter_bank_code": "HDFC",
        "remitter_acc": "123456",
        "beneficiary_bank_code": "ICIC",
        "beneficiary_acc": "654321",
        "txn_amount_inr": -500.0,
        "settlement_time_utc": "2026-10-24T12:00:00Z",
    }
    with pytest.raises(AdapterMappingError) as exc_info:
        adapter.process(bad_cbs)
    assert "Invalid transaction amount" in str(exc_info.value)

    # Invalid zone in Kumbh payload
    k_adapter = KumbhOperationsAdapter()
    bad_kumbh = {
        "sensor_event_id": "IOT-BAD-01",
        "operational_sector": "NonExistentZone",
        "category": "WATCHLIST_SIGHTING",
        "detected_token": "ENT-01",
        "timestamp_local": "2026-10-24T12:00:00Z",
    }
    with pytest.raises(AdapterMappingError) as exc_k:
        k_adapter.process(bad_kumbh)
    assert "Invalid or missing Kumbh zone" in str(exc_k.value)


def test_12_missing_required_fields_fail_cleanly():
    """12. Missing required fields in external raw payloads fail cleanly."""
    cctns = CctnsFirAdapter()

    # Missing fir_num
    with pytest.raises(AdapterMappingError) as exc:
        cctns.adapt({"district_name": "Pune City", "date_of_registration": "2026-02-14"})
    assert "Missing required CCTNS field: 'fir_num'" in str(exc.value)

    # Missing district_name
    with pytest.raises(AdapterMappingError) as exc2:
        cctns.adapt({"fir_num": "0042/2026", "date_of_registration": "2026-02-14"})
    assert "Missing required CCTNS field: 'district_name'" in str(exc2.value)

    # Missing date_of_registration
    with pytest.raises(AdapterMappingError) as exc3:
        cctns.adapt({"fir_num": "0042/2026", "district_name": "Pune City"})
    assert "Missing required CCTNS field: 'date_of_registration'" in str(exc3.value)


# ── Test 13: Backward Compatibility with Existing Datasets ──────────────────


def test_13_backward_compatibility_existing_datasets():
    """13. Existing V1 and V2 dataset records validate against canonical schemas."""
    # V1 accounts
    v1_accts_file = Path("contracts/fixtures/data/MAHA_CYBER/accounts.jsonl")
    acct_validator = _get_schema_validator("canonical_account.schema.json")
    for line in v1_accts_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            acct_validator.validate(json.loads(line))

    # V1 transactions
    v1_txns_file = Path("contracts/fixtures/data/MAHA_CYBER/transactions.jsonl")
    txn_validator = _get_schema_validator("canonical_transaction.schema.json")
    for line in v1_txns_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            txn_validator.validate(json.loads(line))

    # V2 dev seed-42 accounts sample (first 10)
    v2_accts_file = DATA_DIR / "v2" / "dev" / "seed-42" / "MAHA_CYBER" / "accounts.jsonl"
    if v2_accts_file.exists():
        count = 0
        for line in v2_accts_file.read_text(encoding="utf-8").splitlines():
            if line.strip() and count < 10:
                acct_validator.validate(json.loads(line))
                count += 1

    # V2 dev seed-42 transactions sample (first 10)
    v2_txns_file = DATA_DIR / "v2" / "dev" / "seed-42" / "MAHA_CYBER" / "transactions.jsonl"
    if v2_txns_file.exists():
        count = 0
        for line in v2_txns_file.read_text(encoding="utf-8").splitlines():
            if line.strip() and count < 10:
                txn_validator.validate(json.loads(line))
                count += 1


# ── Test 14: Connector Integration ──────────────────────────────────────────


def test_14_connector_integration():
    """14. Simulated connectors use adapters to ingest raw external payloads."""
    # SimulatedCCTNS
    cctns_conn = SimulatedCCTNS()
    raw_cctns = _load_json("raw_cctns_fir.json")
    canonical_fir = cctns_conn.ingest_raw_fir(raw_cctns)
    assert canonical_fir["agency"] == "STATE_POLICE"
    assert canonical_fir["record_id"].startswith("R-STP-")

    # SimulatedMahaCrimeOS
    crimeos_conn = SimulatedMahaCrimeOS()
    canonical_case = crimeos_conn.ingest_raw_record(raw_cctns)
    assert canonical_case["record_type"] == "FIR"

    # SimulatedMahaCyber
    cyber_conn = SimulatedMahaCyber()
    raw_cyber = _load_json("raw_mahacyber_incident.json")
    canonical_comp = cyber_conn.ingest_raw_complaint(raw_cyber)
    assert canonical_comp["agency"] == "MAHA_CYBER"

    raw_bank = _load_json("raw_banking_transaction.json")
    canonical_tx = cyber_conn.ingest_raw_transaction(raw_bank)
    assert canonical_tx["amount"] == 1204.07
