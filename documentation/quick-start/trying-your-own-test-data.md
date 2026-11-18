# Trying Your Own Test Data

Got an essay full of typos and want to see what the checkers do with it? Go
for it. Just keep in mind that your personal typo obstacle course is a
**custom experiment**, not an official benchmark result.

## The easiest way: no code, no dataset surgery

1. Make a copy of the original essay before correcting anything.
2. Write down what you believe the intended corrections are. If possible, ask
   someone else to make that list before looking at tool outputs; otherwise,
   it's easy to move the goalposts after seeing what a checker suggests.
3. Submit the exact same original text to each service, following the
   [quick-and-dirty guide](quick-and-dirty-guide.md).
4. Save each result exactly as returned, along with the date, service, and
   locale or language setting.
5. Compare the outputs against your correction list. Give credit for the
   intended fixes, and note any changes to words or phrasing that were already
   correct.

Here is a short, deliberately typo-heavy sample you can copy and try:

```text
Yesturday our clas took a trip to the musuem. We packt sandwitches, but I left my jurnal on the buss. Our techer said the exibit was facinating, and we shud write about our favorate part. I chose the dinosuar room becaus the skeltons were huge.
```

For this example, the intended spelling corrections are:

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
  "favorate": "favorite",
  "dinosuar": "dinosaur",
  "becaus": "because",
  "skeltons": "skeletons"
}
```

That list is just the answer key for this sample. For your own writing, make
the answer key match what you actually meant, and don't count a preferred
style, dialect, or regional spelling as a typo just because a checker wants
to change it.

## Want the repository's offline scorecard to score it?

That's possible, but it's not a quick text swap. The existing v0.4 scorecard
defines its H-suite passages in
[`benchmark_4pillars_hybrid.py`](../../benchmark_4pillars_hybrid.py) under
`UNSEEN_BENCHMARK_UNITS`. It has no command-line option for passing in a custom
essay. Each passage's input, correction annotations, and the saved output
files have to agree.

For a **local-only experiment**:

1. Make a separate working copy or branch first. Don't replace the shared
   benchmark data or its results.
2. Add a passage with a unique ID in `UNSEEN_BENCHMARK_UNITS`, or replace a
   passage only in your local copy.
3. Put the exact original essay in `input`. Put each intended misspelling and
   accepted correction in `spelling_targets`. Add `grammar_targets` only for
   grammar issues you have deliberately identified. Keep `voice_tokens`,
   `dialect_equivalents`, and `forbidden_rewrites` aligned with what you want
   to measure; don't invent voice or grammar criteria after seeing outputs.
4. Collect new output for every engine listed in the scorecard's `ENGINES`,
   using that same exact input. The scorecard requires complete passage and
   engine coverage; old cached results for the original passage are not
   results for your new essay. Relevant files include
   `raw_results/unseen_10_domains_live_run.json`,
   `raw_results/jspell_web_checker_outputs.json`, and
   `raw_results/grammarly_web_checker_outputs.json`.
5. Remember that the existing regression tests and cached outputs are built
   around the original H-suite IDs and passages. A custom corpus may need
   matching test fixtures and output records before the scorecard will run.
   Keep those changes in your local copy and label any result as a custom
   experiment—not as a published benchmark score.

One subtle gotcha: the v0.4 composite has spelling, grammar, and voice
components. If your custom essay only tests spelling, the current scorer gives
an empty grammar-target set 100% grammar accuracy, so the composite can be
misleading. Report the spelling results on their own or design a balanced
custom test before interpreting the composite.

The v0.5 draft is a different dataset and protocol. It is not frozen or
scoreable, so don't edit it and call the result an official v0.5 run. For
official collection requirements, see the
[reproduction guide](../reproduction-guide.md).

## A few friendly guardrails

- Only send text to external services if you have the right to share it.
- Don't submit private, confidential, or sensitive writing.
- Keep API keys out of the essay, output files, screenshots, and git history.
- Provider limits and rules can change; check them before submitting a long
  essay.
- Treat the results as a snapshot. A tool can behave differently next time.

In short: bring your own typos, keep your own answer key, and please don't
make the benchmark's official data wear your experimental hat.

## Cross-border legal context (still not legal advice)

Comparative product reports and criticism are part of public discussion, and
freedom-of-expression and press protections help create room for that
discussion. But there is no worldwide “benchmark report” exemption, and
calling something journalism does not automatically make every claim lawful.
The following are only selected examples for the United States, the United
Kingdom, and Canada—not a survey of every country's laws or a ruling on this
project.

- **United States:** The First Amendment protects speech and press against
  government restrictions; it is not blanket immunity from private claims or
  other laws. Commercial promotions can also be subject to the Federal Trade
  Commission Act's rules against unfair or deceptive practices. Advertising
  claims should be truthful and supported, and endorsements may require clear
  disclosure of material connections. U.S. copyright fair use can cover
  criticism, comment, or news reporting in some circumstances, but it is a
  fact-specific analysis—not an automatic permission slip.
- **United Kingdom:** Article 10 of the European Convention on Human Rights,
  given effect through the Human Rights Act 1998, protects expression subject
  to lawful limits. The Digital Markets, Competition and Consumers Act 2024
  addresses unfair commercial practices; the CAP Code is a separate
  self-regulatory code for marketing communications and requires competitor
  comparisons in ads to be non-misleading and based on relevant, verifiable,
  representative features. The Defamation Act 2013 includes a public-interest
  defence in England and Wales, but whether it applies depends on the facts;
  that Act's section 4 is not a blanket defence for anything labelled
  journalism.
- **Canada:** Charter section 2(b) includes freedom of expression and of the
  press, generally as a limit on government action rather than a universal
  shield from private claims. The Competition Act addresses materially false
  or misleading public representations made to promote a product or business
  interest. Whether a particular report falls within those rules depends on
  its purpose and context.

Here, “independent comparative commentary” describes the project's intent; it
does not certify a legal status or guarantee that a report qualifies as
journalism under any country's law. Keep test methods and evidence available,
separate measured results from opinion, correct errors, and disclose any
funding, sponsorship, free access, affiliate links, or other relevant
connections. A disclaimer cannot fix an inaccurate claim or waive rights that
the law does not allow to be waived.

For primary references, see the [U.S. Bill of Rights](https://www.archives.gov/founding-docs/bill-of-rights-transcript),
[FTC Act and FTC advertising guidance](https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business),
and [U.S. Copyright Office Fair Use Index](https://www.copyright.gov/fair-use/);
the [Human Rights Act 1998, Schedule 1, Article 10](https://www.legislation.gov.uk/ukpga/1998/42/schedule/1/part/I),
[Digital Markets, Competition and Consumers Act 2024, Part 4, Chapter 1](https://www.legislation.gov.uk/ukpga/2024/13/part/4/chapter/1),
[CAP Code, Section 3](https://www.asa.org.uk/type/non_broadcast/code_section/03.html),
and [Defamation Act 2013, section 4](https://www.legislation.gov.uk/ukpga/2013/26/section/4);
and the [Canadian Charter, section 2(b)](https://www.justice.gc.ca/eng/csj-sjc/rfc-dlc/ccrf-ccdl/check/art2b.html)
and [Competition Act, section 74.01](https://laws-lois.justice.gc.ca/eng/acts/C-34/section-74.01.html).
Laws and official guidance change; check the current text and get qualified
local legal advice before relying on it.
