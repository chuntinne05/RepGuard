import json
import zipfile

import pytest

from thesis_pilot import evalplus_published as P


def test_model_name():
    assert P.model_name("code-llama-13b_temp_0.zip") == "code-llama-13b"
    assert P.model_name("mistral-7b_temp_0.0.zip") == "mistral-7b"


def test_zip_samples(tmp_path):
    p = tmp_path / "m_temp_0.0.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("m_temp_0.0/Mbpp_287/0.py", "def f(): pass\n")
        z.writestr("m_temp_0.0/Mbpp_287/1.py", "x")
        z.writestr("m_temp_0.0/readme.txt", "x")
    assert P.zip_samples(p) == {"Mbpp/287": "def f(): pass\n"}


def test_fractional_k():
    # v1: 5 models, 32 tasks -> |H|=155 -> 16, 39
    assert P.fractional_ks(32, 5) == [16, 39]
    assert P.fractional_ks(32, 4) == [12, 31]


def test_confirmation_refused_without_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "RUN", tmp_path)
    with pytest.raises(SystemExit):
        P.require_gate_passed()
    g = tmp_path / "gate_development.json"
    g.write_text(json.dumps({"pools": {"P7": {"PASS": False}}}))
    with pytest.raises(SystemExit):
        P.require_gate_passed()
    g.write_text(json.dumps({"pools": {"P7": {"PASS": True}}}))
    P.require_gate_passed()
