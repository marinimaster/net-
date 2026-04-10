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
    """Standard quiz runner with linear progression."""

    def __init__(self, questions: Sequence[Question], time_limit_seconds: int | None = None) -> None:
        if not questions:
            raise ValueError("QuizSession requires at least one question")
        self._questions = list(questions)
        self._position = 0
        self._records: list[AnswerRecord] = []
        self._flagged_ids: set[str] = set()
        self._time_limit = time_limit_seconds
        self._timed_out = False
        self.is_review = False

    @property
    def questions(self) -> tuple[Question, ...]: return tuple(self._questions)
    @property
    def position(self) -> int: return self._position
    @property
    def total_questions(self) -> int: return len(self._questions)
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
    def score(self) -> int: return sum(record.is_correct for record in self._records)
    @property
    def missed_questions(self) -> list[Question]:
        return [record.question for record in self._records if not record.is_correct]

    @property
    def finished(self) -> bool: return self._position >= len(self._questions) or self._timed_out

    def current_question(self) -> Question | None:
        if self.finished: return None
        return self._questions[self._position]

    def answer_current(self, selected_indices: tuple[int, ...]) -> AnswerRecord:
        question = self.current_question()
        if question is None: raise RuntimeError("Quiz already finished")
        is_correct = set(selected_indices) == set(question.answer_indices)
        record = AnswerRecord(question=question, selected_indices=selected_indices, is_correct=is_correct)
        self._records.append(record)
        self._position += 1
        return record


class ReviewSession:
    """Mastery-based review: 3 streaks to clear, mixed with fillers."""

    def __init__(self, missed_questions: Sequence[Question], bank: Sequence[Question]) -> None:
        # pool: qid -> [Question, streak]
        self._pool = {q.id: [q, 0] for q in missed_questions}
        self._bank = list(bank)
        self.is_review = True
        self._records: list[AnswerRecord] = []
        
        self._current_q: Question | None = None
        self._current_shuffled_choices: list[str] = []
        self._current_correct_indices: list[int] = []
        self._is_current_filler = False
        
        self._total_cleared = 0
        self._total_to_clear = len(missed_questions)
        
        self._filler_count_remaining = 0
        self._pick_next()

    @property
    def finished(self) -> bool: return len(self._pool) == 0
    @property
    def total_questions(self) -> int: return self._total_to_clear
    @property
    def position(self) -> int: return self._total_cleared
    @property
    def score(self) -> int: return self._total_cleared # Simplified for review UI
    
    @property
    def domain_stats(self) -> dict[int, dict[str, int]]:
        stats = {i: {"correct": 0, "total": 0} for i in range(1, 6)}
        for record in self._records:
            d_id = record.question.domain_id
            stats[d_id]["total"] += 1
            if record.is_correct:
                stats[d_id]["correct"] += 1
        return stats

    def current_question(self) -> Question | None: return self._current_q
    
    @property
    def current_choices(self) -> list[str]: return self._current_shuffled_choices

    def _pick_next(self) -> None:
        if self.finished:
            self._current_q = None
            return

        if self._filler_count_remaining > 0:
            self._is_current_filler = True
            ref_q = random.choice(list(self._pool.values()))[0]
            fillers = [q for q in self._bank if q.domain_id == ref_q.domain_id and q.id not in self._pool]
            if not fillers: fillers = self._bank
            self._current_q = random.choice(fillers)
            self._filler_count_remaining -= 1
        else:
            self._is_current_filler = False
            qid = random.choice(list(self._pool.keys()))
            self._current_q = self._pool[qid][0]
            self._filler_count_remaining = random.randint(1, 2)

        self._current_shuffled_choices, self._current_correct_indices = self._current_q.get_shuffled_data()

    def answer_current(self, selected_indices: tuple[int, ...]) -> AnswerRecord:
        is_correct = set(selected_indices) == set(self._current_correct_indices)
        
        if not self._is_current_filler:
            qid = self._current_q.id
            if is_correct:
                self._pool[qid][1] += 1
                if self._pool[qid][1] >= 3:
                    del self._pool[qid]
                    self._total_cleared += 1
            else:
                self._pool[qid][1] = 0

        # Create a record using a mock question with shuffled choices for feedback consistency
        mock_q = Question(
            id=self._current_q.id, topic=self._current_q.topic, prompt=self._current_q.prompt,
            choices=tuple(self._current_shuffled_choices),
            answer_indices=tuple(self._current_correct_indices),
            explanation=self._current_q.explanation, source_file=self._current_q.source_file,
            domain_id=self._current_q.domain_id, difficulty=self._current_q.difficulty
        )
        record = AnswerRecord(question=mock_q, selected_indices=selected_indices, is_correct=is_correct)
        self._records.append(record)
        
        self._pick_next()
        return record


class FlashcardSession:
    def __init__(self, flashcards: Sequence[Flashcard]) -> None:
        self._cards = list(flashcards); self._position = 0; self._results: dict[str, bool] = {}
    @property
    def current_card(self) -> Flashcard | None: return self._cards[self._position] if self._position < len(self._cards) else None
    @property
    def position(self) -> int: return self._position
    @property
    def total(self) -> int: return len(self._cards)
    def report(self, known: bool) -> None:
        card = self.current_card
        if card: self._results[card.id] = known; self._position += 1


class SubnetEngine:
    @staticmethod
    def generate_challenge() -> dict:
        import ipaddress
        # Range: 16 to 30 as requested
        cidr = random.randint(16, 30)
        
        # Determine address space (Tricky ranges included)
        # 1: Private Class A, 2: Private Class B, 3: Private Class C, 4: APIPA, 5: Random Public
        pool = random.randint(1, 5)
        if pool == 1: # 10.x.x.x
            octets = [10, random.randint(0, 255), random.randint(0, 255), random.randint(1, 254)]
        elif pool == 2: # 172.16.x.x - 172.31.x.x
            octets = [172, random.randint(16, 31), random.randint(0, 255), random.randint(1, 254)]
        elif pool == 3: # 192.168.x.x
            octets = [192, 168, random.randint(0, 255), random.randint(1, 254)]
        elif pool == 4: # 169.254.x.x (APIPA)
            octets = [169, 254, random.randint(0, 255), random.randint(1, 254)]
        else: # Random Public (avoiding 127.0.0.0/8 and 0.0.0.0/8)
            octets = [random.choice([r for r in range(1, 224) if r not in {10, 127, 169, 172, 192}]), 
                      random.randint(0, 255), random.randint(0, 255), random.randint(1, 254)]
        
        ip_str = ".".join(map(str, octets))
        try:
            # Create a network object based on the random IP and CIDR
            # strict=False allows the IP to not be the network address
            iface = ipaddress.IPv4Interface(f"{ip_str}/{cidr}")
            net = iface.network
            
            # For /31 and /32 there are no usable hosts in the traditional sense, 
            # but the user requested /16-/30.
            hosts = list(net.hosts())
            first_usable = str(hosts[0]) if hosts else "N/A"
            last_usable = str(hosts[-1]) if hosts else "N/A"
            num_hosts = net.num_addresses - 2 if net.num_addresses > 2 else 0
            
            return {
                "ip": ip_str,
                "cidr": cidr,
                "mask": str(net.netmask),
                "network": str(net.network_address),
                "broadcast": str(net.broadcast_address),
                "first_usable": first_usable,
                "last_usable": last_usable,
                "num_hosts": num_hosts
            }
        except ValueError:
            # Fallback if something goes wrong (though with 16-30 it shouldn't)
            return SubnetEngine.generate_challenge()
