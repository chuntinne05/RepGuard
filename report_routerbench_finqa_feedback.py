"""Verify all real FinQA judge responses and recompute fixed diagnostic locally."""
import hashlib
import json
import numpy as np
import run_routerbench_finqa_feedback as cli
from routerbench_finqa_feedback_core import MODEL, MODEL_DIGEST, probability, analyze
from routerbench_finqa_feedback_pipeline import verify, validate


def near_equal(a, b):
    if isinstance(a, dict):
        if a.keys() != b.keys():
            raise ValueError('Analysis keys differ')
        for key in a:
            near_equal(a[key], b[key])
    elif isinstance(a, list):
        if len(a) != len(b):
            raise ValueError('Analysis list length differs')
        for x, y in zip(a, b):
            near_equal(x, y)
    elif isinstance(a, float):
        if not np.isclose(a, b, atol=1e-10, rtol=1e-10):
            raise ValueError(f'Analysis float mismatch: {a} vs {b}')
    elif a != b:
        raise ValueError('Analysis value differs')


def main():
    root = cli.OUTPUT / 'cloud'
    packet = json.loads((root / 'input_private.json').read_text()); verify(packet)
    if packet != json.loads((cli.OUTPUT / 'packet_private.json').read_text()):
        raise ValueError('Cloud packet differs from frozen local input')
    for name, checksum in packet['source_sha256'].items():
        if hashlib.sha256((cli.ROOT / name).read_bytes()).hexdigest() != checksum:
            raise ValueError('Local source changed: ' + name)
    parent = cli.ROOT / 'results/routerbench_headroom_v1/cloud'
    for name, key in (('input_private.json', 'parent_input_sha256'),
                      ('analysis.json', 'parent_analysis_sha256')):
        if hashlib.sha256((parent / name).read_bytes()).hexdigest() != packet[key]:
            raise ValueError('Changed parent headroom artifact')
    status = json.loads((root / 'status.json').read_text())
    if status['state'] != 'completed_pilot_review_required' or status['completed_cases'] != 960:
        raise ValueError('FinQA pilot incomplete')
    env = json.loads((root / 'judge_environment.json').read_text())
    if env['model'] != MODEL or env['model_digest'] != MODEL_DIGEST or env['archive_mounted'] or env['think']:
        raise ValueError('Judge environment differs')
    inputs = json.loads((root / 'judge_inputs_private.json').read_text()); validate(inputs)
    gold = json.loads((root / 'pilot_gold_private.json').read_text())
    ledger = json.loads((root / 'ledger.json').read_text())
    if inputs['run_id'] != packet['run_id'] or gold['query_ids'] != packet['query_ids'] or gold['models'] != packet['models']:
        raise ValueError('Mixed input/gold identity')
    if len(inputs['cases']) != 960 or len(ledger) != 960:
        raise ValueError('Wrong case count')
    p = np.full((48, 20), np.nan); invalid = np.zeros((48, 20), bool); boxed = np.zeros((48, 20), bool)
    usage = {'attempts_started': 0, 'responses_recorded': 0, 'prompt_tokens_recorded': 0,
             'completion_tokens_recorded': 0, 'unknown_usage_attempts': 0,
             'inference_seconds_recorded': 0.}
    for case in inputs['cases']:
        if hashlib.sha256(case['prompt'].encode()).hexdigest() != case['prompt_sha256']:
            raise ValueError('Prompt checksum mismatch')
        visible = json.loads(case['prompt'])
        if set(visible) != {'problem', 'candidate_final_answer', 'answer_is_partial'}:
            raise ValueError('Unexpected judge input fields')
        if len(visible['problem']) != case['full_prompt_chars'] or visible['answer_is_partial'] != case['answer_is_partial']:
            raise ValueError('Judge input metadata differs')
        if case['query_sha256'] != packet['query_ids'][case['query_index']] or case['record_position'] != packet['positions'][packet['models'][case['model_index']]][case['query_sha256']]:
            raise ValueError('Case identity/position differs')
        row = json.loads((root / f"case_{case['index']:04d}.json").read_text()); validate(row)
        if (row['run_id'] != packet['run_id'] or row['index'] != case['index'] or
                row['artifact_sha256'] != ledger[str(case['index'])] or
                not row['complete'] or row['prompt_sha256'] != case['prompt_sha256']):
            raise ValueError('Judge case/ledger mismatch')
        valid = []
        for attempt in row['attempts']:
            usage['attempts_started'] += 1
            if 'response' not in attempt:
                usage['unknown_usage_attempts'] += 1
                continue
            response = attempt['response']; usage['responses_recorded'] += 1
            if response['model'] != MODEL:
                raise ValueError('Unexpected response model')
            usage['prompt_tokens_recorded'] += response.get('prompt_eval_count', 0)
            usage['completion_tokens_recorded'] += response.get('eval_count', 0)
            usage['inference_seconds_recorded'] += response.get('total_duration', 0) / 1e9
            if attempt['state'] == 'response_received':
                if not response['done'] or response.get('eval_count', 0) <= 0:
                    raise ValueError('Incomplete recorded response')
                valid.append(probability(response['message']['content']))
        if not 1 <= len(row['attempts']) <= 2:
            raise ValueError('Attempt budget violated')
        if row['invalid']:
            if row['probability'] != .5 or valid:
                raise ValueError('Fabricated fallback')
        elif not valid or valid[-1] != row['probability']:
            raise ValueError('Probability differs from response')
        qi, mi = case['query_index'], case['model_index']
        if np.isfinite(p[qi, mi]):
            raise ValueError('Duplicate question-model case')
        p[qi, mi] = row['probability']; invalid[qi, mi] = row['invalid']
        boxed[qi, mi] = case['extraction_mode'] == 'complete_boxed'
    result = analyze(np.array(gold['success']), p, invalid, boxed)
    result.update({'run_id': packet['run_id'], 'usage': usage})
    near_equal(result, json.loads((root / 'analysis.json').read_text()))
    if result['operational_pass'] != status['operational_pass'] or result['expansion_signal_pass'] != status['expansion_signal_pass']:
        raise ValueError('Cloud status/gate mismatch')
    summary = {k: v for k, v in result.items() if k not in ('calibrated_predictions', 'gold_only_predictions')}
    summary.update({'environment': env, 'source_sha256': packet['source_sha256'], 'verified_cases': 960})
    out = cli.ROOT / 'docs/analysis'
    (out / 'routerbench_finqa_feedback_v1_results_2026-10-06.json').write_text(json.dumps(summary, indent=2) + '\n')
    ci = result['pair_residual_variance_ratio_ci95']
    lines = ['# FinQA: kết quả pilot judge thật', '',
             f"Run `{packet['run_id']}`: 48 câu ×20 model = **960/960 judgment**; "
             'đã kiểm chứng artifacts và tính lại tại local.', '',
             '| Chỉ số | Giá trị |', '|---|---:|',
             f"| Judgment hợp lệ | {100*result['valid_fraction']:.2f}% |",
             f"| Trích được boxed answer hoàn chỉnh | {100*result['boxed_fraction']:.2f}% |",
             f"| Brier judge thô | {result['brier']['raw_judge']:.6f} |",
             f"| Brier judge sau cross-fit | {result['brier']['crossfit_judge']:.6f} |",
             f"| Brier gold-only control | {result['brier']['crossfit_gold_only']:.6f} |",
             f"| Brier gain | {result['brier_gain_vs_gold_only']:.6f} |",
             f"| Tỷ số phương sai residual differences | {result['pair_residual_variance_ratio']:.6f} |",
             f"| CI95 tỷ số | {ci} |",
             f"| Attempts / recorded responses | {usage['attempts_started']} / {usage['responses_recorded']} |",
             f"| Input / output tokens ghi nhận | {usage['prompt_tokens_recorded']:,} / {usage['completion_tokens_recorded']:,} |", '',
             f"Operational gate: **{'PASS' if result['operational_pass'] else 'FAIL'}**. "
             f"Expansion screening: **{'PASS' if result['expansion_signal_pass'] else 'FAIL'}**.", '',
             'Judge thấy full FinQA prompt và candidate final answer đã trích từ archived '
             'solver output. Gold là binary score archived, không được chấm lại. '
             'Cross-fit dùng toàn gold của 36 câu khác mỗi fold; chưa đo lợi ích chọn '
             'model ở 5/10/20% gold hoặc chi phí ròng. CI bootstrap giữ nguyên fitted '
             'predictions và 48 câu development, không phải independent confirmation.', '',
             '[Protocol](routerbench_finqa_feedback_v1_protocol_2026-10-06.md) · '
             '[JSON](routerbench_finqa_feedback_v1_results_2026-10-06.json) · '
             '[Headroom](routerbench_headroom_v1_assessment_2026-10-06.md)', '']
    (out / 'routerbench_finqa_feedback_v1_assessment_2026-10-06.md').write_text('\n'.join(lines))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
