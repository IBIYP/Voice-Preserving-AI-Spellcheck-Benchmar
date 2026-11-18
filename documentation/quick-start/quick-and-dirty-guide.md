# Quick and Dirty Guide for Running the Benchmark

So, you want to try the benchmark fast. Fair enough. This is a **temporary,
informal guide**, not the best or official way to run the benchmark—but if you
just want a quick look, it'll do.

The short version: give every tool the same text, keep its output exactly as
returned (with the one exception below), and write down what you did.

## 1. The RapidAPI options

Create or sign in to RapidAPI, then open these API pages. See the [Notes](#notes)
at the end for plan and key details:

- [TextGears](https://rapidapi.com/Textgears/api/textgears)
- [JSpell Checker](https://rapidapi.com/page-scholar-inc-page-scholar-inc-default/api/jspell-checker)
- [BCorrect](https://rapidapi.com/BCSC/api/bcorrect-api)

## 2. Pick one text and keep it consistent

Choose a test passage that you are allowed to submit to these services. Don't
paste private, confidential, or personal writing into an external checker.
Use the **same original passage** for every service, and save a copy before
you start—future-you will appreciate the control group.

For an informal run, you can use a passage from the public draft dataset at
[`benchmark_data/v0.5_anchor_draft.json`](../../benchmark_data/v0.5_anchor_draft.json).
That dataset is still a draft, though: its review is not complete, and using
it this way does **not** make your run an official v0.5 result.

## 3. Try the web checkers

### Sapling

Open [Sapling's grammar checker](https://sapling.ai/grammar-check) and paste in
the original passage. For this quick-and-dirty method, apply the **first
suggestion for each flagged issue**. Don't recheck the edited text; save the
result after that one pass. This is a simple rule to make the experiment
repeatable-ish, not a claim that the first suggestion is always the right one.

### DeepL Write

Open [DeepL Write](https://www.deepl.com/en/write) and submit the same original
passage. Save the returned text as-is. DeepL Write may rewrite more than
individual errors, so don't tidy it up by hand before comparing.

## 4. Keep a tiny lab notebook

For each tool, note the date, product/page or API route, plan or access tier,
language/locale setting, and the exact output. Keep the original text beside
the outputs. If the service shows a product or model version, record it; if it
doesn't, write “not reported” instead of guessing. Check the provider's terms
before sharing or publishing any output.

## 5. What this does and doesn't tell you

This method is useful for a fast spot-check. It is not a controlled,
automatically scored, or fully reproducible benchmark: web interfaces and API
responses can change, accounts may have different limits, and “first
suggestion” is a deliberately crude choice. Free access points, quotas,
endpoints, and product behavior can all change without this guide noticing.

Also, this manual process does not feed its results into the repository's
scorer. The v0.5 protocol is currently a draft, is not frozen, and has no
collected outputs; do not label these results as official v0.5 scores. For the
current local checks and the formal collection requirements, see the
[reproduction guide](../reproduction-guide.md) and
[v0.5 protocol draft](../benchmark-v0.5-draft.md).

If you just want to run the existing offline scorecard and its tests, from the
repository root:

```bash
python benchmark_4pillars_hybrid.py
python -m unittest discover -s tests -v
```

Those commands use the outputs already included in the repository; they do not
call the services above. The
[JSpell collector](../../run_jspell_control.py) makes external API requests,
so review it before running it.

There you go: quick, dirty, and honest about being quick and dirty.


## Notes

- Free plans, quotas, and access rules change; choose a current plan that fits
  your test. Use each API's documentation or test console for request steps.
- Put your RapidAPI app key in the root `.env` file:

  ```text
  x-rapidapi-key=your_rapidapi_key_here
  ```

- The JSpell collector reads this same `x-rapidapi-key` name. TextGears and
  BCorrect are not wired into collectors here. RapidAPI keys are app-specific,
  and some APIs may also require a separate provider key. Keep all keys private.
  See [RapidAPI's key guide](https://docs.rapidapi.com/docs/keys-and-key-rotation).

## Legal disclaimer

This guide is informal, general-purpose commentary for convenience. It is not
legal, professional, technical, security, financial, or procurement advice, and
it is not an official recommendation or endorsement by any provider. Any
opinions or suggestions here are just that: informal suggestions, not official
positions or advice.

TextGears, JSpell, BCorrect, Sapling, DeepL, RapidAPI, and their products and
marks belong to their respective owners. Mentioning or linking to them does
not mean this project is affiliated with, sponsored by, or endorsed by them.
They may change, restrict, rename, or discontinue products, pages, endpoints,
plans, pricing, quotas, and terms at any time. We do not control or guarantee
any third-party service, its availability, its security, its output, or the
continued accuracy of links and instructions in this guide.

You are responsible for deciding whether a service is suitable and for
reviewing its current terms, privacy policy, applicable laws, data rights, and
any costs or usage limits before using it. Do not submit confidential,
personal, or otherwise sensitive information unless you have the right to do
so and have checked that the service's terms and your obligations allow it.
Keep API keys secret, and check your account for usage or charges. Verify
outputs yourself; they can be incomplete, incorrect, or different on another
day.

The guide and its suggestions are provided “as is,” without a promise that
they are accurate, complete, current, suitable for your purpose, or
error-free. To the fullest extent permitted by applicable law, the project
contributors disclaim responsibility for losses or damages arising from use
of this guide, the benchmark, or any third-party service. Nothing here is
intended to exclude or limit a responsibility that cannot legally be excluded
or limited.

In short: this is a friendly shortcut, not a lawyer in a trench coat. This
disclaimer is not a guarantee of legal protection; if you need advice about
your particular situation, ask a qualified lawyer.

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
  fact-specific analysis not an automatic permission slip.
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
