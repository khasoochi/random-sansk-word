#!/usr/bin/env python3
"""Smoke tests for the Flask app: pages, dictionary API, and word games."""

import sys
import json

try:
    from app import app, DICTIONARY_DATA, WORDLE_PUZZLES, SCRAMBLE_PUZZLES, CROSSWORD_PUZZLES
    print("✓ App imported successfully")
except Exception as e:
    print(f"✗ Failed to import app: {e}")
    sys.exit(1)

print(f"✓ Dictionary loaded with {len(DICTIONARY_DATA)} entries")
print(f"✓ Puzzles loaded: {len(WORDLE_PUZZLES)} wordle, "
      f"{len(SCRAMBLE_PUZZLES)} scramble, {len(CROSSWORD_PUZZLES)} crossword")

failures = []


def check(label, condition):
    status = "✓" if condition else "✗"
    print(f"{status} {label}")
    if not condition:
        failures.append(label)


with app.test_client() as client:
    for path in ('/', '/random', '/search', '/learn',
                 '/games/wordle', '/games/scramble', '/games/crossword'):
        r = client.get(path)
        check(f"page {path} -> 200", r.status_code == 200)

    r = client.get('/api/random?count=3')
    data = json.loads(r.data)
    check("random API returns 3 words", data.get('success') and data.get('count') == 3)

    r = client.get('/api/stats')
    data = json.loads(r.data)
    check("stats API has total_words", data.get('total_words', 0) > 0)

    r = client.get('/api/search?q=dharma')
    data = json.loads(r.data)
    check("search (transliteration) finds results", data.get('success') and data.get('count', 0) > 0)

    r = client.get('/api/search?q=^%E0%A4%A7%E0%A4%B0.*&regex=1')
    data = json.loads(r.data)
    check("regex search succeeds", data.get('success') is True)

    r = client.get('/api/search?q=(&regex=1')
    data = json.loads(r.data)
    check("invalid regex returns success:false", data.get('success') is False)

    r = client.get('/api/suggest?q=dhar')
    data = json.loads(r.data)
    check("suggest returns results", data.get('success') and data.get('count', 0) > 0)

    # Wordle: new -> guess -> solved with the real answer, never leaked up front
    r = client.get('/api/games/wordle/new')
    puzzle = json.loads(r.data)
    check("wordle/new has no answer fields", 'word' not in puzzle and 'aksharas' not in puzzle)
    reveal = json.loads(client.get(f"/api/games/wordle/{puzzle['id']}/reveal").data)
    guess = json.loads(client.post('/api/games/wordle/guess',
                                    json={'id': puzzle['id'], 'guess': reveal['aksharas']}).data)
    check("wordle correct guess solves puzzle", guess.get('solved') is True)

    # Scramble: new -> check with real answer
    r = client.get('/api/games/scramble/new')
    puzzle = json.loads(r.data)
    check("scramble/new has no answer fields", 'word' not in puzzle and 'aksharas' not in puzzle)
    reveal = json.loads(client.get(f"/api/games/scramble/{puzzle['id']}/reveal").data)
    result = json.loads(client.post('/api/games/scramble/check',
                                     json={'id': puzzle['id'], 'order': reveal['aksharas']}).data)
    check("scramble correct order is marked correct", result.get('correct') is True)

    # Crossword: new -> full solve via reveal
    r = client.get('/api/games/crossword/new')
    puzzle = json.loads(r.data)
    check("crossword/new words omit letters", all('aksharas' not in w for w in puzzle['words']))
    reveal = json.loads(client.get(f"/api/games/crossword/{puzzle['id']}/reveal").data)
    result = json.loads(client.post('/api/games/crossword/check',
                                     json={'id': puzzle['id'], 'cells': reveal['cells']}).data)
    check("crossword full solution is solved", result.get('solved') is True)

if failures:
    print(f"\n❌ {len(failures)} check(s) failed: {failures}")
    sys.exit(1)

print("\n✅ All checks passed.")
