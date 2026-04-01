from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .models import Question


@dataclass(frozen=True)
class AnswerRecord:
    question: Question
    selected_index: int
    is_correct: bool


class QuizSession:
    """Stateful quiz runner separated from the UI layer."""

    def __init__(self, questions: Sequence[Question]) -> None:
        if not questions:
            raise ValueError("QuizSession requires at least one question")
        self._questions = list(questions)
        self._position = 0
        self._records: list[AnswerRecord] = []

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
    def records(self) -> tuple[AnswerRecord, ...]:
        return tuple(self._records)

    @property
    def finished(self) -> bool:
        return self._position >= len(self._questions)

    def current_question(self) -> Question | None:
        if self.finished:
            return None
        return self._questions[self._position]

    def answer_current(self, selected_index: int) -> AnswerRecord:
        question = self.current_question()
        if question is None:
            raise RuntimeError("The quiz is already finished")
        if not 0 <= selected_index < len(question.choices):
            raise ValueError("Selected choice is out of range")

        record = AnswerRecord(
            question=question,
            selected_index=selected_index,
            is_correct=(selected_index == question.answer_index),
        )
        self._records.append(record)
        self._position += 1
        return record

