"""
Entity-first generator for Sutradhar synthetic data.

Generates true persons first (the ground truth), then emits records
that mention those persons with varying levels of noise.

All names, phones, accounts, and other identifiers are ENTIRELY FICTIONAL.
"""

import random
import string
from typing import Any

from .lexicons import (
    BANK_CODES,
    DISTRICTS,
    FATHER_NAMES,
    FIRST_NAMES,
    POLICE_STATIONS,
    SURNAMES,
)


def _gen_phone(rng: random.Random) -> str:
    """Generate a synthetic 10-digit Indian mobile number."""
    first = rng.choice("6789")
    rest = "".join(rng.choices(string.digits, k=9))
    return first + rest


def _gen_account(rng: random.Random, bank_code: str) -> str:
    """Generate a synthetic bank account number."""
    return "".join(rng.choices(string.digits, k=14))


def _gen_ifsc(rng: random.Random, bank: dict) -> str:
    """Generate a synthetic IFSC code."""
    suffix = "".join(rng.choices(string.ascii_uppercase + string.digits, k=6))
    return bank["ifsc_prefix"] + suffix


def _gen_vehicle(rng: random.Random) -> str:
    """Generate a synthetic Maharashtra vehicle plate."""
    dist_code = rng.randint(1, 50)
    letters = "".join(rng.choices(string.ascii_uppercase, k=2))
    num = rng.randint(1000, 9999)
    return f"MH{dist_code:02d}{letters}{num}"


class PersonRecord:
    """A true person with canonical identity."""

    def __init__(
        self,
        person_id: str,
        first_name: dict,
        father_name: dict,
        surname: dict,
        age: int,
        district: str,
        gender: str,
        phones: list[str],
        accounts: list[dict],
        vehicles: list[str],
        addresses: list[str],
        network: str,
        role: str,
        aliases: list[str] | None = None,
    ):
        self.person_id = person_id
        self.first_name = first_name
        self.father_name = father_name
        self.surname = surname
        self.age = age
        self.district = district
        self.gender = gender
        self.phones = phones
        self.accounts = accounts
        self.vehicles = vehicles
        self.addresses = addresses
        self.network = network
        self.role = role
        self.aliases = aliases or []

    @property
    def canonical_name_dev(self) -> str:
        return f"{self.first_name['canonical_dev']} {self.father_name['canonical_dev']} {self.surname['canonical_dev']}"

    @property
    def canonical_name_rom(self) -> str:
        return f"{self.first_name['canonical_rom']} {self.father_name['canonical_rom']} {self.surname['canonical_rom']}"

    def to_truth_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "canonical_name": self.canonical_name_rom,
            "canonical_name_dev": self.canonical_name_dev,
            "network": self.network,
            "role": self.role,
            "district": self.district,
            "phones": self.phones,
            "accounts": [a["account_key"] for a in self.accounts],
            "aliases": self.aliases,
        }


def _find_name_entry(entries: list[dict], canonical_rom: str) -> dict | None:
    """Find a lexicon entry by canonical Roman name."""
    for e in entries:
        if e["canonical_rom"] == canonical_rom:
            return e
    return None


def _find_surname_entry(canonical_rom: str) -> dict:
    entry = _find_name_entry(SURNAMES, canonical_rom)
    if entry is None:
        raise ValueError(f"Surname '{canonical_rom}' not found in lexicons")
    return entry


def _find_first_name_entry(canonical_rom: str) -> dict:
    entry = _find_name_entry(FIRST_NAMES, canonical_rom)
    if entry is None:
        raise ValueError(f"First name '{canonical_rom}' not found in lexicons")
    return entry


def _find_father_name_entry(canonical_rom: str) -> dict:
    entry = _find_name_entry(FATHER_NAMES, canonical_rom)
    if entry is None:
        # Fall back to first names
        entry = _find_name_entry(FIRST_NAMES, canonical_rom)
    if entry is None:
        raise ValueError(f"Father name '{canonical_rom}' not found in lexicons")
    return entry


class EntityGenerator:
    """Generates the true entity population for a dataset version."""

    def __init__(self, rng: random.Random, version: str = "v0"):
        self.rng = rng
        self.version = version
        self.persons: list[PersonRecord] = []
        self._person_counter = 0
        self._account_counter = 0
        self._phone_counter = 0

    def _next_person_id(self) -> str:
        self._person_counter += 1
        return f"P-{self._person_counter:06d}"

    def _next_account_key(self, bank_code: str, acct_no: str) -> str:
        return f"{bank_code}:{acct_no}"

    def _make_account(self, bank_code: str | None = None) -> dict:
        bank = (
            self.rng.choice(BANK_CODES)
            if bank_code is None
            else next(b for b in BANK_CODES if b["code"] == bank_code)
        )
        acct_no = _gen_account(self.rng, bank["code"])
        return {
            "bank": bank["code"],
            "bank_name": bank["name"],
            "account_no": acct_no,
            "account_key": self._next_account_key(bank["code"], acct_no),
            "ifsc": _gen_ifsc(self.rng, bank),
            "holder_name": "",  # filled after person creation
        }

    def _create_person(
        self,
        first_name_rom: str,
        father_name_rom: str,
        surname_rom: str,
        age: int,
        district: str,
        network: str,
        role: str,
        gender: str = "M",
        num_phones: int = 1,
        num_accounts: int = 1,
        num_vehicles: int = 0,
        aliases: list[str] | None = None,
        bank_code: str | None = None,
        forced_phone: str | None = None,
    ) -> PersonRecord:
        """Create a specific person with known attributes."""
        pid = self._next_person_id()
        first = _find_first_name_entry(first_name_rom)
        father = _find_father_name_entry(father_name_rom)
        surname = _find_surname_entry(surname_rom)

        phones = []
        if forced_phone:
            phones.append(forced_phone)
            num_phones -= 1
        for _ in range(num_phones):
            phones.append(_gen_phone(self.rng))

        accounts = []
        for _ in range(num_accounts):
            acct = self._make_account(bank_code)
            acct["holder_name"] = f"{first_name_rom} {surname_rom}"
            accounts.append(acct)

        vehicles = [_gen_vehicle(self.rng) for _ in range(num_vehicles)]

        station = self.rng.choice(POLICE_STATIONS)
        address = f"{self.rng.randint(1, 999)}, {station.replace(' PS', '')}, {district}"

        person = PersonRecord(
            person_id=pid,
            first_name=first,
            father_name=father,
            surname=surname,
            age=age,
            district=district,
            gender=gender,
            phones=phones,
            accounts=accounts,
            vehicles=vehicles,
            addresses=[address],
            network=network,
            role=role,
            aliases=aliases,
        )
        self.persons.append(person)
        return person

    def _create_random_person(
        self, network: str = "NONE", role: str = "NEUTRAL", district: str | None = None
    ) -> PersonRecord:
        """Create a random background person."""
        first = self.rng.choice(FIRST_NAMES)
        father = self.rng.choice(FATHER_NAMES)
        surname = self.rng.choice(SURNAMES)
        age = self.rng.randint(20, 60)
        dist = district or self.rng.choice(DISTRICTS)

        return self._create_person(
            first_name_rom=first["canonical_rom"],
            father_name_rom=father["canonical_rom"],
            surname_rom=surname["canonical_rom"],
            age=age,
            district=dist,
            network=network,
            role=role,
            gender=first.get("gender", "M"),
            num_phones=self.rng.randint(1, 2),
            num_accounts=self.rng.randint(0, 1),
            num_vehicles=self.rng.randint(0, 1),
        )

    def generate_planted_cast(self) -> dict[str, list[PersonRecord]]:
        """Generate the planted networks and bridges from the PRD cast."""
        cast: dict[str, list[PersonRecord]] = {
            "A": [],
            "B": [],
            "C": [],
            "bridges": [],
            "collisions": [],
            "innocents": [],
            "background": [],
        }

        # --- Bridge 1: Rakesh Dagdu Pawar ---
        # Appears across all 3 agencies
        bridge_phone = _gen_phone(self.rng)  # shared phone across networks
        rakesh = self._create_person(
            "Rakesh",
            "Dagdu",
            "Pawar",
            34,
            "Thane",
            network="B",
            role="BROKER",
            aliases=["राका", "Raka"],
            forced_phone=bridge_phone,
            num_vehicles=1,
        )
        cast["bridges"].append(rakesh)

        # --- Network A: Cyber-fraud mule ring (MAHA_CYBER) ---
        # Recruiter: Sachin Kale
        sachin = self._create_person(
            "Sachin",
            "Tukaram",
            "Kale",
            29,
            "Pune",
            network="A",
            role="RECRUITER",
            aliases=["Sachu", "साचू"],
            bank_code="HDFC",
        )
        cast["A"].append(sachin)

        # Controller: Nitin Gaikwad (also Bridge 2)
        nitin_phone = _gen_phone(self.rng)
        nitin = self._create_person(
            "Nitin",
            "Shankar",
            "Gaikwad",
            38,
            "Pune",
            network="A",
            role="CONTROLLER",
            forced_phone=nitin_phone,
            bank_code="SBIN",
        )
        cast["A"].append(nitin)
        cast["bridges"].append(nitin)

        # Mule account holders for Network A
        # 8+ deceived holders (v0 = smaller scale)
        num_deceived = 8 if self.version != "v0" else 4
        num_mules = max(12, num_deceived + 4) if self.version != "v0" else 8
        victim_districts = self.rng.sample(DISTRICTS, min(6, len(DISTRICTS)))

        for i in range(num_deceived):
            p = self._create_random_person(
                network="A",
                role="DECEIVED_HOLDER",
                district=self.rng.choice(victim_districts),
            )
            cast["A"].append(p)

        for i in range(num_mules - num_deceived):
            p = self._create_random_person(
                network="A",
                role="MEMBER",
                district=self.rng.choice(victim_districts),
            )
            cast["A"].append(p)

        # Victims (complainants)
        for i in range(min(6, len(victim_districts))):
            p = self._create_random_person(
                network="NONE",
                role="NEUTRAL",
                district=victim_districts[i],
            )
            cast["A"].append(p)

        # --- Network B: Extortion gang (STATE_POLICE) ---
        # Leader: Anil Jadhav (rarely appears)
        anil = self._create_person(
            "Anil",
            "Ramchandra",
            "Jadhav",
            45,
            "Mumbai Suburban",
            network="B",
            role="LEADER",
            aliases=["Boss", "बॉस"],
        )
        cast["B"].append(anil)

        # 6 members across 3 stations
        b_members_data = [
            ("Vijay", "Ganpat", "Shinde", 30, "Thane"),
            ("Sandeep", "Namdev", "More", 33, "Pune"),
            ("Deepak", "Vitthal", "Bhosale", 27, "Mumbai Suburban"),
            ("Manoj", "Laxman", "Sonawane", 35, "Thane"),
            ("Ganesh", "Bapu", "Kamble", 28, "Pune"),
        ]
        for fn, fatn, sn, age, dist in b_members_data:
            p = self._create_person(
                fn,
                fatn,
                sn,
                age,
                dist,
                network="B",
                role="MEMBER",
            )
            cast["B"].append(p)

        # --- Network C: Drug chain (CENTRAL_AGENCY + STATE_POLICE) ---
        # Financier: Mahendra Rathore (outside Maharashtra)
        mahendra = self._create_person(
            "Mahendra",
            "Arjun",
            "Rathore",
            50,
            "Nagpur",
            network="C",
            role="FINANCIER",
        )
        cast["C"].append(mahendra)

        # Lab operator: Prakash Shinde
        prakash = self._create_person(
            "Prakash",
            "Sadashiv",
            "Shinde",
            42,
            "Pune",
            network="C",
            role="MEMBER",
            num_vehicles=1,
        )
        cast["C"].append(prakash)

        # 4 couriers
        courier_data = [
            ("Ravi", "Krishna", "Salve", 25, "Nashik"),
            ("Harsh", "Subhash", "Lokhande", 31, "Kolhapur"),
            ("Tushar", "Pandurang", "Waghmare", 28, "Aurangabad"),
            ("Bharat", "Dattatray", "Thomare", 33, "Solapur"),
        ]
        for fn, fatn, sn, age, dist in courier_data:
            p = self._create_person(
                fn,
                fatn,
                sn,
                age,
                dist,
                network="C",
                role="COURIER",
                num_vehicles=1,
            )
            cast["C"].append(p)

        # Bridge 2: Nitin Gaikwad also receives funds in C
        # (already created above, just note the cross-network link)

        # --- Common-name collision groups (30+) ---
        # Create groups of 2-3 people with very similar names but different identities
        collision_first_names = [
            "Rakesh",
            "Sachin",
            "Nitin",
            "Vijay",
            "Sandeep",
            "Amit",
            "Rajesh",
            "Sanjay",
            "Sunil",
            "Ramesh",
            "Deepak",
            "Manoj",
            "Ganesh",
            "Vikas",
            "Prashant",
        ]
        collision_surnames = [
            "Pawar",
            "Patil",
            "Shinde",
            "Jadhav",
            "More",
            "Kale",
            "Deshmukh",
            "Kulkarni",
            "Gaikwad",
            "Bhosale",
        ]

        collision_count = 0
        num_collision_groups = 32 if self.version != "v0" else 16
        used_combos: set[tuple[str, str]] = set()

        for _ in range(num_collision_groups):
            fn = self.rng.choice(collision_first_names)
            sn = self.rng.choice(collision_surnames)
            combo = (fn, sn)
            if combo in used_combos:
                continue
            used_combos.add(combo)

            # 2-3 distinct people with same first+surname but different fathers/districts
            group_size = self.rng.randint(2, 3)
            for _ in range(group_size):
                father = self.rng.choice(FATHER_NAMES)
                dist = self.rng.choice(DISTRICTS)
                p = self._create_person(
                    fn,
                    father["canonical_rom"],
                    sn,
                    self.rng.randint(22, 55),
                    dist,
                    network="NONE",
                    role="NEUTRAL",
                    gender="M",
                )
                cast["collisions"].append(p)
            collision_count += 1

        # --- Innocent look-alikes (10+) ---
        # Share a bank or district with organisers but have no crime link
        organiser_districts = ["Thane", "Pune", "Mumbai Suburban"]
        organiser_banks = ["HDFC", "SBIN"]
        num_innocents = 12 if self.version != "v0" else 6
        for _ in range(num_innocents):
            dist = self.rng.choice(organiser_districts)
            bank = self.rng.choice(organiser_banks)
            p = self._create_random_person(
                network="NONE",
                role="NEUTRAL",
                district=dist,
            )
            # Ensure they have an account at the same bank
            if not p.accounts:
                acct = self._make_account(bank)
                acct["holder_name"] = p.canonical_name_rom
                p.accounts.append(acct)
            cast["innocents"].append(p)

        # --- Background noise ---
        num_bg = 10 if self.version == "v0" else 30
        for _ in range(num_bg):
            p = self._create_random_person()
            cast["background"].append(p)

        return cast
