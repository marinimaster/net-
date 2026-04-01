from __future__ import annotations

import unittest

from netplus_quiz.engine import QuizSession, SubnetEngine
from netplus_quiz.quiz_bank import (
    QUESTION_BANK,
    available_domains,
    get_questions,
)


class QuizBankTests(unittest.TestCase):
    def test_question_bank_has_valid_domains(self) -> None:
        self.assertGreater(len(QUESTION_BANK), 0)
        for question in QUESTION_BANK:
            self.assertTrue(1 <= question.domain_id <= 5)
            self.assertTrue(question.source_file.exists(), f"Source missing: {question.source_file}")

    def test_domain_filtering(self) -> None:
        domains = available_domains()
        if domains:
            d = domains[0]
            filtered = get_questions(domains=[d], shuffle=False)
            self.assertTrue(all(q.domain_id == d for q in filtered))

    def test_quiz_session_tracks_domain_stats(self) -> None:
        questions = get_questions(limit=2, shuffle=False)
        session = QuizSession(questions)

        first = session.current_question()
        self.assertIsNotNone(first)
        session.answer_current(first.answer_indices)

        stats = session.domain_stats
        self.assertEqual(stats[first.domain_id]["correct"], 1)
        self.assertEqual(stats[first.domain_id]["total"], 1)

    def test_subnet_engine_math(self) -> None:
        # Test a few /24 challenges
        for _ in range(5):
            chal = SubnetEngine.generate_challenge(difficulty="standard")
            if chal["cidr"] == 24:
                # Mask for /24 is always 255.255.255.0
                self.assertEqual(chal["mask"], "255.255.255.0")
                # Network ID should end in .0
                self.assertTrue(chal["network"].endswith(".0"))
                # Broadcast should end in .255
                self.assertTrue(chal["broadcast"].endswith(".255"))

if __name__ == "__main__":
    unittest.main()
