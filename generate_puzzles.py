#!/usr/bin/env python3
"""
Generate Devanagari word-game puzzles from the enriched Sanskrit dictionary:
  - Wordle  (guess the word, akshara by akshara, with green/yellow/gray feedback)
  - Scramble (rearrange shuffled aksharas back into the original word)
  - Crossword (small grid of intersecting words, built from shared aksharas)

Key design decision: Devanagari is an abugida, so the "letter" unit for these
games must be an akshara (orthographic syllable, e.g. "क्ष", "स्कृ"), not a
raw Unicode codepoint (a lone matra like 'ि' is meaningless on its own). All
three games operate on devanagari_utils.split_aksharas() output.

Run this to (re)generate puzzles/*.json. Increase --wordle/--scramble/--crossword
counts, or re-run with a different --seed, to produce more puzzles later.
"""

import json
import random
import argparse

from devanagari_utils import (
    split_aksharas, is_devanagari, clean_english_hint, clean_hindi_hint, best_hint,
)

import re

MAX_HINT_LEN = 140
_TRAILING_DEVA_PAREN = re.compile(r'\s*\([^)]*[ऀ-ॿ][^)]*\)\s*$')


def trim(text, n=MAX_HINT_LEN):
    text = text.strip()
    # A semicolon usually separates the core gloss from an illustrative
    # Sanskrit citation ("A river, stream; फेनायमानं ... Śi.3.72") -- prefer
    # cutting there so the hint reads as a clean phrase, not a footnote.
    semi = text.find(';')
    if 8 <= semi <= n:
        text = text[:semi].strip()
    text = _TRAILING_DEVA_PAREN.sub('', text).strip()
    if len(text) <= n:
        return text
    return text[:n].rsplit(' ', 1)[0] + '...'


def has_enough_latin(text, min_letters=5):
    """Guard against corrupted/garbled entries that are pure Devanagari
    noise with no actual English gloss content."""
    return sum(1 for c in text if c.isascii() and c.isalpha()) >= min_letters


def load_candidates(min_ak=2, max_ak=6):
    """Load and filter dictionary entries suitable for word games:
    pure Devanagari (no digits/Latin/spaces), reasonable syllable length,
    and non-trivial meanings on both sides."""
    with open('sanskrit_dictionary.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    candidates = []
    seen = set()
    for e in data:
        word = e['sanskrit']
        if word in seen:
            continue
        if ' ' in word or any(ord(c) < 128 for c in word):
            continue
        if not is_devanagari(word):
            continue

        # Use only the safely-cleaned gloss (headword/etymology stripped) as
        # the puzzle hint -- the raw text leads with the word's own root,
        # which would spoil the answer.
        hint_en = best_hint(e['english_meanings'], clean_english_hint)
        hint_hi = best_hint(e['hindi_meanings'], clean_hindi_hint)
        if len(hint_en) < 8 or not hint_hi or not has_enough_latin(hint_en):
            continue
        # Belt-and-braces: reject if the hint still contains the answer word.
        if word in hint_en or word in hint_hi:
            continue

        aksharas = split_aksharas(word)
        if not (min_ak <= len(aksharas) <= max_ak):
            continue
        seen.add(word)
        candidates.append({
            'sanskrit': word,
            'roman': e.get('roman', ''),
            'gender': e['gender'],
            'aksharas': aksharas,
            'hint_en': trim(hint_en),
            'hint_hi': trim(hint_hi),
        })
    return candidates


# --------------------------------------------------------------------------
# Wordle
# --------------------------------------------------------------------------

def make_wordle_puzzles(candidates, count, rng):
    pool = [c for c in candidates if 3 <= len(c['aksharas']) <= 5]
    rng.shuffle(pool)
    puzzles = []
    for i, c in enumerate(pool):
        if len(puzzles) >= count:
            break
        puzzles.append({
            'id': f'wl{i:04d}',
            'word': c['sanskrit'],
            'roman': c['roman'],
            'aksharas': c['aksharas'],
            'length': len(c['aksharas']),
            'gender': c['gender'],
            'hint_en': c['hint_en'],
            'hint_hi': c['hint_hi'],
        })
    return puzzles


# --------------------------------------------------------------------------
# Scramble
# --------------------------------------------------------------------------

def make_scramble_puzzles(candidates, count, rng, exclude_words=()):
    pool = [c for c in candidates if 3 <= len(c['aksharas']) <= 6 and c['sanskrit'] not in exclude_words]
    rng.shuffle(pool)
    puzzles = []
    for i, c in enumerate(pool):
        if len(puzzles) >= count:
            break
        aksharas = c['aksharas']
        scrambled = aksharas[:]
        tries = 0
        while scrambled == aksharas and tries < 10:
            rng.shuffle(scrambled)
            tries += 1
        puzzles.append({
            'id': f'sc{i:04d}',
            'word': c['sanskrit'],
            'roman': c['roman'],
            'aksharas': aksharas,
            'scrambled': scrambled,
            'gender': c['gender'],
            'hint_en': c['hint_en'],
            'hint_hi': c['hint_hi'],
        })
    return puzzles


# --------------------------------------------------------------------------
# Crossword
# --------------------------------------------------------------------------

GRID_SIZE = 13
MAX_WORDS_PER_GRID = 8
MIN_WORDS_PER_GRID = 4


def fits(grid, aksharas, row, col, direction, size):
    if row < 0 or col < 0:
        return False
    if direction == 'across':
        if col + len(aksharas) > size:
            return False
        # cell immediately before/after the word must be empty (word boundary)
        if (row, col - 1) in grid or (row, col + len(aksharas)) in grid:
            return False
    else:
        if row + len(aksharas) > size:
            return False
        if (row - 1, col) in grid or (row + len(aksharas), col) in grid:
            return False

    crossed = False
    for k, ak in enumerate(aksharas):
        r = row + (k if direction == 'down' else 0)
        c = col + (k if direction == 'across' else 0)
        if (r, c) in grid:
            if grid[(r, c)] != ak:
                return False
            crossed = True
        else:
            # a perpendicular neighbour cell must be empty, to avoid
            # accidentally forming an unintended adjacent word
            if direction == 'across':
                if (r - 1, c) in grid or (r + 1, c) in grid:
                    return False
            else:
                if (r, c - 1) in grid or (r, c + 1) in grid:
                    return False
    return crossed


def try_build_one_crossword(pool, rng, target_words=MAX_WORDS_PER_GRID, size=GRID_SIZE):
    seed = rng.choice(pool)
    grid = {}
    placed = []

    start_col = (size - len(seed['aksharas'])) // 2
    row = size // 2
    for k, ak in enumerate(seed['aksharas']):
        grid[(row, start_col + k)] = ak
    placed.append({'entry': seed, 'row': row, 'col': start_col, 'dir': 'across'})
    used = {seed['sanskrit']}

    remaining = [c for c in pool if c['sanskrit'] not in used]
    rng.shuffle(remaining)

    for cand in remaining:
        if len(placed) >= target_words:
            break
        cand_ak = cand['aksharas']
        options = []
        for p in placed:
            p_ak = p['entry']['aksharas']
            new_dir = 'down' if p['dir'] == 'across' else 'across'
            for i, a in enumerate(p_ak):
                for j, b in enumerate(cand_ak):
                    if a != b:
                        continue
                    if p['dir'] == 'across':
                        inter_row, inter_col = p['row'], p['col'] + i
                        new_row, new_col = inter_row - j, inter_col
                    else:
                        inter_row, inter_col = p['row'] + i, p['col']
                        new_row, new_col = inter_row, inter_col - j
                    options.append((new_row, new_col, new_dir))
        rng.shuffle(options)
        for (nr, nc, ndir) in options:
            if fits(grid, cand_ak, nr, nc, ndir, size):
                for k, ak in enumerate(cand_ak):
                    r = nr + (k if ndir == 'down' else 0)
                    c = nc + (k if ndir == 'across' else 0)
                    grid[(r, c)] = ak
                placed.append({'entry': cand, 'row': nr, 'col': nc, 'dir': ndir})
                used.add(cand['sanskrit'])
                break

    if len(placed) < MIN_WORDS_PER_GRID:
        return None

    # Trim to bounding box.
    rows = [p['row'] for p in placed] + [
        p['row'] + (len(p['entry']['aksharas']) - 1 if p['dir'] == 'down' else 0) for p in placed
    ]
    cols = [p['col'] for p in placed] + [
        p['col'] + (len(p['entry']['aksharas']) - 1 if p['dir'] == 'across' else 0) for p in placed
    ]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)

    for p in placed:
        p['row'] -= min_r
        p['col'] -= min_c

    n_rows = max_r - min_r + 1
    n_cols = max_c - min_c + 1

    # Number words: cells shared by an across+down start get the same number.
    starts = {}
    for p in placed:
        starts.setdefault((p['row'], p['col']), []).append(p)
    words = []
    number = 1
    for key in sorted(starts.keys()):
        for p in starts[key]:
            e = p['entry']
            words.append({
                'number': number,
                'direction': p['dir'],
                'row': p['row'],
                'col': p['col'],
                'length': len(e['aksharas']),
                'aksharas': e['aksharas'],
                'word': e['sanskrit'],
                'roman': e['roman'],
                'clue_en': e['hint_en'],
                'clue_hi': e['hint_hi'],
            })
        number += 1

    return {'rows': n_rows, 'cols': n_cols, 'words': words}


def make_crossword_puzzles(candidates, count, rng, attempts_per_puzzle=400):
    pool = [c for c in candidates if 2 <= len(c['aksharas']) <= 6]
    puzzles = []
    attempts = 0
    max_total_attempts = attempts_per_puzzle * count * 3
    while len(puzzles) < count and attempts < max_total_attempts:
        attempts += 1
        result = try_build_one_crossword(pool, rng)
        if result:
            result['id'] = f'cw{len(puzzles):04d}'
            puzzles.append(result)
    return puzzles


# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wordle', type=int, default=40)
    parser.add_argument('--scramble', type=int, default=40)
    parser.add_argument('--crossword', type=int, default=12)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    candidates = load_candidates()
    print(f'Loaded {len(candidates)} candidate words for puzzles.')

    wordle = make_wordle_puzzles(candidates, args.wordle, rng)
    print(f'Generated {len(wordle)} Wordle puzzles.')

    scramble = make_scramble_puzzles(candidates, args.scramble, rng,
                                      exclude_words={w['word'] for w in wordle})
    print(f'Generated {len(scramble)} Scramble puzzles.')

    crossword = make_crossword_puzzles(candidates, args.crossword, rng)
    print(f'Generated {len(crossword)} Crossword puzzles '
          f'(avg {sum(len(c["words"]) for c in crossword) / max(1, len(crossword)):.1f} words/grid).')

    import os
    os.makedirs('puzzles', exist_ok=True)
    with open('puzzles/wordle.json', 'w', encoding='utf-8') as f:
        json.dump(wordle, f, ensure_ascii=False, indent=2)
    with open('puzzles/scramble.json', 'w', encoding='utf-8') as f:
        json.dump(scramble, f, ensure_ascii=False, indent=2)
    with open('puzzles/crossword.json', 'w', encoding='utf-8') as f:
        json.dump(crossword, f, ensure_ascii=False, indent=2)

    print('Saved puzzles/wordle.json, puzzles/scramble.json, puzzles/crossword.json')


if __name__ == '__main__':
    main()
