"""Explicit post-hoc diagnostics and blank human-review packets. No inference."""
from collections import Counter
from pathlib import Path
import json

from experiments.verification_v1.prepare import OUT, ROOT, digest, write


def main():
    plan = json.loads((OUT / 'registered_plan.json').read_text())
    d = OUT / 'runs' / plan['plan_id']
    summary = json.loads((d / 'analysis.json').read_text())
    public = json.loads((d / 'public_pilot.json').read_text())
    gold = json.loads((OUT / 'private_pilot_gold.json').read_text())['labels']
    records = {(r['item_id'], r['workflow']): r for p in (d / 'responses').glob('*.json')
               for r in [json.loads(p.read_text())]}
    workflows = ('A', 'B', 'AA', 'BB', 'AB', 'BA')
    items = public['items']
    diagnostics = {'scope': 'Post-hoc saved-response diagnostics; no change to registered score/gate.',
                   'plan_id': plan['plan_id'], 'gold_counts': dict(Counter(gold[r['id']] for r in items)),
                   'workflows': {}, 'errors_private_packet': str(d / 'errors_private.json'),
                   'new_inference_calls': 0, 'human_reviews_completed': 0}
    for w in workflows:
        selected = [records[(r['id'], w)] for r in items]
        labels = [r['parsed'].get('label') for r in selected]
        correct = sum(p == gold[r['id']] for p, r in zip(labels, items))
        assert correct == summary['metrics'][w]['correct']
        matrix = [[sum(gold[r['id']] == y and p == c for p, r in zip(labels, items))
                   for c in (0, 1, 2, 3, None)] for y in range(4)]
        approved = [i for i, p in enumerate(labels) if p == 2]
        approval_errors = sum(gold[items[i]['id']] != 2 for i in approved)
        serving = selected + ([records[(r['id'], w[0])] for r in items] if len(w) == 2 else [])
        diagnostics['workflows'][w] = {
            'correct_recomputed': correct, 'confusion_rows_gold_cols_0_1_2_3_invalid': matrix,
            'supported_approvals': len(approved), 'false_supported_approvals': approval_errors,
            'false_supported_approval_risk': approval_errors / len(approved) if approved else None,
            'supported_approval_coverage': len(approved) / len(items),
            'quote_grounded_sufficient': sum(r['parsed'].get('grounded_sufficient', False) for r in selected),
            'serving_calls_including_reused_initial': len(serving),
            'serving_input_tokens': sum(r['response'].get('prompt_eval_count', 0) for r in serving),
            'serving_output_tokens': sum(r['response'].get('eval_count', 0) for r in serving),
            'mean_serving_request_seconds': sum(r['wall_seconds'] for r in serving) / len(items),
            'mean_ollama_eval_seconds': sum(r['response'].get('eval_duration', 0) / 1e9 for r in serving) / len(items),
        }
    errors = []
    for r in items:
        predictions = {w: records[(r['id'], w)]['parsed'].get('label') for w in workflows}
        if len(set(predictions.values())) > 1 or any(p != gold[r['id']] for p in predictions.values()):
            errors.append({'id': r['id'], 'group': r['group'], 'case': r['case'],
                           'published_gold': gold[r['id']], 'predictions': predictions,
                           'responses': {w: records[(r['id'], w)]['raw_text'] for w in workflows}})
    write(d / 'errors_private.json', errors)
    # Review all pilot pairs, ordered without model outcomes, not just model errors.
    ordered = sorted(items, key=lambda r: digest({'human_blind_order_v1': r['id']}))
    blind = [{'review_id': f'V1-{i+1:03d}', 'case': r['case'],
              'annotation': {'label': None, 'ambiguous_claim': None, 'missing_definition': None,
                             'evidence_quote': '', 'rationale': '', 'needs_adjudication': None}}
             for i, r in enumerate(ordered)]
    write(OUT / 'human_review/source_only_all120.json', blind)
    write(OUT / 'human_review/private_id_mapping.json', {f'V1-{i+1:03d}': r['id'] for i, r in enumerate(ordered)})
    write(ROOT / 'docs/reports/2026-11-09/verification_v1_diagnostics.json', diagnostics)
    write(ROOT / 'docs/reports/2026-11-09/verification_v1_summary.json', summary)
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
