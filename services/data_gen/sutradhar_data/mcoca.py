"""
services/data_gen/sutradhar_data/mcoca.py
MCOCA (Maharashtra Control of Organised Crime Act) evaluation rules & ground-truth builder.
DISCLAIMER: Legal parameters are configurable placeholders and must be verified against the statute.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class MCOCARuleConfig:
    min_chargesheets: int = 2
    window_years: int = 10
    cognizance_required: bool = True
    min_offence_severity_years: int = 3
    disclaimer: str = "Parameters configurable for benchmark; to be verified against the statute"


def is_mcoca_eligible(
    chargesheets: list[dict[str, Any]],
    as_of_date: datetime,
    config: MCOCARuleConfig | None = None,
) -> dict[str, Any]:
    """
    Evaluate MCOCA Section 2(1)(d) continuing unlawful activity prerequisite:
    - More than one chargesheet (min 2) filed within preceding 10 years
    - Competent court has taken cognizance
    - Offense punishable with imprisonment of 3 years or more
    """
    cfg = config or MCOCARuleConfig()
    cutoff_date = as_of_date - timedelta(days=cfg.window_years * 365)

    qualifying_chargesheets = []
    disqualified_reasons = []

    for cs in chargesheets:
        filing_dt = datetime.strptime(cs["filed_date"], "%Y-%m-%d")
        
        # Check window
        if filing_dt < cutoff_date:
            disqualified_reasons.append(f"{cs.get('chargesheet_id', 'CS')}: filed outside {cfg.window_years}-year window ({cs['filed_date']})")
            continue
            
        # Check cognizance
        if cfg.cognizance_required and not cs.get("cognizance_taken", True):
            disqualified_reasons.append(f"{cs.get('chargesheet_id', 'CS')}: court cognizance not taken")
            continue

        # Check severity (years of imprisonment prescribed)
        severity = cs.get("penalty_years", 3)
        if severity < cfg.min_offence_severity_years:
            disqualified_reasons.append(f"{cs.get('chargesheet_id', 'CS')}: penalty ({severity} yrs) below threshold ({cfg.min_offence_severity_years} yrs)")
            continue

        qualifying_chargesheets.append(cs)

    eligible = len(qualifying_chargesheets) >= cfg.min_chargesheets

    return {
        "eligible": eligible,
        "qualifying_count": len(qualifying_chargesheets),
        "required_count": cfg.min_chargesheets,
        "qualifying_chargesheets": [cs.get("chargesheet_id") for cs in qualifying_chargesheets],
        "disqualified_notes": disqualified_reasons,
        "config_applied": asdict(cfg),
    }


def generate_mcoca_test_cases(as_of_date: datetime) -> dict[str, Any]:
    """
    Generate ground truth MCOCA edge cases for evaluation scoring.
    """
    cfg = MCOCARuleConfig()
    cutoff = as_of_date - timedelta(days=cfg.window_years * 365)

    test_syndicates = {
        # 1. Clear Eligible Case (Network B Extortion Gang)
        "COM-002": {
            "name": "Urban Extortion Syndicate (Network B)",
            "chargesheets": [
                {
                    "chargesheet_id": "CS-SPO-2023-088",
                    "filed_date": (as_of_date - timedelta(days=365 * 3)).strftime("%Y-%m-%d"),
                    "court": "Sessions Court, Thane",
                    "cognizance_taken": True,
                    "sections": ["BNS-308", "BNS-351"],
                    "penalty_years": 7,
                },
                {
                    "chargesheet_id": "CS-SPO-2025-014",
                    "filed_date": (as_of_date - timedelta(days=365 * 1)).strftime("%Y-%m-%d"),
                    "court": "Chief Judicial Magistrate, Pune",
                    "cognizance_taken": True,
                    "sections": ["BNS-309"],
                    "penalty_years": 10,
                },
            ],
        },
        # 2. Boundary Case: Exactly 10 years (Day 3650 vs 3651)
        "SYND-MCOCA-EDGE-10YR": {
            "name": "Boundary Timing Gang",
            "chargesheets": [
                {
                    "chargesheet_id": "CS-SPO-2016-001",
                    "filed_date": cutoff.strftime("%Y-%m-%d"),  # exactly on the 10-year cutoff line
                    "court": "Sessions Court, Mumbai",
                    "cognizance_taken": True,
                    "sections": ["BNS-308"],
                    "penalty_years": 7,
                },
                {
                    "chargesheet_id": "CS-SPO-2024-099",
                    "filed_date": (as_of_date - timedelta(days=365)).strftime("%Y-%m-%d"),
                    "court": "Sessions Court, Mumbai",
                    "cognizance_taken": True,
                    "sections": ["BNS-308"],
                    "penalty_years": 7,
                },
            ],
        },
        # 3. Disqualified: No Cognizance Taken
        "SYND-MCOCA-NO-COGNIZANCE": {
            "name": "Pending Cognizance Syndicate",
            "chargesheets": [
                {
                    "chargesheet_id": "CS-SPO-2024-101",
                    "filed_date": (as_of_date - timedelta(days=200)).strftime("%Y-%m-%d"),
                    "court": "Sessions Court, Nashik",
                    "cognizance_taken": False,  # Court has NOT taken cognizance yet
                    "sections": ["BNS-308"],
                    "penalty_years": 7,
                },
                {
                    "chargesheet_id": "CS-SPO-2025-002",
                    "filed_date": (as_of_date - timedelta(days=50)).strftime("%Y-%m-%d"),
                    "court": "Sessions Court, Nashik",
                    "cognizance_taken": True,
                    "sections": ["BNS-308"],
                    "penalty_years": 7,
                },
            ],
        },
        # 4. Disqualified: Penalty below 3-year threshold
        "SYND-MCOCA-LOW-SEVERITY": {
            "name": "Minor Offense Ring",
            "chargesheets": [
                {
                    "chargesheet_id": "CS-SPO-2023-019",
                    "filed_date": (as_of_date - timedelta(days=400)).strftime("%Y-%m-%d"),
                    "court": "JMFC, Kolhapur",
                    "cognizance_taken": True,
                    "sections": ["BNS-285"],  # minor misdemeanor
                    "penalty_years": 1,        # below 3-year severity threshold
                },
                {
                    "chargesheet_id": "CS-SPO-2024-055",
                    "filed_date": (as_of_date - timedelta(days=150)).strftime("%Y-%m-%d"),
                    "court": "JMFC, Kolhapur",
                    "cognizance_taken": True,
                    "sections": ["BNS-285"],
                    "penalty_years": 1,
                },
            ],
        },
        # 5. Disqualified: Single Chargesheet Only
        "SYND-MCOCA-SINGLE-CS": {
            "name": "First-Time Extortion Gang",
            "chargesheets": [
                {
                    "chargesheet_id": "CS-SPO-2025-333",
                    "filed_date": (as_of_date - timedelta(days=90)).strftime("%Y-%m-%d"),
                    "court": "Sessions Court, Solapur",
                    "cognizance_taken": True,
                    "sections": ["BNS-308"],
                    "penalty_years": 7,
                }
            ],
        },
    }

    truth: dict[str, Any] = {
        "rule_config": asdict(cfg),
        "as_of_date": as_of_date.strftime("%Y-%m-%d"),
        "syndicates": {},
    }

    for syn_id, syn_data in test_syndicates.items():
        eval_res = is_mcoca_eligible(syn_data["chargesheets"], as_of_date, cfg)
        truth["syndicates"][syn_id] = {
            "name": syn_data["name"],
            "chargesheets": syn_data["chargesheets"],
            "ground_truth_eligible": eval_res["eligible"],
            "evaluation_detail": eval_res,
        }

    return truth
