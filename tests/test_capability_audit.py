"""Tests for the GeminiProvider and Capability Audit system.

All tests run WITHOUT network access by:
- Using a mocked httpx.Client for GeminiProvider tests.
- Using ``use_synthetic: true`` for CapabilityAudit tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from repguard.audit.capability_audit import (
    AgentConfig,
    CapabilityAudit,
    CapabilityAuditConfig,
    _check_heterogeneity,
    update_research_ops,
)
from repguard.config import ProviderConfig, ProviderParams
from repguard.providers.gemini_ import GeminiProvider, _estimate_cost, _extract_text


# ─────────────────────────────────────────────────────────────────────────────
# GeminiProvider tests (mocked HTTP)
# ─────────────────────────────────────────────────────────────────────────────

class TestGeminiProvider:
    """Unit tests for GeminiProvider using a mocked HTTP client."""

    def _make_provider(self) -> GeminiProvider:
        config = ProviderConfig(
            name="gemini",
            model_id="gemini-flash-latest",
            parameters=ProviderParams(temperature=0.0, max_tokens=512, top_p=1.0),
        )
        return GeminiProvider(config, api_key="test-key-xxx")

    def _make_api_response(self, text: str, input_tokens: int = 10, output_tokens: int = 5) -> dict:
        """Build a fake Gemini API response dictionary."""
        return {
            "candidates": [
                {
                    "content": {"parts": [{"text": text}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": input_tokens,
                "candidatesTokenCount": output_tokens,
                "totalTokenCount": input_tokens + output_tokens,
            },
        }

    def test_complete_returns_text(self) -> None:
        """complete() should return the text from the first candidate."""
        provider = self._make_provider()
        fake_resp = self._make_api_response("The answer is A.")

        mock_http = MagicMock()
        mock_http.json.return_value = fake_resp
        mock_http.raise_for_status.return_value = None

        with patch.object(provider._client, "post", return_value=mock_http):
            response = provider.complete("What is 2+2? (A) 4 (B) 5")

        assert response.content == "The answer is A."
        assert response.model_id == "gemini-flash-latest"
        assert response.input_tokens == 10
        assert response.output_tokens == 5
        assert response.total_tokens == 15
        assert response.cost_usd >= 0.0
        assert response.cached is False

    def test_complete_tracks_cost_across_calls(self) -> None:
        """Each call should accumulate total_cost and total_calls."""
        provider = self._make_provider()
        fake_resp = self._make_api_response("B", input_tokens=100, output_tokens=5)

        mock_http = MagicMock()
        mock_http.json.return_value = fake_resp
        mock_http.raise_for_status.return_value = None

        with patch.object(provider._client, "post", return_value=mock_http):
            provider.complete("q1")
            provider.complete("q2")

        stats = provider.get_stats()
        assert stats["total_calls"] == 2
        assert stats["total_cost_usd"] > 0.0

    def test_http_error_raises_runtime_error(self) -> None:
        """HTTP 4xx/5xx should raise RuntimeError."""
        import httpx

        provider = self._make_provider()
        mock_request = MagicMock(spec=httpx.Request)
        mock_request.url = "https://example.com"
        fake_error_response = MagicMock(spec=httpx.Response)
        fake_error_response.status_code = 429
        fake_error_response.text = "RATE_LIMIT_EXCEEDED"

        with patch.object(
            provider._client,
            "post",
            side_effect=httpx.HTTPStatusError(
                "rate limited",
                request=mock_request,
                response=fake_error_response,
            ),
        ):
            with pytest.raises(RuntimeError, match="429"):
                provider.complete("test prompt")

    def test_empty_candidates_returns_empty_string(self) -> None:
        """An API response with no candidates should return empty text."""
        provider = self._make_provider()
        fake_resp: dict = {"candidates": [], "usageMetadata": {}}

        mock_http = MagicMock()
        mock_http.json.return_value = fake_resp
        mock_http.raise_for_status.return_value = None

        with patch.object(provider._client, "post", return_value=mock_http):
            response = provider.complete("test")

        assert response.content == ""

    def test_repr(self) -> None:
        provider = self._make_provider()
        assert "gemini-flash-latest" in repr(provider)


class TestExtractText:
    """Unit tests for the _extract_text helper."""

    def test_normal_response(self) -> None:
        raw = {
            "candidates": [
                {"content": {"parts": [{"text": "Hello!"}]}}
            ]
        }
        assert _extract_text(raw) == "Hello!"

    def test_missing_candidates(self) -> None:
        assert _extract_text({}) == ""

    def test_empty_candidates_list(self) -> None:
        assert _extract_text({"candidates": []}) == ""

    def test_missing_parts(self) -> None:
        raw = {"candidates": [{"content": {"parts": []}}]}
        assert _extract_text(raw) == ""

    def test_malformed_structure(self) -> None:
        assert _extract_text({"candidates": [None]}) == ""


class TestEstimateCost:
    """Unit tests for the _estimate_cost helper."""

    def test_gemini_flash_cost(self) -> None:
        # 1M input tokens at $0.075 for gemini-1.5-flash
        cost_15 = _estimate_cost("gemini-1.5-flash", 1_000_000, 0)
        assert abs(cost_15 - 0.075) < 1e-6
        # 1M input tokens at $0.10 for gemini-flash-latest
        cost_latest = _estimate_cost("gemini-flash-latest", 1_000_000, 0)
        assert abs(cost_latest - 0.10) < 1e-6

    def test_gemini_pro_cost_higher_than_flash(self) -> None:
        cost_flash = _estimate_cost("gemini-flash", 10_000, 1_000)
        cost_pro = _estimate_cost("gemini-pro", 10_000, 1_000)
        assert cost_pro > cost_flash

    def test_zero_tokens_is_zero_cost(self) -> None:
        assert _estimate_cost("gemini-flash", 0, 0) == 0.0

    def test_unknown_model_fallback(self) -> None:
        cost = _estimate_cost("totally-unknown-model-xyz", 1_000, 1_000)
        assert cost > 0.0  # should return a positive default


# ─────────────────────────────────────────────────────────────────────────────
# CapabilityAuditConfig tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCapabilityAuditConfig:
    """Tests for YAML config loading."""

    def test_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = """
audit:
  seed: 123
  n_samples_per_domain: 5
  domains: [math, history]
  use_synthetic: true
  synthetic_n: 50
  output_dir: ./test_output

agents:
  - name: mock-agent
    provider: mock
    model_id: mock-v1
    temperature: 0.0
    max_tokens: 256
    top_p: 1.0
    api_key_env: ""
"""
        config_file = tmp_path / "test_audit.yaml"
        config_file.write_text(yaml_content)

        cfg = CapabilityAuditConfig.from_yaml(config_file)

        assert cfg.seed == 123
        assert cfg.n_samples_per_domain == 5
        assert cfg.domains == ["math", "history"]
        assert cfg.use_synthetic is True
        assert cfg.synthetic_n == 50
        assert len(cfg.agents) == 1
        assert cfg.agents[0].name == "mock-agent"
        assert cfg.agents[0].provider == "mock"

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            CapabilityAuditConfig.from_yaml("/nonexistent/path/audit.yaml")

    def test_agent_to_provider_config(self) -> None:
        agent = AgentConfig(
            name="test",
            provider="gemini",
            model_id="gemini-flash-latest",
            temperature=0.5,
            max_tokens=1024,
            top_p=0.9,
        )
        pc = agent.to_provider_config()
        assert pc.name == "gemini"
        assert pc.model_id == "gemini-flash-latest"
        assert pc.parameters.temperature == 0.5
        assert pc.parameters.max_tokens == 1024


# ─────────────────────────────────────────────────────────────────────────────
# Heterogeneity gate tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHeterogeneityGate:
    """Tests for the _check_heterogeneity gate logic."""

    def _make_result(
        self, agent: str, domain: str, accuracy: float, n: int = 10
    ):
        from repguard.audit.capability_audit import AgentDomainResult
        return AgentDomainResult(
            agent_name=agent, domain=domain, n_tasks=n,
            n_correct=int(n * accuracy), accuracy=accuracy,
            ci_lower=max(0.0, accuracy - 0.1),
            ci_upper=min(1.0, accuracy + 0.1),
        )

    def test_gate_passes_with_heterogeneous_agents(self) -> None:
        agents = ["agent_a", "agent_b"]
        domains = ["math", "history"]
        # agent_a wins math (0.90 vs 0.30), agent_b wins history (0.80 vs 0.50)
        # agent_a mean = 0.70, agent_b mean = 0.55 -> spread = 0.15 >= 0.10
        results = {
            "agent_a": {
                "math": self._make_result("agent_a", "math", 0.90),
                "history": self._make_result("agent_a", "history", 0.50),
            },
            "agent_b": {
                "math": self._make_result("agent_b", "math", 0.30),
                "history": self._make_result("agent_b", "history", 0.80),
            },
        }
        gate = _check_heterogeneity(agents, domains, results)
        assert gate.passed is True
        assert gate.n_domains_best_changes is True
        assert gate.performance_spread >= 0.10

    def test_gate_fails_when_one_agent_dominates(self) -> None:
        agents = ["strong", "weak"]
        domains = ["math", "history", "law"]
        # strong wins everything
        results = {
            "strong": {
                d: self._make_result("strong", d, 0.85) for d in domains
            },
            "weak": {
                d: self._make_result("weak", d, 0.15) for d in domains
            },
        }
        gate = _check_heterogeneity(agents, domains, results)
        # Even though spread is large, best agent does NOT change
        assert gate.n_domains_best_changes is False
        assert gate.passed is False

    def test_gate_fails_with_single_agent(self) -> None:
        agents = ["only_agent"]
        domains = ["math"]
        results = {
            "only_agent": {
                "math": self._make_result("only_agent", "math", 0.70)
            }
        }
        gate = _check_heterogeneity(agents, domains, results)
        assert gate.passed is False

    def test_gate_fails_when_spread_too_small(self) -> None:
        agents = ["a", "b"]
        domains = ["math", "history"]
        # Both agents perform similarly
        results = {
            "a": {
                "math": self._make_result("a", "math", 0.55),
                "history": self._make_result("a", "history", 0.45),
            },
            "b": {
                "math": self._make_result("b", "math", 0.50),
                "history": self._make_result("b", "history", 0.50),
            },
        }
        gate = _check_heterogeneity(agents, domains, results)
        # spread ≈ 0.025 < 0.10
        assert gate.performance_spread < 0.10
        assert gate.passed is False


# ─────────────────────────────────────────────────────────────────────────────
# Full pipeline smoke test (synthetic data, mock provider, no network)
# ─────────────────────────────────────────────────────────────────────────────

class TestCapabilityAuditSynthetic:
    """End-to-end capability audit using synthetic tasks and mock provider."""

    def _make_synthetic_config(self, tmp_path: Path) -> CapabilityAuditConfig:
        return CapabilityAuditConfig(
            seed=42,
            n_samples_per_domain=3,
            domains=["math", "physics", "history"],
            prompt_mode="direct",
            use_synthetic=True,
            synthetic_n=200,
            output_dir=str(tmp_path / "audit_output"),
            agents=[
                AgentConfig(
                    name="mock-a",
                    provider="mock",
                    model_id="mock-v1",
                ),
                AgentConfig(
                    name="mock-b",
                    provider="mock",
                    model_id="mock-v2",   # different seed → different answers
                ),
            ],
        )

    def test_audit_runs_end_to_end(self, tmp_path: Path) -> None:
        cfg = self._make_synthetic_config(tmp_path)
        audit = CapabilityAudit(cfg)
        matrix = audit.run()

        assert len(matrix.agents) == 2
        assert len(matrix.domains) > 0
        assert matrix.seed == 42

        # Every configured agent should have results for every domain
        for agent in matrix.agents:
            for domain in matrix.domains:
                result = matrix.results[agent][domain]
                assert result is not None
                assert 0 <= result.n_correct <= result.n_tasks
                assert 0.0 <= result.accuracy <= 1.0
                assert result.ci_lower <= result.accuracy
                assert result.accuracy <= result.ci_upper

    def test_audit_save_creates_files(self, tmp_path: Path) -> None:
        cfg = self._make_synthetic_config(tmp_path)
        audit = CapabilityAudit(cfg)
        matrix = audit.run()
        out_dir = audit.save(matrix)

        assert (out_dir / "capability_matrix.json").exists()
        assert (out_dir / "capability_matrix.csv").exists()
        assert (out_dir / "heterogeneity_gate.txt").exists()

        # JSON should be valid and contain expected keys
        data = json.loads((out_dir / "capability_matrix.json").read_text())
        assert "agents" in data
        assert "domains" in data
        assert "results" in data
        assert "heterogeneity" in data

    def test_matrix_to_dict_is_serialisable(self, tmp_path: Path) -> None:
        cfg = self._make_synthetic_config(tmp_path)
        audit = CapabilityAudit(cfg)
        matrix = audit.run()
        d = matrix.to_dict()
        # Should be JSON-serialisable without error
        json.dumps(d)

    def test_best_agent_per_domain_is_populated(self, tmp_path: Path) -> None:
        cfg = self._make_synthetic_config(tmp_path)
        audit = CapabilityAudit(cfg)
        matrix = audit.run()
        best = matrix.best_agent_per_domain()

        assert set(best.keys()) == set(matrix.domains)
        for domain, winner in best.items():
            assert winner in matrix.agents

    def test_update_research_ops(self, tmp_path: Path) -> None:
        """update_research_ops should write log and registry files."""
        cfg = self._make_synthetic_config(tmp_path)
        audit = CapabilityAudit(cfg)
        matrix = audit.run()

        ops_dir = tmp_path / "research_ops"
        ops_dir.mkdir()
        update_research_ops(matrix, research_ops_dir=ops_dir)

        assert (ops_dir / "research_log.md").exists()
        assert (ops_dir / "experiment_registry.csv").exists()

        registry_text = (ops_dir / "experiment_registry.csv").read_text()
        assert "mock-a" in registry_text
        assert "mock-b" in registry_text

    def test_reproducibility(self, tmp_path: Path) -> None:
        """Two audits with the same config must produce identical accuracies."""
        cfg = self._make_synthetic_config(tmp_path)

        m1 = CapabilityAudit(cfg).run()
        m2 = CapabilityAudit(cfg).run()

        for agent in m1.agents:
            for domain in m1.domains:
                r1 = m1.results[agent][domain]
                r2 = m2.results[agent][domain]
                assert r1.accuracy == r2.accuracy, (
                    f"Non-reproducible result for {agent}/{domain}: "
                    f"{r1.accuracy} vs {r2.accuracy}"
                )
