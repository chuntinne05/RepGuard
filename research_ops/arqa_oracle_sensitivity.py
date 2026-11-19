"""Post-hoc whole-pilot measurement sensitivity. Never replaces frozen primary."""
from __future__ import annotations

import json
import re
from collections import Counter
from decimal import Decimal

from experiments.arqa_v2.preflight import OUT, REPORT, write
from experiments.arqa_v2.oracle import close, norm, number
from experiments.arqa_v2.study import PROFILES, WORKFLOWS


def main():
    root=OUT/'runs/deaee6167f9609bd2f045f46'
    assert (root/'analysis.json').exists(),'Run frozen scoring first'
    public=json.loads((root/'public_pilot.json').read_text())['items']
    gold=json.loads((OUT/'private_pilot_gold.json').read_text())
    records={(r['item_id'],r['profile'],r['workflow']):r for r in [json.loads(p.read_text()) for p in (root/'responses').glob('*.json')]}
    rows=[]
    for r in public:
        i=r['id'];t=r['case']['table'];q=r['case']['question'];g=gold[i]
        flags=[]
        if 'production' in t['title'].casefold() and re.search(r'\b(sold|sales|deliveries)\b',q,re.I):
            flags.append('question_measure_vs_production_title_review_required')
        labels=Counter((c['row_index'],norm(c['row'])) for c in t['cells'])
        row_names=Counter(label for ri,label in labels if label)
        if any(count>1 and label in norm(q) for label,count in row_names.items()):
            flags.append('question_mentions_repeated_row_label_without_explicit_scope_check')
        if not g['unit']:flags.append('published_unit_empty_requires_semantic_unit_review')
        if not close(g['published_value'],g['value']):
            flags.append('published_display_precision_differs_from_frozen_half_cent_rule')
        if any(re.fullmatch(r'[+-]?\d+(?:\.\d+)?',str(h)) and not re.fullmatch(r'(?:19|20)\d{2}',str(h)) for h in t['headers'][1:]):
            flags.append('numeric_header_may_need_source_layout_review')
        if any(norm(c['column'])=='total segments' for c in t['cells']) and 'all segments' in q.casefold():
            flags.append('segments_vs_consolidated_reconciliation_scope_review')
        rows.append({'qa_id':i,'table_id':t['table_id'],'flags':flags})
    sensitivity={}
    for p in PROFILES:
        for w in WORKFLOWS:
            displayed=program_numeric=program_but_wrong_answer=0
            for r in public:
                i=r['id'];g=gold[i];a=records[(i,p,w)]['parsed']
                if not a['valid'] or a.get('abstained'):continue
                val=number(g['published_value']);exp=val.as_tuple().exponent
                tolerance=max(Decimal('0.005000001'),Decimal('0.50000001').scaleb(exp)) if exp<0 else Decimal('0.005000001')
                displayed+=close(a['answer']['answer_value'],g['published_value'],tolerance)
                if a.get('source_bound'):
                    pc=close(a['recomputed'],g['value']);program_numeric+=pc
                    program_but_wrong_answer+=pc and not close(a['answer']['answer_value'],g['value'])
            sensitivity[p+'/'+w]={'published_precision_numeric_only':displayed,'source_program_numeric_only':program_numeric,
                                  'program_matches_oracle_but_answer_value_does_not':program_but_wrong_answer,'n':len(public)}
    output={'scope':'Post-hoc whole24pilot source/measurement flags, automatic heuristics and author inspection, NOT independent human adjudication. No item removed/relabelled, no primary score replaced.',
            'flag_counts':dict(Counter(f for r in rows for f in r['flags'])),'items_with_any_flag':sum(bool(r['flags']) for r in rows),
            'item_flags':rows,'sensitivity':sensitivity,
            'warning':'Sensitivity changes rounding/ignores units or scores program instead of declared answer. It is a different readout, not method superiority or human semantic truth.'}
    write(REPORT/'arqa_v2_oracle_sensitivity.json',output)
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
