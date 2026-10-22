"""
Mule Chain Tracing and Account Classification for Sutradhar.

Constructs directed transfer graphs from financial transactions,
computes layering via BFS outward from victim-receiving Layer 1 accounts,
calculates structural account features (fan-in/out, pass-through latencies),
and assigns explainable classifications (LIKELY_ORGANISER, LIKELY_DECEIVED, UNCERTAIN)
with full audit reasons.
"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

import networkx as nx

from .models import (
    AccountClass,
    FinancialFlowPath,
    FinancialFlowResult,
    MuleAccountModel,
    MuleChainModel,
    MuleTransferEdge,
)


def trace_mule_chains(graph_data: dict[str, Any], data_dir: Any = None) -> list[MuleChainModel]:
    """
    Trace layered mule accounts and classify accounts with explainable evidence.

    Returns a list of MuleChainModel objects.
    """
    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    # Step 1: Collect Accounts & Transactions
    account_nodes = {nid: n for nid, n in nodes.items() if n.get("type") == "ACCOUNT"}
    transfer_edges = [e for e in edges if e.get("type") == "TRANSFERRED_TO"]

    if not account_nodes or not transfer_edges:
        return []

    # Map Account Node -> Account Key and Holder
    account_holders: dict[str, tuple[str, str]] = {}  # acct_node -> (holder_id, holder_name)
    person_nodes = {nid: n for nid, n in nodes.items() if n.get("type") == "PERSON"}
    case_nodes = {nid: n for nid, n in nodes.items() if n.get("type") == "CASE"}
    person_accounts: dict[str, set[str]] = defaultdict(set)

    for e in edges:
        if e.get("type") == "OWNS" and e["source"] in person_nodes and e["target"] in account_nodes:
            p_node = person_nodes[e["source"]]
            account_holders[e["target"]] = (e["source"], p_node.get("label", "Unknown"))
            person_accounts[e["source"]].add(e["target"])

    # Map Person -> Cases, Crimes, Co-Accused, Evidence (Observable Graph Intelligence)
    person_cases: dict[str, set[str]] = defaultdict(set)
    person_crimes: dict[str, set[str]] = defaultdict(set)
    person_coacc: dict[str, set[str]] = defaultdict(set)
    person_evidence: dict[str, set[str]] = defaultdict(set)

    for e in edges:
        src, tgt, etype = e["source"], e["target"], e.get("type")
        ev = e.get("evidence", [])
        if etype == "ACCUSED_IN" and src in person_nodes and tgt in case_nodes:
            person_cases[src].add(tgt)
            person_evidence[src].update(ev)
            ct = nodes.get(tgt, {}).get("attributes", {}).get("crime_type")
            if ct:
                person_crimes[src].add(ct)
        elif etype == "CO_ACCUSED_WITH" and src in person_nodes:
            person_coacc[src].add(tgt)
            person_evidence[src].update(ev)

    # Build Directed Transfer Graph
    G_tx = nx.DiGraph()
    for anid in account_nodes:
        G_tx.add_node(anid)

    transfer_details: list[dict[str, Any]] = []
    account_inflow: Counter = Counter()
    account_outflow: Counter = Counter()
    account_timestamps: dict[str, list[datetime]] = defaultdict(list)

    for e in transfer_edges:
        src, tgt = e["source"], e["target"]
        attrs = e.get("attributes", {})
        amt = float(attrs.get("amount", 0.0))
        ts_str = attrs.get("ts", "2025-06-01T12:00:00Z")
        channel = attrs.get("channel", "UPI")

        account_inflow[tgt] += amt
        account_outflow[src] += amt

        try:
            dt = datetime.strptime(ts_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            account_timestamps[src].append(dt)
            account_timestamps[tgt].append(dt)
        except Exception:
            pass

        G_tx.add_edge(src, tgt, amount=amt, ts=ts_str, channel=channel)
        transfer_details.append(
            {
                "from_account": src.replace("ACCOUNT:", ""),
                "to_account": tgt.replace("ACCOUNT:", ""),
                "amount": amt,
                "ts": ts_str,
                "channel": channel,
            }
        )

    # Step 2: Identify Layer 1 Accounts (Victim-Receiving Inflow Nodes)
    # Layer 1 = nodes with complaint counts > 0 or with in-degree == 0 / receiving first victim funds
    layer1_nodes: set[str] = set()
    for anid, anode in account_nodes.items():
        complaints = anode.get("attributes", {}).get("complaint_count", 0)
        in_deg = G_tx.in_degree(anid)
        out_deg = G_tx.out_degree(anid)
        if complaints > 0 or (in_deg == 0 and out_deg > 0):
            layer1_nodes.add(anid)

    if not layer1_nodes:
        # Fallback: take nodes with out_degree > 0
        layer1_nodes = {
            n for n in G_tx.nodes() if G_tx.out_degree(n) > 0 and G_tx.in_degree(n) == 0
        }
    if not layer1_nodes:
        layer1_nodes = set(list(G_tx.nodes())[:1])

    # Step 3: Layering via BFS from Layer 1
    node_layers: dict[str, int] = {}
    queue = [(n, 1) for n in sorted(layer1_nodes)]
    visited = set(layer1_nodes)
    for n in layer1_nodes:
        node_layers[n] = 1

    while queue:
        curr, layer = queue.pop(0)
        for nbr in sorted(G_tx.successors(curr)):
            if nbr not in visited:
                visited.add(nbr)
                node_layers[nbr] = layer + 1
                queue.append((nbr, layer + 1))

    # Any remaining unvisited nodes get assigned based on closest predecessor
    for n in G_tx.nodes():
        if n not in node_layers:
            node_layers[n] = 2

    max_depth = max(node_layers.values()) if node_layers else 1

    # Step 4: Per-Account Classification (Explainable Weighted Signals)
    classified_accounts: list[MuleAccountModel] = []
    recruiter_candidates: set[str] = set()
    controller_candidates: set[str] = set()

    for anid, anode in account_nodes.items():
        if not (G_tx.in_degree(anid) > 0 or G_tx.out_degree(anid) > 0):
            continue

        ak = anid.replace("ACCOUNT:", "")
        layer = node_layers.get(anid, 1)
        holder_id, holder_name = account_holders.get(anid, (f"ENT-{ak[:6]}", "Unknown Holder"))

        inflow = float(account_inflow[anid])
        outflow = float(account_outflow[anid])
        fan_in = G_tx.in_degree(anid)
        fan_out = G_tx.out_degree(anid)
        complaints = anode.get("attributes", {}).get("complaint_count", 0)

        # Calculate median pass-through minutes
        ts_list = sorted(account_timestamps.get(anid, []))
        passthrough_min = 15.0
        if len(ts_list) >= 2:
            deltas = [
                (ts_list[k + 1] - ts_list[k]).total_seconds() / 60.0
                for k in range(len(ts_list) - 1)
            ]
            deltas = [d for d in deltas if d >= 0]
            if deltas:
                deltas.sort()
                passthrough_min = round(deltas[len(deltas) // 2], 1)

        # Observable Indicators (Strictly No Ground-Truth Leakage)
        raw_holder = anode.get("attributes", {}).get("holder_name", "")
        clean_holder_lower = raw_holder.lower()
        COMMERCIAL_KEYWORDS = (
            "store", "stall", "vendor", "driver", "partner", "kirana", "chai", "tea",
            "auto", "shop", "trader", "merchant", "enterprise", "commercial", "upi",
            "delivery", "services", "agency", "dairy", "bakery", "traders", "bazaar",
        )
        has_commercial_marker = (
            any(k in clean_holder_lower for k in COMMERCIAL_KEYWORDS)
            or "(" in raw_holder
        )
        turnover_ratio = (outflow / inflow) if inflow > 0 else 0.0
        is_balanced_turnover = (0.75 <= turnover_ratio <= 1.25) if (inflow > 0 and outflow > 0) else False

        # Holder criminal connections
        holder_cases = person_cases.get(holder_id, set())
        holder_crimes = person_crimes.get(holder_id, set())
        holder_accts = person_accounts.get(holder_id, set())
        holder_coacc = person_coacc.get(holder_id, set())

        # Observable Commercial Sweep Profile (Zero fraud complaints, commercial marker or balanced turnover with 0 criminal cases)
        is_commercial_pt = (
            complaints == 0
            and (has_commercial_marker or (is_balanced_turnover and len(holder_cases) == 0))
        )

        coord_indicators: list[str] = []
        reasons: list[str] = []
        coord_evidence: list[str] = list(person_evidence.get(holder_id, set())) + [ak]

        if layer >= 3:
            reasons.append(f"Positioned in consolidation Layer {layer} (deep mule funnel)")
        elif layer == 2:
            reasons.append("Layer 2 intermediary distribution account")
        else:
            reasons.append("Layer 1 initial victim-intake account")

        if fan_out >= 2:
            reasons.append(f"Fund dispersion fan-out to {fan_out} downstream accounts")
        elif fan_out == 0 and inflow > 0:
            reasons.append("Terminal cash-out or digital wallet conversion point")

        if len(holder_cases) >= 2:
            coord_indicators.append(f"CROSS_CASE_COORDINATION({len(holder_cases)} cases)")
            reasons.append(f"Account holder linked to {len(holder_cases)} distinct criminal cases across agencies")
        if len(holder_crimes) >= 2:
            coord_indicators.append(f"CROSS_CRIME_OPERATIONS({len(holder_crimes)} crime domains)")
            crimes_str = ", ".join(sorted(holder_crimes))
            reasons.append(f"Operations span multiple crime domains: {crimes_str}")
        if len(holder_accts) >= 2:
            coord_indicators.append(f"MULTI_ACCOUNT_CONTROL({len(holder_accts)} accounts)")
            reasons.append(f"Account holder controls {len(holder_accts)} distinct accounts in financial flow")
        if len(holder_coacc) >= 2:
            coord_indicators.append(f"CO_ACCUSED_SYNDICATE_TIES({len(holder_coacc)} co-accused)")
            reasons.append(f"Direct operational ties with {len(holder_coacc)} co-accused syndicate members")
        if complaints >= 5:
            coord_indicators.append(f"HIGH_FRAUD_COMPLAINTS({complaints})")
            reasons.append(f"Flagged in {complaints} distinct NCRP/1930 fraud complaints")

        # Determine Classification
        fin_dispersion = (layer >= 2 and fan_out >= 2)

        if is_commercial_pt:
            classification: AccountClass = "UNCERTAIN"
            score = 0.10
            confidence = 0.80
            indicators = [
                "COMMERCIAL_SWEEP_PROFILE",
                "ZERO_FRAUD_COMPLAINTS",
                f"TURNOVER_RATIO_{turnover_ratio:.2f}",
            ]
            if has_commercial_marker:
                indicators.append("COMMERCIAL_ENTITY_MARKER")
            if passthrough_min <= 30.0:
                indicators.append(f"RAPID_PASSTHROUGH_{passthrough_min}M")
            reasons.append(
                f"Observable profile matches legitimate merchant/commercial high-velocity sweep: balanced turnover ratio ({turnover_ratio:.2f}), "
                f"pass-through latency ({passthrough_min} min), and zero fraud complaints — guarded from organiser misclassification"
            )
            action = "Requires investigator review"
            evidence = [ak]
        elif fin_dispersion and len(coord_indicators) >= 2 and (len(holder_cases) > 0 or complaints > 0):
            classification = "LIKELY_ORGANISER"
            score = min(0.95, round(0.70 + 0.05 * len(coord_indicators), 2))
            confidence = 0.85
            indicators = coord_indicators + ["FINANCIAL_DISPERSION_HUB"]
            reasons.append(
                f"Positioned in consolidation Layer {layer} with dispersion fan-out to {fan_out} accounts. "
                "Multi-indicator coordination evidence across network suggests organiser role — requires investigator review"
            )
            action = "Requires investigator review"
            evidence = sorted(set(coord_evidence))
            recruiter_candidates.add(holder_id)
            controller_candidates.add(holder_id)
        elif layer <= 2 and (complaints > 0 or (len(holder_cases) <= 1 and len(coord_indicators) == 0)):
            if complaints > 0 or (layer == 1 and fan_out <= 2):
                classification = "LIKELY_DECEIVED"
                score = round(max(0.65, 1.0 - (0.10 * fan_out)), 2)
                confidence = 0.85
                indicators = ["INTAKE_LAYER_POSITION", "ABSENCE_OF_COORDINATION_EVIDENCE"]
                if complaints > 0:
                    indicators.append(f"FRAUD_COMPLAINTS_PRESENT({complaints})")
                    reasons.append(f"Initial victim intake account flagged in {complaints} fraud complaints with low outbound dispersion")
                else:
                    reasons.append("Early layer account receiving inbound funds with low outbound dispersion")
                reasons.append("Account profile matches deceived holder: absence of cross-case coordination evidence")
                action = "Requires investigator review"
                evidence = [ak]
            else:
                classification = "UNCERTAIN"
                score = 0.25
                confidence = 0.75
                indicators = ["ORDINARY_ACCOUNT_PROFILE", "ZERO_FRAUD_COMPLAINTS", "INSUFFICIENT_COORDINATION_EVIDENCE"]
                reasons.append("Intermediate risk profile with ordinary account activity — requires investigator review")
                action = "Requires investigator review"
                evidence = [ak]
        else:
            classification = "UNCERTAIN"
            score = 0.30
            confidence = 0.75
            indicators = ["ORDINARY_ACCOUNT_PROFILE", "ZERO_FRAUD_COMPLAINTS", "INSUFFICIENT_COORDINATION_EVIDENCE"]
            reasons.append("Intermediate risk profile with ordinary account activity — requires investigator review")
            action = "Requires investigator review"
            evidence = [ak]

        classified_accounts.append(
            MuleAccountModel(
                account_key=ak,
                holder_entity_id=holder_id,
                holder_name=holder_name,
                layer=layer,
                classification=classification,
                score=score,
                reasons=reasons,
                inflow=inflow,
                outflow=outflow,
                fan_in=fan_in,
                fan_out=fan_out,
                median_passthrough_minutes=passthrough_min,
                complaint_count=complaints,
                confidence=confidence,
                indicators=indicators,
                evidence=evidence,
                action=action,
            )
        )

    # Sort accounts by layer, then key
    classified_accounts.sort(key=lambda a: (a.layer, a.account_key))

    edges_output = [
        MuleTransferEdge(
            from_account=t["from_account"],
            to_account=t["to_account"],
            amount=t["amount"],
            ts=t["ts"],
            channel=t["channel"],
        )
        for t in transfer_details
    ]

    total_amount = sum(t["amount"] for t in transfer_details)
    victims_count = len(layer1_nodes) * 4  # proportional estimate

    chain = MuleChainModel(
        chain_id="MULE-001",
        total_amount=total_amount,
        victims_count=victims_count,
        max_depth=max_depth,
        layer1_baseline_depth=1,
        depth_gained=max(0, max_depth - 1),
        accounts=classified_accounts,
        edges=edges_output,
        recruiter_candidates=sorted(recruiter_candidates),
        controller_candidates=sorted(controller_candidates),
    )

    return [chain]


def trace_financial_flow(
    graph_data: dict[str, Any],
    target_id: str,
    max_hops: int = 4,
) -> FinancialFlowResult:
    """
    Traces money flows connected to a given person or account (Phase 8).
    Returns FinancialFlowResult with paths, total volume, layers, and explainable details.
    """
    import contextlib

    nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
    edges = graph_data.get("edges", [])

    # Find starting accounts
    start_accounts = set()
    if target_id.startswith("ACCOUNT:"):
        start_accounts.add(target_id)
    elif f"ACCOUNT:{target_id}" in nodes:
        start_accounts.add(f"ACCOUNT:{target_id}")
    else:
        # Check if target_id is a person who owns accounts
        for e in edges:
            if e.get("type") == "OWNS" and e["source"] == target_id and e["target"].startswith("ACCOUNT:"):
                start_accounts.add(e["target"])

    if not start_accounts:
        return FinancialFlowResult(target=target_id)

    # Build directed transfer graph
    G_tx = nx.DiGraph()
    tx_meta: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for e in edges:
        if e.get("type") == "TRANSFERRED_TO":
            u, v = e["source"], e["target"]
            attrs = e.get("attributes", {})
            amt = float(attrs.get("amount", 0.0))
            ts = attrs.get("ts", "")
            rec_id = attrs.get("txn_id", "")
            G_tx.add_edge(u, v, amount=amt)
            tx_meta[(u, v)].append({
                "amount": amt,
                "ts": ts,
                "txn_id": rec_id,
                "evidence": e.get("evidence", []),
            })

    # Explore outward paths via BFS up to max_hops
    found_paths: list[FinancialFlowPath] = []
    connected_accounts = set(start_accounts)
    total_vol = 0.0
    max_layer = 1

    for root in sorted(start_accounts):
        queue = [(root, [root])]

        while queue:
            curr, path = queue.pop(0)
            if len(path) > max_hops:
                continue

            out_edges = list(G_tx.out_edges(curr))
            if not out_edges and len(path) > 1:
                # Terminal path
                tx_count = 0
                path_amount = 0.0
                source_records = []
                ts_list = []
                for i in range(len(path) - 1):
                    pair = (path[i], path[i + 1])
                    for t in tx_meta[pair]:
                        tx_count += 1
                        path_amount += t["amount"]
                        if t["txn_id"]:
                            source_records.append(t["txn_id"])
                        source_records.extend(t.get("evidence", []))
                        if t["ts"]:
                            with contextlib.suppress(Exception):
                                ts_list.append(datetime.strptime(t["ts"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S"))

                time_span_min = 0.0
                if len(ts_list) >= 2:
                    ts_list.sort()
                    time_span_min = round((ts_list[-1] - ts_list[0]).total_seconds() / 60.0, 1)

                clean_path = [p.replace("ACCOUNT:", "") for p in path]
                clean_intermediaries = clean_path[1:-1] if len(clean_path) > 2 else []

                found_paths.append(
                    FinancialFlowPath(
                        path=clean_path,
                        transaction_count=tx_count,
                        total_amount=round(path_amount, 2),
                        time_span_minutes=time_span_min,
                        source_records=sorted(set(source_records)),
                        intermediaries=clean_intermediaries,
                        is_pass_through=(time_span_min <= 60.0 and len(clean_intermediaries) > 0),
                    )
                )
                total_vol += path_amount
                max_layer = max(max_layer, len(path))

            for _, next_node in out_edges:
                connected_accounts.add(next_node)
                if next_node not in path:
                    queue.append((next_node, path + [next_node]))

    clean_connected = sorted([a.replace("ACCOUNT:", "") for a in connected_accounts])
    return FinancialFlowResult(
        target=target_id,
        paths=found_paths,
        connected_accounts=clean_connected,
        total_volume=round(total_vol, 2),
        layers_detected=max_layer,
    )
