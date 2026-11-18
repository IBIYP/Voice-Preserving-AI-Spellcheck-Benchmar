# Trying Your Own Test Data

## Already running the benchmark?

Got it working and want to try your own test essay? This unofficial guide
shows how. Keep custom trials separate: they don't change the official data or
count as official results.

## Add your essay to a local scorecard

The v0.4 scorecard has no custom-text option; its H-suite is defined in
[`benchmark_4pillars_hybrid.py`](../../benchmark_4pillars_hybrid.py) under
`UNSEEN_BENCHMARK_UNITS`. Inputs, annotations, and saved outputs must match.

For a **local-only experiment**:

1. Work in a separate copy or branch; don't replace shared data or results.
2. Add a uniquely identified passage (or replace one locally) in
   `UNSEEN_BENCHMARK_UNITS`. Set `input` and exact `spelling_targets`; add only
   the grammar, voice, dialect, and over-edit annotations you can justify.
3. Collect new output for every engine and update the matching caches:
   `raw_results/unseen_10_domains_live_run.json`,
   `raw_results/jspell_web_checker_outputs.json`, and
   `raw_results/grammarly_web_checker_outputs.json`. The scorecard requires
   complete passage and engine coverage; existing tests expect the original
   H-suite.
4. Keep the result local and label it a custom experiment, not an official
   benchmark score.

The v0.4 composite gives 100% for an empty grammar target set, which can skew a
spelling-only test. Report spelling separately. The v0.5 draft is not frozen or
scoreable; see the [reproduction guide](../reproduction-guide.md).

Only submit text you may share. Keep private data and API keys out of services,
outputs, and git. Results and provider limits can change.

Bring your own typos, keep your own answer key, and leave the official data
untouched.

## Quick, no-code test

If you just want to try an essay in web checkers without editing code:

1. Keep a copy of the original essay.
2. Write an answer key before checking it; this helps prevent moving the
   goalposts after seeing suggestions.
3. Submit the same text to each service using the
   [quick-and-dirty guide](quick-and-dirty-guide.md).
4. Save each output unchanged with the date, service, and language setting.
5. Compare results with your answer key, noting missed errors and unwanted
   edits.

Try this deliberately typo-heavy sample:

```text
Yesturday our clas took a trip to the musuem. We packt sandwitches, but I left my jurnal on the buss. Our techer said the exibit was facinating, and we shud write about our favorate part. I chose the dinosuar room becaus the skeltons were huge.
```

Answer key:

```json
{
  "Yesturday": "Yesterday",
  "clas": "class",
  "musuem": "museum",
  "packt": "packed",
  "sandwitches": "sandwiches",
  "jurnal": "journal",
  "buss": "bus",
  "techer": "teacher",
  "exibit": "exhibit",
  "facinating": "fascinating",
  "shud": "should",
  "favorate": "favourite",
  "dinosuar": "dinosaur",
  "becaus": "because",
  "skeltons": "skeletons"
}
```

Define your own intended corrections first. Don't count a preferred style,
dialect, or regional spelling as an error.

## Found something out of date?

Services, plans, links and benchmark instructions can change. If you spot an
outdated detail, please let us know by opening an issue or suggesting an edit.

## Legal disclaimer

This informal guide is not legal or professional advice, nor an endorsement by
any provider. Product names belong to their owners; this project is not
affiliated with them. Laws and services change. Check current terms, protect
private information and keys, and verify results. The guide is provided “as
is”; nothing here limits responsibilities that cannot lawfully be limited.
Ask a qualified lawyer about your situation.

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

Keep evidence, distinguish findings from opinion, correct errors, and disclose
relevant funding, free access, or affiliate links. For sources, see the
[U.S. Bill of Rights](https://www.archives.gov/founding-docs/bill-of-rights-transcript),
[FTC advertising guidance](https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business),
and [Copyright Office Fair Use Index](https://www.copyright.gov/fair-use/);
the [UK Human Rights Act](https://www.legislation.gov.uk/ukpga/1998/42/schedule/1/part/I),
[Digital Markets Act](https://www.legislation.gov.uk/ukpga/2024/13/part/4/chapter/1),
[CAP Code](https://www.asa.org.uk/type/non_broadcast/code_section/03.html),
and [Defamation Act section 4](https://www.legislation.gov.uk/ukpga/2013/26/section/4);
and the [Canadian Charter](https://www.justice.gc.ca/eng/csj-sjc/rfc-dlc/ccrf-ccdl/check/art2b.html)
and [Competition Act](https://laws-lois.justice.gc.ca/eng/acts/C-34/section-74.01.html).
Check current sources and get local legal advice.
