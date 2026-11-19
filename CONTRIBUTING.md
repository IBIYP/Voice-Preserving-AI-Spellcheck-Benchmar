# Help Out (Volunteer Guide)

This benchmark is put together by volunteers who care about keeping human voice
in writing. You don't need to be an engineer or an NLP researcher to help, most
of the best work here is just reading messy paragraphs and checking if a tool
fixed the typos without ruining how the writer sounds.

## Easy ways to pitch in

- **Write fresh test passages:** Help us build the next 10-passage H-suite
  batch. Real-sounding writing (casual banter, regional voice, technical notes,
  sports, fiction) with natural typos is the hardest thing to get right.
- **Run a web checker:** Some tools (like Grammarly, Sapling, DeepL Write, or
  JSpell) don't have easy free APIs. Running a frozen batch through a web demo
  and opening an issue with the exact outputs helps everyone.
- **Call out unfair scoring:** If you see a tool get dinged for a fair UK/US
  spelling or a reasonable fix, open an issue and tell us.
- **Add or update an engine:** Tool makers and users are welcome to submit
  updated runs or suggest better settings.

## A few ground rules

- **No private or sensitive text:** Only submit text that is okay to publish.
- **No API keys or secrets:** Keep keys in your local `.env` (never commit them).
- **Keep it honest:** Don't cherry-pick passages to help or hurt any tool, and
  don't guess missing numbers (like latency) — just mark them `null` or `n/a`.
- **Keep it friendly:** We're testing tools in good faith, not dunking on anyone.

## Quick local check

If you edit code or test data, run the unit tests before opening a PR:

```bash
python -m unittest discover -s tests
```

Not sure where to start? Just open an issue and say hi — we're happy to point
you to something small.
