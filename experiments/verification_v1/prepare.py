"""Pin a public source and prepare metadata-only grouped partitions.

Gold is stored in a separate local packet, never the inference packet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/verification_v1"
COMMIT = "dc65e18a0a3e40e13c461c05b55103379db1fd8e"
REPO = "https://github.com/dweebee/dg-evidence-750"
SALT = "repguard-verification-v1-20261109"
PUBLIC_FIELDS = ("claim", "claim_date", "source_title", "domain", "source_date", "passage")


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def normalize(text):
    return re.sub(r"\s+", " ", text.strip().casefold())


def fetch():
    source = OUT / "source"
    source.mkdir(parents=True, exist_ok=True)
    for name in ("README.md", "dg-evidence-750.jsonl"):
        path = source / name
        if path.exists():
            continue
        url = f"https://raw.githubusercontent.com/dweebee/dg-evidence-750/{COMMIT}/{name}"
        request = urllib.request.Request(url, headers={"User-Agent": "RepGuard-research"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
        path.write_bytes(data)
    data_path = source / "dg-evidence-750.jsonl"
    rows = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]
    print(json.dumps({"rows": len(rows), "fields": sorted(rows[0]),
                      "claim_ids": len({str(r['claim_id']) for r in rows}),
                      "bytes": data_path.stat().st_size, "sha256": digest(data_path.read_bytes())}))
    return rows


def prepare():
    rows = fetch()
    ids = [str(r["item_id"]) for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate item IDs")
    by_claim = defaultdict(list)
    for row in rows:
        if set(PUBLIC_FIELDS) - row.keys():
            raise ValueError("Missing public fields")
        if int(row["final_label"]) not in range(4):
            raise ValueError("Invalid gold label")
        by_claim[str(row["claim_id"])].append(row)
    parent = {c: c for c in by_claim}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    def union(a, b):
        aa, bb = find(a), find(b)
        parent[max(aa, bb)] = min(aa, bb)

    seen_claim, seen_passage = {}, {}
    duplicate_links = []
    for row in rows:
        c = str(row["claim_id"])
        for kind, text, seen in (("claim", row["claim"], seen_claim),
                                 ("passage", row["passage"], seen_passage)):
            h = digest(normalize(text))
            if h in seen and seen[h] != c:
                union(c, seen[h])
                duplicate_links.append({"kind": kind, "claim_a": c, "claim_b": seen[h]})
            seen[h] = c
    groups = defaultdict(list)
    for c in by_claim:
        groups[find(c)].append(c)
    order = sorted(groups, key=lambda g: digest({"salt": SALT, "group": sorted(groups[g])}))
    if len(order) < 80:
        raise ValueError("Too few independent metadata groups; amend protocol before generation")
    partition_groups = {"pilot": order[:24], "history_dev": order[24:80],
                        "calibration": order[80:100], "reserve": order[100:]}
    partitions = {p: sorted(c for g in gs for c in groups[g]) for p, gs in partition_groups.items()}
    packet, gold = [], {}
    pilot_ids = set(partitions["pilot"])
    for row in rows:
        c = str(row["claim_id"])
        if c not in pilot_ids:
            continue
        item_id = str(row["item_id"])
        case = {k: row[k] for k in PUBLIC_FIELDS}
        packet.append({"id": item_id, "group": find(c), "case": case})
        gold[item_id] = int(row["final_label"])
    group_position = {g: n for n, g in enumerate(order)}
    packet.sort(key=lambda r: (group_position[r["group"]], digest({"item": r["id"], "salt": SALT})))
    write(OUT / "public_pilot.json", {"source_commit": COMMIT, "items": packet})
    write(OUT / "private_pilot_gold.json", {"scope": "Standalone passage labels only", "labels": gold})
    write(OUT / "split_manifest.json", {"salt": SALT, "groups": dict(groups), "partitions": partitions,
                                        "partition_groups": partition_groups,
                                        "duplicate_links": duplicate_links})
    inventory = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "source_repo": REPO,
        "source_commit": COMMIT, "source_sha256": digest((OUT / "source/dg-evidence-750.jsonl").read_bytes()),
        "total_rows": len(rows), "total_claims": len(by_claim), "metadata_groups": len(groups),
        "rows_per_claim_counts": dict(Counter(len(v) for v in by_claim.values())),
        "partition_claim_counts": {p: len(v) for p, v in partitions.items()},
        "partition_group_counts": {p: len(v) for p, v in partition_groups.items()},
        "duplicate_link_count": len(duplicate_links), "pilot_items": len(packet),
        "public_sha256": digest(json.loads((OUT / "public_pilot.json").read_text())),
        "gold_sha256": digest(json.loads((OUT / "private_pilot_gold.json").read_text())),
        "selection_used_labels": False, "selection_used_model_scores": False,
        "gold_distributions_opened": False,
        "licensing": "No redistribution license confirmed. Raw downloaded source and excerpts stay in ignored results; release code/manifests/URLs only.",
        "scope": "Expert passage sufficiency annotations, not report truth or joint multi-passage sufficiency.",
    }
    write(OUT / "inventory.json", inventory)
    print(json.dumps(inventory, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("fetch", "prepare"))
    args = parser.parse_args()
    {"fetch": fetch, "prepare": prepare}[args.action]()
