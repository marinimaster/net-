from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Question:
    """Multiple-choice question tied to a source note file."""

    id: str
    topic: str
    prompt: str
    choices: tuple[str, ...]
    answer_indices: tuple[int, ...]
    explanation: str
    source_file: Path
    domain_id: int = 1  # 1-5 based on CompTIA Domains
    difficulty: str = "standard"
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 1 <= self.domain_id <= 5:
            raise ValueError(f"{self.id} has an invalid domain_id: {self.domain_id}")
        if self.difficulty not in {"standard", "hard"}:
            raise ValueError(f"{self.id} has an unsupported difficulty: {self.difficulty}")
        if len(self.choices) < 2:
            raise ValueError(f"{self.id} must have at least two choices")
        if not self.answer_indices:
            raise ValueError(f"{self.id} must have at least one answer")
        for idx in self.answer_indices:
            if not 0 <= idx < len(self.choices):
                raise ValueError(f"{self.id} has an invalid answer index: {idx}")

    @property
    def answer_texts(self) -> tuple[str, ...]:
        return tuple(self.choices[i] for i in self.answer_indices)

    @property
    def is_multi_select(self) -> bool:
        return len(self.answer_indices) > 1


@dataclass
class Flashcard:
    """Term-Definition pair for flashcard mode."""
    id: str
    term: str
    definition: str
    domain_id: int
    mastery_level: int = 0  # 0: New, 1: Learning, 2: Review, 3: Mastered
    last_reviewed: float = 0.0
