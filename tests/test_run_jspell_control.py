import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError

from run_jspell_control import (
    API_HOST,
    API_KEY_NAME,
    API_URL,
    collect_all,
    collect_passage,
    load_local_api_key,
    process_response,
    request_jspell,
    safe_http_error_detail,
    utf16_offset_to_index,
)


class RapidApiKeyTests(unittest.TestCase):
    def test_loads_header_named_key_from_process_environment(self):
        with patch.dict(os.environ, {API_KEY_NAME: "test-key"}, clear=True):
            self.assertEqual(load_local_api_key(), "test-key")

    def test_loads_header_named_key_from_dotenv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text(
                f'{API_KEY_NAME}="test-key"\n',
                encoding="utf-8",
            )
            with (
                patch("run_jspell_control.ROOT", root),
                patch.dict(os.environ, {}, clear=True),
            ):
                self.assertEqual(load_local_api_key(), "test-key")

    def test_reports_header_key_name_when_missing(self):
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("run_jspell_control.ROOT", Path(temp_dir)),
            patch.dict(os.environ, {}, clear=True),
        ):
            with self.assertRaisesRegex(RuntimeError, "x-rapidapi-key"):
                load_local_api_key()


class JSpellResponseTests(unittest.TestCase):
    def test_applies_first_suggestion_once_using_utf16_offsets(self):
        text = "\U0001F600 speling typo"
        response = {
            "elements": [{
                "errors": [
                    {"word": "typo", "position": 11, "suggestions": ["type", "typos"]},
                    {"word": "speling", "position": 3, "suggestions": ["spelling"]},
                ]
            }]
        }

        result = process_response(text, response)

        self.assertEqual(result["text"], "\U0001F600 spelling type")
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
            utf16_offset_to_index("\U0001F600word", 1)

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


class JSpellSuiteCollectionTests(unittest.TestCase):
    def test_collection_records_request_timestamps_in_utc(self):
        response = {"elements": [{"errors": []}]}
        with patch("run_jspell_control.request_jspell", return_value=response):
            result = collect_passage("A test passage.", "test-key")

        started = datetime.fromisoformat(result["request_started_at_utc"])
        completed = datetime.fromisoformat(result["request_completed_at_utc"])
        self.assertEqual(started.utcoffset().total_seconds(), 0)
        self.assertEqual(completed.utcoffset().total_seconds(), 0)
        self.assertLessEqual(started, completed)

    def test_collection_only_includes_current_h_suite(self):
        units = [
            {"id": "H-01", "input": "A test passage."},
            {"id": "H-02", "input": "Another test passage."},
        ]
        with (
            patch("run_jspell_control.UNSEEN_BENCHMARK_UNITS", units),
            patch(
                "run_jspell_control.collect_passage",
                return_value={"text": "Corrected text.", "lat": 1.0},
            ),
            patch("run_jspell_control.time.sleep"),
        ):
            results = collect_all("test-key")

        self.assertEqual(set(results["h_suite"]), {"H-01", "H-02"})
        self.assertNotIn("blind_v3", results)
        self.assertEqual(results["benchmark_metadata"]["request_count"], 2)
        metadata = results["benchmark_metadata"]
        started = datetime.fromisoformat(metadata["run_started_at_utc"])
        completed = datetime.fromisoformat(metadata["run_completed_at_utc"])
        self.assertLessEqual(started, completed)
        self.assertEqual(metadata["collection_mode"], "api")
        self.assertEqual(metadata["gateway"], "RapidAPI")


if __name__ == "__main__":
    unittest.main()
