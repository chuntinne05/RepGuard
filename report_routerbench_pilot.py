"""Independently validate cloud inference records and recompute pilot diagnostics."""
import hashlib
import json
from pathlib import Path
import numpy as np
import run_routerbench_pilot as cli
from routerbench_pilot_pipeline import verify, validate
from routerbench_pilot_core import MODEL, MODEL_DIGEST, probability, query_hash, analyze, MODELS, dev_query


def near_equal(a, b):
    if isinstance(a, dict):
        assert a.keys() == b.keys()
        for key in a:
            near_equal(a[key], b[key])
    elif isinstance(a, list):
        assert len(a) == len(b)
        for aa, bb in zip(a, b):
            near_equal(aa, bb)
    elif isinstance(a, float):
        assert np.isclose(a, b, atol=1e-10, rtol=1e-10), (a, b)
    else:
        assert a == b, (a, b)


def main():
    root = cli.OUTPUT / 'cloud'
    packet = json.loads((root / 'input_private.json').read_text()); verify(packet)
    status = json.loads((root / 'status.json').read_text())
    if status['state'] != 'completed_pilot_review_required' or status['completed_cases'] != 288:
        raise SystemExit('Pilot is not complete; no final scientific report generated.')
    env = json.loads((root / 'judge_environment.json').read_text())
    assert env['model'] == MODEL and env['model_digest'] == MODEL_DIGEST and not env['archive_mounted']
    assert not env['think'] and env['num_ctx'] == 16384
    inputs = json.loads((root / 'judge_inputs_private.json').read_text()); validate(inputs)
    ledger = json.loads((root / 'ledger.json').read_text())
    gold = json.loads((root / 'pilot_gold_private.json').read_text())
    assert gold['query_ids'] == packet['query_ids'] and gold['models'] == list(MODELS)
    assert len(set(gold['query_ids'])) == 48 and all(dev_query(q) for q in gold['query_ids'])
    assert len(inputs['cases']) == len(ledger) == 288
    p = np.full((48, 6), np.nan); invalid = np.zeros_like(p, bool); clipped = np.zeros_like(p, bool)
    attempts = tokens_in = tokens_out = unknown = responses = 0; seconds = 0.
    for case in inputs['cases']:
        assert hashlib.sha256(case['prompt'].encode()).hexdigest() == case['prompt_sha256']
        prompt = json.loads(case['prompt'])
        assert set(prompt) == {'problem', 'candidate_answer', 'answer_is_partial'}
        assert query_hash(prompt['problem']) == case['query_sha256'] == packet['query_ids'][case['query_index']]
        row = json.loads((root / f"case_{case['index']:04d}.json").read_text()); validate(row)
        assert row['run_id'] == packet['run_id'] and row['index'] == case['index'] and row['complete']
        assert row['artifact_sha256'] == ledger[str(case['index'])] and row['prompt_sha256'] == case['prompt_sha256']
        assert 1 <= len(row['attempts']) <= 2
        valid = []
        for attempt in row['attempts']:
            attempts += 1
            if 'response' not in attempt:
                unknown += 1; continue
            r = attempt['response']; responses += 1
            assert r['model'] == MODEL
            tokens_in += r.get('prompt_eval_count', 0); tokens_out += r.get('eval_count', 0)
            seconds += r.get('total_duration', 0) / 1e9
            if attempt['state'] == 'response_received':
                assert r['done'] and r.get('eval_count', 0) > 0
                valid.append(probability(r['message']['content']))
        if row['invalid']:
            assert row['probability'] == .5 and not valid
        else:
            assert valid and valid[-1] == row['probability']
        qi, mi = case['query_index'], case['model_index']
        assert not np.isfinite(p[qi, mi])
        p[qi, mi] = row['probability']; invalid[qi, mi] = row['invalid']; clipped[qi, mi] = case['answer_clipped']
    result = analyze(np.array(gold['success']), p, invalid, clipped)
    result.update(run_id=packet['run_id'], usage={'attempts_started': attempts, 'responses_recorded': responses,
                  'prompt_tokens_recorded': tokens_in, 'completion_tokens_recorded': tokens_out,
                  'unknown_usage_attempts': unknown, 'inference_seconds_recorded': seconds})
    near_equal(result, json.loads((root / 'analysis.json').read_text()))
    out = cli.ROOT / 'docs/analysis'
    summary = {k: v for k, v in result.items() if k not in ('calibrated_predictions', 'gold_only_predictions')}
    summary.update({'environment': env, 'source_sha256': packet['source_sha256'], 'verified_cases': 288})
    (out / 'routerbench_pilot_results_2026-10-06.json').write_text(json.dumps(summary, indent=2) + '\n')
    rci = result['pair_residual_variance_ratio_ci95']
    lines = ['# Pilot judge thật trên MATH500: kết quả', '',
             f"Run `{packet['run_id']}`: **288/288 judgment** cho 48 câu × 6 model; đã kiểm chứng artifacts và tính lại kết quả.", '',
             '## Phạm vi', '',
             'Qwen3-14B chạy thật trên Modal, think=false, context 16.384. Candidate answers là '
             'execution có sẵn trong LLMRouterBench; không gọi mới sáu solver. Đây là pilot development '
             'đánh giá feedback, chưa phải DART routing hay xác nhận thắng baseline.', '',
             '## Các con số', '',
             '| Chỉ số | Kết quả |', '|---|---:|',
             f"| Judgment hợp lệ | {100*result['valid_fraction']:.2f}% |",
             f"| Answer bị cắt bớt | {100*result['clipped_fraction']:.2f}% |",
             f"| Brier judge thô — thấp tốt hơn | {result['brier']['raw_judge']:.6f} |",
             f"| Brier hiệu chỉnh cross-fit | {result['brier']['crossfit_judge']:.6f} |",
             f"| Brier control không judge | {result['brier']['crossfit_gold_only']:.6f} |",
             f"| Cải thiện Brier so với control không judge | {result['crossfit_brier_gain']:.6f} |",
             f"| CI95 cải thiện Brier | [{result['crossfit_brier_gain_ci95'][0]:.6f}, {result['crossfit_brier_gain_ci95'][1]:.6f}] |",
             f"| Tỷ số phương sai residual / outcome differences | {result['pair_residual_variance_ratio']:.6f} |",
             f"| CI95 tỷ số trên | [{rci[0]:.6f}, {rci[1]:.6f}] |" if rci else '| CI95 tỷ số trên | Không xác định |',
             f"| Attempts đã khởi tạo | {attempts} |",
             f"| Input tokens ghi nhận | {tokens_in:,} |",
             f"| Output tokens ghi nhận | {tokens_out:,} |",
             f"| Attempts chưa biết đủ usage | {unknown} |",
             f"| Tổng thời gian inference ghi nhận | {seconds/60:.2f} phút |", '',
             f"**Operational gate: {'PASS' if result['operational_pass'] else 'FAIL'}.**",
             f"**Expansion signal: {'PASS' if result['expansion_signal_pass'] else 'FAIL'}.**", '',
             'Expansion yêu cầu ít nhất 95% valid, tối đa 50% answers bị cắt, tỷ số phương sai ≤0,90 '
             'và CI upper<1. Tiêu chí được khóa trước judgment; không sửa sau kết quả.', '',
             '## Diễn giải', '',
             f"Tỷ số {result['pair_residual_variance_ratio']:.4f} tương ứng giảm khoảng "
             f"{100*(1-result['pair_residual_variance_ratio']):.2f}% phương sai trong các chênh lệch giữa model. "
             'Feedback đã hiệu chỉnh có thông tin ngoài khả năng trung bình của từng model, '
             'theo chẩn đoán held-out của pilot này. Brier thấp hơn nghĩa là xác suất dự báo '
             'gần gold hơn, không phải accuracy hay số task thành công.', '',
             'Đây là bằng chứng để thử bước tiếp với gold thưa. Chưa đo được số nhãn có thể '
             'tiết kiệm, lợi ích chọn agent, hay lợi ích ròng sau chi phí judge. Calibration '
             'ở pilot được học từ toàn gold của 36 câu khác trong mỗi fold; cần kiểm tra lại '
             'khi chỉ cấp 5%, 10%, 20% nhãn và so với đối chứng cùng quyền truy cập.', '',
             '## Giới hạn và quyết định tiếp', '',
             '- Tất cả gold của pilot được dùng cho chẩn đoán cross-fit: 36 câu train, 12 câu held-out mỗi fold. '
             'Không gọi đây là routing với ngân sách 10%.',
             '- Bootstrap 2.000 lần theo question trên prediction cố định; chưa refit toàn bộ learner, '
             'chưa chứng nhận template/near-duplicate independence.',
             '- Gold là binary score của evaluator MATH500 đã lưu, không phải đáp án được người kiểm chứng lại '
             'trong pilot. Không đọc gold của các câu ngoài pilot vào analysis.',
             '- Model-only ridge là bản thích ứng mới; không dùng parser tên model để giả lập scaffold.',
             '- Usage chỉ là inference đã ghi nhận; tổng Modal billing, thời gian startup và unknown attempts '
             'phải tính riêng, không đổi token count thành USD khi chưa có hóa đơn.',
             '- Pipeline đã dừng theo giới hạn pilot. Nếu gate fail, phân tích feedback/clipping/calibration '
             'trước mở rộng. Nếu pass, khóa study lớn hơn và các đối chứng cùng ngân sách trước khi chạy.', '',
             '[Protocol](routerbench_pilot_protocol_2026-10-06.md) · '
             '[JSON đầy đủ](routerbench_pilot_results_2026-10-06.json)', '']
    (out / 'routerbench_pilot_assessment_2026-10-06.md').write_text('\n'.join(lines))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
