"""Tests for deterministic seed management."""

from __future__ import annotations

from repguard.seed import SeedManager


class TestSeedManager:
    """Tests for the SeedManager class."""

    def test_derive_is_deterministic(self) -> None:
        """Same master seed + namespace should always produce the same child seed."""
        sm1 = SeedManager(42)
        sm2 = SeedManager(42)
        assert sm1.derive("test") == sm2.derive("test")

    def test_different_namespaces_produce_different_seeds(self) -> None:
        """Different namespaces should produce different child seeds."""
        sm = SeedManager(42)
        assert sm.derive("data_split") != sm.derive("mock_provider")

    def test_different_master_seeds_produce_different_children(self) -> None:
        """Different master seeds should produce different child seeds."""
        sm1 = SeedManager(42)
        sm2 = SeedManager(99)
        assert sm1.derive("test") != sm2.derive("test")

    def test_derived_seed_is_positive(self) -> None:
        """Derived seeds should be non-negative integers."""
        sm = SeedManager(42)
        for ns in ["a", "b", "c", "long_namespace_name", "123"]:
            seed = sm.derive(ns)
            assert seed >= 0
            assert isinstance(seed, int)

    def test_get_rng_is_deterministic(self) -> None:
        """Random instances from same namespace should produce same sequence."""
        sm = SeedManager(42)
        rng1 = sm.get_rng("test")
        rng2 = sm.get_rng("test")
        assert [rng1.random() for _ in range(10)] == [rng2.random() for _ in range(10)]

    def test_get_numpy_rng_is_deterministic(self) -> None:
        """Numpy generators from same namespace should produce same values."""
        sm = SeedManager(42)
        rng1 = sm.get_numpy_rng("test")
        rng2 = sm.get_numpy_rng("test")
        vals1 = [float(rng1.random()) for _ in range(10)]
        vals2 = [float(rng2.random()) for _ in range(10)]
        assert vals1 == vals2

    def test_to_dict(self) -> None:
        """Serialization should capture master seed."""
        sm = SeedManager(42)
        d = sm.to_dict()
        assert d == {"master_seed": 42}

    def test_repr(self) -> None:
        """String representation should be readable."""
        sm = SeedManager(42)
        assert "42" in repr(sm)
