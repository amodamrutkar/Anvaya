"""
Noise operators for Sutradhar synthetic data.

Each operator applies a specific type of realistic messiness to person mentions.
Probabilities are controlled per dataset version.
"""

import random
from typing import Any

from .lexicons import HONORIFICS_DEV, HONORIFICS_ROM

# Per-version noise probabilities
VERSION_NOISE = {
    "v0": {
        "translit": 0.05,
        "script_mix": 0.05,
        "initials": 0.05,
        "honorific": 0.05,
        "word_order": 0.02,
        "alias": 0.05,
        "missing_father": 0.05,
        "typo": 0.02,
        "missing_field": 0.02,
        "old_phone": 0.02,
        "address_change": 0.02,
        "age_drift": 0.05,
    },
    "v1": {
        "translit": 0.10,
        "script_mix": 0.08,
        "initials": 0.08,
        "honorific": 0.10,
        "word_order": 0.05,
        "alias": 0.08,
        "missing_father": 0.10,
        "typo": 0.05,
        "missing_field": 0.05,
        "old_phone": 0.05,
        "address_change": 0.05,
        "age_drift": 0.08,
    },
    "v2": {
        "translit": 0.30,
        "script_mix": 0.25,
        "initials": 0.20,
        "honorific": 0.20,
        "word_order": 0.15,
        "alias": 0.20,
        "missing_father": 0.25,
        "typo": 0.15,
        "missing_field": 0.15,
        "old_phone": 0.12,
        "address_change": 0.15,
        "age_drift": 0.15,
    },
    "v3": {
        "translit": 0.50,
        "script_mix": 0.40,
        "initials": 0.35,
        "honorific": 0.30,
        "word_order": 0.30,
        "alias": 0.35,
        "missing_father": 0.40,
        "typo": 0.30,
        "missing_field": 0.25,
        "old_phone": 0.20,
        "address_change": 0.25,
        "age_drift": 0.25,
    },
}


def _swap_char(s: str, rng: random.Random) -> str:
    """Introduce a single character swap typo."""
    if len(s) < 3:
        return s
    i = rng.randint(1, len(s) - 2)
    chars = list(s)
    chars[i], chars[i + 1] = chars[i + 1], chars[i]
    return "".join(chars)


def apply_noise(person, rng: random.Random, version: str) -> dict[str, Any]:
    """
    Apply noise operators to a person record, returning a noisy mention dict
    and a list of difficulty_tags.

    Returns (mention_fields, difficulty_tags).
    """
    probs = VERSION_NOISE.get(version, VERSION_NOISE["v1"])
    tags: list[str] = []

    # Start with canonical values
    first_rom = person.first_name["canonical_rom"]
    first_dev = person.first_name["canonical_dev"]
    father_rom = person.father_name["canonical_rom"]
    father_dev = person.father_name["canonical_dev"]
    surname_rom = person.surname["canonical_rom"]
    surname_dev = person.surname["canonical_dev"]
    age = person.age
    phones = list(person.phones)
    address = person.addresses[0] if person.addresses else ""
    use_devanagari = False

    # --- Transliteration variant ---
    if rng.random() < probs["translit"]:
        tags.append("translit")
        variants = person.surname.get("variants_rom", [])
        if variants:
            surname_rom = rng.choice(variants)
        f_variants = person.first_name.get("variants_rom", [])
        if f_variants:
            first_rom = rng.choice(f_variants)

    # --- Script mixing ---
    if rng.random() < probs["script_mix"]:
        tags.append("script_mix")
        use_devanagari = True
        # May also use Devanagari variants
        dev_variants = person.surname.get("variants_dev", [])
        if dev_variants and rng.random() < 0.5:
            surname_dev = rng.choice(dev_variants)

    # --- Initials ---
    if rng.random() < probs["initials"]:
        tags.append("initials")
        father_rom = father_rom[0] + "."
        father_dev = father_dev[0] + "."

    # --- Honorific ---
    honorific_rom = ""
    honorific_dev = ""
    if rng.random() < probs["honorific"]:
        tags.append("honorific")
        honorific_rom = rng.choice(HONORIFICS_ROM) + " "
        honorific_dev = rng.choice(HONORIFICS_DEV) + " "

    # --- Word order (surname first) ---
    reversed_order = False
    if rng.random() < probs["word_order"]:
        tags.append("word_order")
        reversed_order = True

    # --- Alias ---
    use_alias = False
    alias_value = ""
    if rng.random() < probs["alias"] and person.aliases:
        tags.append("alias")
        use_alias = True
        alias_value = rng.choice(person.aliases)

    # --- Missing father name ---
    father_missing = False
    if rng.random() < probs["missing_father"]:
        tags.append("missing_father")
        father_missing = True

    # --- Typo ---
    if rng.random() < probs["typo"]:
        tags.append("typo")
        first_rom = _swap_char(first_rom, rng)

    # --- Missing field ---
    missing_fields: list[str] = []
    if rng.random() < probs["missing_field"]:
        tags.append("missing_field")
        # Randomly drop a phone or address
        field_to_drop = rng.choice(["phone", "address"])
        missing_fields.append(field_to_drop)

    # --- Old phone ---
    old_phone_used = False
    if rng.random() < probs["old_phone"] and len(phones) > 0:
        tags.append("old_phone")
        old_phone_used = True
        # Replace one phone with a different number
        from .entities import _gen_phone

        old_idx = rng.randint(0, len(phones) - 1)
        phones[old_idx] = _gen_phone(rng)

    # --- Address change ---
    if rng.random() < probs["address_change"]:
        tags.append("address_change")
        from .lexicons import DISTRICTS as _D

        new_dist = rng.choice(_D)
        address = f"{rng.randint(1, 999)}, New Area, {new_dist}"

    # --- Age drift ---
    if rng.random() < probs["age_drift"]:
        tags.append("age_drift")
        age = age + rng.choice([-2, -1, 1, 2])

    # Build the name string
    if use_devanagari:
        if reversed_order:
            name = f"{honorific_dev}{surname_dev} {first_dev}"
            if not father_missing:
                name = f"{honorific_dev}{surname_dev} {first_dev} {father_dev}"
        else:
            if father_missing:
                name = f"{honorific_dev}{first_dev} {surname_dev}"
            else:
                name = f"{honorific_dev}{first_dev} {father_dev} {surname_dev}"
        script = "DEVANAGARI"
    else:
        if reversed_order:
            name = f"{honorific_rom}{surname_rom} {first_rom}"
            if not father_missing:
                name = f"{honorific_rom}{surname_rom} {first_rom} {father_rom}"
        else:
            if father_missing:
                name = f"{honorific_rom}{first_rom} {surname_rom}"
            else:
                name = f"{honorific_rom}{first_rom} {father_rom} {surname_rom}"
        script = "ROMAN"

    # Handle missing fields
    if "phone" in missing_fields:
        phones = []
    if "address" in missing_fields:
        address = ""

    father_name_raw = "" if father_missing else (father_dev if use_devanagari else father_rom)

    mention = {
        "name_raw": name.strip(),
        "name_script": script,
        "father_name_raw": father_name_raw,
        "age": age,
        "address_raw": address,
        "district": person.district,
        "phones": phones,
        "accounts": [a["account_key"] for a in person.accounts],
        "vehicles": person.vehicles,
        "aliases": [alias_value] if use_alias else [],
    }

    # If no tags, it's an easy mention
    if not tags:
        tags.append("clean")

    return mention, tags
