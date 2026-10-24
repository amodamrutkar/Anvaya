"""
services/data_gen/sutradhar_data/lexicons/multilingual.py
Multilingual demographic pools and weighted surname distributions:
- Marathi (~55%), Hindi (~20%), Gujarati (~10%), Marwari (~5%), Muslim (~5%), South Indian (~5%)
- Zipfian surname frequency for realistic collisions
- Devanagari canonical forms, Roman transliterations, and variants
"""

from __future__ import annotations

import random
import re
from typing import Any
from ..safety import is_denylisted

# ─────────────────────────────────────────────────────────────
# Surnames by Demographic Pool with Frequency Weights
# ─────────────────────────────────────────────────────────────
MULTILINGUAL_SURNAMES: dict[str, list[dict[str, Any]]] = {
    "marathi": [
        # Heavy frequency (Zipf head)
        {"canonical_rom": "Pawar", "canonical_dev": "पवार", "variants_rom": ["Powar", "Pavar", "Pawaar"], "variants_dev": ["पोवार", "पावार"], "weight": 28},
        {"canonical_rom": "Patil", "canonical_dev": "पाटील", "variants_rom": ["Pateel", "Paatil", "Patel"], "variants_dev": ["पाटिल", "पटील"], "weight": 26},
        {"canonical_rom": "Jadhav", "canonical_dev": "जाधव", "variants_rom": ["Jadhao", "Jadav", "Yadav"], "variants_dev": ["जाधो", "यादव"], "weight": 24},
        {"canonical_rom": "Shinde", "canonical_dev": "शिंदे", "variants_rom": ["Shindey", "Shindhe", "Sindhe"], "variants_dev": ["शिंधे", "सिंधे"], "weight": 22},
        {"canonical_rom": "Gaikwad", "canonical_dev": "गायकवाड", "variants_rom": ["Gaekwad", "Gaikwaad", "Gaykwad"], "variants_dev": ["गाएकवाड", "गायक्वाड"], "weight": 20},
        {"canonical_rom": "Kale", "canonical_dev": "काळे", "variants_rom": ["Kaale", "Kaley", "Kaaley"], "variants_dev": ["काले", "कळे"], "weight": 18},
        {"canonical_rom": "More", "canonical_dev": "मोरे", "variants_rom": ["Morey", "Morre", "Moray"], "variants_dev": ["मोरे", "मोऱे"], "weight": 16},
        {"canonical_rom": "Deshmukh", "canonical_dev": "देशमुख", "variants_rom": ["Deshmukhey", "Deshmuk", "Desmukh"], "variants_dev": ["देशमुक"], "weight": 14},
        {"canonical_rom": "Bhosale", "canonical_dev": "भोसले", "variants_rom": ["Bhosle", "Bhonsle", "Bhonsale"], "variants_dev": ["भोसले"], "weight": 12},
        {"canonical_rom": "Kulkarni", "canonical_dev": "कुलकर्णी", "variants_rom": ["Kulkarny", "Kulkarniee"], "variants_dev": ["कुलकर्णि"], "weight": 12},
        # Mid & long tail
        {"canonical_rom": "Chavan", "canonical_dev": "चव्हाण", "variants_rom": ["Chavhan", "Chouhan"], "variants_dev": ["चौहान"], "weight": 8},
        {"canonical_rom": "Kamble", "canonical_dev": "कांबळे", "variants_rom": ["Kambley", "Kamblee"], "variants_dev": ["कांबले"], "weight": 8},
        {"canonical_rom": "Sawant", "canonical_dev": "सावंत", "variants_rom": ["Sawanth", "Samant"], "variants_dev": ["सावन्त"], "weight": 6},
        {"canonical_rom": "Shedge", "canonical_dev": "शेडगे", "variants_rom": ["Shedage", "Sedage"], "variants_dev": ["शेडगे"], "weight": 4},
        {"canonical_rom": "Tambe", "canonical_dev": "तांबे", "variants_rom": ["Tambey"], "variants_dev": ["ताम्बे"], "weight": 4},
    ],
    "hindi": [
        {"canonical_rom": "Sharma", "canonical_dev": "शर्मा", "variants_rom": ["Sarma", "Sharmma"], "variants_dev": ["शर्मा"], "weight": 25},
        {"canonical_rom": "Verma", "canonical_dev": "वर्मा", "variants_rom": ["Varma", "Varmma"], "variants_dev": ["वरमा"], "weight": 20},
        {"canonical_rom": "Singh", "canonical_dev": "सिंह", "variants_rom": ["Singha", "Sing"], "variants_dev": ["सिंग"], "weight": 22},
        {"canonical_rom": "Yadav", "canonical_dev": "यादव", "variants_rom": ["Yadava", "Jadav"], "variants_dev": ["जादव"], "weight": 18},
        {"canonical_rom": "Mishra", "canonical_dev": "मिश्रा", "variants_rom": ["Misra", "Mishraa"], "variants_dev": ["मिश्र"], "weight": 15},
        {"canonical_rom": "Pandey", "canonical_dev": "पांडेय", "variants_rom": ["Pande", "Panday"], "variants_dev": ["पांडे"], "weight": 14},
        {"canonical_rom": "Gupta", "canonical_dev": "गुप्ता", "variants_rom": ["Goopta", "Guptha"], "variants_dev": ["गुपता"], "weight": 12},
        {"canonical_rom": "Tiwari", "canonical_dev": "तिवारी", "variants_rom": ["Tewari", "Tiwary"], "variants_dev": ["तिवारी"], "weight": 10},
    ],
    "gujarati": [
        {"canonical_rom": "Shah", "canonical_dev": "शाह", "variants_rom": ["Shaah", "Saah"], "variants_dev": ["साह"], "weight": 25},
        {"canonical_rom": "Patel", "canonical_dev": "पटेल", "variants_rom": ["Patell", "Pateyl"], "variants_dev": ["पटील"], "weight": 25},
        {"canonical_rom": "Mehta", "canonical_dev": "मेहता", "variants_rom": ["Maheta", "Meheta"], "variants_dev": ["महेता"], "weight": 18},
        {"canonical_rom": "Desai", "canonical_dev": "देसाई", "variants_rom": ["Desaye", "Dessai"], "variants_dev": ["देसाय"], "weight": 15},
        {"canonical_rom": "Parekh", "canonical_dev": "पारेख", "variants_rom": ["Parikh", "Parikh"], "variants_dev": ["पारिख"], "weight": 12},
        {"canonical_rom": "Zaveri", "canonical_dev": "झवेरी", "variants_rom": ["Jhaveri", "Zaveree"], "variants_dev": ["झावेरी"], "weight": 8},
    ],
    "marwari": [
        {"canonical_rom": "Agrawal", "canonical_dev": "अग्रवाल", "variants_rom": ["Agarwal", "Aggarwal"], "variants_dev": ["अगरवाल"], "weight": 22},
        {"canonical_rom": "Maheshwari", "canonical_dev": "माहेश्वरी", "variants_rom": ["Maheswari", "Maheshwary"], "variants_dev": ["माहेशवरी"], "weight": 18},
        {"canonical_rom": "Bhandari", "canonical_dev": "भंडारी", "variants_rom": ["Bhandary"], "variants_dev": ["भन्डारी"], "weight": 14},
        {"canonical_rom": "Oswal", "canonical_dev": "ओसवाल", "variants_rom": ["Osawal"], "variants_dev": ["ओसवाल"], "weight": 12},
        {"canonical_rom": "Kothari", "canonical_dev": "कोठारी", "variants_rom": ["Kothary"], "variants_dev": ["कोठारी"], "weight": 10},
        {"canonical_rom": "Joshi", "canonical_dev": "जोशी", "variants_rom": ["Joshy"], "variants_dev": ["जोसि"], "weight": 10},
    ],
    "muslim": [
        {"canonical_rom": "Shaikh", "canonical_dev": "शेख", "variants_rom": ["Sheikh", "Sheik", "Sayyad"], "variants_dev": ["शैक", "सैयद"], "weight": 25},
        {"canonical_rom": "Khan", "canonical_dev": "खान", "variants_rom": ["Khaan", "Kahn"], "variants_dev": ["ख़ान"], "weight": 25},
        {"canonical_rom": "Ansari", "canonical_dev": "अंसारी", "variants_rom": ["Ansary", "Ansaari"], "variants_dev": ["अन्सारी"], "weight": 18},
        {"canonical_rom": "Qureshi", "canonical_dev": "कुरेशी", "variants_rom": ["Quraishi", "Kureshi"], "variants_dev": ["कुरैशी"], "weight": 15},
        {"canonical_rom": "Siddiqui", "canonical_dev": "सिद्दीकी", "variants_rom": ["Siddiki", "Siddiqi"], "variants_dev": ["सिद्दिक़ी"], "weight": 12},
        {"canonical_rom": "Sayyed", "canonical_dev": "सय्यद", "variants_rom": ["Sayed", "Syed"], "variants_dev": ["सैयद"], "weight": 12},
    ],
    "south_indian": [
        {"canonical_rom": "Nair", "canonical_dev": "नायर", "variants_rom": ["Nayyar", "Nayer"], "variants_dev": ["नायर"], "weight": 22},
        {"canonical_rom": "Menon", "canonical_dev": "मेनन", "variants_rom": ["Mennon"], "variants_dev": ["मेनोन"], "weight": 18},
        {"canonical_rom": "Pillai", "canonical_dev": "पिल्लई", "variants_rom": ["Pillay", "Pillai"], "variants_dev": ["पिल्लै"], "weight": 15},
        {"canonical_rom": "Rao", "canonical_dev": "राव", "variants_rom": ["Raoo", "Row"], "variants_dev": ["राओ"], "weight": 20},
        {"canonical_rom": "Reddy", "canonical_dev": "रेड्डी", "variants_rom": ["Reddi", "Raddi"], "variants_dev": ["रेड्डि"], "weight": 18},
        {"canonical_rom": "Iyer", "canonical_dev": "अय्यर", "variants_rom": ["Aiyar", "Aiyer"], "variants_dev": ["अय्यर"], "weight": 12},
    ],
}

# ─────────────────────────────────────────────────────────────
# First Names by Demographic Pool
# ─────────────────────────────────────────────────────────────
MULTILINGUAL_FIRST_NAMES: dict[str, list[dict[str, Any]]] = {
    "marathi": [
        {"canonical_rom": "Sachin", "canonical_dev": "सचिन", "gender": "M"},
        {"canonical_rom": "Rakesh", "canonical_dev": "राकेश", "gender": "M"},
        {"canonical_rom": "Vijay", "canonical_dev": "विजय", "gender": "M"},
        {"canonical_rom": "Sandeep", "canonical_dev": "संदीप", "gender": "M"},
        {"canonical_rom": "Nitin", "canonical_dev": "नितिन", "gender": "M"},
        {"canonical_rom": "Ganesh", "canonical_dev": "गणेश", "gender": "M"},
        {"canonical_rom": "Manoj", "canonical_dev": "मनोज", "gender": "M"},
        {"canonical_rom": "Deepak", "canonical_dev": "दीपक", "gender": "M"},
        {"canonical_rom": "Prakash", "canonical_dev": "प्रकाश", "gender": "M"},
        {"canonical_rom": "Ramesh", "canonical_dev": "रमेश", "gender": "M"},
        {"canonical_rom": "Anil", "canonical_dev": "अनिल", "gender": "M"},
        {"canonical_rom": "Sunil", "canonical_dev": "सुनील", "gender": "M"},
        {"canonical_rom": "Pooja", "canonical_dev": "पूजा", "gender": "F"},
        {"canonical_rom": "Snehal", "canonical_dev": "स्नेहल", "gender": "F"},
        {"canonical_rom": "Priyanka", "canonical_dev": "प्रियंका", "gender": "F"},
        {"canonical_rom": "Kavita", "canonical_dev": "कविता", "gender": "F"},
    ],
    "hindi": [
        {"canonical_rom": "Amit", "canonical_dev": "अमित", "gender": "M"},
        {"canonical_rom": "Rajesh", "canonical_dev": "राजेश", "gender": "M"},
        {"canonical_rom": "Sanjay", "canonical_dev": "संजय", "gender": "M"},
        {"canonical_rom": "Ajay", "canonical_dev": "अजय", "gender": "M"},
        {"canonical_rom": "Vikram", "canonical_dev": "विक्रम", "gender": "M"},
        {"canonical_rom": "Alok", "canonical_dev": "आलोक", "gender": "M"},
        {"canonical_rom": "Pradeep", "canonical_dev": "प्रदीप", "gender": "M"},
        {"canonical_rom": "Neha", "canonical_dev": "नेहा", "gender": "F"},
        {"canonical_rom": "Sunita", "canonical_dev": "सुनीता", "gender": "F"},
        {"canonical_rom": "Anjali", "canonical_dev": "अंजलि", "gender": "F"},
    ],
    "gujarati": [
        {"canonical_rom": "Bhavin", "canonical_dev": "भाविन", "gender": "M"},
        {"canonical_rom": "Jignesh", "canonical_dev": "जिग्नेश", "gender": "M"},
        {"canonical_rom": "Chirag", "canonical_dev": "चिराग", "gender": "M"},
        {"canonical_rom": "Hiren", "canonical_dev": "हिरेन", "gender": "M"},
        {"canonical_rom": "Paresh", "canonical_dev": "परेश", "gender": "M"},
        {"canonical_rom": "Dhaval", "canonical_dev": "धवल", "gender": "M"},
        {"canonical_rom": "Komal", "canonical_dev": "कोमल", "gender": "F"},
        {"canonical_rom": "Daksha", "canonical_dev": "दक्षा", "gender": "F"},
    ],
    "marwari": [
        {"canonical_rom": "Manish", "canonical_dev": "मनीष", "gender": "M"},
        {"canonical_rom": "Naveen", "canonical_dev": "नवीन", "gender": "M"},
        {"canonical_rom": "Gaurav", "canonical_dev": "गौरव", "gender": "M"},
        {"canonical_rom": "Piyush", "canonical_dev": "पीयूष", "gender": "M"},
        {"canonical_rom": "Kamal", "canonical_dev": "कमल", "gender": "M"},
        {"canonical_rom": "Ritu", "canonical_dev": "रितु", "gender": "F"},
        {"canonical_rom": "Rekha", "canonical_dev": "रेखा", "gender": "F"},
    ],
    "muslim": [
        {"canonical_rom": "Imran", "canonical_dev": "इमरान", "gender": "M"},
        {"canonical_rom": "Wasim", "canonical_dev": "वसीम", "gender": "M"},
        {"canonical_rom": "Rizwan", "canonical_dev": "रिजवान", "gender": "M"},
        {"canonical_rom": "Farhan", "canonical_dev": "फरहान", "gender": "M"},
        {"canonical_rom": "Tariq", "canonical_dev": "तारिक", "gender": "M"},
        {"canonical_rom": "Asif", "canonical_dev": "आसिफ", "gender": "M"},
        {"canonical_rom": "Shabana", "canonical_dev": "शबाना", "gender": "F"},
        {"canonical_rom": "Nasreen", "canonical_dev": "नसरीन", "gender": "F"},
    ],
    "south_indian": [
        {"canonical_rom": "Karthik", "canonical_dev": "कार्तिक", "gender": "M"},
        {"canonical_rom": "Suresh", "canonical_dev": "सुरेश", "gender": "M"},
        {"canonical_rom": "Venkatesh", "canonical_dev": "वेंकटेश", "gender": "M"},
        {"canonical_rom": "Ramesh", "canonical_dev": "रमेश", "gender": "M"},
        {"canonical_rom": "Ashwin", "canonical_dev": "अश्विन", "gender": "M"},
        {"canonical_rom": "Lakshmi", "canonical_dev": "लक्ष्मी", "gender": "F"},
        {"canonical_rom": "Deepa", "canonical_dev": "दीपा", "gender": "F"},
    ],
}

# Regional / Demographic distribution weights for sampling
DEMOGRAPHIC_WEIGHTS = {
    "marathi": 55,
    "hindi": 20,
    "gujarati": 10,
    "marwari": 5,
    "muslim": 5,
    "south_indian": 5,
}


def sample_demographic_identity(
    rng: random.Random,
    forced_pool: str | None = None,
) -> dict[str, Any]:
    """
    Sample a demographic identity (first name, father name, surname)
    guaranteeing it does NOT collide with the real-world VIP/criminal denylist.
    """
    pools = list(DEMOGRAPHIC_WEIGHTS.keys())
    weights = [DEMOGRAPHIC_WEIGHTS[p] for p in pools]

    for _ in range(100):
        pool = forced_pool or rng.choices(pools, weights=weights, k=1)[0]
        
        # Select first name
        fn_entry = rng.choice(MULTILINGUAL_FIRST_NAMES[pool])
        # Select father name (typically another male first name from same pool)
        male_names = [n for n in MULTILINGUAL_FIRST_NAMES[pool] if n.get("gender") == "M"]
        fatn_entry = rng.choice(male_names)
        
        # Select surname according to Zipfian weights
        surnames = MULTILINGUAL_SURNAMES[pool]
        sn_weights = [s["weight"] for s in surnames]
        sn_entry = rng.choices(surnames, weights=sn_weights, k=1)[0]

        # Verify against denylist
        if not is_denylisted(fn_entry["canonical_rom"], sn_entry["canonical_rom"]):
            return {
                "pool": pool,
                "first_name": fn_entry,
                "father_name": fatn_entry,
                "surname": sn_entry,
                "gender": fn_entry.get("gender", "M"),
            }

    # Fallback to safe synthetic default
    return {
        "pool": "marathi",
        "first_name": {"canonical_rom": "Swapnil", "canonical_dev": "स्वप्निल", "gender": "M"},
        "father_name": {"canonical_rom": "Pandurang", "canonical_dev": "पांडुरंग", "gender": "M"},
        "surname": {"canonical_rom": "Kadam", "canonical_dev": "कदम", "variants_rom": ["Kadam"], "variants_dev": ["कदम"], "weight": 5},
        "gender": "M",
    }


# ─────────────────────────────────────────────────────────────
# Phonetic Confusion, OCR Noise & Marathi Numerals
# ─────────────────────────────────────────────────────────────

MARATHI_DIGITS = {
    "0": "०", "1": "१", "2": "२", "3": "३", "4": "४",
    "5": "५", "6": "६", "7": "७", "8": "८", "9": "९",
}


def render_marathi_numerals(phone_or_num: str) -> str:
    """Convert digits in a string to Marathi/Devanagari numerals."""
    return "".join(MARATHI_DIGITS.get(ch, ch) for ch in phone_or_num)


PHONETIC_CONFUSION_RULES = [
    # v/w
    (re.compile(r"\bV", re.IGNORECASE), "W", "phonetic_v_w"),
    (re.compile(r"\bW", re.IGNORECASE), "V", "phonetic_v_w"),
    (re.compile(r"(?<=[aeiou])v", re.IGNORECASE), "w", "phonetic_v_w"),
    (re.compile(r"(?<=[aeiou])w", re.IGNORECASE), "v", "phonetic_v_w"),
    # sh/s
    (re.compile(r"sh", re.IGNORECASE), "s", "phonetic_sh_s"),
    (re.compile(r"\bS(?=[aeiou])", re.IGNORECASE), "Sh", "phonetic_sh_s"),
    # d/dh
    (re.compile(r"dh", re.IGNORECASE), "d", "phonetic_d_dh"),
    (re.compile(r"d(?=[aeiou])", re.IGNORECASE), "dh", "phonetic_d_dh"),
    # ph/f
    (re.compile(r"ph", re.IGNORECASE), "f", "phonetic_ph_f"),
    (re.compile(r"f", re.IGNORECASE), "ph", "phonetic_ph_f"),
    # ee/i
    (re.compile(r"ee", re.IGNORECASE), "i", "phonetic_ee_i"),
    (re.compile(r"i\b", re.IGNORECASE), "ee", "phonetic_ee_i"),
    # oo/u
    (re.compile(r"oo", re.IGNORECASE), "u", "phonetic_oo_u"),
    (re.compile(r"u(?=[a-z])", re.IGNORECASE), "oo", "phonetic_oo_u"),
]


def apply_phonetic_confusion(name_rom: str, rng: random.Random) -> tuple[str, list[str]]:
    """Apply realistic phonetic spelling confusion to Romanized Indian names."""
    applicable = []
    for pattern, repl, tag in PHONETIC_CONFUSION_RULES:
        if pattern.search(name_rom):
            applicable.append((pattern, repl, tag))
    if not applicable:
        return name_rom, []
    pattern, repl, tag = rng.choice(applicable)
    modified = pattern.sub(repl, name_rom, count=1)
    return modified, [tag]


DEVANAGARI_OCR_CONFUSION = [
    ("श", "स", "ocr_sha_sa"),
    ("स", "श", "ocr_sa_sha"),
    ("ण", "न", "ocr_na_na"),
    ("ळ", "ल", "ocr_la_la"),
    ("व", "ब", "ocr_va_ba"),
    ("ध", "घ", "ocr_dha_gha"),
    ("भ", "म", "ocr_bha_ma"),
]


def apply_devanagari_ocr_noise(name_dev: str, rng: random.Random) -> tuple[str, list[str]]:
    """Apply realistic Devanagari OCR character confusion."""
    applicable = []
    for src, dst, tag in DEVANAGARI_OCR_CONFUSION:
        if src in name_dev:
            applicable.append((src, dst, tag))
    if not applicable:
        return name_dev, []
    src, dst, tag = rng.choice(applicable)
    modified = name_dev.replace(src, dst, 1)
    return modified, [tag]


def format_administrative_name_order(
    first_name: str,
    father_name: str,
    surname: str,
    order: str = "SURNAME_FIRST_FATHER",
) -> str:
    """Format name in administrative order, e.g. SURNAME FIRST FATHER."""
    if order == "SURNAME_FIRST_FATHER":
        if father_name:
            return f"{surname} {first_name} {father_name}"
        return f"{surname} {first_name}"
    elif order == "FIRST_FATHER_SURNAME":
        if father_name:
            return f"{first_name} {father_name} {surname}"
        return f"{first_name} {surname}"
    return f"{first_name} {surname}"
