from __future__ import annotations

from .engine import QuizSession
from .quiz_bank import (
    QUESTION_BANK,
    available_domains,
    get_port_questions,
    get_questions,
)


def _run_session(title: str, session: QuizSession) -> None:
    print(f"--- {title} ---")
    print(f"Starting a {session.total_questions}-question quiz.\n")

    while not session.finished:
        question = session.current_question()
        assert question is not None

        print(f"Question {session.position + 1}/{session.total_questions}")
        print(f"Domain {question.domain_id} | Topic: {question.topic}")
        prompt = question.prompt
        if question.is_multi_select:
            prompt += f" (Select {len(question.answer_indices)})"
        print(prompt)
        
        for index, choice in enumerate(question.choices, start=1):
            print(f"  {index}. {choice}")

        while True:
            raw = input(f"Select an answer (1-{len(question.choices)}): ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(question.choices):
                selected_index = int(raw) - 1
                break
            print("Enter one of the listed option numbers.")

        # Wrap in tuple for engine compatibility
        record = session.answer_current((selected_index,))
        if record.is_correct:
            print("Correct.")
        else:
            print(f"Incorrect. Correct answer: {', '.join(record.question.answer_texts)}")

        print(f"Explanation: {record.question.explanation}")
        print(f"Source: {record.question.source_file.name}\n")

    print(f"Final score: {session.score}/{session.total_questions}")


def run_cli() -> None:
    """Fallback terminal UI when a graphical display is unavailable."""
    total = min(10, len(QUESTION_BANK))
    # Default to all domains
    _run_session("Network+ Quiz", QuizSession(get_questions(limit=total)))


def run_ports_cli(*, secure_only: bool = False) -> None:
    title = "CompTIA Secure Ports Practice" if secure_only else "CompTIA Protocols and Ports Practice"
    questions = get_port_questions(secure_only=secure_only, limit=10)
    if not questions:
        print("No ports questions found.")
        return
    _run_session(title, QuizSession(questions))
