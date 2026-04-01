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
    answer_index: int
    explanation: str
    source_file: Path
    difficulty: str = "standard"
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.difficulty not in {"standard", "hard"}:
            raise ValueError(f"{self.id} has an unsupported difficulty: {self.difficulty}")
        if len(self.choices) < 2:
            raise ValueError(f"{self.id} must have at least two choices")
        if not 0 <= self.answer_index < len(self.choices):
            raise ValueError(f"{self.id} has an invalid answer index")

    @property
    def answer_text(self) -> str:
        return self.choices[self.answer_index]
