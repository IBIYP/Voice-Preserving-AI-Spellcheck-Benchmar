import io
import json
import unittest
from urllib.error import HTTPError

from run_jspell_control import (
    API_HOST,
    API_URL,
    process_response,
    request_jspell,
    safe_http_error_detail,
    utf16_offset_to_index,
)


class JSpellResponseTests(unittest.TestCase):
    def test_applies_first_suggestion_once_using_utf16_offsets(self):
        text = "😀 speling typo"
        response = {
            "elements": [{
                "errors": [
                    {"word": "typo", "position": 11, "suggestions": ["type", "typos"]},
                    {"word": "speling", "position": 3, "suggestions": ["spelling"]},
                ]
            }]
        }

        result = process_response(text, response)

        self.assertEqual(result["text"], "😀 spelling type")
        self.assertEqual(len(result["edits"]), 2)
        self.assertEqual(result["errors"][0]["word"], "speling")

    def test_keeps_error_without_suggestions_unchanged(self):
        result = process_response(
            "term",
            {"elements": [{"errors": [
                {"word": "term", "position": 0, "suggestions": []}
            ]}]},
        )

        self.assertEqual(result["text"], "term")
        self.assertEqual(result["edits"], [])

    def test_rejects_offset_inside_surrogate_pair(self):
        with self.assertRaisesRegex(ValueError, "surrogate pair"):
            utf16_offset_to_index("😀word", 1)

    def test_rejects_error_word_that_does_not_match_source(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            process_response(
                "speling",
                {"elements": [{"errors": [
                    {"word": "speilng", "position": 0, "suggestions": ["spelling"]}
                ]}]},
            )

    def test_request_uses_documented_endpoint_and_headers(self):
        captured = {}

        def fake_open(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return io.BytesIO(b'{"elements":[{"errors":[]}]}')

        response = request_jspell("speling", "test-key", opener=fake_open)
        request = captured["request"]

        self.assertEqual(request.full_url, API_URL)
        self.assertEqual(request.get_header("X-rapidapi-host"), API_HOST)
        self.assertEqual(request.get_header("X-rapidapi-key"), "test-key")
        self.assertEqual(json.loads(request.data.decode("utf-8"))["fieldvalues"], "speling")
        self.assertEqual(captured["timeout"], 30)
        self.assertEqual(response["elements"][0]["errors"], [])

    def test_http_errors_redact_key_and_submitted_text(self):
        body = json.dumps({
            "message": "Rejected key test-key while checking private passage"
        }).encode("utf-8")

        def fake_open(request, timeout):
            raise HTTPError(
                API_URL,
                403,
                "Forbidden",
                {"x-rapidapi-request-id": "request-123"},
                io.BytesIO(body),
            )

        with self.assertRaises(RuntimeError) as raised:
            request_jspell("private passage", "test-key", opener=fake_open)

        message = str(raised.exception)
        self.assertIn("HTTP 403", message)
        self.assertIn("request-123", message)
        self.assertNotIn("test-key", message)
        self.assertNotIn("private passage", message)

    def test_non_json_error_details_are_withheld(self):
        self.assertEqual(
            safe_http_error_detail("unstructured response", "test-key", "private text"),
            "non-JSON error details withheld",
        )


if __name__ == "__main__":
    unittest.main()
