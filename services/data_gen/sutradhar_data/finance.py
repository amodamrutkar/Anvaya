"""
services/data_gen/sutradhar_data/finance.py
Background financial data generator:
- ~1,500 synthetic accounts
- ~15,000 transactions with realistic legitimate and illicit patterns:
  A. Kirana / small merchant activity (daytime micro-UPI, evening supplier sweeps, 0 complaints)
  B. Gig-worker platform payouts (regular weekly credits, personal expenses, 0 complaints)
  C. Corporate payroll (monthly recurring credits on 1st/30th, rent/utility bills, 0 complaints)
  D. Ordinary savings accounts (P2P UPI, bill payments)
- 3 Multi-layer mule chains (preserving hero MULE-001 / CH-001 / AC-000310)
  with realistic behavioral differences between controllers, recruiters, deceived holders,
  and legitimate pass-through accounts.
- Zero truth leakage to public data.
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
        incorporating multi-layer mule chains and realistic legitimate banking.
        """
        self.accounts = []
        self.transactions = []
        self._txn_counter = 0

        # Existing account keys set
        existing_keys: set[str] = set()

        # Person lookup by person_id
        person_by_id = {p["person_id"]: p for p in persons}

        # ─────────────────────────────────────────────────────────
        # 1. Multi-Layer Mule Chains (3 Chains)
        # ─────────────────────────────────────────────────────────
        # We preserve hero MULE-001 (CH-001, AC-000310, COM-001) and add CH-002 (COM-004) and CH-003 (COM-005)
        # Find hero personas
        hero_deceived = person_by_id.get("P-000102")  # Ajay Ashok Shinde
        hero_recruiter = person_by_id.get("P-000101")  # Sachin Tukaram Kale
        hero_controller = person_by_id.get("P-000046")  # Nitin Shankar Gaikwad

        # Helper to create an account
        def _create_acct(
            bank_code: str,
            holder_name: str,
            person_id: str | None,
            category: str,
            classification: str,
            layer: int,
            complaints: int,
            opened_days_ago: int,
            fixed_key: str | None = None,
            mule_chain_id: str | None = None,
        ) -> dict[str, Any]:
            if fixed_key:
                acct_key = fixed_key
                bank = fixed_key.split(":")[0]
            else:
                bank = bank_code
                acct_no = generate_account_number(self.rng)
                acct_key = f"{bank}:{acct_no}"
                while acct_key in existing_keys:
                    acct_no = generate_account_number(self.rng)
                    acct_key = f"{bank}:{acct_no}"

            existing_keys.add(acct_key)
            opened_date = (self.base_date - timedelta(days=opened_days_ago)).strftime("%Y-%m-%d")
            return {
                "account_key": acct_key,
                "bank": bank,
                "ifsc": generate_ifsc(self.rng, bank),
                "holder_name_raw": holder_name,
                "opened_date": opened_date,
                "complaint_count": complaints,
                "account_category": category,
                "record_ids": [],
                # Truth fields (isolated in account_truth.jsonl):
                "person_id": person_id,
                "layer": layer,
                "class": classification,
                "category": category,
                "mule_chain_id": mule_chain_id,
            }

        # ── Chain 1: Hero Chain CH-001 (Mule Syndicate A, COM-001, Pune-Nashik) ──
        # Layer 1: 3 victim intake accounts (flagged in complaints)
        ch1_l1 = [
            _create_acct(
                "BARB",
                f"{self.rng.choice(persons)['canonical_name']}",
                None,
                "MULE_INTAKE",
                "COMPLICIT",
                1,
                complaints=self.rng.randint(2, 4),
                opened_days_ago=self.rng.randint(30, 90),
                mule_chain_id="CH-001",
            )
            for _ in range(3)
        ]

        # Layer 2: Deceived holder AC-000310 (BARB:54004320985996, Ajay Ashok Shinde)
        ch1_l2 = [
            _create_acct(
                "BARB",
                hero_deceived["canonical_name"] if hero_deceived else "Ajay Ashok Shinde",
                "P-000102",
                "MULE_DECEIVED",
                "DECEIVED",
                2,
                complaints=1,
                opened_days_ago=120,
                fixed_key="BARB:54004320985996",
                mule_chain_id="CH-001",
            )
        ]

        # Layer 3: Consolidation & dispersion hub (Sachin Kale / Nitin Gaikwad)
        ch1_l3 = [
            _create_acct(
                "HDFC",
                hero_recruiter["canonical_name"] if hero_recruiter else "Sachin Tukaram Kale",
                "P-000101",
                "MULE_RECRUITER",
                "ORGANISER",
                3,
                complaints=5,
                opened_days_ago=250,
                mule_chain_id="CH-001",
            ),
            _create_acct(
                "ICIC",
                hero_controller["canonical_name"] if hero_controller else "Nitin Shankar Gaikwad",
                "P-000046",
                "MULE_CONTROLLER",
                "ORGANISER",
                3,
                complaints=6,
                opened_days_ago=400,
                mule_chain_id="CH-001",
            ),
        ]

        # Layer 4: Cash-out / Crypto conversion terminals
        ch1_l4 = [
            _create_acct(
                "SBIN",
                f"{self.rng.choice(persons)['canonical_name']}",
                None,
                "MULE_CASHOUT",
                "COMPLICIT",
                4,
                complaints=1,
                opened_days_ago=60,
                mule_chain_id="CH-001",
            )
            for _ in range(2)
        ]

        # ── Chain 2: Chain CH-002 (Cyber Phishing Ring D1, COM-004, Wardha-Nagpur) ──
        # Find members of COM-004 if available, otherwise random persons
        com4_members = [p for p in persons if p.get("network") == "COM-004"]
        c2_recruiter = com4_members[0] if len(com4_members) > 0 else self.rng.choice(persons)
        c2_deceived_holder = com4_members[1] if len(com4_members) > 1 else self.rng.choice(persons)

        ch2_l1 = [
            _create_acct(
                "MAHB",
                f"{self.rng.choice(persons)['canonical_name']}",
                None,
                "MULE_INTAKE",
                "COMPLICIT",
                1,
                complaints=self.rng.randint(2, 3),
                opened_days_ago=self.rng.randint(40, 100),
                mule_chain_id="CH-002",
            )
            for _ in range(2)
        ]
        ch2_l2 = [
            _create_acct(
                "PUNB",
                c2_deceived_holder["canonical_name"],
                c2_deceived_holder["person_id"],
                "MULE_DECEIVED",
                "DECEIVED",
                2,
                complaints=1,
                opened_days_ago=90,
                mule_chain_id="CH-002",
            )
        ]
        ch2_l3 = [
            _create_acct(
                "KKBK",
                c2_recruiter["canonical_name"],
                c2_recruiter["person_id"],
                "MULE_CONTROLLER",
                "ORGANISER",
                3,
                complaints=5,
                opened_days_ago=300,
                mule_chain_id="CH-002",
            )
        ]
        ch2_l4 = [
            _create_acct(
                "AXIS",
                f"{self.rng.choice(persons)['canonical_name']}",
                None,
                "MULE_CASHOUT",
                "COMPLICIT",
                4,
                complaints=1,
                opened_days_ago=50,
                mule_chain_id="CH-002",
            )
            for _ in range(2)
        ]

        # ── Chain 3: Chain CH-003 (Investment Task Scam Ring D2, COM-005, Navi Mumbai) ──
        com5_members = [p for p in persons if p.get("network") == "COM-005"]
        c3_controller = com5_members[0] if len(com5_members) > 0 else self.rng.choice(persons)
        c3_deceived_holder = com5_members[1] if len(com5_members) > 1 else self.rng.choice(persons)

        ch3_l1 = [
            _create_acct(
                "UBIN",
                f"{self.rng.choice(persons)['canonical_name']}",
                None,
                "MULE_INTAKE",
                "COMPLICIT",
                1,
                complaints=self.rng.randint(2, 4),
                opened_days_ago=self.rng.randint(30, 80),
                mule_chain_id="CH-003",
            )
            for _ in range(2)
        ]
        ch3_l2 = [
            _create_acct(
                "CANB",
                c3_deceived_holder["canonical_name"],
                c3_deceived_holder["person_id"],
                "MULE_DECEIVED",
                "DECEIVED",
                2,
                complaints=1,
                opened_days_ago=75,
                mule_chain_id="CH-003",
            )
        ]
        ch3_l3 = [
            _create_acct(
                "IDFB",
                c3_controller["canonical_name"],
                c3_controller["person_id"],
                "MULE_CONTROLLER",
                "ORGANISER",
                3,
                complaints=5,
                opened_days_ago=220,
                mule_chain_id="CH-003",
            )
        ]
        ch3_l4 = [
            _create_acct(
                "HDFC",
                f"{self.rng.choice(persons)['canonical_name']}",
                None,
                "MULE_CASHOUT",
                "COMPLICIT",
                4,
                complaints=1,
                opened_days_ago=45,
                mule_chain_id="CH-003",
            )
            for _ in range(2)
        ]

        all_mule_accts = (
            ch1_l1 + ch1_l2 + ch1_l3 + ch1_l4 +
            ch2_l1 + ch2_l2 + ch2_l3 + ch2_l4 +
            ch3_l1 + ch3_l2 + ch3_l3 + ch3_l4
        )
        self.accounts.extend(all_mule_accts)

        # ─────────────────────────────────────────────────────────
        # 2. Realistic Legitimate Financial Population
        # ─────────────────────────────────────────────────────────
        # A. Kirana / Small Merchant Accounts (~80 accounts)
        kirana_biz_types = [
            "Kirana Store", "General Stores", "Dairy & Bakery", "Provision Store",
            "Supermarket", "Vegetable Vendor", "Hardware Stores", "Chai Stall UPI",
        ]
        kirana_accounts: list[dict[str, Any]] = []
        for i in range(80):
            bank = self.rng.choice(BANK_CODES)
            p = self.rng.choice(persons) if persons else {"canonical_name": f"Merchant {i}", "person_id": None}
            biz = self.rng.choice(kirana_biz_types)
            cat = "INNOCENT_FAST_PASSTHROUGH" if i < 50 else "MERCHANT_CURRENT"
            acct = _create_acct(
                bank_code=bank["code"],
                holder_name=f"{p['canonical_name']} ({biz})",
                person_id=p.get("person_id"),
                category=cat,
                classification="LEGITIMATE_PASSTHROUGH",
                layer=0,
                complaints=0,
                opened_days_ago=self.rng.randint(300, 1800),
            )
            kirana_accounts.append(acct)
        self.accounts.extend(kirana_accounts)

        # B. Gig-Worker Platform Payout Accounts (~80 accounts)
        gig_platforms = [
            "Delivery Partner", "Zomato Partner", "Swiggy Fleet",
            "Uber Partner", "Blinkit Partner", "Auto Rickshaw Driver",
        ]
        gig_accounts: list[dict[str, Any]] = []
        for i in range(80):
            bank = self.rng.choice(BANK_CODES)
            p = self.rng.choice(persons) if persons else {"canonical_name": f"GigWorker {i}", "person_id": None}
            plat = self.rng.choice(gig_platforms)
            cat = "INNOCENT_FAST_PASSTHROUGH" if i < 50 else "SAVINGS_ACCOUNT"
            acct = _create_acct(
                bank_code=bank["code"],
                holder_name=f"{p['canonical_name']} ({plat})",
                person_id=p.get("person_id"),
                category=cat,
                classification="LEGITIMATE_PASSTHROUGH",
                layer=0,
                complaints=0,
                opened_days_ago=self.rng.randint(200, 1200),
            )
            gig_accounts.append(acct)
        self.accounts.extend(gig_accounts)

        # C. Corporate Payroll Accounts (~180 accounts)
        payroll_accounts: list[dict[str, Any]] = []
        for i in range(180):
            bank = self.rng.choice(BANK_CODES)
            p = self.rng.choice(persons) if persons else {"canonical_name": f"Employee {i}", "person_id": None}
            acct = _create_acct(
                bank_code=bank["code"],
                holder_name=p["canonical_name"],
                person_id=p.get("person_id"),
                category="SALARY_ACCOUNT",
                classification="ORDINARY",
                layer=0,
                complaints=0,
                opened_days_ago=self.rng.randint(300, 2000),
            )
            payroll_accounts.append(acct)
        self.accounts.extend(payroll_accounts)

        # D. Ordinary Savings Accounts (Fill up to target_accounts ~ 1,500)
        remaining = target_accounts - len(self.accounts)
        ordinary_accounts: list[dict[str, Any]] = []
        for i in range(max(0, remaining)):
            bank = self.rng.choice(BANK_CODES)
            p = self.rng.choice(persons) if persons else {"canonical_name": f"Citizen {i}", "person_id": None}
            acct = _create_acct(
                bank_code=bank["code"],
                holder_name=p["canonical_name"],
                person_id=p.get("person_id"),
                category="ORDINARY_SAVINGS",
                classification="ORDINARY",
                layer=0,
                complaints=0,
                opened_days_ago=self.rng.randint(100, 2000),
            )
            ordinary_accounts.append(acct)
        self.accounts.extend(ordinary_accounts)

        # Ensure account list is deterministically sorted by account_key
        self.accounts.sort(key=lambda a: a["account_key"])

        # ─────────────────────────────────────────────────────────
        # 3. Generating Transactions (~15,000)
        # ─────────────────────────────────────────────────────────
        all_account_keys = [a["account_key"] for a in self.accounts]
        ordinary_keys = [a["account_key"] for a in ordinary_accounts]
        payroll_keys = [a["account_key"] for a in payroll_accounts]
        kirana_keys = [a["account_key"] for a in kirana_accounts]
        gig_keys = [a["account_key"] for a in gig_accounts]

        # ── 3a. Mule Chain Transactions (Structured Layered Bursts) ──
        # Helper to generate a multi-layer transfer burst
        def _generate_chain_transfers(
            l1_accts: list[dict[str, Any]],
            l2_accts: list[dict[str, Any]],
            l3_accts: list[dict[str, Any]],
            l4_accts: list[dict[str, Any]],
            days_ago: int,
            burst_amount_base: float,
        ) -> None:
            burst_dt = self.base_date - timedelta(days=days_ago, hours=self.rng.randint(10, 18))

            # 1. Victims send money into Layer 1 intake accounts
            l1_totals: dict[str, float] = {a["account_key"]: 0.0 for a in l1_accts}
            for l1 in l1_accts:
                num_victims = self.rng.randint(2, 4)
                for _ in range(num_victims):
                    vic_acct = self.rng.choice(ordinary_keys)
                    amt = round(self.rng.uniform(burst_amount_base * 0.15, burst_amount_base * 0.35), 2)
                    l1_totals[l1["account_key"]] += amt
                    t_in = burst_dt - timedelta(minutes=self.rng.randint(30, 90))
                    self._add_transaction(vic_acct, l1["account_key"], amt, "UPI_P2P", t_in)

            # 2. Layer 1 transfers to Layer 2 (Deceived accounts)
            l2_totals: dict[str, float] = {a["account_key"]: 0.0 for a in l2_accts}
            for l1 in l1_accts:
                target_l2 = self.rng.choice(l2_accts)
                fwd_amt = round(l1_totals[l1["account_key"]] * 0.98, 2)
                l2_totals[target_l2["account_key"]] += fwd_amt
                t_fwd = burst_dt - timedelta(minutes=self.rng.randint(15, 30))
                self._add_transaction(l1["account_key"], target_l2["account_key"], fwd_amt, "IMPS", t_fwd)

            # 3. Layer 2 (Deceived account): Rapid sweep-out within 8-14 minutes, low fan-out = 1
            for l2 in l2_accts:
                target_l3 = self.rng.choice(l3_accts)
                # Sweep out almost all funds (passive conduit)
                sweep_amt = round(l2_totals[l2["account_key"]] * 0.99, 2)
                t_sweep = burst_dt - timedelta(minutes=self.rng.randint(2, 10))
                self._add_transaction(l2["account_key"], target_l3["account_key"], sweep_amt, "IMPS", t_sweep)

            # 4. Layer 3 (Controller/Recruiter hub): High dispersion fan-out to Layer 4 terminals
            for l3 in l3_accts:
                # Disperse funds to all Layer 4 cash-out accounts
                for l4 in l4_accts:
                    disp_amt = round(self.rng.uniform(burst_amount_base * 0.25, burst_amount_base * 0.45), 2)
                    t_disp = burst_dt + timedelta(minutes=self.rng.randint(10, 45))
                    self._add_transaction(l3["account_key"], l4["account_key"], disp_amt, "RTGS", t_disp)

        # Generate bursts across time for each chain
        # Hero Chain CH-001 (~3 bursts over past 6 months)
        _generate_chain_transfers(ch1_l1, ch1_l2, ch1_l3, ch1_l4, days_ago=15, burst_amount_base=500000.0)
        _generate_chain_transfers(ch1_l1, ch1_l2, ch1_l3, ch1_l4, days_ago=45, burst_amount_base=450000.0)
        _generate_chain_transfers(ch1_l1, ch1_l2, ch1_l3, ch1_l4, days_ago=90, burst_amount_base=400000.0)

        # Chain CH-002 (~2 bursts)
        _generate_chain_transfers(ch2_l1, ch2_l2, ch2_l3, ch2_l4, days_ago=25, burst_amount_base=300000.0)
        _generate_chain_transfers(ch2_l1, ch2_l2, ch2_l3, ch2_l4, days_ago=75, burst_amount_base=280000.0)

        # Chain CH-003 (~2 bursts)
        _generate_chain_transfers(ch3_l1, ch3_l2, ch3_l3, ch3_l4, days_ago=35, burst_amount_base=350000.0)
        _generate_chain_transfers(ch3_l1, ch3_l2, ch3_l3, ch3_l4, days_ago=110, burst_amount_base=320000.0)

        # ── 3b. Legitimate Kirana Merchant Flows (Daytime micro-UPI, evening supplier sweeps) ──
        for k_acct in kirana_keys:
            # 6-12 customer micro-UPI payments during daytime business hours (09:00 - 20:00)
            num_customers = self.rng.randint(6, 12)
            day_offset = self.rng.randint(5, 300)
            day_date = self.base_date - timedelta(days=day_offset)
            total_sales = 0.0

            for _ in range(num_customers):
                customer = self.rng.choice(ordinary_keys)
                sale_amt = round(self.rng.uniform(40.0, 1250.0), 2)
                total_sales += sale_amt
                t_cust = day_date.replace(
                    hour=self.rng.randint(9, 20),
                    minute=self.rng.randint(0, 59),
                    second=self.rng.randint(0, 59),
                )
                self._add_transaction(customer, k_acct, sale_amt, "UPI_P2P", t_cust)

            # Evening batch sweep to distributor/supplier (balanced turnover)
            supplier_acct = self.rng.choice(ordinary_keys)
            sweep_amt = round(total_sales * self.rng.uniform(0.88, 0.96), 2)
            t_supplier = day_date.replace(
                hour=21,
                minute=self.rng.randint(15, 55),
                second=self.rng.randint(0, 59),
            )
            self._add_transaction(k_acct, supplier_acct, sweep_amt, "NEFT_SUPPLIER_SWEEP", t_supplier)

        # ── 3c. Gig-Worker Platform Payout Flows (Weekly payouts, daily living expenses) ──
        for g_acct in gig_keys:
            # Platform payout credit
            payout_days_ago = self.rng.randint(3, 180)
            t_payout = self.base_date - timedelta(days=payout_days_ago, hours=self.rng.randint(9, 12))
            payout_amt = round(self.rng.uniform(3500.0, 11500.0), 2)
            platform_acct = self.rng.choice(payroll_keys)
            self._add_transaction(platform_acct, g_acct, payout_amt, "SALARY_CREDIT", t_payout)

            # 4-6 small fuel/food/recharge UPI expenditures
            for _ in range(self.rng.randint(4, 7)):
                vendor = self.rng.choice(kirana_keys) if kirana_keys else self.rng.choice(ordinary_keys)
                exp_amt = round(self.rng.uniform(60.0, 450.0), 2)
                t_exp = t_payout + timedelta(days=self.rng.randint(1, 5), hours=self.rng.randint(1, 10))
                self._add_transaction(g_acct, vendor, exp_amt, "UPI_P2P", t_exp)

        # ── 3d. Corporate Payroll & Salary Flows ──
        for p_acct in payroll_keys:
            # Recurring salary credits on 1st/30th
            for month_offset in [30, 60, 90]:
                t_sal = self.base_date - timedelta(days=month_offset, hours=10)
                sal_amt = round(self.rng.uniform(32000.0, 115000.0), 2)
                corp_acct = self.rng.choice(ordinary_keys)
                self._add_transaction(corp_acct, p_acct, sal_amt, "SALARY_CREDIT", t_sal)

                # Utility bill and grocery shopping
                utility_amt = round(self.rng.uniform(1200.0, 4800.0), 2)
                t_util = t_sal + timedelta(days=self.rng.randint(2, 7))
                utility_vendor = self.rng.choice(ordinary_keys)
                self._add_transaction(p_acct, utility_vendor, utility_amt, "UTILITY_BILL", t_util)

        # ── 3e. Fill Remaining Background Ordinary Transactions up to target_transactions (~15,000) ──
        remaining_txns = target_transactions - len(self.transactions)
        for _ in range(max(0, remaining_txns)):
            src, dst = self.rng.sample(all_account_keys, 2)
            txn_type = self.rng.choices(
                ["UPI_P2P", "MERCHANT_PAYMENT", "SALARY_CREDIT", "UTILITY_BILL"],
                weights=[65, 20, 10, 5],
                k=1,
            )[0]

            if txn_type == "SALARY_CREDIT":
                amt = round(self.rng.uniform(25000.0, 110000.0), 2)
            elif txn_type == "UTILITY_BILL":
                amt = round(self.rng.uniform(350.0, 4200.0), 2)
            elif txn_type == "MERCHANT_PAYMENT":
                amt = round(self.rng.uniform(80.0, 6500.0), 2)
            else:
                amt = round(self.rng.uniform(150.0, 12000.0), 2)

            ts = self.base_date - timedelta(
                days=self.rng.randint(1, 365),
                hours=self.rng.randint(0, 23),
                minutes=self.rng.randint(0, 59),
            )
            self._add_transaction(src, dst, amt, txn_type, ts)

        # Deterministic sort: by timestamp, then transaction ID
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
