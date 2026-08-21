# संस्कृत शब्दकोश — Sanskrit Dictionary & Word Games

A Flask web app built on the Apte Sanskrit–English–Hindi dictionary: search
words (Devanagari, transliteration, or regex), flip through flashcards, and
play three Devanagari-first word games — Wordle, Scramble, and Crossword —
all built on **aksharas** (orthographic syllables) rather than raw Unicode
characters, since Devanagari is an abugida and a single glyph is rarely a
meaningful "letter" on its own.

## Features

- 🔍 **Search** — by Devanagari, transliteration ("dharma" finds धर्म), or
  regex (e.g. `^धर्म` or `.*ईश्वर.*`), with live autocomplete suggestions.
- 📖 **Learn** — flashcards: tap to flip between the word and its meanings.
- 🎲 **Random Words** — generate a batch of 1–100 random words at once.
- 🀄 **अक्षर-Wordle** — guess the word one akshara at a time, with
  green/yellow/gray feedback, using a virtual Devanagari keyboard.
- 🔤 **Word Scramble** — tap shuffled aksharas back into the right order.
- 🧩 **Crossword** — small grids of intersecting words built from shared
  aksharas, clued by meaning (never by the word itself).
- 🧹 **Cleaned cross-references** — "See XYZ" (English) / "दे* XYZ" (Hindi)
  are resolved to XYZ's actual meaning instead of leaving a dead-end pointer.
- 📱 Mobile-friendly, single CSS/JS stack, no build step.

## Dictionary Source

- `apte-sa.babylon` — Sanskrit-English dictionary
- `apte-hi.babylon` — Sanskrit-Hindi dictionary

## Data Pipeline

Three scripts turn the raw Babylon files into everything the app serves.
Re-run them in order whenever the source dictionaries change:

```bash
python3 parse_dictionaries.py   # babylon -> sanskrit_dictionary.json/.csv
python3 enrich_dictionary.py    # + transliteration, + cross-ref resolution
python3 generate_puzzles.py     # -> puzzles/{wordle,scramble,crossword}.json
```

- **`parse_dictionaries.py`** merges the two babylon files on shared
  headwords (18,051 words have entries in both), extracts gender, and pulls
  just the Hindi *gloss* out of each entry (dictionary-internal codes like
  `H1 - NP` and the etymology are discarded — see `extract_hindi_gloss`).
- **`enrich_dictionary.py`** adds a `roman` transliteration field per word
  (plain Latin, no diacritics — `dharma`, not `dharmaḥ`) and resolves
  "See X" / "दे* X" cross-references to X's actual meaning, when X is also
  in the merged dictionary.
- **`generate_puzzles.py`** builds the game content (see below). Run it
  again with different `--wordle/--scramble/--crossword` counts or
  `--seed` to generate more puzzles later — see "Generating More Puzzles".
- **`devanagari_utils.py`** is the shared library both scripts (and
  `app.py`) depend on: `split_aksharas()` (syllable segmentation),
  `transliterate()`, and the hint-cleaning helpers that strip a gloss's
  leading headword/etymology so puzzle hints don't spoil the answer.

## Installation

```bash
pip install -r requirements.txt
python3 parse_dictionaries.py
python3 enrich_dictionary.py
python3 generate_puzzles.py
python3 app.py
```

The app runs at `http://localhost:5000`. `sanskrit_dictionary.json` and
`puzzles/*.json` are committed to the repo so the app also runs as-is
without regenerating anything (only needed if you change the source data
or want more/different puzzles).

## Why aksharas, not characters?

Devanagari is an abugida: a consonant carries an inherent vowel unless
modified by a vowel sign, and consonants can stack into conjuncts via a
halant (e.g. र् + म → र्म). A "letter" a player types or guesses has to be
that whole cluster — क, धर्म's र्म, कृ — not a lone matra like "ि", which is
meaningless without a base consonant. `split_aksharas()` in
`devanagari_utils.py` implements this segmentation, and every game
(Wordle scoring, Scramble tiles, Crossword cells) operates on its output.
The on-screen keyboard (`static/js/devkeyboard.js`) lets players compose
an akshara from vowels/consonants/matras/halant one tap at a time, so the
games work without needing a native Devanagari input method.

## Generating More Puzzles

`generate_puzzles.py` is reusable — it's not a one-off script:

```bash
python3 generate_puzzles.py --wordle 60 --scramble 60 --crossword 20 --seed 7
```

It filters the dictionary for clean, spoiler-safe candidates (see
`load_candidates`), then:
- **Wordle**: picks words of 3–5 aksharas.
- **Scramble**: picks words of 3–6 aksharas, shuffles them.
- **Crossword**: greedily places words on a grid so they intersect at
  shared aksharas (`try_build_one_crossword`), retrying with different
  random seeds until enough puzzles hit the target word count.

Candidate hints are generated from the *cleaned* gloss
(`clean_english_hint` / `clean_hindi_hint`), never the raw dictionary
text, because raw entries lead with the headword's own etymology, which
would give the answer away.

## Puzzle Answer Security

Puzzle solutions are **never sent to the browser**. `/api/games/*/new`
returns only the puzzle id, length/shape, and meaning-based hints; guesses
are checked server-side (`/api/games/*/guess` or `/check`), and the
solution is only revealed via an explicit `/reveal` call (the "Give Up"
button).

## Project Structure

```
random-sansk-word/
├── app.py                     # Flask app: pages + all APIs
├── devanagari_utils.py        # akshara segmentation, transliteration, hint cleaning
├── parse_dictionaries.py      # babylon -> sanskrit_dictionary.json/.csv
├── enrich_dictionary.py       # + roman field, + cross-reference resolution
├── generate_puzzles.py        # -> puzzles/{wordle,scramble,crossword}.json
├── puzzles/                   # generated puzzle content (server-side only)
├── sanskrit_dictionary.json   # merged, enriched dictionary (18,051 words)
├── sanskrit_dictionary.csv    # same, as CSV
├── apte-sa.babylon            # source: Sanskrit-English
├── apte-hi.babylon            # source: Sanskrit-Hindi
├── templates/
│   ├── base.html              # nav + shared layout
│   ├── index.html             # dashboard home
│   ├── random.html / search.html / learn.html
│   └── wordle.html / scramble.html / crossword.html
└── static/
    ├── css/style.css
    └── js/
        ├── devkeyboard.js     # shared virtual Devanagari keyboard
        ├── nav.js / home.js / random.js / search.js / learn.js
        └── wordle.js / scramble.js / crossword.js
```

## API Reference

### Dictionary
- `GET /api/random?count=5` — random words.
- `GET /api/stats` — total word count + gender distribution.
- `GET /api/search?q=dharma&regex=0` — search by Devanagari substring,
  transliteration substring, or (if `regex=1`) a Python regex tested
  against both. Returns 400 with a message on invalid regex.
- `GET /api/suggest?q=dhar&limit=8` — autocomplete: prefix matches first,
  then substring matches, `{sanskrit, roman}` pairs only.

### Games
- `GET /api/games/wordle/new[?length=3]`, `POST /api/games/wordle/guess`
  `{id, guess: [akshara, ...]}` → `{feedback: [correct|present|absent, ...], solved}`,
  `GET /api/games/wordle/<id>/reveal`.
- `GET /api/games/scramble/new`, `POST /api/games/scramble/check`
  `{id, order: [akshara, ...]}` → `{correct}`,
  `GET /api/games/scramble/<id>/reveal`.
- `GET /api/games/crossword/new` → grid shape + clues (no letters),
  `POST /api/games/crossword/check` `{id, cells: {"r,c": akshara}}` →
  `{results: {"r,c": bool}, solved}`,
  `GET /api/games/crossword/<id>/reveal`.

## Deployment (Vercel)

`vercel.json` is already configured for the Python/Flask runtime. Push to
GitHub and import the repo in Vercel — no environment variables needed.
`sanskrit_dictionary.json` and `puzzles/*.json` are committed so the
deployed app has everything it needs without a build step. `/health`
reports dictionary/puzzle load status for debugging a failed deploy.

## License

Uses the Apte Dictionary data — ensure compliance with its usage terms.
