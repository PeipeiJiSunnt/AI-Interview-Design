"""Streamlit AppTest with fake backend; no real API calls or research data."""
import os
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from test_engine import FakeBackend, review


def button(app, label):
    return next(b for b in app.button if b.label == label)


class AppTests(unittest.TestCase):
    def launch(self, condition="C"):
        self.env = patch.dict(os.environ, {"OPENAI_API_KEY": "offline-placeholder", "INTERVIEW_CONDITION": condition})
        self.env.start()
        self.addCleanup(self.env.stop)
        app = AppTest.from_file("app.py").run()
        app.checkbox[0].check().run()
        button(app, "Start interview").click().run()
        self.assertFalse(app.exception)
        return app

    def test_no_key_prevents_start(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            app = AppTest.from_file("app.py").run()
            app.checkbox[0].check().run()
            button(app, "Start interview").click().run()
            self.assertTrue(app.error)
            self.assertIsNone(app.session_state["interview"])

    def test_complete_yes_no_b_c_and_reset(self):
        for condition in ("B", "C"):
            for answer in ("Yes", "No"):
                with self.subTest(condition=condition, answer=answer):
                    app = self.launch(condition)
                    backend = FakeBackend(["Could you describe that?"] * 30)
                    with patch("engine.OpenAIBackend", return_value=backend):
                        app.chat_input[0].set_value("Graduate student in linguistics").run()
                        self.assertEqual(len(app.radio), 1)
                        app.radio[0].set_value(answer)
                        button(app, "Continue").click().run()
                        self.assertEqual(app.session_state["interview"].stage, "branch")
                        for _ in range(30):
                            if app.session_state["interview"].stage == "done":
                                break
                            app.chat_input[0].set_value("A synthetic answer").run()
                            self.assertFalse(app.exception)
                        self.assertEqual(app.session_state["interview"].stage, "done")
                        self.assertEqual(len(app.get("download_button")), 2)
                        button(app, "Start over").click().run()
                        button(app, "Confirm start over").click().run()
                        self.assertIsNone(app.session_state["interview"])
                        self.assertEqual(len(app.checkbox), 1)

    def test_retry_does_not_duplicate_answer_or_regenerate_candidate(self):
        app = self.launch()
        backend = FakeBackend(["Can you describe that?"], [TimeoutError(), review()])
        with patch("engine.OpenAIBackend", return_value=backend):
            app.chat_input[0].set_value("Graduate student").run()
            app.radio[0].set_value("No")
            button(app, "Continue").click().run()
            app.chat_input[0].set_value("I prefer textbooks").run()
            self.assertTrue(app.error)
            self.assertTrue(any("REQUEST_TIMEOUT" in c.value for c in app.caption))
            count = len(app.session_state["interview"].messages)
            app.run()  # Download/other reruns must not silently issue another request.
            self.assertEqual(len(backend.checked), 1)
            button(app, "Retry next question").click().run()
            self.assertFalse(app.error)
            self.assertFalse(app.exception)
            self.assertEqual(len(backend.generated), 1)
            self.assertEqual(len(app.session_state["interview"].messages), count + 1)


if __name__ == "__main__":
    unittest.main()
