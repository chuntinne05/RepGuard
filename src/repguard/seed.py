"""Deterministic seed management for reproducible experiments.

Uses SHA-256-based derivation to produce independent child seeds from a
master seed, ensuring every stochastic operation in the pipeline is
independently reproducible without global-state mutation.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any

import numpy as np


class SeedManager:
    """Manages deterministic seed derivation for reproducible experiments.

    Given a master seed, derives independent child seeds for different
    components (data splitting, prompt generation, mock responses, etc.)
    using SHA-256 hashing. This avoids the fragile pattern of relying on
    a global random state that changes when code is reordered.

    Example:
        >>> sm = SeedManager(master_seed=42)
        >>> split_seed = sm.derive("data_split")
        >>> mock_seed = sm.derive("mock_provider")
        >>> assert split_seed != mock_seed
        >>> assert sm.derive("data_split") == split_seed  # deterministic
    """

    def __init__(self, master_seed: int) -> None:
        """Initialize with a master seed.

        Args:
            master_seed: The root seed from which all child seeds are derived.
        """
        self._master_seed = master_seed

    @property
    def master_seed(self) -> int:
        """The root master seed."""
        return self._master_seed

    def derive(self, namespace: str) -> int:
        """Derive a deterministic child seed for a named component.

        The derivation uses SHA-256(master_seed || namespace) to produce
        a 32-bit integer seed. This is deterministic: the same master_seed
        and namespace always produce the same child seed.

        Args:
            namespace: A unique identifier for the component (e.g., "data_split",
                "mock_provider", "prompt_shuffle").

        Returns:
            A deterministic integer seed in [0, 2^31 - 1].
        """
        key = f"{self._master_seed}:{namespace}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        # Use the first 8 hex chars (32 bits) and mask to positive int
        return int(digest[:8], 16) & 0x7FFFFFFF

    def get_rng(self, namespace: str) -> random.Random:
        """Get a seeded random.Random instance for a namespace.

        Returns a stdlib Random instance seeded with the derived seed.
        Useful for operations that need a full Random API without
        mutating global state.

        Args:
            namespace: Component identifier.

        Returns:
            A seeded random.Random instance.
        """
        return random.Random(self.derive(namespace))

    def get_numpy_rng(self, namespace: str) -> np.random.Generator:
        """Get a seeded numpy Generator for a namespace.

        Returns a numpy random Generator seeded with the derived seed.
        Preferred over np.random.seed() because it avoids global state.

        Args:
            namespace: Component identifier.

        Returns:
            A seeded numpy random Generator.
        """
        return np.random.default_rng(self.derive(namespace))

    def seed_everything(self, namespace: str) -> int:
        """Seed both stdlib random and numpy global state for a namespace.

        This is a convenience method for code that cannot easily accept
        injected RNG instances. Prefer get_rng() / get_numpy_rng() when
        possible to avoid global state mutation.

        Args:
            namespace: Component identifier.

        Returns:
            The derived seed that was used.
        """
        seed = self.derive(namespace)
        random.seed(seed)
        np.random.seed(seed)  # noqa: NPY002
        return seed

    def __repr__(self) -> str:
        """Return a human-readable representation."""
        return f"SeedManager(master_seed={self._master_seed})"

    def to_dict(self) -> dict[str, Any]:
        """Serialize seed manager state for logging.

        Returns:
            Dictionary with master seed value.
        """
        return {"master_seed": self._master_seed}
