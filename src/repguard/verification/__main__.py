"""Local CLI: trusted contract/store files are separate from agent proposal."""
import argparse
import json
from pathlib import Path

from .engine import EvidenceStore, verify
from .models import Candidate, Contract


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract", required=True, type=Path)
    p.add_argument("--store", required=True, type=Path)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    contract = Contract.model_validate_json(args.contract.read_text())
    packet = json.loads(args.store.read_text())
    if set(packet) != {"facts", "admitted_fact_ids"}:
        raise ValueError("Unexpected store keys")
    store = EvidenceStore(packet["facts"], packet["admitted_fact_ids"])
    candidate = Candidate.model_validate_json(args.candidate.read_text())
    result = verify(contract, candidate, store).model_dump_json(indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + "\n")
    else:
        print(result)


if __name__ == "__main__":
    main()
