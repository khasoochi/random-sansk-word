#!/usr/bin/env python3
"""
Enrich sanskrit_dictionary.json with:
  1. A 'roman' transliteration field (for Latin-script / transliteration search).
  2. Resolved cross-references: "See X" (English) and "दे* X" (Hindi) are
     replaced with the actual meaning of X, instead of leaving the reader
     to look X up themselves.

Run after parse_dictionaries.py. Overwrites sanskrit_dictionary.json and
sanskrit_dictionary.csv in place.
"""

import json
import re
import csv

from devanagari_utils import transliterate, is_devanagari

DEVA_TOKEN = r'[ऀ-ॿ]+'

# English: "See X", "See under X", "See also X" -> resolve X's first meaning.
# Non-word targets like "See above", "See next word" are skipped because they
# won't match any Devanagari token.
RE_SEE_EN = re.compile(
    r'\bSee(?:\s+under|\s+also)?\s+(' + DEVA_TOKEN + r')(?:\.|,|;|\s|$)'
)

# Hindi: "दे*" is the dictionary's abbreviation for "देखें" (see).
RE_SEE_HI = re.compile(r'दे\*\s*(' + DEVA_TOKEN + r')')

MAX_RESOLVED_MEANING_LEN = 150


def build_index(entries):
    return {e['sanskrit']: e for e in entries}


def first_meaning(entry, key):
    meanings = entry.get(key) or []
    if not meanings:
        return None
    text = meanings[0]
    if len(text) > MAX_RESOLVED_MEANING_LEN:
        text = text[:MAX_RESOLVED_MEANING_LEN].rsplit(' ', 1)[0] + '...'
    return text


def resolve_english(text, index):
    def repl(m):
        target = m.group(1)
        entry = index.get(target)
        if not entry:
            return m.group(0)
        meaning = first_meaning(entry, 'english_meanings')
        if not meaning:
            return m.group(0)
        tail = m.group(0)[-1] if m.group(0)[-1] in '.,; ' else ''
        return f'{target} ({meaning}){tail}'

    return RE_SEE_EN.sub(repl, text)


def resolve_hindi(text, index):
    def repl(m):
        target = m.group(1)
        entry = index.get(target)
        if not entry:
            return m.group(0)
        meaning = first_meaning(entry, 'hindi_meanings')
        if not meaning:
            return m.group(0)
        return f'{target} ({meaning})'

    return RE_SEE_HI.sub(repl, text)


def main():
    with open('sanskrit_dictionary.json', 'r', encoding='utf-8') as f:
        entries = json.load(f)

    index = build_index(entries)

    resolved_en = 0
    resolved_hi = 0

    for entry in entries:
        entry['roman'] = transliterate(entry['sanskrit'])

        new_en = []
        for m in entry['english_meanings']:
            r = resolve_english(m, index)
            if r != m:
                resolved_en += 1
            new_en.append(r)
        entry['english_meanings'] = new_en

        new_hi = []
        for m in entry['hindi_meanings']:
            r = resolve_hindi(m, index)
            if r != m:
                resolved_hi += 1
            new_hi.append(r)
        entry['hindi_meanings'] = new_hi

    print(f'Resolved {resolved_en} English cross-references')
    print(f'Resolved {resolved_hi} Hindi cross-references')

    with open('sanskrit_dictionary.json', 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    with open('sanskrit_dictionary.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Sanskrit', 'Roman', 'Gender', 'English Meaning', 'Hindi Meaning'])
        for e in entries:
            eng = e['english_meanings'][0] if e['english_meanings'] else ''
            hin = e['hindi_meanings'][0] if e['hindi_meanings'] else ''
            eng = (eng[:200] + '...') if len(eng) > 200 else eng
            hin = (hin[:200] + '...') if len(hin) > 200 else hin
            writer.writerow([e['sanskrit'], e['roman'], e['gender'], eng, hin])

    print(f'Enriched {len(entries)} entries with transliteration + cross-reference resolution.')


if __name__ == '__main__':
    main()
