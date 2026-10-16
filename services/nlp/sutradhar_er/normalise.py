"""Name normalisation — Devanagari transliteration, lexicon mapping, honorific stripping.

Core approach:
  1. Detect script (Devanagari vs Latin)
  2. Transliterate Devanagari → Latin
  3. Apply custom Marathi/Hindi name lexicon mapping variants → canonical
  4. Strip honorifics
  5. Collapse vowels/consonant equivalences
  6. Handle initials
"""

from __future__ import annotations

import re
import unicodedata

# ── Devanagari detection ─────────────────────────────────────────────────────

_DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")


def detect_script(text: str) -> str:
    """Return 'DEVANAGARI', 'LATIN', or 'MIXED'."""
    if not text.strip():
        return "LATIN"
    dev_count = len(_DEVANAGARI_RANGE.findall(text))
    alpha_count = sum(1 for c in text if c.isalpha())
    if alpha_count == 0:
        return "LATIN"
    ratio = dev_count / alpha_count
    if ratio > 0.8:
        return "DEVANAGARI"
    elif ratio < 0.2:
        return "LATIN"
    return "MIXED"


def detect_language(text: str) -> str:
    """Simple language tag: 'mr', 'hi', or 'en' based on script and common markers."""
    script = detect_script(text)
    if script in ("DEVANAGARI", "MIXED"):
        # rough heuristic — Marathi markers
        marathi_markers = ["आरोपी", "फिर्यादी", "तक्रारदार", "पोलीस", "ठाणे", "जिल्हा"]
        for m in marathi_markers:
            if m in text:
                return "mr"
        return "hi"
    return "en"


# ── Transliteration (Devanagari → Latin) ─────────────────────────────────────

# Basic Devanagari to Latin mapping covering common characters
_DEVANAGARI_TO_LATIN: dict[str, str] = {
    # Vowels
    "अ": "a",
    "आ": "aa",
    "इ": "i",
    "ई": "ii",
    "उ": "u",
    "ऊ": "uu",
    "ऋ": "ri",
    "ए": "e",
    "ऐ": "ai",
    "ओ": "o",
    "औ": "au",
    # Vowel marks (matras)
    "ा": "a",
    "ि": "i",
    "ी": "i",
    "ु": "u",
    "ू": "u",
    "ृ": "ri",
    "े": "e",
    "ै": "ai",
    "ो": "o",
    "ौ": "au",
    # Consonants
    "क": "k",
    "ख": "kh",
    "ग": "g",
    "घ": "gh",
    "ङ": "ng",
    "च": "ch",
    "छ": "chh",
    "ज": "j",
    "झ": "jh",
    "ञ": "ny",
    "ट": "t",
    "ठ": "th",
    "ड": "d",
    "ढ": "dh",
    "ण": "n",
    "त": "t",
    "थ": "th",
    "द": "d",
    "ध": "dh",
    "न": "n",
    "प": "p",
    "फ": "ph",
    "ब": "b",
    "भ": "bh",
    "म": "m",
    "य": "y",
    "र": "r",
    "ल": "l",
    "व": "v",
    "श": "sh",
    "ष": "sh",
    "स": "s",
    "ह": "h",
    "ळ": "l",  # Marathi-specific
    "क्ष": "ksh",
    "त्र": "tr",
    "ज्ञ": "dny",  # conjuncts
    # Misc
    "ं": "n",
    "ँ": "n",
    "ः": "h",
    "्": "",  # halant — removes inherent 'a'
    "़": "",  # nukta
    "ॅ": "e",  # candra e
    "ॉ": "o",  # candra o
}


def transliterate_devanagari(text: str) -> str:
    """Convert Devanagari text to a rough Latin transliteration.

    Uses `indic-transliteration` (ITRANS) with schwa handling,
    falling back to a character table.
    """
    try:
        from indic_transliteration import sanscript

        trans = sanscript.transliterate(
            text, sanscript.DEVANAGARI, sanscript.ITRANS
        ).lower()
        trans = trans.replace("~n", "n").replace(".n", "n").replace(".m", "m")
        parts = []
        for word in trans.split():
            if word.endswith("a") and not word.endswith("aa") and len(word) > 3:
                word = word[:-1]
            parts.append(word)
        return " ".join(parts)
    except (ImportError, ValueError, TypeError, AttributeError):
        pass

    result: list[str] = []
    i = 0
    chars = list(text)
    n = len(chars)

    while i < n:
        ch = chars[i]

        # try two-char conjuncts first
        if i + 1 < n:
            pair = ch + chars[i + 1]
            if pair in _DEVANAGARI_TO_LATIN:
                result.append(_DEVANAGARI_TO_LATIN[pair])
                i += 2
                continue

        if ch in _DEVANAGARI_TO_LATIN:
            mapped = _DEVANAGARI_TO_LATIN[ch]
            # halant: remove previous inherent 'a' if any
            if ch == "्" and result and result[-1] == "a":
                result.pop()
            else:
                result.append(mapped)
            i += 1
            continue

        # Check for Devanagari consonant with inherent 'a'
        cat = unicodedata.category(ch)
        if _DEVANAGARI_RANGE.match(ch) and cat.startswith("L"):
            result.append(ch)
            i += 1
            continue

        result.append(ch)
        i += 1

    return "".join(result)


# ── Custom Marathi/Hindi name lexicon ────────────────────────────────────────
# Maps known spelling variants (Devanagari and Latin) to canonical Latin forms.
# At least 40 surnames + 40 first names as required by PRD.

SURNAME_LEXICON: dict[str, str] = {
    # Canonical: "pavar" — the Pawar/Powar family
    "pawar": "pavar",
    "powar": "pavar",
    "pavar": "pavar",
    "pawaar": "pavar",
    "पवार": "pavar",
    "पोवार": "pavar",
    "पवर": "pavar",
    # Canonical: "jadhav"
    "jadhav": "jadhav",
    "jadav": "jadhav",
    "yadav": "jadhav",
    "जाधव": "jadhav",
    "यादव": "jadhav",
    # Canonical: "shinde"
    "shinde": "shinde",
    "shindey": "shinde",
    "sinde": "shinde",
    "शिंदे": "shinde",
    "शिन्दे": "shinde",
    # Canonical: "gaikwad"
    "gaikwad": "gaikwad",
    "gaikawad": "gaikwad",
    "gaekwad": "gaikwad",
    "गायकवाड": "gaikwad",
    "गाइकवाड": "gaikwad",
    # Canonical: "kale"
    "kale": "kale",
    "kaale": "kale",
    "काळे": "kale",
    "काले": "kale",
    # Canonical: "patil"
    "patil": "patil",
    "patel": "patil",
    "paatil": "patil",
    "पाटील": "patil",
    "पटेल": "patil",
    # Canonical: "deshmukh"
    "deshmukh": "deshmukh",
    "deshmukhh": "deshmukh",
    "देशमुख": "deshmukh",
    # Canonical: "kulkarni"
    "kulkarni": "kulkarni",
    "kulkarnee": "kulkarni",
    "कुलकर्णी": "kulkarni",
    # Canonical: "more"
    "more": "more",
    "morey": "more",
    "मोरे": "more",
    # Canonical: "bhosale"
    "bhosale": "bhosale",
    "bhosle": "bhosale",
    "भोसले": "bhosale",
    "भोसळे": "bhosale",
    # Canonical: "rathore"
    "rathore": "rathore",
    "rathor": "rathore",
    "rathod": "rathore",
    "राठोर": "rathore",
    "राठोड": "rathore",
    # Canonical: "chavan"
    "chavan": "chavan",
    "chauhan": "chavan",
    "चव्हाण": "chavan",
    "चौहान": "chavan",
    # Canonical: "kamble"
    "kamble": "kamble",
    "kambale": "kamble",
    "कांबळे": "kamble",
    "कांबले": "kamble",
    # Canonical: "solanke"
    "solanke": "solanke",
    "solanki": "solanke",
    "सोळंके": "solanke",
    "सोलंकी": "solanke",
    # Canonical: "nikam"
    "nikam": "nikam",
    "nikkam": "nikam",
    "निकम": "nikam",
    # Canonical: "thorat"
    "thorat": "thorat",
    "thoraat": "thorat",
    "थोरात": "thorat",
    # Canonical: "ghodke"
    "ghodke": "ghodke",
    "ghodkey": "ghodke",
    "घोडके": "ghodke",
    # Canonical: "waghmare"
    "waghmare": "vaghmare",
    "vaghmare": "vaghmare",
    "waghamare": "vaghmare",
    "वाघमारे": "vaghmare",
    # Canonical: "mane"
    "mane": "mane",
    "maane": "mane",
    "माने": "mane",
    # Canonical: "joshi"
    "joshi": "joshi",
    "joshee": "joshi",
    "जोशी": "joshi",
    # Canonical: "deshpande"
    "deshpande": "deshpande",
    "deshpandey": "deshpande",
    "देशपांडे": "deshpande",
    # Canonical: "sawant"
    "sawant": "savant",
    "savant": "savant",
    "सावंत": "savant",
    # Canonical: "salunke"
    "salunke": "salunke",
    "salunkhe": "salunke",
    "साळुंके": "salunke",
    # Canonical: "londhe"
    "londhe": "londhe",
    "londhey": "londhe",
    "लोंढे": "londhe",
    # Canonical: "wagh"
    "wagh": "vagh",
    "vagh": "vagh",
    "वाघ": "vagh",
    # Canonical: "shirke"
    "shirke": "shirke",
    "shirkey": "shirke",
    "शिर्के": "shirke",
    # Canonical: "thakur"
    "thakur": "thakur",
    "thakkar": "thakur",
    "ठाकूर": "thakur",
    # Canonical: "ingale"
    "ingale": "ingale",
    "ingaley": "ingale",
    "इंगळे": "ingale",
    # Canonical: "mhatre"
    "mhatre": "mhatre",
    "mhatrey": "mhatre",
    "म्हात्रे": "mhatre",
    # Canonical: "naik"
    "naik": "naik",
    "nayak": "naik",
    "नाईक": "naik",
    "नायक": "naik",
    # Canonical: "gavhane"
    "gavhane": "gavhane",
    "gawane": "gavhane",
    "गव्हाणे": "gavhane",
    # Canonical: "lokhande"
    "lokhande": "lokhande",
    "lokhandey": "lokhande",
    "लोखंडे": "lokhande",
    # Canonical: "parab"
    "parab": "parab",
    "paraab": "parab",
    "पारब": "parab",
    # Canonical: "suryavanshi"
    "suryavanshi": "suryavanshi",
    "suryawanshi": "suryavanshi",
    "सूर्यवंशी": "suryavanshi",
    # Canonical: "kadam"
    "kadam": "kadam",
    "kadaam": "kadam",
    "कदम": "kadam",
    # Canonical: "ghule"
    "ghule": "ghule",
    "ghuley": "ghule",
    "घुले": "ghule",
    # Canonical: "bhor"
    "bhor": "bhor",
    "bhoar": "bhor",
    "भोर": "bhor",
    # Canonical: "rane"
    "rane": "rane",
    "raney": "rane",
    "राणे": "rane",
    # Canonical: "shelke"
    "shelke": "shelke",
    "shelkey": "shelke",
    "शेळके": "shelke",
    # Canonical: "dhage"
    "dhage": "dhage",
    "dhagey": "dhage",
    "ढगे": "dhage",
    # Canonical: "garje"
    "garje": "garje",
    "garjey": "garje",
    "गर्जे": "garje",
    # Canonical: "potdar"
    "potdar": "potdar",
    "potdaar": "potdar",
    "पोतदार": "potdar",
    # Canonical: "khan"
    "khan": "khan",
    "khaan": "khan",
    "खान": "khan",
    # Canonical: "shaikh"
    "shaikh": "shaikh",
    "sheikh": "shaikh",
    "shaik": "shaikh",
    "शेख": "shaikh",
    "शैख": "shaikh",
    # Canonical: "syed"
    "syed": "syed",
    "sayyed": "syed",
    "sayyad": "syed",
    "सय्यद": "syed",
}

FIRST_NAME_LEXICON: dict[str, str] = {
    # Canonical: "rakesh"
    "rakesh": "rakesh",
    "raakesh": "rakesh",
    "raksh": "rakesh",
    "राकेश": "rakesh",
    "राकेष": "rakesh",
    # Canonical: "sachin"
    "sachin": "sachin",
    "sacheen": "sachin",
    "सचिन": "sachin",
    # Canonical: "nitin"
    "nitin": "nitin",
    "nittin": "nitin",
    "नितिन": "nitin",
    "नितीन": "nitin",
    # Canonical: "anil"
    "anil": "anil",
    "aneel": "anil",
    "अनिल": "anil",
    # Canonical: "prakash"
    "prakash": "prakash",
    "prakaash": "prakash",
    "प्रकाश": "prakash",
    # Canonical: "mahendra"
    "mahendra": "mahendra",
    "mahendara": "mahendra",
    "महेंद्र": "mahendra",
    "महेन्द्र": "mahendra",
    # Canonical: "sunil"
    "sunil": "sunil",
    "suneel": "sunil",
    "सुनील": "sunil",
    "सुनिल": "sunil",
    # Canonical: "ramesh"
    "ramesh": "ramesh",
    "ramsh": "ramesh",
    "रमेश": "ramesh",
    # Canonical: "rajesh"
    "rajesh": "rajesh",
    "raajesh": "rajesh",
    "राजेश": "rajesh",
    # Canonical: "vijay"
    "vijay": "vijay",
    "vijaay": "vijay",
    "विजय": "vijay",
    # Canonical: "sanjay"
    "sanjay": "sanjay",
    "sanjaay": "sanjay",
    "संजय": "sanjay",
    # Canonical: "ganesh"
    "ganesh": "ganesh",
    "ganeesh": "ganesh",
    "गणेश": "ganesh",
    # Canonical: "dagdu"
    "dagdu": "dagdu",
    "dagadu": "dagdu",
    "दगडू": "dagdu",
    "दगडु": "dagdu",
    # Canonical: "bharat"
    "bharat": "bharat",
    "bharaat": "bharat",
    "भारत": "bharat",
    # Canonical: "suresh"
    "suresh": "suresh",
    "sureesh": "suresh",
    "सुरेश": "suresh",
    # Canonical: "manoj"
    "manoj": "manoj",
    "maanuj": "manoj",
    "मनोज": "manoj",
    # Canonical: "ashok"
    "ashok": "ashok",
    "aashok": "ashok",
    "अशोक": "ashok",
    # Canonical: "dinesh"
    "dinesh": "dinesh",
    "dineesh": "dinesh",
    "दिनेश": "dinesh",
    # Canonical: "pradeep"
    "pradeep": "pradip",
    "pradip": "pradip",
    "प्रदीप": "pradip",
    # Canonical: "deepak"
    "deepak": "dipak",
    "dipak": "dipak",
    "दीपक": "dipak",
    # Canonical: "yogesh"
    "yogesh": "yogesh",
    "yogeesh": "yogesh",
    "योगेश": "yogesh",
    # Canonical: "rahul"
    "rahul": "rahul",
    "raahul": "rahul",
    "राहुल": "rahul",
    # Canonical: "amol"
    "amol": "amol",
    "amool": "amol",
    "अमोल": "amol",
    # Canonical: "tushar"
    "tushar": "tushar",
    "tushaar": "tushar",
    "तुषार": "tushar",
    # Canonical: "vishal"
    "vishal": "vishal",
    "vishaal": "vishal",
    "विशाल": "vishal",
    # Canonical: "sandip"
    "sandip": "sandip",
    "sandeep": "sandip",
    "संदीप": "sandip",
    # Canonical: "kiran"
    "kiran": "kiran",
    "keeran": "kiran",
    "किरण": "kiran",
    # Canonical: "ajay"
    "ajay": "ajay",
    "ajaay": "ajay",
    "अजय": "ajay",
    # Canonical: "hemant"
    "hemant": "hemant",
    "hemanta": "hemant",
    "हेमंत": "hemant",
    # Canonical: "milind"
    "milind": "milind",
    "millind": "milind",
    "मिलिंद": "milind",
    # Canonical: "balaji"
    "balaji": "balaji",
    "baalaji": "balaji",
    "बालाजी": "balaji",
    # Canonical: "santosh"
    "santosh": "santosh",
    "santoosh": "santosh",
    "संतोष": "santosh",
    # Canonical: "pravin"
    "pravin": "pravin",
    "praveen": "pravin",
    "प्रवीण": "pravin",
    # Canonical: "ravi"
    "ravi": "ravi",
    "ravee": "ravi",
    "रवी": "ravi",
    "रवि": "ravi",
    # Canonical: "tanaji"
    "tanaji": "tanaji",
    "taanaji": "tanaji",
    "तानाजी": "tanaji",
    # Canonical: "popat"
    "popat": "popat",
    "poapat": "popat",
    "पोपट": "popat",
    # Canonical: "ankush"
    "ankush": "ankush",
    "ankuush": "ankush",
    "अंकुश": "ankush",
    # Canonical: "arvind"
    "arvind": "arvind",
    "aravind": "arvind",
    "अरविंद": "arvind",
    # Canonical: "dattatray"
    "dattatray": "dattatray",
    "dattatrey": "dattatray",
    "दत्तात्रय": "dattatray",
    # Canonical: "mohan"
    "mohan": "mohan",
    "mohaan": "mohan",
    "मोहन": "mohan",
    # Canonical: "narayan"
    "narayan": "narayan",
    "naraayan": "narayan",
    "नारायण": "narayan",
}

# Combined name lexicon (first + surname)
_NAME_LEXICON = {**SURNAME_LEXICON, **FIRST_NAME_LEXICON}


# ── Honorifics ───────────────────────────────────────────────────────────────

_HONORIFICS_SET = {
    "shri",
    "shree",
    "smt",
    "mr",
    "mrs",
    "ms",
    "dr",
    "prof",
    "श्री",
    "श्रीमती",
    "श्रीम",
    "सौ",
    "कु",
    "मा",
}

_INITIAL_PATTERN = re.compile(r"\b([A-Za-z])\.\s*")  # "R. " or "D. "


# ── Vowel / consonant equivalences ───────────────────────────────────────────

_EQUIVALENCES: list[tuple[str, str]] = [
    ("aa", "a"),
    ("ee", "i"),
    ("ii", "i"),
    ("oo", "u"),
    ("uu", "u"),
    ("ph", "f"),
    ("w", "v"),
    ("sh", "sh"),  # keep 'sh' as-is
    ("chh", "ch"),
    ("th", "th"),  # keep 'th' — common in Indian names
    ("dh", "dh"),
    ("bh", "bh"),
    ("gh", "gh"),
    ("kh", "kh"),
    ("jh", "jh"),
]


def _apply_equivalences(text: str) -> str:
    """Apply vowel/consonant equivalences for fuzzy matching."""
    for src, dst in _EQUIVALENCES:
        text = text.replace(src, dst)
    # collapse any remaining doubled consonants
    result = []
    for i, ch in enumerate(text):
        if i > 0 and ch == text[i - 1] and ch.isalpha():
            continue
        result.append(ch)
    return "".join(result)


# ── Public API ───────────────────────────────────────────────────────────────


def normalise_name(raw: str) -> str:
    """Normalise a person name to a canonical Latin form.

    Steps:
      1. Strip honorifics (Devanagari and Latin)
      2. Handle initials ("R." → kept as single letter "r")
      3. Lexicon lookup per token (Devanagari and Latin variants)
      4. Transliterate Devanagari if not in lexicon
      5. Apply vowel/consonant equivalences
      6. Strip excess whitespace and dots
    """
    if not raw or not raw.strip():
        return ""

    text = raw.strip()

    # Step 1: handle initials — "R." → "r "
    text = _INITIAL_PATTERN.sub(r"\1 ", text)

    # Step 2: strip dots and split
    text = text.replace(".", " ")
    tokens = text.split()

    normalised_tokens = []
    for token in tokens:
        clean = token.strip()
        if not clean:
            continue

        # Strip honorifics
        if (
            clean.lower().rstrip(".") in _HONORIFICS_SET
            or clean.rstrip(".") in _HONORIFICS_SET
        ):
            continue

        # Check lexicon directly (handles Devanagari e.g. "पवार", "राकेश", "दगडू")
        if clean in _NAME_LEXICON:
            normalised_tokens.append(_NAME_LEXICON[clean])
            continue
        if clean.lower() in _NAME_LEXICON:
            normalised_tokens.append(_NAME_LEXICON[clean.lower()])
            continue

        # If Devanagari, transliterate and re-check lexicon
        if detect_script(clean) in ("DEVANAGARI", "MIXED"):
            clean = transliterate_devanagari(clean).lower()
            if clean in _NAME_LEXICON:
                normalised_tokens.append(_NAME_LEXICON[clean])
                continue

        # Lowercase Latin and check equivalences
        clean = clean.lower()
        clean = _apply_equivalences(clean)
        if clean in _NAME_LEXICON:
            normalised_tokens.append(_NAME_LEXICON[clean])
        else:
            normalised_tokens.append(clean)

    return " ".join(normalised_tokens)


def normalise_father_name(raw: str) -> str:
    """Normalise a father's name — same process, but typically a single name."""
    return normalise_name(raw)


def expand_aliases(raw_alias: str) -> list[str]:
    """Normalise an alias string. Returns list of normalised alias forms."""
    if not raw_alias or not raw_alias.strip():
        return []
    # aliases can be comma or slash separated
    parts = re.split(r"[,/]", raw_alias)
    return [normalise_name(p) for p in parts if p.strip()]
