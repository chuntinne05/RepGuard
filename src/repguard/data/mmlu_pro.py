"""MMLU-Pro dataset download, parsing, and caching.

Handles automated download of MMLU-Pro from HuggingFace, parsing into
TaskRecord objects with proper metadata extraction, and local caching
to avoid redundant downloads. Raw data is stored in the configured
data directory (excluded from git via .gitignore).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from repguard.data.models import TaskMetadata, TaskRecord

logger = logging.getLogger("repguard")

# MMLU-Pro subject-to-domain mapping based on the benchmark paper
SUBJECT_TO_DOMAIN: dict[str, str] = {
    "math": "STEM",
    "physics": "STEM",
    "chemistry": "STEM",
    "biology": "STEM",
    "computer science": "STEM",
    "engineering": "STEM",
    "health": "Other",
    "psychology": "Social Science",
    "business": "Social Science",
    "economics": "Social Science",
    "history": "Humanities",
    "philosophy": "Humanities",
    "law": "Humanities",
    "other": "Other",
}

# Skill family groupings for transfer estimation (Week 2+)
SUBJECT_TO_SKILL_FAMILY: dict[str, str] = {
    "math": "quantitative_reasoning",
    "physics": "quantitative_reasoning",
    "chemistry": "natural_science",
    "biology": "natural_science",
    "computer science": "technical",
    "engineering": "technical",
    "health": "applied_science",
    "psychology": "social_behavioral",
    "business": "social_behavioral",
    "economics": "quantitative_reasoning",
    "history": "humanities_knowledge",
    "philosophy": "humanities_reasoning",
    "law": "humanities_reasoning",
    "other": "general",
}

# Answer index to letter mapping
INDEX_TO_LETTER: dict[int, str] = {
    0: "A", 1: "B", 2: "C", 3: "D", 4: "E",
    5: "F", 6: "G", 7: "H", 8: "I", 9: "J",
}


def load_mmlu_pro(
    data_dir: str | Path = "./data",
    dataset_id: str = "TIGER-Lab/MMLU-Pro",
    max_tasks: int | None = None,
    cache_to_disk: bool = True,
) -> list[TaskRecord]:
    """Download and parse MMLU-Pro into TaskRecord objects.

    Downloads the dataset from HuggingFace on first call, then caches
    the parsed records locally as JSON for faster subsequent loads.
    Raw HuggingFace cache is stored in the default cache directory
    (excluded from git).

    Args:
        data_dir: Local directory for caching parsed data.
        dataset_id: HuggingFace dataset identifier.
        max_tasks: Maximum number of tasks to load (None = all).
        cache_to_disk: Whether to cache parsed records to disk.

    Returns:
        List of TaskRecord objects with full metadata.

    Raises:
        RuntimeError: If the dataset cannot be loaded or parsed.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    cache_file = data_dir / "mmlu_pro_parsed.json"

    # Try loading from local cache first
    if cache_file.exists():
        logger.info(f"Loading MMLU-Pro from cache: {cache_file}")
        return _load_from_cache(cache_file, max_tasks)

    # Download from HuggingFace
    logger.info(f"Downloading MMLU-Pro from HuggingFace: {dataset_id}")
    records = _download_and_parse(dataset_id)

    # Cache to disk
    if cache_to_disk:
        _save_to_cache(records, cache_file)
        logger.info(f"Cached {len(records)} records to {cache_file}")

    if max_tasks is not None:
        records = records[:max_tasks]

    logger.info(f"Loaded {len(records)} MMLU-Pro tasks across {_count_subjects(records)} subjects")
    return records


def _download_and_parse(dataset_id: str) -> list[TaskRecord]:
    """Download MMLU-Pro from HuggingFace and parse into TaskRecords.

    Args:
        dataset_id: HuggingFace dataset identifier.

    Returns:
        List of parsed TaskRecord objects.

    Raises:
        RuntimeError: If the dataset cannot be loaded.
    """
    try:
        from datasets import load_dataset
    except ImportError as e:
        msg = (
            "The 'datasets' package is required to download MMLU-Pro. "
            "Install it with: pip install datasets"
        )
        raise RuntimeError(msg) from e

    try:
        ds = load_dataset(dataset_id, split="test")
    except Exception as e:
        msg = f"Failed to load dataset '{dataset_id}': {e}"
        raise RuntimeError(msg) from e

    records: list[TaskRecord] = []

    for idx, item in enumerate(ds):
        record = _parse_item(idx, item)
        if record is not None:
            records.append(record)

    return records


def _parse_item(idx: int, item: dict[str, Any]) -> TaskRecord | None:
    """Parse a single MMLU-Pro item into a TaskRecord.

    Args:
        idx: Item index (used for task_id generation).
        item: Raw item dictionary from the HuggingFace dataset.

    Returns:
        Parsed TaskRecord, or None if the item is invalid.
    """
    try:
        question = item.get("question", "")
        options_raw = item.get("options", [])
        answer_key = item.get("answer", "")
        answer_index = item.get("answer_index", -1)
        subject = item.get("category", "other").lower().strip()
        question_id = item.get("question_id", idx)

        if not question or not options_raw:
            logger.warning(f"Skipping item {idx}: missing question or options")
            return None

        options = tuple(str(opt) for opt in options_raw)

        # Resolve answer index
        if isinstance(answer_index, int) and 0 <= answer_index < len(options):
            gt_index = answer_index
        elif isinstance(answer_key, str) and len(answer_key) == 1:
            gt_index = ord(answer_key.upper()) - ord("A")
        else:
            logger.warning(f"Skipping item {idx}: cannot resolve answer index")
            return None

        if gt_index < 0 or gt_index >= len(options):
            logger.warning(f"Skipping item {idx}: answer index {gt_index} out of range")
            return None

        gt_answer = INDEX_TO_LETTER.get(gt_index, str(gt_index))
        domain = SUBJECT_TO_DOMAIN.get(subject, "Other")
        skill_family = SUBJECT_TO_SKILL_FAMILY.get(subject, "general")

        task_id = f"mmlu_pro_{question_id}"

        metadata = TaskMetadata(
            domain=domain,
            subject=subject,
            difficulty="unknown",
            skill_family=skill_family,
            extra={"source": "MMLU-Pro", "question_id": question_id},
        )

        return TaskRecord(
            task_id=task_id,
            question=question,
            options=options,
            ground_truth_answer=gt_answer,
            ground_truth_index=gt_index,
            metadata=metadata,
            raw_data=dict(item),
        )

    except Exception as e:
        logger.warning(f"Error parsing item {idx}: {e}")
        return None


def _load_from_cache(cache_file: Path, max_tasks: int | None) -> list[TaskRecord]:
    """Load pre-parsed TaskRecords from a JSON cache file.

    Args:
        cache_file: Path to the cached JSON file.
        max_tasks: Maximum number of tasks to return.

    Returns:
        List of TaskRecord objects.
    """
    with open(cache_file) as f:
        data = json.load(f)

    records = [_dict_to_task_record(d) for d in data]

    if max_tasks is not None:
        records = records[:max_tasks]

    logger.info(f"Loaded {len(records)} tasks from cache")
    return records


def _save_to_cache(records: list[TaskRecord], cache_file: Path) -> None:
    """Save parsed TaskRecords to a JSON cache file.

    Args:
        records: List of TaskRecord objects to cache.
        cache_file: Path to write the cache file.
    """
    data = [_task_record_to_dict(r) for r in records]
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2)


def _task_record_to_dict(record: TaskRecord) -> dict[str, Any]:
    """Serialize a TaskRecord to a dictionary for JSON caching.

    Args:
        record: TaskRecord to serialize.

    Returns:
        Dictionary representation.
    """
    return {
        "task_id": record.task_id,
        "question": record.question,
        "options": list(record.options),
        "ground_truth_answer": record.ground_truth_answer,
        "ground_truth_index": record.ground_truth_index,
        "metadata": {
            "domain": record.metadata.domain,
            "subject": record.metadata.subject,
            "difficulty": record.metadata.difficulty,
            "skill_family": record.metadata.skill_family,
            "extra": record.metadata.extra,
        },
    }


def _dict_to_task_record(d: dict[str, Any]) -> TaskRecord:
    """Deserialize a dictionary to a TaskRecord.

    Args:
        d: Dictionary representation from cache.

    Returns:
        TaskRecord instance.
    """
    meta = d["metadata"]
    metadata = TaskMetadata(
        domain=meta["domain"],
        subject=meta["subject"],
        difficulty=meta.get("difficulty", "unknown"),
        skill_family=meta.get("skill_family", "general"),
        extra=meta.get("extra", {}),
    )

    return TaskRecord(
        task_id=d["task_id"],
        question=d["question"],
        options=tuple(d["options"]),
        ground_truth_answer=d["ground_truth_answer"],
        ground_truth_index=d["ground_truth_index"],
        metadata=metadata,
    )


def _count_subjects(records: list[TaskRecord]) -> int:
    """Count the number of distinct subjects in a list of records."""
    return len({r.metadata.subject for r in records})


def create_synthetic_tasks(n: int = 50, seed: int = 42) -> list[TaskRecord]:
    """Create synthetic MMLU-Pro-like tasks for testing without network access.

    Generates deterministic synthetic multiple-choice questions across
    several subjects. Used by tests and the dry-run smoke test to validate
    the pipeline without downloading the actual dataset.

    Args:
        n: Number of synthetic tasks to create.
        seed: Random seed for deterministic generation.

    Returns:
        List of synthetic TaskRecord objects.
    """
    import random as _random

    rng = _random.Random(seed)

    subjects = list(SUBJECT_TO_DOMAIN.keys())
    records: list[TaskRecord] = []

    for i in range(n):
        subject = subjects[i % len(subjects)]
        domain = SUBJECT_TO_DOMAIN[subject]
        skill_family = SUBJECT_TO_SKILL_FAMILY[subject]
        num_options = rng.choice([4, 5, 6, 8, 10])
        gt_index = rng.randint(0, num_options - 1)

        options = tuple(
            f"Option {INDEX_TO_LETTER.get(j, str(j))}: "
            f"{'Correct' if j == gt_index else 'Incorrect'} answer for {subject} Q{i}"
            for j in range(num_options)
        )

        metadata = TaskMetadata(
            domain=domain,
            subject=subject,
            difficulty=rng.choice(["easy", "medium", "hard"]),
            skill_family=skill_family,
            extra={"source": "synthetic", "question_id": i},
        )

        records.append(TaskRecord(
            task_id=f"synthetic_{i:04d}",
            question=(
                f"[Synthetic] This is a test question about {subject} (Q{i}). "
                f"Which of the following is the correct answer?"
            ),
            options=options,
            ground_truth_answer=INDEX_TO_LETTER.get(gt_index, str(gt_index)),
            ground_truth_index=gt_index,
            metadata=metadata,
        ))

    return records
