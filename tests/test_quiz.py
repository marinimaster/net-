from __future__ import annotations

import unittest

from netplus_quiz.engine import QuizSession
from netplus_quiz.quiz_bank import (
    QUESTION_BANK,
    available_difficulties,
    available_topics,
    get_port_questions,
    get_questions,
)


class QuizBankTests(unittest.TestCase):
    def test_question_bank_has_valid_sources_and_answers(self) -> None:
        self.assertGreater(len(QUESTION_BANK), 0)
        for question in QUESTION_BANK:
            self.assertTrue(question.source_file.exists(), question.id)
            self.assertGreaterEqual(question.answer_index, 0)
            self.assertLess(question.answer_index, len(question.choices))

    def test_topic_filtering_returns_matching_questions(self) -> None:
        topic = available_topics()[0]
        filtered = get_questions(topics=[topic], shuffle=False)
        self.assertGreater(len(filtered), 0)
        self.assertTrue(all(question.topic == topic for question in filtered))

    def test_difficulty_filtering_returns_hard_questions(self) -> None:
        self.assertIn("hard", available_difficulties())
        filtered = get_questions(difficulties=["hard"], shuffle=False)
        self.assertGreater(len(filtered), 0)
        self.assertTrue(all(question.difficulty == "hard" for question in filtered))

    def test_port_practice_returns_only_port_questions(self) -> None:
        filtered = get_port_questions(shuffle=False)
        self.assertGreater(len(filtered), 0)
        self.assertTrue(all(question.topic == "Protocols and Ports" for question in filtered))
        self.assertTrue(all("ports" in question.tags for question in filtered))

    def test_secure_port_practice_returns_only_secure_port_questions(self) -> None:
        filtered = get_port_questions(secure_only=True, shuffle=False)
        self.assertGreater(len(filtered), 0)
        self.assertTrue(all("ports" in question.tags for question in filtered))
        self.assertTrue(all("secure" in question.tags for question in filtered))

    def test_quiz_session_tracks_score(self) -> None:
        questions = get_questions(limit=2, shuffle=False)
        session = QuizSession(questions)

        first = session.current_question()
        self.assertIsNotNone(first)
        session.answer_current(first.answer_index)

        second = session.current_question()
        self.assertIsNotNone(second)
        wrong_index = (second.answer_index + 1) % len(second.choices)
        session.answer_current(wrong_index)

        self.assertTrue(session.finished)
        self.assertEqual(session.score, 1)
        self.assertEqual(session.total_questions, 2)


if __name__ == "__main__":
    unittest.main()
