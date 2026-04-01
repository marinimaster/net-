from __future__ import annotations

import json
from pathlib import Path
from random import Random
from typing import Iterable

from .models import Flashcard, Question

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_JSON = PROJECT_ROOT / "notes" / "questions.json"
FLASHCARDS_JSON = PROJECT_ROOT / "notes" / "flashcards.json"
PERFORMANCE_JSON = PROJECT_ROOT / "notes" / "performance.json"
FC_PERFORMANCE_JSON = PROJECT_ROOT / "notes" / "flashcard_perf.json"


def _load_questions() -> tuple[Question, ...]:
    if not QUESTIONS_JSON.exists():
        return ()
    
    with open(QUESTIONS_JSON, "r") as f:
        data = json.load(f)
    
    questions = []
    for item in data:
        questions.append(
            Question(
                id=item["id"],
                topic=item["topic"],
                prompt=item["prompt"],
                choices=tuple(item["choices"]),
                answer_indices=tuple(item["answer_indices"]),
                explanation=item["explanation"],
                source_file=PROJECT_ROOT / item["source_file"],
                domain_id=item.get("domain_id", 1),
                difficulty=item.get("difficulty", "standard"),
                tags=tuple(item.get("tags", ())),
            )
        )
    return tuple(questions)


def _load_flashcards() -> tuple[Flashcard, ...]:
    if not FLASHCARDS_JSON.exists():
        return ()
    
    with open(FLASHCARDS_JSON, "r") as f:
        data = json.load(f)
    
    # Load mastery from fc_performance
    mastery = {}
    if FC_PERFORMANCE_JSON.exists():
        with open(FC_PERFORMANCE_JSON, "r") as f:
            mastery = json.load(f)
            
    cards = []
    for item in data:
        m_info = mastery.get(item["id"], {"level": 0, "last": 0.0})
        cards.append(
            Flashcard(
                id=item["id"],
                term=item["term"],
                definition=item["definition"],
                domain_id=item["domain_id"],
                mastery_level=m_info["level"],
                last_reviewed=m_info["last"],
            )
        )
    return tuple(cards)


QUESTION_BANK: tuple[Question, ...] = _load_questions()
FLASHCARD_BANK: tuple[Flashcard, ...] = _load_flashcards()


def available_topics() -> tuple[str, ...]:
    return tuple(sorted(set(question.topic for question in QUESTION_BANK)))


def available_domains() -> tuple[int, ...]:
    return tuple(sorted(set(question.domain_id for question in QUESTION_BANK)))


def get_questions(
    *,
    domains: Iterable[int] | None = None,
    topics: Iterable[str] | None = None,
    limit: int | None = None,
    shuffle: bool = True,
    seed: int | None = None,
) -> list[Question]:
    domain_filter = set(domains) if domains is not None else None
    topic_filter = set(topics) if topics is not None else None

    filtered = [
        question
        for question in QUESTION_BANK
        if (domain_filter is None or question.domain_id in domain_filter)
        and (topic_filter is None or question.topic in topic_filter)
    ]

    if not filtered:
        return []

    if shuffle:
        rng = Random(seed)
        rng.shuffle(filtered)

    if limit is not None:
        return filtered[:limit]
    return filtered


def get_flashcards(
    *,
    domains: Iterable[int] | None = None,
    limit: int | None = None,
    shuffle: bool = True,
) -> list[Flashcard]:
    domain_filter = set(domains) if domains is not None else None
    filtered = [
        card
        for card in FLASHCARD_BANK
        if domain_filter is None or card.domain_id in domain_filter
    ]
    if shuffle:
        Random().shuffle(filtered)
    if limit:
        return filtered[:limit]
    return filtered


def get_port_questions(
    *,
    secure_only: bool = False,
    limit: int | None = None,
    shuffle: bool = True,
    seed: int | None = None,
) -> list[Question]:
    tags = ("ports", "secure") if secure_only else ("ports",)
    # Search by topic and tags
    filtered = [
        q for q in QUESTION_BANK
        if q.topic == "Protocols and Ports" and all(t in q.tags for t in tags)
    ]
    if shuffle:
        rng = Random(seed)
        rng.shuffle(filtered)
    if limit:
        return filtered[:limit]
    return filtered


def save_performance(question_id: str, is_correct: bool) -> None:
    """Updates performance tracking in performance.json."""
    perf = {}
    if PERFORMANCE_JSON.exists():
        with open(PERFORMANCE_JSON, "r") as f:
            perf = json.load(f)
    
    stats = perf.get(question_id, {"correct": 0, "total": 0})
    stats["total"] += 1
    if is_correct:
        stats["correct"] += 1
    
    perf[question_id] = stats
    with open(PERFORMANCE_JSON, "w") as f:
        json.dump(perf, f, indent=4)


def save_flashcard_mastery(card_id: str, known: bool) -> None:
    """Updates flashcard mastery level and last reviewed time."""
    import time
    perf = {}
    if FC_PERFORMANCE_JSON.exists():
        with open(FC_PERFORMANCE_JSON, "r") as f:
            perf = json.load(f)
            
    m_info = perf.get(card_id, {"level": 0, "last": 0.0})
    if known:
        m_info["level"] = min(3, m_info["level"] + 1)
    else:
        m_info["level"] = max(0, m_info["level"] - 1)
    
    m_info["last"] = time.time()
    perf[card_id] = m_info
    
    with open(FC_PERFORMANCE_JSON, "w") as f:
        json.dump(perf, f, indent=4)


def get_global_stats() -> dict:
    """Aggregates accuracy and coverage stats for the dashboard."""
    # Accuracy from performance.json
    perf = {}
    if PERFORMANCE_JSON.exists():
        with open(PERFORMANCE_JSON, "r") as f:
            perf = json.load(f)
            
    stats = {i: {"correct": 0, "total": 0, "seen": 0, "bank_size": 0} for i in range(1, 6)}
    
    for q in QUESTION_BANK:
        d_id = q.domain_id
        stats[d_id]["bank_size"] += 1
        if q.id in perf:
            stats[d_id]["seen"] += 1
            stats[d_id]["correct"] += perf[q.id]["correct"]
            stats[d_id]["total"] += perf[q.id]["total"]
            
    return stats
