"""
services/data_gen/sutradhar_data/safety.py
Synthetic data safety utilities:
1. Verhoeff checksum validation and generation of pseudo-Aadhaar numbers that strictly fail validation.
2. Denylist of prominent real-world political and criminal figures to prevent coincidental collisions.
"""

from __future__ import annotations

import random
import re

# ─────────────────────────────────────────────────────────────
# Verhoeff Algorithm Tables
# ─────────────────────────────────────────────────────────────
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_checksum(number: str) -> int:
    """Compute the Verhoeff check digit for a string of digits."""
    c = 0
    digits = [int(d) for d in reversed(number)]
    for i, d in enumerate(digits):
        c = _VERHOEFF_D[c][_VERHOEFF_P[(i + 1) % 8][d]]
    return _VERHOEFF_INV[c]


def verhoeff_validate(number: str) -> bool:
    """Validate a number containing a Verhoeff check digit at the end."""
    digits = [int(d) for d in reversed(number)]
    c = 0
    for i, d in enumerate(digits):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][d]]
    return c == 0


def generate_invalid_pseudo_aadhaar(rng: random.Random) -> str:
    """
    Generate a 12-digit pseudo-Aadhaar number that is GUARANTEED to FAIL
    the Verhoeff checksum algorithm. Never starts with 0 or 1.
    """
    first_11 = str(rng.randint(2, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(10))
    valid_digit = verhoeff_checksum(first_11)
    
    # Pick a check digit that is explicitly NOT the valid Verhoeff digit
    invalid_digits = [d for d in range(10) if d != valid_digit]
    bad_digit = rng.choice(invalid_digits)
    candidate = first_11 + str(bad_digit)
    
    # Assert guarantee
    assert not verhoeff_validate(candidate), "Candidate must fail Verhoeff algorithm"
    return f"{candidate[:4]} {candidate[4:8]} {candidate[8:]}"


# ─────────────────────────────────────────────────────────────
# Real-World VIP / Political / Criminal Figure Denylist
# ─────────────────────────────────────────────────────────────
DENYLIST_NAMES = {
    # Prominent national and Maharashtra political figures
    ("narendra", "modi"),
    ("amit", "shah"),
    ("rahul", "gandhi"),
    ("sonia", "gandhi"),
    ("priyanka", "gandhi"),
    ("sharad", "pawar"),
    ("ajit", "pawar"),
    ("supriya", "sule"),
    ("devendra", "fadnavis"),
    ("eknath", "shinde"),
    ("uddhav", "thackeray"),
    ("aditya", "thackeray"),
    ("raj", "thackeray"),
    ("bal", "thackeray"),
    ("chhatrapati", "shivaji"),
    ("babasaheb", "ambedkar"),
    ("jyotirao", "phule"),
    ("ashok", "chavan"),
    ("prithviraj", "chavan"),
    ("vilasrao", "deshmukh"),
    ("narayan", "rane"),
    ("nitin", "gadkari"),
    ("sanjay", "raut"),
    ("nawab", "malik"),
    ("anil", "deshmukh"),
    ("chhagan", "bhujbal"),
    ("manoj", "jarange"),
    # Well-known real-world underworld / criminal figures
    ("dawood", "ibrahim"),
    ("chhota", "rajan"),
    ("chhota", "shakeel"),
    ("tiger", "memon"),
    ("yakub", "memon"),
    ("abu", "salem"),
    ("arun", "gawli"),
    ("amar", "naik"),
    ("ashwin", "naik"),
    ("varadarajan", "mudaliar"),
    ("karim", "lala"),
    ("haji", "mastan"),
    ("iqbal", "mirchi"),
    ("lawrence", "bishnoi"),
    ("goldy", "brar"),
    ("vikas", "dubey"),
    ("ateeq", "ahmad"),
    ("mukhtar", "ansari"),
    ("harshad", "mehta"),
    ("ketan", "parekh"),
    ("nirav", "modi"),
    ("mehul", "choksi"),
    ("vijay", "mallya"),
}


def is_denylisted(first_name: str, surname: str) -> bool:
    """Return True if the first name and surname match a denylisted real entity."""
    fn = re.sub(r"[^a-z]", "", first_name.lower())
    sn = re.sub(r"[^a-z]", "", surname.lower())
    return (fn, sn) in DENYLIST_NAMES


def validate_pseudo_aadhaar_fails_verhoeff(number: str) -> bool:
    """Return True if the pseudo-Aadhaar number strictly fails Verhoeff validation."""
    clean = re.sub(r"\D", "", number)
    if len(clean) != 12:
        return True
    return not verhoeff_validate(clean)


def check_name_denylist(full_name: str) -> bool:
    """Return True if the full name does NOT match any denylisted figure (safe)."""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        first, last = parts[0], parts[-1]
        if is_denylisted(first, last):
            return False
    return True

