"""Explanation — template-based explanation_text for links.

English by default, plus Marathi for hero links (PRD 4.6).
"""

from __future__ import annotations

from .models import Link, Mention

# ── English templates ────────────────────────────────────────────────────────

_CLUE_TEMPLATES_EN = {
    "SHARED_PHONE": "Same phone number ({detail})",
    "SHARED_ACCOUNT": "Same bank account ({detail})",
    "SHARED_VEHICLE": "Same vehicle ({detail})",
    "NAME_SIMILARITY": "Near-identical name ({detail})",
    "FATHER_NAME_MATCH": "Father's name matches ({detail})",
    "FATHER_NAME_CONFLICT": "Father's name conflicts ({detail})",
    "FATHER_NAME_MISMATCH": "Father's name absent in one record",
    "AGE_MATCH": "Age is close ({detail})",
    "AGE_CONFLICT": "Age differs significantly ({detail})",
    "SAME_DISTRICT": "Both in the same district ({detail})",
    "ALIAS_MATCH": "Alias overlap ({detail})",
    "NAME_ONLY_PENALTY": "Name match only; no strong identifier shared",
    "COMMON_NAME_GUARD": "Common name requires strong identifier",
    "SAME_RECORD_DIFFERENT_NAME": "Same record but different names — cannot merge",
    "STRONG_ID_CORROBORATION": "Identifier corroborated by matching name ({detail})",
    "DECISION_CANNOT_LINK": "Manually separated ({detail})",
    "DECISION_MUST_LINK": "Manually confirmed ({detail})",
}

# ── Marathi templates (for hero links) ───────────────────────────────────────

_CLUE_TEMPLATES_MR = {
    "SHARED_PHONE": "समान फोन नंबर ({detail})",
    "SHARED_ACCOUNT": "समान बँक खाते ({detail})",
    "SHARED_VEHICLE": "समान वाहन ({detail})",
    "NAME_SIMILARITY": "जवळजवळ सारखे नाव ({detail})",
    "FATHER_NAME_MATCH": "वडिलांचे नाव जुळते ({detail})",
    "FATHER_NAME_CONFLICT": "वडिलांचे नाव भिन्न ({detail})",
    "FATHER_NAME_MISMATCH": "एका नोंदीत वडिलांचे नाव नाही",
    "AGE_MATCH": "वय जवळपास ({detail})",
    "AGE_CONFLICT": "वय खूप वेगळे ({detail})",
    "SAME_DISTRICT": "एकाच जिल्ह्यातील ({detail})",
    "ALIAS_MATCH": "टोपणनाव जुळते ({detail})",
    "NAME_ONLY_PENALTY": "फक्त नाव जुळते; इतर ओळख नाही",
    "COMMON_NAME_GUARD": "सामान्य नाव — पुष्टी आवश्यक",
    "SAME_RECORD_DIFFERENT_NAME": "एकाच नोंदीत वेगळी नावे — विलीन करता येत नाही",
    "STRONG_ID_CORROBORATION": "ओळख पटवणारा पुरावा आणि नाव जुळते ({detail})",
    "DECISION_CANNOT_LINK": "व्यक्तिचलित विभक्त ({detail})",
    "DECISION_MUST_LINK": "व्यक्तिचलित पुष्टी ({detail})",
}


def _format_reason(clue: str, detail: str, templates: dict[str, str]) -> str:
    tmpl = templates.get(clue, clue)
    if "{detail}" in tmpl and detail:
        return tmpl.format(detail=detail)
    return tmpl.replace(" ({detail})", "").replace("({detail})", "")


def generate_explanation(
    link: Link,
    mention_map: dict[str, Mention] | None = None,
    language: str = "en",
) -> str:
    """Generate explanation_text from link reasons using templates.

    language: 'en' or 'mr' for Marathi.
    """
    templates = _CLUE_TEMPLATES_MR if language == "mr" else _CLUE_TEMPLATES_EN

    # Only include reasons that were actually computed (non-zero weight or informational)
    parts = []
    for_reasons = [r for r in link.reasons if r.direction == "FOR" and r.weight > 0]
    against_reasons = [r for r in link.reasons if r.direction == "AGAINST" and r.weight != 0]
    info_reasons = [
        r for r in link.reasons if r.weight == 0 and r.clue not in ("DECISION_MUST_LINK",)
    ]

    for r in for_reasons:
        parts.append(_format_reason(r.clue, r.detail, templates))

    if against_reasons:
        for r in against_reasons:
            parts.append(_format_reason(r.clue, r.detail, templates))

    if info_reasons:
        for r in info_reasons:
            text = _format_reason(r.clue, r.detail, templates)
            if text not in parts:
                parts.append(text)

    if not parts:
        return "No specific reasons computed."

    # Join with semicolons
    return "; ".join(parts) + "."


def generate_all_explanations(
    links: list[Link],
    mention_map: dict[str, Mention],
    hero_mention_ids: set[str] | None = None,
) -> list[Link]:
    """Generate explanation_text for all links.

    Hero links (involving hero_mention_ids) get both English and Marathi.
    """
    if hero_mention_ids is None:
        hero_mention_ids = set()

    for link in links:
        is_hero = link.a_mention_id in hero_mention_ids or link.b_mention_id in hero_mention_ids

        link.explanation_text = generate_explanation(link, mention_map, "en")
        link.explanation_source = "TEMPLATE"

        if is_hero:
            # Append Marathi translation
            mr_text = generate_explanation(link, mention_map, "mr")
            link.explanation_text = f"{link.explanation_text}\n[mr] {mr_text}"

    return links
