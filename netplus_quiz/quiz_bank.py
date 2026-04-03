from __future__ import annotations

import json
import os
import random
from pathlib import Path
from random import Random
from typing import Iterable

from .models import Flashcard, Question

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = PROJECT_ROOT / "notes"
QUESTIONS_JSON = NOTES_DIR / "questions.json"
FLASHCARDS_JSON = NOTES_DIR / "flashcards.json"
PERFORMANCE_JSON = NOTES_DIR / "performance.json"
FC_PERFORMANCE_JSON = NOTES_DIR / "flashcard_perf.json"
SETTINGS_JSON = NOTES_DIR / "settings.json"

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

def available_domains() -> tuple[int, ...]:
    return tuple(sorted(set(question.domain_id for question in QUESTION_BANK)))

def get_questions(*, domains: Iterable[int] | None = None, topics: Iterable[str] | None = None, limit: int | None = None, shuffle: bool = True) -> list[Question]:
    d_filter = set(domains) if domains is not None else None
    t_filter = set(topics) if topics is not None else None
    
    filtered = [
        q for q in QUESTION_BANK 
        if (d_filter is None or q.domain_id in d_filter)
        and (t_filter is None or q.topic in t_filter)
    ]
    if shuffle: Random().shuffle(filtered)
    return filtered[:limit] if limit else filtered

def get_flashcards(*, domains: Iterable[int] | None = None, limit: int | None = None, shuffle: bool = True) -> list[Flashcard]:
    d_filter = set(domains) if domains is not None else None
    filtered = [c for c in FLASHCARD_BANK if d_filter is None or c.domain_id in d_filter]
    if shuffle: Random().shuffle(filtered)
    return filtered[:limit] if limit else filtered

def get_port_questions(*, secure_only: bool = False, limit: int | None = None) -> list[Question]:
    tags = ("ports", "secure") if secure_only else ("ports",)
    filtered = [q for q in QUESTION_BANK if q.topic == "Protocols and Ports" and all(t in q.tags for t in tags)]
    Random().shuffle(filtered)
    return filtered[:limit] if limit else filtered

def get_port_drill_questions(*, secure_only: bool = False, limit: int = 20) -> list[Question]:
    """Generates synthetic bidirectional port questions for drill mode."""
    # Find all questions in "Protocols and Ports" topic
    base_qs = [q for q in QUESTION_BANK if q.topic == "Protocols and Ports"]
    if secure_only:
        base_qs = [q for q in base_qs if "secure" in q.tags]
    
    # Extract pairs of (Protocol, Port) from prompts/explanations/etc
    # This is a bit complex since data is unstructured in prompt. 
    # Let's use a hardcoded reference for the drill to ensure 100% accuracy.
    PORT_DATA = [
        ("FTP", "20/21"), ("SSH", "22"), ("Telnet", "23"), ("SMTP", "25"),
        ("DNS", "53"), ("DHCP", "67/68"), ("TFTP", "69"), ("HTTP", "80"),
        ("POP3", "110"), ("NTP", "123"), ("IMAP", "143"), ("SNMP", "161/162"),
        ("BGP", "179"), ("LDAP", "389"), ("HTTPS", "443"), ("SMB", "445"),
        ("Syslog", "514"), ("SMTPS", "587"), ("LDAPS", "636"), ("IMAPS", "993"),
        ("POP3S", "995"), ("SQL Server", "1433"), ("Oracle", "1521"),
        ("RDP", "3389"), ("MySQL", "3306"), ("PostgreSQL", "5432"), ("SIP", "5060"), ("SIPS (TLS)", "5061")
    ]
    
    if secure_only:
        secure_names = {"SSH", "HTTPS", "SMTPS", "LDAPS", "IMAPS", "POP3S", "SIPS (TLS)", "SFTP"}
        PORT_DATA = [p for p in PORT_DATA if p[0] in secure_names or "S" in p[0]]

    drill_qs = []
    all_ports = [p[1] for p in PORT_DATA]
    all_names = [p[0] for p in PORT_DATA]

    for _ in range(limit):
        pair = random.choice(PORT_DATA)
        direction = random.choice(["to_port", "to_name"])
        
        if direction == "to_port":
            prompt = f"What is the default port for {pair[0]}?"
            correct = pair[1]
            # Get 3 random decoys
            others = [p for p in all_ports if p != correct]
            decoys = random.sample(others, min(3, len(others)))
            choices = decoys + [correct]
            random.shuffle(choices)
            drill_qs.append(Question(
                id=f"drill-p-{pair[0]}", topic="Port Drill", prompt=prompt,
                choices=tuple(choices), answer_indices=(choices.index(correct),),
                explanation=f"{pair[0]} uses port {pair[1]}.",
                source_file=PROJECT_ROOT / "notes/protocols_ports_compTIA.txt",
                domain_id=1
            ))
        else:
            prompt = f"Which protocol uses port {pair[1]}?"
            correct = pair[0]
            others = [n for n in all_names if n != correct]
            decoys = random.sample(others, min(3, len(others)))
            choices = decoys + [correct]
            random.shuffle(choices)
            drill_qs.append(Question(
                id=f"drill-n-{pair[1]}", topic="Port Drill", prompt=prompt,
                choices=tuple(choices), answer_indices=(choices.index(correct),),
                explanation=f"Port {pair[1]} is used by {pair[0]}.",
                source_file=PROJECT_ROOT / "notes/protocols_ports_compTIA.txt",
                domain_id=1
            ))
            
    return drill_qs

def save_performance(question_id: str, is_correct: bool) -> None:
    perf = {}
    if PERFORMANCE_JSON.exists():
        with open(PERFORMANCE_JSON, "r") as f: perf = json.load(f)
    stats = perf.get(question_id, {"correct": 0, "total": 0})
    stats["total"] += 1
    if is_correct: stats["correct"] += 1
    perf[question_id] = stats
    with open(PERFORMANCE_JSON, "w") as f: json.dump(perf, f, indent=4)

def save_flashcard_mastery(card_id: str, known: bool) -> None:
    import time
    perf = {}
    if FC_PERFORMANCE_JSON.exists():
        with open(FC_PERFORMANCE_JSON, "r") as f: perf = json.load(f)
    m_info = perf.get(card_id, {"level": 0, "last": 0.0})
    m_info["level"] = min(3, m_info["level"] + 1) if known else max(0, m_info["level"] - 1)
    m_info["last"] = time.time()
    perf[card_id] = m_info
    with open(FC_PERFORMANCE_JSON, "w") as f: json.dump(perf, f, indent=4)

def reset_all_data() -> None:
    for p in [PERFORMANCE_JSON, FC_PERFORMANCE_JSON]:
        if p.exists(): os.remove(p)

def get_global_stats() -> dict:
    perf = {}
    if PERFORMANCE_JSON.exists():
        with open(PERFORMANCE_JSON, "r") as f: perf = json.load(f)
    stats = {i: {"correct": 0, "total": 0, "seen": 0, "bank_size": 0} for i in range(1, 6)}
    for q in QUESTION_BANK:
        d_id = q.domain_id
        stats[d_id]["bank_size"] += 1
        if q.id in perf:
            stats[d_id]["seen"] += 1
            stats[d_id]["correct"] += perf[q.id]["correct"]
            stats[d_id]["total"] += perf[q.id]["total"]
    return stats

def load_settings() -> dict:
    defaults = {"font_size": 12, "theme": "dark", "peek_mode": True}
    if SETTINGS_JSON.exists():
        with open(SETTINGS_JSON, "r") as f: return {**defaults, **json.load(f)}
    return defaults

def save_settings(settings: dict) -> None:
    with open(SETTINGS_JSON, "w") as f: json.dump(settings, f, indent=4)
