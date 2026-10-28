# Contributing

## Before you start

Read `CLAUDE.md`. It lists five invariants that, when broken, fail silently at build time and
produce a wrong product. The versification lock and the ASCII rule in particular have both
already caused real bugs.

## Setup

```bash
make dev-deps      # Playwright, the only dev dependency
make serve         # http://localhost:8000
```

The app cannot be opened from `file://` — it fetches its data and browsers block that on file
URLs.

## Before every commit

```bash
make verify && make check
```

`verify` checks data integrity: book offsets contiguous, every chapter the right verse count
in every translation, every cross-reference target in range, every journey stop present in
the gazetteer, and `app/index.html` still pure ASCII. It takes about a second.

`check` renders all five views headless (26 assertions, 8 screenshots with --shots) and fails on
any console or page error, plus asserts the behaviours that have broken before — the trail leaking outside the reader, mojibake in
the verse quote, a canvas sized before its container was visible, horizontal scroll at phone
width.

## Changing the data

Regenerating is a six-script pipeline with a strict order (`make data`). `geo.py` must run
before `spans.py`, and `spans.py` before `journeys.py`; out of order you get stale output and
no error.

Data files are committed deliberately. The app is static, GitHub Pages serves it directly,
and vendoring the output is what lets someone clone and run with no build step.

## Scope

Proposals that add a server need to say who pays for it and why the feature cannot be done
statically. The static design is what makes the app free to run, and free was the point.
