"""
services/data_gen/sutradhar_data/finance.py
Background financial data generator:
- ~1,500 synthetic accounts
- ~15,000 ordinary transactions (salary, UPI, utility, merchant payments)
- Innocent fast pass-through accounts (gig workers, kirana merchants) as hard negatives
"""

from __future__ import annotations

from datetime import datetime, timedelta
import random
import string
from typing import Any

from .lexicons import BANK_CODES


def generate_account_number(rng: random.Random) -> str:
    """Generate a synthetic 14-digit bank account number."""
    return "".join(rng.choices(string.digits, k=14))


def generate_ifsc(rng: random.Random, bank_prefix: str) -> str:
    """Generate a synthetic IFSC code with bank prefix."""
    suffix = "".join(rng.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{bank_prefix[:4]}0{suffix}"


class BackgroundFinanceGenerator:
    """Generates realistic synthetic banking networks for MAHA_CYBER."""

    def __init__(self, rng: random.Random, base_date: datetime):
        self.rng = rng
        self.base_date = base_date
        self.accounts: list[dict[str, Any]] = []
        self.transactions: list[dict[str, Any]] = []
        self._txn_counter = 0

    def generate_financial_dataset(
        self,
        persons: list[dict[str, Any]],
        mule_accounts: list[dict[str, Any]],
        target_accounts: int = 1500,
        target_transactions: int = 15000,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Generate full financial tables (accounts.jsonl, transactions.jsonl)
        incorporating mule chains and background banking.
        """
        self.accounts = list(mule_accounts)
        existing_keys = {a["account_key"] for a in self.accounts}

        # 1. Generate innocent fast pass-through accounts (~100 hard negatives)
        num_fast_passthrough = min(120, max(60, target_accounts // 15))
        for i in range(num_fast_passthrough):
            bank = self.rng.choice(BANK_CODES)
            acct_no = generate_account_number(self.rng)
            acct_key = f"{bank['code']}:{acct_no}"
            if acct_key in existing_keys:
                continue
            existing_keys.add(acct_key)

            business_types = ["Kirana Store", "Chai Stall UPI", "Delivery Partner", "Auto Rickshaw Driver", "Vegetable Vendor"]
            biz = self.rng.choice(business_types)
            person_choice = self.rng.choice(persons) if persons else {"canonical_name": f"Trader {i}"}

            self.accounts.append(
                {
                    "account_key": acct_key,
                    "bank": bank["code"],
                    "ifsc": generate_ifsc(self.rng, bank["code"]),
                    "holder_name_raw": f"{person_choice['canonical_name']} ({biz})",
                    "opened_date": (self.base_date - timedelta(days=self.rng.randint(300, 1500))).strftime("%Y-%m-%d"),
                    "complaint_count": 0,
                    "account_category": "INNOCENT_FAST_PASSTHROUGH",
                    "record_ids": [],
                }
            )

        # 2. Fill remaining accounts up to target (~1,500 total)
        remaining = target_accounts - len(self.accounts)
        for i in range(max(0, remaining)):
            bank = self.rng.choice(BANK_CODES)
            acct_no = generate_account_number(self.rng)
            acct_key = f"{bank['code']}:{acct_no}"
            if acct_key in existing_keys:
                continue
            existing_keys.add(acct_key)

            person_choice = self.rng.choice(persons) if persons else {"canonical_name": f"Citizen {i}"}
            cat = self.rng.choices(
                ["ORDINARY_SAVINGS", "SALARY_ACCOUNT", "MERCHANT_CURRENT"],
                weights=[60, 30, 10],
                k=1,
            )[0]

            self.accounts.append(
                {
                    "account_key": acct_key,
                    "bank": bank["code"],
                    "ifsc": generate_ifsc(self.rng, bank["code"]),
                    "holder_name_raw": person_choice["canonical_name"],
                    "opened_date": (self.base_date - timedelta(days=self.rng.randint(100, 2000))).strftime("%Y-%m-%d"),
                    "complaint_count": 0,
                    "account_category": cat,
                    "record_ids": [],
                }
            )

        # Ensure account ordering is deterministic
        self.accounts.sort(key=lambda a: a["account_key"])

        # 3. Generate Transactions (~15,000)
        all_account_keys = [a["account_key"] for a in self.accounts]
        passthrough_keys = [a["account_key"] for a in self.accounts if a.get("account_category") == "INNOCENT_FAST_PASSTHROUGH"]
        standard_keys = [a["account_key"] for a in self.accounts if a.get("account_category") != "INNOCENT_FAST_PASSTHROUGH"]

        # 3a. Generate innocent fast pass-through transaction chains (rapid sweep)
        for pt_key in passthrough_keys:
            # 5-10 incoming micro-UPI transactions followed by rapid sweep out
            num_inflow = self.rng.randint(4, 8)
            sweep_time = self.base_date - timedelta(days=self.rng.randint(10, 200), hours=self.rng.randint(1, 20))
            total_in = 0.0

            for j in range(num_inflow):
                in_amt = round(self.rng.uniform(50.0, 1200.0), 2)
                total_in += in_amt
                src = self.rng.choice(standard_keys)
                in_ts = sweep_time - timedelta(minutes=self.rng.randint(5, 45))
                self._add_transaction(src, pt_key, in_amt, "UPI_P2P", in_ts)

            # Rapid sweep to supplier/distributor within 15-30 minutes
            if standard_keys:
                supplier = self.rng.choice(standard_keys)
                out_amt = round(total_in * self.rng.uniform(0.92, 0.98), 2)
                out_ts = sweep_time + timedelta(minutes=self.rng.randint(10, 25))
                self._add_transaction(pt_key, supplier, out_amt, "NEFT_SUPPLIER_SWEEP", out_ts)

        # 3b. Fill remaining background transactions up to target (~15,000)
        remaining_txns = target_transactions - len(self.transactions)
        for _ in range(max(0, remaining_txns)):
            src, dst = self.rng.sample(all_account_keys, 2)
            txn_type = self.rng.choices(
                ["UPI_P2P", "MERCHANT_PAYMENT", "SALARY_CREDIT", "UTILITY_BILL"],
                weights=[60, 25, 10, 5],
                k=1,
            )[0]

            if txn_type == "SALARY_CREDIT":
                amt = round(self.rng.uniform(25000.0, 120000.0), 2)
            elif txn_type == "UTILITY_BILL":
                amt = round(self.rng.uniform(400.0, 4500.0), 2)
            elif txn_type == "MERCHANT_PAYMENT":
                amt = round(self.rng.uniform(100.0, 8000.0), 2)
            else:
                amt = round(self.rng.uniform(200.0, 15000.0), 2)

            ts = self.base_date - timedelta(days=self.rng.randint(1, 365), hours=self.rng.randint(0, 23), minutes=self.rng.randint(0, 59))
            self._add_transaction(src, dst, amt, txn_type, ts)

        # Sort transactions deterministically by timestamp, then transaction ID
        self.transactions.sort(key=lambda t: (t["timestamp"], t["txn_id"]))
        return self.accounts, self.transactions

    def _add_transaction(self, src: str, dst: str, amt: float, txn_type: str, ts: datetime) -> None:
        self._txn_counter += 1
        self.transactions.append(
            {
                "txn_id": f"TXN-CYB-{self._txn_counter:07d}",
                "from_account": src,
                "to_account": dst,
                "amount": amt,
                "type": txn_type,
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
