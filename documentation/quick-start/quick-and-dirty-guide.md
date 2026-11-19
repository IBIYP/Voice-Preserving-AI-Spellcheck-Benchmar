# Quick and Dirty Guide for Running the Benchmark

This is a quick, informal way to try the v0.4 benchmark and its fresh repeat
set. It is not the official collection method, and the v0.5 protocol is still
a draft.

**Important:** `benchmark_4pillars_hybrid.py` scores saved v0.4 outputs; it
does not fetch results from services. For a fresh API run, use the separate
H-suite repeat workflow below. It preserves the original scorecard and saves
new results separately.

## Run a fresh H-suite repeat

The repeat set in
[`h_suite_repeat_v1.json`](../../benchmark_data/h_suite_repeat_v1.json) has ten
new passages, with the same 49 spelling and 12 grammar targets as the original
H-suite. The collector sends each repeat passage to BCorrect, TextGears, and
JSpell Cloud API. It also runs JSpell Cloud API on the original H-suite as a
same-route control; this is separate from the original JSpell free web-checker
result.

Configure these names in the process environment or the ignored `.env` file:

```text
BCORRECT_API_KEY=...
TEXTGEARS_API_KEY=...
JSPELL_RAPIDAPI_KEY=...
```

`x-rapidapi-key` can be used in place of `JSPELL_RAPIDAPI_KEY`. Keep real keys
local; do not paste them into chat or commit them. From the repository root,
run:

```bash
python run_h_suite_repeat.py
```

The run makes ten requests each to BCorrect and TextGears, plus twenty JSpell
requests for the old-suite control and new repeat set. It stores raw responses
in `raw_results/h_suite_repeat_v1_runs.json` and scores in
`raw_results/h_suite_repeat_v1_scores.json`. If interrupted, continue without
repeating completed requests:

```bash
python run_h_suite_repeat.py --resume
```

If JSpell Cloud API denies access, do not try to bypass the block. You can
finish the BCorrect and TextGears comparison without JSpell and clearly mark
the same-route control as blocked:

```bash
python run_h_suite_repeat.py --resume --skip-jspell
```

After JSpell access is restored, retry the control requests with
`python run_h_suite_repeat.py --resume --retry-jspell`.

For JSpell's request body, key handling, and HTTP 403 troubleshooting, see the
[JSpell RapidAPI setup notes](../../Docs/providers/JSPELL_RAPIDAPI_SETUP.md).

The repeat scorecard uses the existing v0.4 scoring weights, but it is a
separate result and does not replace the original public leaderboard. API
availability, plan limits, and terms can change; check them before running.

## Phase 1: Set up RapidAPI and run the baseline

1. Create or sign in to [RapidAPI](https://rapidapi.com/), then open:
   - [TextGears](https://rapidapi.com/Textgears/api/textgears)
   - [JSpell Checker](https://rapidapi.com/page-scholar-inc-page-scholar-inc-default/api/jspell-checker)
   - [BCorrect](https://rapidapi.com/BCSC/api/bcorrect-api)
2. Subscribe to a free plan for each service **if one is offered and suits
   your test**. For a small test, a free plan will probably be enough; check
   current quotas, especially for lots of text. Use each API's current docs or
   test console to submit requests.
3. To run the JSpell Cloud API collector, put your RapidAPI app key in `.env`
   at the repository root. The file should contain this line; replace the
   placeholder locally. Never put a real key in this guide or commit or share
   it:

   ```text
   x-rapidapi-key=YOUR_RAPIDAPI_APP_KEY
   ```

4. From the repository root, optionally collect the ten JSpell API outputs:

   ```bash
   python run_jspell_control.py
   ```

   This makes ten API requests and saves to
   `raw_results/jspell_control_outputs.json`. It does **not** feed into the
   scorecard automatically.
5. Run the original scorecard:

   ```bash
   python benchmark_4pillars_hybrid.py
   ```

   This checks the included cached results; it makes no API calls and does not
   read `jspell_control_outputs.json`. The scorecard's JSpell entry is the
   free **web checker**, not the RapidAPI Cloud API.

## Phase 2: Collect web-checker results and rerun

1. Use the same ten H-suite passages defined by
   [`UNSEEN_BENCHMARK_UNITS`](../../benchmark_4pillars_hybrid.py) with
   [DeepL Write](https://www.deepl.com/en/write), [Sapling](https://sapling.ai/grammar-check),
   and Grammarly's web checker. Save each output unchanged. For Sapling, apply
   the first suggestion for each issue once; this is a consistency rule, not
   a claim that its first suggestion is always right.
2. In a separate copy or branch, update the saved JSON outputs locally. The
   main cache, `raw_results/unseen_10_domains_live_run.json`, is organised by
   passage ID. In VS Code, find an ID such as `H-01`, then its engine name, and
   replace only that engine's `text` with the full corrected passage. Use
   `TextGears API` or `BCorrect (FMM)` for your Phase 1 results, and `DeepL
   Write` or `Sapling Grammar Checker` for these results. Do this for each
   passage you collected; don't change the source input or duplicate an engine
   key.

   For example, this is the TextGears part of the `H-01` entry. The actual file
   has other engines under `H-01` too, so replace only the `text` value:

   ```json
   {
     "H-01": {
       "TextGears API": {
         "text": "Paste the complete corrected passage here",
         "lat": null
       }
     }
   }
   ```

   The other saved outputs are separate files: in
   `raw_results/jspell_web_checker_outputs.json`, replace
   `four_pillar[H-ID].text` for JSpell's free web checker. In
   `raw_results/grammarly_web_checker_outputs.json`, replace
   `four_pillar[H-ID].text` for Grammarly; update its collection date and keep
   the required `web_demo` and complete-H-suite metadata.

   Keep all ten passages (`H-01` to `H-10`) and all seven engine outputs; the
   scorecard rejects incomplete coverage. Set latency to `null` unless you
   measured it. The JSpell Cloud API file from Phase 1 is not a substitute
   for the JSpell web-checker file.
3. Rerun the scorecard:

   ```bash
   python benchmark_4pillars_hybrid.py
   ```

The scorecard writes `raw_results/blind_4pillars_eval_run_v4.json`. Record the
collection date, service, plan, language setting and version (if shown).
If you refresh only some services, the results have different collection
dates; note that when comparing them. Check provider terms before sharing
outputs, and never submit private or sensitive text.

For formal requirements, see the [reproduction guide](../reproduction-guide.md).
For a custom essay instead of the H-suite, see
[Trying Your Own Test Data](trying-your-own-test-data.md).

## Found something out of date?

Services, plans, links and benchmark instructions can change. If you spot an
outdated detail, please let us know by opening an issue or suggesting an edit.

## Legal disclaimer

This informal guide is not legal or professional advice, nor an endorsement by
any provider. Product names belong to their owners; this project is not
affiliated with them. Services, terms, and prices can change. Check them
yourself, protect private information and API keys, and verify outputs. The
guide is provided “as is”; nothing here limits responsibilities that cannot
lawfully be limited. Ask a qualified lawyer about your situation.

### Selected legal context

Speech and press protections make room for reporting and criticism, but do
not give every comparison blanket immunity. Calling a report “independent
journalism” does not establish a legal status. These examples are not a full
review of any country's laws.

- **United States:** The First Amendment limits government restrictions on
  speech and press; it does not prevent all private claims. The FTC Act can
  apply to unfair or deceptive commercial promotions. Copyright fair use may
  cover criticism or reporting, but depends on the circumstances.
- **United Kingdom:** Article 10, through the Human Rights Act 1998, protects
  expression subject to lawful limits. The Digital Markets, Competition and
  Consumers Act 2024 covers unfair commercial practices; the CAP Code sets
  rules for advertising comparisons. The Defamation Act 2013 has a
  public-interest defence in England and Wales, not an automatic pass for
  anything labelled journalism.
- **Canada:** Charter section 2(b) protects expression and press freedom
  against government action. The Competition Act addresses materially false
  or misleading claims made to promote products or business interests.

Keep methods and evidence, distinguish findings from opinion, correct errors,
and disclose relevant funding, free access, or affiliate links. For sources,
see the [U.S. Bill of Rights](https://www.archives.gov/founding-docs/bill-of-rights-transcript),
[FTC advertising guidance](https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business),
and [Copyright Office Fair Use Index](https://www.copyright.gov/fair-use/);
the [UK Human Rights Act](https://www.legislation.gov.uk/ukpga/1998/42/schedule/1/part/I),
[Digital Markets, Competition and Consumers Act 2024](https://www.legislation.gov.uk/ukpga/2024/13/part/4/chapter/1),
[CAP Code](https://www.asa.org.uk/type/non_broadcast/code_section/03.html),
and [Defamation Act section 4](https://www.legislation.gov.uk/ukpga/2013/26/section/4);
and the [Canadian Charter](https://www.justice.gc.ca/eng/csj-sjc/rfc-dlc/ccrf-ccdl/check/art2b.html)
and [Competition Act](https://laws-lois.justice.gc.ca/eng/acts/C-34/section-74.01.html).
Laws change; check current sources and get local legal advice.
