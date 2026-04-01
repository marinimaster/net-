from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from .models import Flashcard, Question


@dataclass(frozen=True)
class AnswerRecord:
    question: Question
    selected_indices: tuple[int, ...]
    is_correct: bool


class QuizSession:
    """Stateful quiz runner separated from the UI layer."""

    def __init__(self, questions: Sequence[Question], time_limit_seconds: int | None = None) -> None:
        if not questions:
            raise ValueError("QuizSession requires at least one question")
        self._questions = list(questions)
        self._position = 0
        self._records: list[AnswerRecord] = []
        self._flagged_ids: set[str] = set()
        self._time_limit = time_limit_seconds
        self._timed_out = False

    @property
    def questions(self) -> tuple[Question, ...]:
        return tuple(self._questions)

    @property
    def position(self) -> int:
        return self._position

    @property
    def total_questions(self) -> int:
        return len(self._questions)

    @property
    def score(self) -> int:
        return sum(record.is_correct for record in self._records)

    @property
    def domain_stats(self) -> dict[int, dict[str, int]]:
        """Returns correctness stats per domain (1-5)."""
        stats = {i: {"correct": 0, "total": 0} for i in range(1, 6)}
        for record in self._records:
            d_id = record.question.domain_id
            stats[d_id]["total"] += 1
            if record.is_correct:
                stats[d_id]["correct"] += 1
        return stats

    @property
    def records(self) -> tuple[AnswerRecord, ...]:
        return tuple(self._records)

    @property
    def finished(self) -> bool:
        return self._position >= len(self._questions) or self._timed_out

    @property
    def timed_out(self) -> bool:
        return self._timed_out

    def set_timed_out(self) -> None:
        self._timed_out = True

    def toggle_flag(self, question_id: str) -> None:
        if question_id in self._flagged_ids:
            self._flagged_ids.remove(question_id)
        else:
            self._flagged_ids.add(question_id)

    def is_flagged(self, question_id: str) -> bool:
        return question_id in self._flagged_ids

    def current_question(self) -> Question | None:
        if self.finished:
            return None
        return self._questions[self._position]

    def answer_current(self, selected_indices: tuple[int, ...]) -> AnswerRecord:
        question = self.current_question()
        if question is None:
            raise RuntimeError("The quiz is already finished")
        
        for idx in selected_indices:
            if not 0 <= idx < len(question.choices):
                raise ValueError("Selected choice is out of range")

        is_correct = set(selected_indices) == set(question.answer_indices)
        record = AnswerRecord(
            question=question,
            selected_indices=selected_indices,
            is_correct=is_correct,
        )
        self._records.append(record)
        self._position += 1
        return record


class FlashcardSession:
    """Handles tracking and self-reporting for a flashcard study session."""

    def __init__(self, flashcards: Sequence[Flashcard]) -> None:
        self._cards = list(flashcards)
        self._position = 0
        self._results: dict[str, bool] = {} # card_id -> reported_correct

    @property
    def current_card(self) -> Flashcard | None:
        if self._position >= len(self._cards):
            return None
        return self._cards[self._position]

    @property
    def position(self) -> int:
        return self._position

    @property
    def total(self) -> int:
        return len(self._cards)

    def report(self, known: bool) -> None:
        card = self.current_card
        if card:
            self._results[card.id] = known
            self._position += 1


class SubnetEngine:
    """Generates random IPv4 subnetting challenges."""

    @staticmethod
    def generate_challenge(difficulty: str = "standard") -> dict:
        """Generates a challenge dict with IP, CIDR, and correct answers."""
        if difficulty == "standard":
            cidr = random.randint(24, 30)
        else:
            cidr = random.randint(8, 23)

        octets = [random.randint(1, 254) for _ in range(4)]
        if octets[0] == 127: octets[0] = 126 # Skip loopback
        
        ip_str = ".".join(map(str, octets))
        
        # Calculate mask
        mask_int = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
        mask_str = ".".join(str((mask_int >> i) & 0xFF) for i in (24, 16, 8, 0))
        
        # Calculate network ID
        ip_int = (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]
        net_int = ip_int & mask_int
        net_str = ".".join(str((net_int >> i) & 0xFF) for i in (24, 16, 8, 0))
        
        # Calculate broadcast
        broad_int = net_int | (~mask_int & 0xFFFFFFFF)
        broad_str = ".".join(str((broad_int >> i) & 0xFF) for i in (24, 16, 8, 0))
        
        return {
            "ip": ip_str,
            "cidr": cidr,
            "mask": mask_str,
            "network": net_str,
            "broadcast": broad_str
        }
