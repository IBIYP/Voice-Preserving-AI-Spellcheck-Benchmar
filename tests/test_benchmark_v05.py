import json
import unittest

from benchmark_v05 import (
    PROTOCOL_PATH,
    _stable_digest,
    _evaluate_sample,
    _control_result,
    _sample_records,
    _sha256_text,
    _validate_protocol,
    _validate_raw_runs,
    run_evaluation,
    score_runs,
)


def _protocol(status="frozen"):
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    protocol["metadata"]["status"] = status
    if status == "frozen":
        protocol["metadata"]["protocol_version"] = "0.5.0"
    return protocol


def _complete_cache(protocol, change=None):
    engine = "Example Engine"
    outputs = {}
    for sample_id, sample in _sample_records(protocol).items():
        text = sample["input"]
        if change:
            text = change(sample_id, text)
        outputs[sample_id] = {
            "input_sha256": _sha256_text(sample["input"]),
            "engine_outputs": {
                engine: {"text": text, "latency_ms": None}
            },
        }
    return {
        "metadata": {
            "status": "complete",
            "protocol_version": protocol["metadata"]["protocol_version"],
            "protocol_sha256": _stable_digest(protocol),
            "locale_mode": "automatic",
            "control_set_frozen_at_utc": "2026-11-16T10:00:00Z",
            "collection_started_at_utc": "2026-11-16T11:00:00Z",
            "engine_metadata": {
                engine: {
                    "product_version": "not reported",
                    "collection_route": "test fixture",
                    "source_url": "https://example.invalid",
                    "locale_setting": "not-set",
                }
            },
        },
        "outputs": outputs,
    }


class V05ProtocolTests(unittest.TestCase):
    def test_checked_in_protocol_is_a_draft_and_cannot_be_frozen_by_scorer(self):
        protocol = _protocol("draft")

        with self.assertRaisesRegex(ValueError, "draft"):
            _validate_protocol(protocol, require_frozen=True)
        with self.assertRaisesRegex(ValueError, "draft"):
            run_evaluation()

    def test_manifest_has_ten_controls_and_twenty_locale_samples(self):
        protocol = _protocol()

        _validate_protocol(protocol, require_frozen=True)
        self.assertEqual(len(protocol["passages"]), 10)
        self.assertEqual(len(_sample_records(protocol)), 20)
        self.assertEqual(
            {passage["negative_control"]["id"] for passage in protocol["passages"]},
            {f"NC-{index:02d}" for index in range(1, 11)},
        )
        self.assertEqual(
            {passage["id"] for passage in protocol["passages"]},
            {f"V05-{index:02d}" for index in range(1, 11)},
        )

    def test_dataset_license_is_separate_and_present(self):
        protocol = _protocol()
        license_metadata = protocol["metadata"]["data_license"]
        license_path = PROTOCOL_PATH.parent / license_metadata["license_file"]

        self.assertEqual(license_metadata["spdx_id"], "CC0-1.0")
        self.assertTrue(license_path.is_file())
        self.assertIn(
            "CC0 1.0 Universal",
            license_path.read_text(encoding="utf-8"),
        )

    def test_controls_distinguish_known_hits_from_unclassified_changes(self):
        control = _protocol()["passages"][0]["negative_control"]

        self.assertEqual(
            _control_result(control, "We caught the first train out of town.")["classification"],
            "known_negative_control_hit",
        )
        self.assertEqual(
            _control_result(control, "We caught the last train out of town.")["classification"],
            "preserved",
        )
        garden_control = _protocol()["passages"][1]["negative_control"]
        self.assertEqual(
            _control_result(garden_control, "The marker was gone by noon.")["classification"],
            "unclassified_change",
        )

    def test_cache_rejects_missing_sample_and_forced_locale(self):
        protocol = _protocol()
        incomplete = _complete_cache(protocol)
        del incomplete["outputs"]["V05-10-en-GB"]
        with self.assertRaisesRegex(ValueError, "sample coverage mismatch"):
            _validate_raw_runs(incomplete, protocol)

        forced = _complete_cache(protocol)
        forced["metadata"]["engine_metadata"]["Example Engine"][
            "locale_setting"
        ] = "en-US"
        with self.assertRaisesRegex(ValueError, "auto-detect or not-set"):
            _validate_raw_runs(forced, protocol)

    def test_cache_rejects_changed_protocol_input_and_engine_coverage(self):
        protocol = _protocol()

        changed_protocol = _complete_cache(protocol)
        changed_protocol["metadata"]["protocol_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "protocol digest"):
            _validate_raw_runs(changed_protocol, protocol)

        changed_input = _complete_cache(protocol)
        changed_input["outputs"]["V05-01-en-US"]["input_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Input hash mismatch"):
            _validate_raw_runs(changed_input, protocol)

        missing_engine = _complete_cache(protocol)
        del missing_engine["outputs"]["V05-01-en-US"]["engine_outputs"]["Example Engine"]
        with self.assertRaisesRegex(ValueError, "Engine coverage mismatch"):
            _validate_raw_runs(missing_engine, protocol)

    def test_cache_requires_controls_to_be_frozen_before_collection(self):
        protocol = _protocol()
        cache = _complete_cache(protocol)
        cache["metadata"]["collection_started_at_utc"] = "2026-11-16T10:00:00Z"

        with self.assertRaisesRegex(ValueError, "after the controls are frozen"):
            _validate_raw_runs(cache, protocol)

    def test_four_pillars_are_equally_weighted_and_control_hits_are_distinct(self):
        protocol = _protocol()

        def change(sample_id, text):
            if sample_id == "V05-01-en-US":
                return text.replace("last train", "first train")
            return text

        report = score_runs(protocol, _complete_cache(protocol, change))
        result = report["engine_summary"]["Example Engine"]

        self.assertEqual(result["pillars"]["negative_control_preservation"], 95.0)
        self.assertEqual(result["weights"], {
            "spelling": 25,
            "grammar": 25,
            "voice": 25,
            "negative_control_preservation": 25,
        })
        self.assertEqual(result["negative_controls"]["known_negative_control_hits"], 1)
        self.assertEqual(result["negative_controls"]["unclassified_changes"], 0)
        self.assertEqual(result["negative_controls"]["total"], 20)
        self.assertEqual(
            result["overall_score"],
            round(sum(result["pillars"].values()) / 4, 2),
        )

    def test_en_gb_dialect_target_is_not_credited_as_en_us(self):
        protocol = _protocol()
        passage = next(item for item in protocol["passages"] if item["id"] == "V05-05")
        gb_input = passage["inputs"]["en-GB"]
        wrong_locale = gb_input.replace("metre", "meter")
        correct_locale = gb_input

        wrong = _evaluate_sample(passage, "en-GB", wrong_locale)
        correct = _evaluate_sample(passage, "en-GB", correct_locale)

        self.assertEqual(
            correct["spelling_target_hits"], wrong["spelling_target_hits"] + 1
        )

    def test_every_annotation_accepts_its_declared_replacement(self):
        protocol = _protocol()

        for passage in protocol["passages"]:
            for locale in ("en-US", "en-GB"):
                corrected = passage["inputs"][locale]
                for source, target in passage["locale_spelling_targets"][locale].items():
                    corrected = corrected.replace(source, target)
                for source, target in passage["grammar_targets"].items():
                    corrected = corrected.replace(source, target)

                metrics = _evaluate_sample(passage, locale, corrected)
                self.assertEqual(
                    metrics["spelling_acc"],
                    100.0,
                    f"{passage['id']} {locale} spelling annotation",
                )
                self.assertEqual(
                    metrics["grammar_acc"],
                    100.0,
                    f"{passage['id']} {locale} grammar annotation",
                )

    def test_all_predefined_control_forms_have_exact_hits(self):
        protocol = _protocol()

        for passage in protocol["passages"]:
            control = passage["negative_control"]
            self.assertEqual(
                _control_result(control, control["protected_span"])["classification"],
                "preserved",
                f"{passage['id']} protected span",
            )
            for false_form in control["known_false_forms"]:
                self.assertEqual(
                    _control_result(control, false_form["text"])["classification"],
                    "known_negative_control_hit",
                    f"{passage['id']} false form",
                )


if __name__ == "__main__":
    unittest.main()
