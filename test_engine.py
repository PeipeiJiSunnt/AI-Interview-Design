"""Offline contract tests only: these do not establish real model behavior."""
import json
import unittest
from engine import Interview, validate_review, B_PROMPT, DEFAULT_MODEL


def review(decision="KEEP", rewrite=None):
    return json.dumps(dict(decision=decision, unsupported_presupposition=decision != "KEEP",
                           leading_wording=False, reason="Test judgment", rewrite=rewrite))


class FakeBackend:
    def __init__(self, candidates=None, reviews=None):
        self.candidates = iter(candidates or ["SKIP"] * 20)
        self.reviews = iter(reviews or [review()] * 20)
        self.generated = []
        self.checked = []

    def generate(self, prompt, session):
        self.generated.append(prompt)
        item = next(self.candidates)
        if isinstance(item, Exception):
            raise item
        return item

    def check(self, candidate, core, history, session):
        self.checked.append((candidate, core, history))
        item = next(self.reviews)
        if isinstance(item, Exception):
            raise item
        return item


def start(condition="C", uses_ai="Yes"):
    s = Interview(condition=condition, mode="offline_test")
    s.answer("Graduate student, linguistics, year 2")
    s.answer(uses_ai)
    return s


class EngineTests(unittest.TestCase):
    def test_background_and_fixed_branch_no_generation(self):
        for answer, expected in [("Yes", "Which tools"), ("No", "What are some reasons")]:
            s = start(uses_ai=answer)
            self.assertEqual(s.stage, "branch")
            self.assertTrue(s.messages[-1]["text"].startswith(expected))
            self.assertEqual(s.audit, [])
            self.assertEqual(sum(m["text"] == "Do you use AI tools for academic work?" for m in s.messages), 1)

    def test_full_yes_no_b_c_routes_and_cap(self):
        for condition in ("B", "C"):
            for uses_ai in ("Yes", "No"):
                s = start(condition, uses_ai)
                backend = FakeBackend(["Could you describe that?"] * 30)
                while s.stage != "done":
                    if s.stage == "decide":
                        s.decide(backend)
                    else:
                        s.answer("An answer")
                topics = {m["topic"] for m in s.messages}
                self.assertEqual("specific" in topics, uses_ai == "Yes")
                self.assertEqual("influence" in topics, uses_ai == "Yes")
                for topic in topics:
                    followups = [m for m in s.messages if m["topic"] == topic and m["kind"] == "followup" and m["role"] == "interviewer"]
                    self.assertEqual(len(followups), 0 if topic == "background" else 2)
                self.assertEqual(len(backend.checked), len(backend.generated) if condition == "C" else 0)

    def test_generator_skip_advances(self):
        s = start(uses_ai="No")
        s.answer("I prefer textbooks")
        b = FakeBackend()
        s.decide(b)
        self.assertEqual(s.topic, "attitude")
        self.assertEqual(b.checked, [])
        self.assertEqual(s.audit[0]["decision"], "GENERATOR_SKIP")

    def test_keep_preserves_original_verbatim(self):
        s = start()
        s.answer("ChatGPT weekly")
        question = "  Could you explain that?\n"
        s.decide(FakeBackend([question]))
        self.assertEqual(s.messages[-1]["text"], question)
        self.assertEqual(s.audit[0]["candidate"], question)

    def test_rewrite_and_skip(self):
        for decision in ("REWRITE", "SKIP"):
            s = start(uses_ai="No")
            s.answer("I don't need it")
            rewritten = "How do you approach assignments?" if decision == "REWRITE" else None
            s.decide(FakeBackend(["Why has AI improved your grades?"], [review(decision, rewritten)]))
            self.assertEqual(s.audit[0]["rewrite"], rewritten)
            self.assertEqual(s.audit[0]["displayed_question"], rewritten)
            if decision == "SKIP":
                self.assertEqual(s.topic, "attitude")

    def test_retry_same_candidate_after_transport_and_bad_json(self):
        s = start()
        s.answer("ChatGPT weekly")
        b = FakeBackend(["What do you use it for?"], [TimeoutError(), "bad json", review()])
        for expected in (TimeoutError, ValueError):
            with self.assertRaises(expected):
                s.decide(b)
            self.assertEqual(s.stage, "decide")
            self.assertEqual(s.followups, 0)
        s.decide(b)
        self.assertEqual(len(b.generated), 1)
        self.assertEqual(len({x[0] for x in b.checked}), 1)
        self.assertEqual(len(s.audit[0]["attempts"]), 3)
        self.assertEqual(s.followups, 1)

    def test_second_decision_includes_first_followup_answer(self):
        s = start("B")
        s.answer("Weekly")
        b = FakeBackend(["How do you use it?", "SKIP"])
        s.decide(b)
        s.answer("I compare explanations")
        s.decide(b)
        self.assertIn("I compare explanations", b.generated[1])
        self.assertIn("Fixed outline branch", b.generated[0])
        self.assertEqual(s.topic, "specific")

    def test_b_c_same_generation_prompt(self):
        prompts = []
        for condition in ("B", "C"):
            s = start(condition)
            s.answer("Weekly")
            for m in s.messages:
                m["at"] = "fixed"
            b = FakeBackend(["What do you use it for?"])
            s.decide(b)
            prompts.append(b.generated[0])
            self.assertEqual(s.model, DEFAULT_MODEL)
        self.assertEqual(*prompts)

    def test_invalid_review_fails_closed(self):
        for value in ["{}", '[]', review("OTHER"), review("REWRITE"), review("KEEP", "changed")]:
            with self.assertRaises(ValueError):
                validate_review(value)

    def test_export_contains_audit_metadata_and_safe_csv(self):
        s = start("B")
        s.answer("=SUM(1,2)")
        s.decide(FakeBackend(["SKIP"]))
        record = json.loads(json.dumps(s.record()))
        self.assertIn("candidate", record["audit"][0])
        self.assertEqual(record["b_prompt"], B_PROMPT)
        self.assertIn("'=SUM", s.csv_record())
        self.assertEqual(record["mode"], "offline_test")

    def test_invalid_answers_leave_state_unchanged(self):
        s = start()
        count = len(s.messages)
        with self.assertRaises(ValueError):
            s.answer("  ")
        self.assertEqual(len(s.messages), count)


if __name__ == "__main__":
    unittest.main()
