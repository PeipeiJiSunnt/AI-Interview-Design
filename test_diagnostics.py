import json
import unittest
from unittest.mock import Mock
import httpx
from openai import AuthenticationError, RateLimitError, NotFoundError, APIConnectionError
from engine import Interview, OpenAIBackend, safe_diagnostic


def error(cls, status, code=None):
    return cls("secret-marker must never appear", response=httpx.Response(status, request=httpx.Request("POST", "https://api.openai.com/v1/responses")),
               body={"code": code, "type": code})


class DiagnosticTests(unittest.TestCase):
    def test_error_classification_and_redaction(self):
        cases = [(error(AuthenticationError, 401), "AUTHENTICATION_FAILED"),
                 (error(NotFoundError, 404, "model_not_found"), "MODEL_OR_RESOURCE_UNAVAILABLE"),
                 (error(RateLimitError, 429, "insufficient_quota"), "QUOTA_EXCEEDED"),
                 (error(RateLimitError, 429, "rate_limit_exceeded"), "RATE_LIMITED"),
                 (APIConnectionError(request=httpx.Request("POST", "https://api.openai.com")), "CONNECTION_FAILED"),
                 (ValueError("secret-marker"), "MODEL_OUTPUT_INVALID")]
        for exc, expected in cases:
            result = safe_diagnostic(exc)
            self.assertEqual(result["code"], expected)
            self.assertNotIn("secret-marker", json.dumps(result))

    def test_call_persists_safe_diagnostic(self):
        backend = object.__new__(OpenAIBackend)
        backend.client = Mock()
        backend.client.responses.create.side_effect = error(RateLimitError, 429, "insufficient_quota")
        s = Interview()
        with self.assertRaises(RateLimitError):
            backend.generate("test", s)
        self.assertEqual(s.calls[-1]["diagnostic"]["code"], "QUOTA_EXCEEDED")
        self.assertNotIn("secret-marker", json.dumps(s.record()))


if __name__ == "__main__":
    unittest.main()
