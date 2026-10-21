"""
services/data_gen/sutradhar_data/v2_generator.py
Comprehensive Dataset v2 Generator for Sutradhar:
- Tiered scaling (dev: ~2k persons, ~5k mentions, ~1.5k accounts, ~15k txns, ~300 Kumbh events)
- Preserves byte-identical v1 hero scenarios and IDs (P-000045, PH-000007, CH-001, AC-000310, KUMBH-EVT-0001..0053)
- Background IDs start at 001000 with no 9999 cap (6-digit width)
- 8 criminal syndicates (3 mule rings, 2 extortion gangs, 2 drug chains, 1 hawala ring) + 5 bridges
- Multilingual pools with Zipfian surname distributions and VIP denylist
- Hard negatives: name collisions, chawls, shared SIMs, and innocent fast pass-through accounts
- Per-agency YAML noise profiles with ~50% Easy / 30% Medium / 20% Hard calibration
- Deterministic seeding to data/v2/<tier>/seed-<n>/ and data/truth/v2/<tier>/seed-<n>/
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
import random
import re
from typing import Any
import yaml

from .finance import BackgroundFinanceGenerator
from .lexicons import BANK_CODES, DISTRICTS, POLICE_STATIONS
from .lexicons.multilingual import sample_demographic_identity
from .mcoca import generate_mcoca_test_cases
from .safety import generate_invalid_pseudo_aadhaar, is_denylisted

REFERENCE_DATE = datetime(2026, 3, 1, 10, 0, 0)


def _gen_phone(rng: random.Random) -> str:
    first = rng.choice("6789")
    rest = "".join(str(rng.randint(0, 9)) for _ in range(9))
    return first + rest


def _gen_vehicle(rng: random.Random) -> str:
    dist = rng.randint(1, 50)
    letters = "".join(rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    num = rng.randint(1000, 9999)
    return f"MH{dist:02d}{letters}{num}"


class V2DatasetGenerator:
    """Orchestrates generation of dataset v2 across tiers and seeds."""

    def __init__(self, tier: str = "dev", seed: int = 42, out_dir: str = "data"):
        self.tier = tier
        self.seed = seed
        self.rng = random.Random(seed)
        self.out_dir = Path(out_dir)
        self.base_date = REFERENCE_DATE

        # Load configs
        cfg_dir = Path(__file__).parent / "config"
        with open(cfg_dir / "v2_tiers.yaml", encoding="utf-8") as f:
            self.tiers_cfg = yaml.safe_load(f)["tiers"]
        with open(cfg_dir / "noise_profiles.yaml", encoding="utf-8") as f:
            self.noise_cfg = yaml.safe_load(f)["profiles"]

        self.tier_spec = self.tiers_cfg.get(tier, self.tiers_cfg["dev"])

        # Counters for background entities starting at 001000
        self._person_seq = 1000
        self._record_seq = {"SPO": 1000, "CYB": 1000, "CEN": 1000}
        self._case_seq = {"SPO": 1000, "CYB": 1000, "CEN": 1000}
        self._mention_seq = 1000
        self._kumbh_seq = 100

        self.persons: list[dict[str, Any]] = []
        self.records: list[dict[str, Any]] = []
        self.mention_truth: list[dict[str, Any]] = []
        self.networks_truth: dict[str, Any] = {}
        self.syndicate_members: dict[str, list[dict[str, Any]]] = {}
        self.bridges: list[dict[str, Any]] = []

    def _next_person_id(self) -> str:
        pid = f"P-{self._person_seq:06d}"
        self._person_seq += 1
        return pid

    def _next_record_id(self, agency_code: str) -> str:
        seq = self._record_seq[agency_code]
        self._record_seq[agency_code] += 1
        return f"R-{agency_code}-{seq:06d}"

    def _next_case_ref(self, agency_code: str) -> str:
        seq = self._case_seq[agency_code]
        self._case_seq[agency_code] += 1
        return f"CASE-{agency_code}-{seq:06d}"

    def _next_mention_id(self, record_id: str) -> str:
        mid = f"M-{record_id}-{self._mention_seq}"
        self._mention_seq += 1
        return mid

    # ─────────────────────────────────────────────────────────
    # 1. Seeding Hero Scenarios & Planted Cast
    # ─────────────────────────────────────────────────────────
    def _seed_hero_cast(self) -> None:
        """Seed the 8 canonical hero scenarios and existing cast unchanged."""
        # Hero Bridge 1: Rakesh Dagdu Pawar (S-01, S-02)
        rakesh = {
            "person_id": "P-000045",
            "canonical_name": "Rakesh Dagdu Pawar",
            "name_dev": "राकेश दगडू पवार",
            "first_name": "Rakesh",
            "father_name": "Dagdu",
            "surname": "Pawar",
            "age": 34,
            "district": "Thane",
            "gender": "M",
            "phones": ["PH-000007"],
            "raw_phones": ["9000012345"],
            "accounts": [],
            "vehicles": ["VH-000003"],
            "addresses": ["950, Sahyadri Vihar, Thane"],
            "network": "COM-002",
            "role": "BROKER",
            "aliases": ["राका", "Raka"],
            "pool": "marathi",
            "is_hero": True,
        }
        self.persons.append(rakesh)
        self.bridges.append(rakesh)

        # Hero Bridge 2: Nitin Shankar Gaikwad (S-02)
        nitin = {
            "person_id": "P-000046",
            "canonical_name": "Nitin Shankar Gaikwad",
            "name_dev": "नितिन शंकर गायकवाड",
            "first_name": "Nitin",
            "father_name": "Shankar",
            "surname": "Gaikwad",
            "age": 38,
            "district": "Pune",
            "gender": "M",
            "phones": ["PH-000008"],
            "raw_phones": ["9822019999"],
            "accounts": [],
            "vehicles": [],
            "addresses": ["420, Model Colony, Pune"],
            "network": "COM-001",
            "role": "CONTROLLER",
            "aliases": ["Nitu"],
            "pool": "marathi",
            "is_hero": True,
        }
        self.persons.append(nitin)
        self.bridges.append(nitin)

        # Hero Network A leader & deceived account holder (S-03)
        sachin = {
            "person_id": "P-000101",
            "canonical_name": "Sachin Tukaram Kale",
            "name_dev": "सचिन तुकाराम काळे",
            "first_name": "Sachin",
            "father_name": "Tukaram",
            "surname": "Kale",
            "age": 29,
            "district": "Pune",
            "gender": "M",
            "phones": ["PH-000009"],
            "raw_phones": ["9822054321"],
            "accounts": [],
            "vehicles": [],
            "addresses": ["110, Kothrud, Pune"],
            "network": "COM-001",
            "role": "RECRUITER",
            "aliases": ["Sachu", "साचू"],
            "pool": "marathi",
            "is_hero": True,
        }
        self.persons.append(sachin)

        deceived_student = {
            "person_id": "P-000102",
            "canonical_name": "Ajay Ashok Shinde",
            "name_dev": "अजय अशोक शिंदे",
            "first_name": "Ajay",
            "father_name": "Ashok",
            "surname": "Shinde",
            "age": 21,
            "district": "Nashik",
            "gender": "M",
            "phones": ["PH-000010"],
            "raw_phones": ["8888012345"],
            "accounts": [{"account_id": "AC-000310", "account_key": "BARB:54004320985996", "classification": "LIKELY_DECEIVED"}],
            "vehicles": [],
            "addresses": ["Room 4, College Hostel, Nashik"],
            "network": "COM-001",
            "role": "DECEIVED_HOLDER",
            "aliases": [],
            "pool": "marathi",
            "is_hero": True,
        }
        self.persons.append(deceived_student)

        # Extortion Gang Leader (COM-002)
        anil_jadhav = {
            "person_id": "P-000103",
            "canonical_name": "Anil Ramchandra Jadhav",
            "name_dev": "अनिल रामचंद्र जाधव",
            "first_name": "Anil",
            "father_name": "Ramchandra",
            "surname": "Jadhav",
            "age": 45,
            "district": "Mumbai Suburban",
            "gender": "M",
            "phones": ["PH-000011"],
            "raw_phones": ["7022735306"],
            "accounts": [],
            "vehicles": [],
            "addresses": ["950, Sahyadri Vihar, Mumbai Suburban"],
            "network": "COM-002",
            "role": "LEADER",
            "aliases": ["Boss", "बॉस"],
            "pool": "marathi",
            "is_hero": True,
        }
        self.persons.append(anil_jadhav)

        for p in self.persons:
            p["pseudo_aadhaar"] = [generate_invalid_pseudo_aadhaar(self.rng)]

    # ─────────────────────────────────────────────────────────
    # 2. Generating 8 Syndicates (Dev Tier) + Bridges
    # ─────────────────────────────────────────────────────────
    def _generate_syndicates(self) -> None:
        """
        Generate 8 syndicates using only existing crime types:
        - 3 Mule Rings (CYBER_FRAUD): COM-001 (Hero A), COM-004 (D1), COM-005 (D2)
        - 2 Extortion Gangs (EXTORTION): COM-002 (Hero B), COM-006 (E1)
        - 2 Drug Chains (NARCOTICS): COM-003 (Hero C), COM-007 (F1)
        - 1 Hawala Transit Ring: COM-008 (H1)
        Plus 4-6 bridge operatives linking multiple syndicates.
        """
        syndicate_defs = [
            ("COM-001", "Mule Syndicate A (Pune-Nashik)", "CYBER_FRAUD"),
            ("COM-002", "Urban Extortion Gang B (Thane-Mumbai)", "EXTORTION"),
            ("COM-003", "Interstate Narcotics Chain C (Nagpur-Pune)", "NARCOTICS"),
            ("COM-004", "Cyber Phishing Ring D1 (Wardha-Nagpur)", "CYBER_FRAUD"),
            ("COM-005", "Investment Task Scam Ring D2 (Navi Mumbai)", "CYBER_FRAUD"),
            ("COM-006", "Protection Racket Gang E1 (Kolhapur-Solapur)", "EXTORTION"),
            ("COM-007", "Chemical Contraband Chain F1 (Aurangabad-Nashik)", "NARCOTICS"),
            ("COM-008", "Hawala Cash Transit Ring H1 (Mumbai-Thane)", "EXTORTION"),
        ]

        roles_pool = ["LEADER", "RECRUITER", "CONTROLLER", "MEMBER", "COURIER", "DECEIVED_HOLDER"]

        for cid, cname, ccrime in syndicate_defs:
            self.syndicate_members[cid] = []
            num_members = self.rng.randint(6, 12)
            for _ in range(num_members):
                identity = sample_demographic_identity(self.rng)
                fn = identity["first_name"]["canonical_rom"]
                sn = identity["surname"]["canonical_rom"]
                fatn = identity["father_name"]["canonical_rom"]
                role = self.rng.choice(roles_pool)
                dist = self.rng.choice(DISTRICTS)

                # Assign multiple phones to some members (burner phones)
                num_phones = self.rng.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0]
                phones = [_gen_phone(self.rng) for _ in range(num_phones)]

                person = {
                    "person_id": self._next_person_id(),
                    "canonical_name": f"{fn} {fatn} {sn}",
                    "name_dev": f"{identity['first_name']['canonical_dev']} {identity['father_name']['canonical_dev']} {identity['surname']['canonical_dev']}",
                    "first_name": fn,
                    "father_name": fatn,
                    "surname": sn,
                    "age": self.rng.randint(22, 58),
                    "district": dist,
                    "gender": identity["gender"],
                    "phones": [f"PH-{self.rng.randint(1000, 9999):06d}" for _ in range(len(phones))],
                    "raw_phones": phones,
                    "accounts": [],
                    "vehicles": [_gen_vehicle(self.rng)] if self.rng.random() < 0.3 else [],
                    "addresses": [f"{self.rng.randint(10, 999)}, {self.rng.choice(POLICE_STATIONS).replace(' PS', '')}, {dist}"],
                    "network": cid,
                    "crime_type": ccrime,
                    "role": role,
                    "aliases": [f"{fn[:4]}ya"] if self.rng.random() < 0.25 else [],
                    "pool": identity["pool"],
                    "is_hero": False,
                }
                self.persons.append(person)
                self.syndicate_members[cid].append(person)

        # Generate 3 additional bridge operatives (total 5 bridges including Rakesh & Nitin)
        bridge_pairs = [
            ("COM-004", "COM-006"),  # Phishing D1 <-> Extortion E1
            ("COM-005", "COM-007"),  # Scam D2 <-> Narcotics F1
            ("COM-008", "COM-002"),  # Hawala H1 <-> Extortion B
        ]
        for c1, c2 in bridge_pairs:
            identity = sample_demographic_identity(self.rng)
            fn = identity["first_name"]["canonical_rom"]
            sn = identity["surname"]["canonical_rom"]
            fatn = identity["father_name"]["canonical_rom"]
            dist = self.rng.choice(DISTRICTS)
            b_phone = _gen_phone(self.rng)

            bridge_person = {
                "person_id": self._next_person_id(),
                "canonical_name": f"{fn} {fatn} {sn}",
                "name_dev": f"{identity['first_name']['canonical_dev']} {identity['father_name']['canonical_dev']} {identity['surname']['canonical_dev']}",
                "first_name": fn,
                "father_name": fatn,
                "surname": sn,
                "age": self.rng.randint(30, 48),
                "district": dist,
                "gender": identity["gender"],
                "phones": [f"PH-{self.rng.randint(1000, 9999):06d}"],
                "raw_phones": [b_phone],
                "accounts": [],
                "vehicles": [_gen_vehicle(self.rng)],
                "addresses": [f"{self.rng.randint(1, 999)}, Station Road, {dist}"],
                "network": c1,
                "secondary_network": c2,
                "role": "BROKER",
                "aliases": [f"Bhai {fn[:3]}"],
                "pool": identity["pool"],
                "is_hero": False,
            }
            self.persons.append(bridge_person)
            self.bridges.append(bridge_person)

    # ─────────────────────────────────────────────────────────
    # 3. Generating Background Population & Hard Negatives
    # ─────────────────────────────────────────────────────────
    def _generate_background_population(self) -> None:
        """
        Generate remaining ordinary citizens up to target (2,000 persons):
        - Chawl and hostel shared address clusters
        - Common name collisions (different people, same name and age)
        - Family clusters sharing home landline / address
        """
        target_persons = self.tier_spec["num_persons"]
        remaining = target_persons - len(self.persons)

        # 3a. Chawl / Hostel shared address hard negatives (~150 persons)
        chawl_addresses = [
            "Room 12, BDD Chawl, Worli, Mumbai Suburban",
            "Room 4, Ganga Niwas Chawl, Thane",
            "Block B, Workers Barracks, MIDC, Pune",
            "Room 108, Pragati Girls Hostel, Shivajinagar, Pune",
            "Dormitory 3, Shramik Bhavan, Nashik",
        ]
        for _ in range(min(150, remaining // 10)):
            identity = sample_demographic_identity(self.rng)
            fn = identity["first_name"]["canonical_rom"]
            sn = identity["surname"]["canonical_rom"]
            fatn = identity["father_name"]["canonical_rom"]
            p = {
                "person_id": self._next_person_id(),
                "canonical_name": f"{fn} {fatn} {sn}",
                "name_dev": f"{identity['first_name']['canonical_dev']} {identity['father_name']['canonical_dev']} {identity['surname']['canonical_dev']}",
                "first_name": fn,
                "father_name": fatn,
                "surname": sn,
                "age": self.rng.randint(19, 32),
                "district": "Pune" if "Pune" in chawl_addresses[0] else "Mumbai Suburban",
                "gender": identity["gender"],
                "phones": [f"PH-{self.rng.randint(1000, 9999):06d}"],
                "raw_phones": [_gen_phone(self.rng)],
                "accounts": [],
                "vehicles": [],
                "addresses": [self.rng.choice(chawl_addresses)],
                "network": "NONE",
                "role": "CIVILIAN_CHAWL_RESIDENT",
                "aliases": [],
                "pool": identity["pool"],
                "is_hero": False,
            }
            self.persons.append(p)

        # 3b. Common name collisions (~50 pairs = 100 persons)
        for _ in range(50):
            identity = sample_demographic_identity(self.rng)
            fn = identity["first_name"]["canonical_rom"]
            sn = identity["surname"]["canonical_rom"]
            fatn = identity["father_name"]["canonical_rom"]
            age_base = self.rng.randint(25, 45)

            # Person A
            dist_a = self.rng.choice(DISTRICTS)
            p_a = {
                "person_id": self._next_person_id(),
                "canonical_name": f"{fn} {fatn} {sn}",
                "name_dev": f"{identity['first_name']['canonical_dev']} {identity['father_name']['canonical_dev']} {identity['surname']['canonical_dev']}",
                "first_name": fn,
                "father_name": fatn,
                "surname": sn,
                "age": age_base,
                "district": dist_a,
                "gender": identity["gender"],
                "phones": [f"PH-{self.rng.randint(1000, 9999):06d}"],
                "raw_phones": [_gen_phone(self.rng)],
                "accounts": [],
                "vehicles": [],
                "addresses": [f"{self.rng.randint(1, 999)}, Gandhi Chowk, {dist_a}"],
                "network": "NONE",
                "role": "COLLISION_A",
                "aliases": [],
                "pool": identity["pool"],
                "is_hero": False,
            }
            # Person B (Same name, same age, DIFFERENT district & phone)
            dist_b = self.rng.choice([d for d in DISTRICTS if d != dist_a])
            p_b = {
                "person_id": self._next_person_id(),
                "canonical_name": f"{fn} {fatn} {sn}",
                "name_dev": f"{identity['first_name']['canonical_dev']} {identity['father_name']['canonical_dev']} {identity['surname']['canonical_dev']}",
                "first_name": fn,
                "father_name": fatn,
                "surname": sn,
                "age": age_base,
                "district": dist_b,
                "gender": identity["gender"],
                "phones": [f"PH-{self.rng.randint(1000, 9999):06d}"],
                "raw_phones": [_gen_phone(self.rng)],
                "accounts": [],
                "vehicles": [],
                "addresses": [f"{self.rng.randint(1, 999)}, Station Road, {dist_b}"],
                "network": "NONE",
                "role": "COLLISION_B",
                "aliases": [],
                "pool": identity["pool"],
                "is_hero": False,
            }
            self.persons.extend([p_a, p_b])

        # 3c. Fill ordinary civilians
        remaining_now = target_persons - len(self.persons)
        for _ in range(max(0, remaining_now)):
            identity = sample_demographic_identity(self.rng)
            fn = identity["first_name"]["canonical_rom"]
            sn = identity["surname"]["canonical_rom"]
            fatn = identity["father_name"]["canonical_rom"]
            dist = self.rng.choice(DISTRICTS)
            p = {
                "person_id": self._next_person_id(),
                "canonical_name": f"{fn} {fatn} {sn}",
                "name_dev": f"{identity['first_name']['canonical_dev']} {identity['father_name']['canonical_dev']} {identity['surname']['canonical_dev']}",
                "first_name": fn,
                "father_name": fatn,
                "surname": sn,
                "age": self.rng.randint(18, 72),
                "district": dist,
                "gender": identity["gender"],
                "phones": [f"PH-{self.rng.randint(1000, 9999):06d}"],
                "raw_phones": [_gen_phone(self.rng)],
                "accounts": [],
                "vehicles": [_gen_vehicle(self.rng)] if self.rng.random() < 0.2 else [],
                "addresses": [f"{self.rng.randint(1, 999)}, {self.rng.choice(POLICE_STATIONS).replace(' PS', '')}, {dist}"],
                "network": "NONE",
                "role": "CIVILIAN",
                "aliases": [],
                "pool": identity["pool"],
                "is_hero": False,
            }
            self.persons.append(p)

        # Assign invalid pseudo-Aadhaars failing Verhoeff checksum
        for p in self.persons:
            if "pseudo_aadhaar" not in p:
                p["pseudo_aadhaar"] = [generate_invalid_pseudo_aadhaar(self.rng)] if self.rng.random() < 0.70 else []

        # Sort persons deterministically by person_id
        self.persons.sort(key=lambda p: p["person_id"])

    # ─────────────────────────────────────────────────────────
    # 4. Applying Per-Agency Noise Profiles
    # ─────────────────────────────────────────────────────────
    def _render_noisy_mention(
        self,
        person: dict[str, Any],
        agency: str,
        role: str,
        record_id: str,
    ) -> tuple[dict[str, Any], str, list[str]]:
        """
        Render a noisy mention using per-agency YAML noise profiles.
        Returns: (mention_dict, difficulty_tier, noise_tags)
        """
        cfg = self.noise_cfg.get(agency, self.noise_cfg["STATE_POLICE"])
        tags: list[str] = []

        fn = person["first_name"]
        fatn = person["father_name"]
        sn = person["surname"]
        age = person["age"]

        # 1. Script Mix & Transliteration
        use_dev = self.rng.random() < cfg.get("script_mix", 0.2)
        if use_dev:
            name_raw = f"{person['name_dev']}"
            name_script = "DEVANAGARI"
            tags.append("script_devanagari")
        else:
            # Check transliteration variant
            if self.rng.random() < cfg.get("transliteration", 0.25):
                # Sample surname or first name variant
                variants = ["Pawar", "Powar", "Pavar", "Patil", "Pateel", "Kale", "Kaale", "Jadhav", "Jadav"]
                v_sn = self.rng.choice(variants) if sn in ["Pawar", "Patil", "Kale", "Jadhav"] else sn
                name_raw = f"{fn} {fatn} {v_sn}"
                tags.append("translit_variant")
            else:
                name_raw = person["canonical_name"]
            name_script = "LATIN"

        # 2. Word Order (Surname First)
        if not use_dev and self.rng.random() < cfg.get("surname_first", 0.15):
            name_raw = f"{sn} {fn} {fatn}"
            tags.append("surname_first")

        # 3. Honorifics
        if self.rng.random() < cfg.get("honorifics", 0.15):
            prefix = "श्री " if use_dev else "Shri "
            name_raw = f"{prefix}{name_raw}"
            tags.append("honorific")

        # 4. Initials
        if not use_dev and self.rng.random() < cfg.get("initials", 0.15):
            name_raw = f"{fn[0]}. {fatn[0]}. {sn}"
            tags.append("initials")

        # 5. Typo
        if not use_dev and len(name_raw) > 6 and self.rng.random() < cfg.get("typos", 0.08):
            idx = self.rng.randint(2, len(name_raw) - 2)
            c_list = list(name_raw)
            c_list[idx], c_list[idx + 1] = c_list[idx + 1], c_list[idx]
            name_raw = "".join(c_list)
            tags.append("typo")

        # 6. Age Drift
        if self.rng.random() < cfg.get("age_drift", 0.15):
            drift = self.rng.choice([-3, -2, -1, 1, 2, 3])
            age = max(18, age + drift)
            tags.append("age_drift")

        # 7. Phone digit swap or Devanagari numerals
        phones = list(person["raw_phones"])
        if phones and self.rng.random() < cfg.get("phone_digit_swap", 0.05):
            ph = list(phones[0])
            if len(ph) == 10:
                ph[3], ph[4] = ph[4], ph[3]
                phones[0] = "".join(ph)
                tags.append("phone_digit_swap")

        # 8. Missing Fields
        fatn_val = fatn
        if self.rng.random() < cfg.get("missing_fields", 0.12):
            fatn_val = None
            tags.append("missing_father")

        # Determine difficulty tier based on number and severity of tags
        hard_ind = any(t in {"phone_digit_swap", "typo", "script_devanagari"} for t in tags)
        if len(tags) == 0 or (len(tags) == 1 and not hard_ind):
            difficulty = "EASY"
        elif len(tags) >= 3 or (len(tags) >= 2 and hard_ind):
            difficulty = "HARD"
        else:
            difficulty = "MEDIUM"

        mid = self._next_mention_id(record_id)
        mention = {
            "mention_id": mid,
            "record_id": record_id,
            "agency": agency,
            "role": role,
            "name_raw": name_raw,
            "name_norm": person["canonical_name"].lower(),
            "name_script": name_script,
            "father_name_raw": fatn_val,
            "father_name_norm": fatn_val.lower() if fatn_val else None,
            "age": age,
            "address_raw": person["addresses"][0] if person["addresses"] else None,
            "district": person["district"],
            "phones": phones,
            "accounts": [a["account_key"] for a in person.get("accounts", []) if "account_key" in a],
            "vehicles": person["vehicles"],
            "aliases": person["aliases"],
            "extraction_method": "FORM",
            "extraction_confidence": 0.95,
        }

        return mention, difficulty, tags

    # ─────────────────────────────────────────────────────────
    # 5. Generating Agency Records
    # ─────────────────────────────────────────────────────────
    def _generate_records(self) -> None:
        """
        Generate agency records partitioned by STATE_POLICE, MAHA_CYBER, CENTRAL_AGENCY.
        """
        target_records = self.tier_spec["num_records"]
        spo_count = int(target_records * 0.40)
        cyb_count = int(target_records * 0.40)
        cen_count = target_records - spo_count - cyb_count

        # 5a. STATE_POLICE Records (FIR & CHARGESHEET)
        for i in range(spo_count):
            rid = self._next_record_id("SPO")
            cref = self._next_case_ref("SPO")
            rec_type = self.rng.choice(["FIR", "CHARGESHEET"])
            crime = self.rng.choice(["EXTORTION", "NARCOTICS"])

            accused_person = self.rng.choice(self.persons)
            m_acc, diff_acc, tags_acc = self._render_noisy_mention(accused_person, "STATE_POLICE", "ACCUSED", rid)
            self.mention_truth.append({
                "mention_id": m_acc["mention_id"],
                "person_id": accused_person["person_id"],
                "record_id": rid,
                "agency": "STATE_POLICE",
                "role": "ACCUSED",
                "difficulty": diff_acc,
                "difficulty_tags": tags_acc,
                "tags": tags_acc,
            })

            comp_person = self.rng.choice(self.persons)
            m_comp, diff_comp, tags_comp = self._render_noisy_mention(comp_person, "STATE_POLICE", "COMPLAINANT", rid)
            self.mention_truth.append({
                "mention_id": m_comp["mention_id"],
                "person_id": comp_person["person_id"],
                "record_id": rid,
                "agency": "STATE_POLICE",
                "role": "COMPLAINANT",
                "difficulty": diff_comp,
                "difficulty_tags": tags_comp,
                "tags": tags_comp,
            })

            rec = {
                "record_id": rid,
                "agency": "STATE_POLICE",
                "record_type": rec_type,
                "crime_type": crime,
                "case_ref": cref,
                "district": accused_person["district"],
                "station": self.rng.choice(POLICE_STATIONS),
                "filed_date": (self.base_date - timedelta(days=self.rng.randint(10, 800))).strftime("%Y-%m-%d"),
                "language": self.rng.choice(["mr", "hi", "en"]),
                "sections": ["BNS-308", "BNS-351"] if crime == "EXTORTION" else ["NDPS-20", "NDPS-29"],
                "form_fields": {
                    "accused": [{
                        "name": m_acc["name_raw"],
                        "father_name": m_acc["father_name_raw"] or "",
                        "age": m_acc["age"] or 30,
                        "address": m_acc["address_raw"] or "",
                        "phone": m_acc["phones"][0] if m_acc["phones"] else "",
                        "alias": m_acc["aliases"][0] if m_acc["aliases"] else "",
                    }],
                    "complainant": {"name": m_comp["name_raw"], "phone": m_comp["phones"][0] if m_comp["phones"] else _gen_phone(self.rng)},
                    "victims": [],
                    "accounts": [],
                    "phones": m_acc["phones"] + m_comp["phones"],
                    "vehicles": m_acc["vehicles"],
                },
                "narrative": f"{rec_type} filed at police station against {m_acc['name_raw']} on complaint by {m_comp['name_raw']}. All data synthetic.",
            }
            self.records.append(rec)

        # 5b. MAHA_CYBER Records (COMPLAINT)
        for i in range(cyb_count):
            rid = self._next_record_id("CYB")
            cref = self._next_case_ref("CYB")
            accused_person = self.rng.choice(self.persons)
            m_acc, diff_acc, tags_acc = self._render_noisy_mention(accused_person, "MAHA_CYBER", "SUSPECT", rid)
            self.mention_truth.append({
                "mention_id": m_acc["mention_id"],
                "person_id": accused_person["person_id"],
                "record_id": rid,
                "agency": "MAHA_CYBER",
                "role": "SUSPECT",
                "difficulty": diff_acc,
                "difficulty_tags": tags_acc,
                "tags": tags_acc,
            })

            victim_person = self.rng.choice(self.persons)
            m_vic, diff_vic, tags_vic = self._render_noisy_mention(victim_person, "MAHA_CYBER", "VICTIM", rid)
            self.mention_truth.append({
                "mention_id": m_vic["mention_id"],
                "person_id": victim_person["person_id"],
                "record_id": rid,
                "agency": "MAHA_CYBER",
                "role": "VICTIM",
                "difficulty": diff_vic,
                "difficulty_tags": tags_vic,
                "tags": tags_vic,
            })

            rec = {
                "record_id": rid,
                "agency": "MAHA_CYBER",
                "record_type": "COMPLAINT",
                "crime_type": "CYBER_FRAUD",
                "case_ref": cref,
                "district": accused_person["district"],
                "station": "Cyber Crime Police Station",
                "filed_date": (self.base_date - timedelta(days=self.rng.randint(5, 400))).strftime("%Y-%m-%d"),
                "language": self.rng.choice(["en", "mr"]),
                "sections": ["IT-66D", "BNS-318"],
                "form_fields": {
                    "accused": [{
                        "name": m_acc["name_raw"],
                        "father_name": m_acc["father_name_raw"] or "",
                        "age": m_acc["age"] or 28,
                        "address": m_acc["address_raw"] or "",
                        "phone": m_acc["phones"][0] if m_acc["phones"] else "",
                        "alias": "",
                    }],
                    "complainant": {"name": m_vic["name_raw"], "phone": m_vic["phones"][0] if m_vic["phones"] else _gen_phone(self.rng)},
                    "victims": [{"name": m_vic["name_raw"], "phone": m_vic["phones"][0] if m_vic["phones"] else ""}],
                    "accounts": [],
                    "phones": m_acc["phones"] + m_vic["phones"],
                    "vehicles": [],
                },
                "narrative": f"Cyber complaint NCRP-1930 received from {m_vic['name_raw']} against {m_acc['name_raw']}. All data synthetic.",
            }
            self.records.append(rec)

        # 5c. CENTRAL_AGENCY Records (SEIZURE_REPORT)
        for i in range(cen_count):
            rid = self._next_record_id("CEN")
            cref = self._next_case_ref("CEN")
            accused_person = self.rng.choice(self.persons)
            m_acc, diff_acc, tags_acc = self._render_noisy_mention(accused_person, "CENTRAL_AGENCY", "ACCUSED", rid)
            self.mention_truth.append({
                "mention_id": m_acc["mention_id"],
                "person_id": accused_person["person_id"],
                "record_id": rid,
                "agency": "CENTRAL_AGENCY",
                "role": "ACCUSED",
                "difficulty": diff_acc,
                "difficulty_tags": tags_acc,
                "tags": tags_acc,
            })

            # Add witness mention to reach ~5,000 mentions
            wit_person = self.rng.choice(self.persons)
            m_wit, diff_wit, tags_wit = self._render_noisy_mention(wit_person, "CENTRAL_AGENCY", "WITNESS", rid)
            self.mention_truth.append({
                "mention_id": m_wit["mention_id"],
                "person_id": wit_person["person_id"],
                "record_id": rid,
                "agency": "CENTRAL_AGENCY",
                "role": "WITNESS",
                "difficulty": diff_wit,
                "difficulty_tags": tags_wit,
                "tags": tags_wit,
            })

            # Also add an optional second accused in some records
            if self.rng.random() < 0.40:
                co_accused = self.rng.choice(self.persons)
                m_co, diff_co, tags_co = self._render_noisy_mention(co_accused, "CENTRAL_AGENCY", "ACCUSED", rid)
                self.mention_truth.append({
                    "mention_id": m_co["mention_id"],
                    "person_id": co_accused["person_id"],
                    "record_id": rid,
                    "agency": "CENTRAL_AGENCY",
                    "role": "ACCUSED",
                    "difficulty": diff_co,
                    "difficulty_tags": tags_co,
                    "tags": tags_co,
                })
                accused_list = [
                    {"name": m_acc["name_raw"], "father_name": m_acc["father_name_raw"] or "", "age": m_acc["age"] or 35, "address": m_acc["address_raw"] or "", "phone": m_acc["phones"][0] if m_acc["phones"] else "", "alias": ""},
                    {"name": m_co["name_raw"], "father_name": m_co["father_name_raw"] or "", "age": m_co["age"] or 32, "address": m_co["address_raw"] or "", "phone": m_co["phones"][0] if m_co["phones"] else "", "alias": ""},
                ]
            else:
                accused_list = [{
                    "name": m_acc["name_raw"],
                    "father_name": m_acc["father_name_raw"] or "",
                    "age": m_acc["age"] or 35,
                    "address": m_acc["address_raw"] or "",
                    "phone": m_acc["phones"][0] if m_acc["phones"] else "",
                    "alias": "",
                }]

            rec = {
                "record_id": rid,
                "agency": "CENTRAL_AGENCY",
                "record_type": "SEIZURE_REPORT",
                "crime_type": "NARCOTICS",
                "case_ref": cref,
                "district": accused_person["district"],
                "station": "Zonal Seizure Unit",
                "filed_date": (self.base_date - timedelta(days=self.rng.randint(20, 600))).strftime("%Y-%m-%d"),
                "language": "en",
                "sections": ["NDPS-8C", "NDPS-21C"],
                "form_fields": {
                    "accused": accused_list,
                    "complainant": None,
                    "victims": [],
                    "accounts": [],
                    "phones": m_acc["phones"],
                    "vehicles": m_acc["vehicles"],
                },
                "narrative": f"Seizure report registered regarding contraband intercepted involving {m_acc['name_raw']}. All data synthetic.",
            }
            self.records.append(rec)

        # Sort records deterministically
        self.records.sort(key=lambda r: (r["agency"], r["record_id"]))
        self.mention_truth.sort(key=lambda m: m["mention_id"])

    # ─────────────────────────────────────────────────────────
    # 6. Generating Kumbh Event Stream (~300 events)
    # ─────────────────────────────────────────────────────────
    def _generate_kumbh_events(self) -> list[dict[str, Any]]:
        """
        Generate Kumbh event stream:
        - Events 0001..0053 are byte-identical to data/kumbh/events.jsonl
        - Background events start at KUMBH-EVT-0100 up to target (~300)
        """
        v1_kumbh_file = Path("data/kumbh/events.jsonl")
        events: list[dict[str, Any]] = []
        if v1_kumbh_file.exists():
            with open(v1_kumbh_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))

        # Add background events starting at 0100
        zones = ["Ramkund", "Panchavati", "Tapovan", "Trimbakeshwar", "Godavari Ghats"]
        types = ["WATCHLIST_SIGHTING", "SCAM_PATTERN", "MISSING_PERSON"]
        weights = [10, 15, 75]  # mostly benign missing persons / lost and found

        target_kumbh = self.tier_spec["num_kumbh_events"]
        remaining = target_kumbh - len(events)
        base_time = datetime(2027, 1, 13, 6, 0, 0)

        for _ in range(max(0, remaining)):
            eid = f"KUMBH-EVT-{self._kumbh_seq:04d}"
            self._kumbh_seq += 1
            z = self.rng.choice(zones)
            ev_type = self.rng.choices(types, weights=weights, k=1)[0]
            offset = timedelta(days=self.rng.randint(0, 44), hours=self.rng.randint(4, 22), minutes=self.rng.randint(0, 59))

            ev = {
                "event_id": eid,
                "ts": (base_time + offset).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "zone": z,
                "event_type": ev_type,
                "subject_token": f"TOK-SYNTH-{self._kumbh_seq:04d}",
                "related_ids": [],
                "details": {
                    "description": f"Synthetic Kumbh event: simulated {ev_type.lower().replace('_', ' ')} observation near {z}.",
                    "confidence": round(self.rng.uniform(0.65, 0.95), 2),
                },
            }
            events.append(ev)

        events.sort(key=lambda e: (e["ts"], e["event_id"]))
        return events

    # ─────────────────────────────────────────────────────────
    # 7. Orchestration & File Emission
    # ─────────────────────────────────────────────────────────
    def generate(self) -> dict[str, Any]:
        """Execute full dataset v2 generation and write to output directories."""
        self._seed_hero_cast()
        self._generate_syndicates()
        self._generate_background_population()
        self._generate_records()

        # Generate financial data (~1,500 accounts, ~15,000 transactions)
        fin_gen = BackgroundFinanceGenerator(self.rng, self.base_date)
        mule_accounts = []
        for p in self.persons:
            for acc in p.get("accounts", []):
                if isinstance(acc, dict) and "account_key" in acc:
                    mule_accounts.append({
                        "account_key": acc["account_key"],
                        "bank": acc["account_key"].split(":")[0],
                        "ifsc": f"{acc['account_key'].split(':')[0]}012345",
                        "holder_name_raw": p["canonical_name"],
                        "opened_date": "2024-01-10",
                        "complaint_count": 1,
                        "account_category": "MULE_ACCOUNT",
                        "person_id": p["person_id"],
                        "classification": acc.get("classification", "LIKELY_DECEIVED" if p.get("role") == "DECEIVED_HOLDER" else "ORGANISER"),
                        "layer": acc.get("layer", 2 if p.get("role") == "DECEIVED_HOLDER" else 1),
                        "record_ids": [],
                    })

        accounts, transactions = fin_gen.generate_financial_dataset(
            persons=self.persons,
            mule_accounts=mule_accounts,
            target_accounts=self.tier_spec["num_accounts"],
            target_transactions=self.tier_spec["num_transactions"],
        )

        kumbh_events = self._generate_kumbh_events()

        # Paths
        tier_dir = self.out_dir / "v2" / self.tier / f"seed-{self.seed}"
        truth_dir = self.out_dir / "truth" / "v2" / self.tier / f"seed-{self.seed}"

        tier_dir.mkdir(parents=True, exist_ok=True)
        truth_dir.mkdir(parents=True, exist_ok=True)

        # Write partitioned records
        spo_records = [r for r in self.records if r["agency"] == "STATE_POLICE"]
        cyb_records = [r for r in self.records if r["agency"] == "MAHA_CYBER"]
        cen_records = [r for r in self.records if r["agency"] == "CENTRAL_AGENCY"]

        def write_jsonl(p: Path, items: list[dict]):
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                for it in items:
                    f.write(json.dumps(it, ensure_ascii=False) + "\n")

        write_jsonl(tier_dir / "STATE_POLICE" / "records.jsonl", spo_records)
        write_jsonl(tier_dir / "MAHA_CYBER" / "records.jsonl", cyb_records)
        write_jsonl(tier_dir / "MAHA_CYBER" / "accounts.jsonl", accounts)
        write_jsonl(tier_dir / "MAHA_CYBER" / "transactions.jsonl", transactions)
        write_jsonl(tier_dir / "CENTRAL_AGENCY" / "records.jsonl", cen_records)
        write_jsonl(tier_dir / "kumbh" / "events.jsonl", kumbh_events)

        # Write truth files
        write_jsonl(truth_dir / "mention_truth.jsonl", self.mention_truth)
        
        person_truth = [{
            "person_id": p["person_id"],
            "canonical_name": p["canonical_name"],
            "canonical_name_dev": p["name_dev"],
            "network": p["network"],
            "role": p["role"],
            "district": p["district"],
            "phones": p["phones"],
            "pseudo_aadhaar": p.get("pseudo_aadhaar", []),
            "pool": p.get("pool", "marathi"),
            "is_hero": p.get("is_hero", False),
        } for p in self.persons]
        write_jsonl(truth_dir / "person_truth.jsonl", person_truth)

        account_truth = [{
            "account_key": a["account_key"],
            "person_id": a.get("person_id"),
            "layer": a.get("layer", 0),
            "class": a.get("classification", "NEUTRAL"),
            "category": a.get("account_category", "ORDINARY"),
            "bank": a.get("bank", ""),
            "complaint_count": a.get("complaint_count", 0),
        } for a in accounts]
        write_jsonl(truth_dir / "account_truth.jsonl", account_truth)

        # Networks truth
        networks_truth = {
            "A": {
                "name": "Mule Syndicate A (Pune-Nashik)",
                "members": [p["person_id"] for p in self.syndicate_members.get("COM-001", [])],
                "bridges": ["P-000045"],
                "leader_id": None,
                "recruiter_id": self.syndicate_members.get("COM-001", [])[0]["person_id"] if self.syndicate_members.get("COM-001") else None,
                "controller_id": "P-000045",
            },
            "B": {
                "name": "Urban Extortion Gang B (Thane-Mumbai)",
                "members": [p["person_id"] for p in self.syndicate_members.get("COM-002", [])],
                "bridges": ["P-000045"],
                "leader_id": "P-000103",
            },
            "C": {
                "name": "Interstate Narcotics Chain C (Nagpur-Pune)",
                "members": [p["person_id"] for p in self.syndicate_members.get("COM-003", [])],
                "bridges": ["P-000046"],
                "leader_id": None,
                "financier_id": self.syndicate_members.get("COM-003", [])[0]["person_id"] if self.syndicate_members.get("COM-003") else None,
            },
            "bridge_1": {
                "person_id": "P-000045",
                "name": "Rakesh Dagdu Pawar",
                "networks": ["COM-001", "COM-002"],
                "agencies": ["STATE_POLICE", "MAHA_CYBER", "CENTRAL_AGENCY"],
            },
            "bridge_2": {
                "person_id": "P-000046",
                "name": "Nitin Suresh Shinde",
                "networks": ["COM-001", "COM-003"],
                "agencies": ["MAHA_CYBER", "CENTRAL_AGENCY"],
            },
            "syndicates": {
                cid: {
                    "members": [p["person_id"] for p in members],
                    "count": len(members),
                } for cid, members in self.syndicate_members.items()
            },
            "bridges": [{
                "person_id": b["person_id"],
                "canonical_name": b["canonical_name"],
                "network": b["network"],
                "secondary_network": b.get("secondary_network"),
            } for b in self.bridges],
        }
        with open(truth_dir / "networks_truth.json", "w", encoding="utf-8") as f:
            json.dump(networks_truth, f, ensure_ascii=False, indent=2)

        # MCOCA Truth
        mcoca_truth = generate_mcoca_test_cases(self.base_date)
        with open(truth_dir / "mcoca_truth.json", "w", encoding="utf-8") as f:
            json.dump(mcoca_truth, f, ensure_ascii=False, indent=2)

        # Compute difficulty mix
        diff_counts = {"EASY": 0, "MEDIUM": 0, "HARD": 0}
        for m in self.mention_truth:
            diff_counts[m["difficulty"]] = diff_counts.get(m["difficulty"], 0) + 1
        total_m = len(self.mention_truth) or 1
        achieved_diff = {k: round(v / total_m, 3) for k, v in diff_counts.items()}

        summary = {
            "version": "v2",
            "tier": self.tier,
            "seed": self.seed,
            "total_persons": len(self.persons),
            "total_records": len(self.records),
            "total_mentions": len(self.mention_truth),
            "total_accounts": len(accounts),
            "total_transactions": len(transactions),
            "total_kumbh_events": len(kumbh_events),
            "total_syndicates": len(self.syndicate_members),
            "total_bridges": len(self.bridges),
            "achieved_difficulty_mix": achieved_diff,
            "tier_dir": str(tier_dir),
            "truth_dir": str(truth_dir),
        }
        return summary
