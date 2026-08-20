"""
Devanagari script utilities: transliteration (Devanagari -> plain Latin, for
search) and akshara (orthographic syllable) segmentation, used to build
Devanagari-first word games (Wordle/Scramble/Crossword) where the natural
"unit" of a word is a syllable cluster, not a raw Unicode code point.
"""

import re

# --- Character classes -------------------------------------------------

INDEPENDENT_VOWELS = set('अआइईउऊऋॠऌॡएऐओऔ')
MATRAS = set('ािीुूृॄॢॣेैोौ')
ANUSVARA_ETC = set('ंःँ')
HALANT = '्'
NUKTA = '़'

CONSONANTS = set(
    'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह' +
    'क़ख़ग़ज़ड़ढ़फ़य़' +  # nukta consonants
    'ऽ'  # avagraha (not a consonant technically, but a standalone glyph)
)

DEVANAGARI_RANGE = re.compile(r'[ऀ-ॿ]')


def is_devanagari(text):
    """True if text contains at least one Devanagari codepoint."""
    return bool(DEVANAGARI_RANGE.search(text or ''))


# --- Akshara (syllable) segmentation ------------------------------------

def split_aksharas(word):
    """
    Split a Devanagari word into orthographic syllables (aksharas).

    Each akshara is a consonant cluster (including conjuncts joined by
    halant) plus its vowel sign / anusvara / visarga, or an independent
    vowel. This is the natural "letter" unit for Devanagari word games,
    since a lone Unicode codepoint (e.g. a matra) isn't meaningful on
    its own.
    """
    clusters = []
    i, n = 0, len(word)

    while i < n:
        ch = word[i]

        if ch in CONSONANTS:
            start = i
            i += 1
            # Consume nukta directly after a consonant, if present.
            if i < n and word[i] == NUKTA:
                i += 1
            # Consume conjunct chains: halant + consonant (+ optional nukta).
            while i + 1 < n and word[i] == HALANT and word[i + 1] in CONSONANTS:
                i += 2
                if i < n and word[i] == NUKTA:
                    i += 1
            # Trailing halant with nothing after it (word-final virama).
            if i < n and word[i] == HALANT:
                i += 1
                clusters.append(word[start:i])
                continue
            # Optional vowel sign.
            if i < n and word[i] in MATRAS:
                i += 1
            # Optional anusvara / visarga / candrabindu.
            while i < n and word[i] in ANUSVARA_ETC:
                i += 1
            clusters.append(word[start:i])

        elif ch in INDEPENDENT_VOWELS:
            start = i
            i += 1
            while i < n and word[i] in ANUSVARA_ETC:
                i += 1
            clusters.append(word[start:i])

        elif ch in ANUSVARA_ETC or ch in MATRAS or ch == HALANT or ch == NUKTA:
            # Stray combining mark with no preceding base (malformed input);
            # attach to previous cluster if any, else keep standalone.
            if clusters:
                clusters[-1] += ch
            else:
                clusters.append(ch)
            i += 1

        else:
            # Non-Devanagari char (digits, danda, punctuation, spaces, ZWJ).
            clusters.append(ch)
            i += 1

    return clusters


# --- Transliteration (Devanagari -> plain Latin) ------------------------
# Deliberately NOT strict IAST (no diacritics) so it's easy to type & search.

_VOWEL_INDEP = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu',
    'ऋ': 'ri', 'ॠ': 'rii', 'ऌ': 'lri', 'ॡ': 'lrii',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
}

_MATRA = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ii', 'ु': 'u', 'ू': 'uu',
    'ृ': 'ri', 'ॄ': 'rii', 'ॢ': 'lri', 'ॣ': 'lrii',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
}

_CONSONANT = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'g', 'ज़': 'z', 'ड़': 'r', 'ढ़': 'rh', 'फ़': 'f', 'य़': 'y',
    'ळ': 'l', 'ऽ': '',
}

_OTHER = {
    'ं': 'm', 'ः': 'h', 'ँ': 'm',
    '्': '',
    '़': '',
    '।': '.', '॥': '.',
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
}


def transliterate(word):
    """
    Render a Devanagari word as a plain Latin string suitable for search
    (e.g. 'धर्म' -> 'dharma', 'कृष्ण' -> 'krishna'). Non-Devanagari
    characters pass through unchanged (lowercased).
    """
    out = []
    i, n = 0, len(word)

    while i < n:
        ch = word[i]

        if ch in CONSONANTS:
            out.append(_CONSONANT.get(ch, ch))
            i += 1
            # Nukta already folded into _CONSONANT lookups above for common cases.
            if i < n and word[i] == NUKTA:
                i += 1
            if i < n and word[i] == HALANT:
                # No inherent vowel; consonant cluster continues.
                out.append('')
                i += 1
            elif i < n and word[i] in MATRAS:
                out.append(_MATRA[word[i]])
                i += 1
            else:
                out.append('a')  # inherent vowel

        elif ch in INDEPENDENT_VOWELS:
            out.append(_VOWEL_INDEP.get(ch, ch))
            i += 1

        elif ch in _OTHER:
            out.append(_OTHER[ch])
            i += 1

        elif ch == ' ':
            out.append(' ')
            i += 1

        else:
            out.append(ch.lower())
            i += 1

    return ''.join(out)


# --- Hint extraction (strip headword/etymology so puzzle hints don't spoil
#     the answer -- dictionary entries lead with "<word> [iast], [etymology]
#     <actual gloss>", and the etymology almost always reuses the word's own
#     root, so it must be stripped, not just the transliteration bracket). ---

_POS_OR_NUM = re.compile(r'^(?:\d+|[A-Za-z]{1,6}\.)\s*')
# A bare Devanagari token immediately followed by an IAST bracket or a short
# POS abbreviation ('f.', 'm.', 'a.') is a restated headword/variant form,
# not part of the gloss -- Apte entries sometimes repeat these (e.g. for
# feminine forms) before the real definition even starts.
_RESTATED_HEADWORD = re.compile(r'^[ऀ-ॿ]+\s*(?=\[|[A-Za-z]{1,4}\.(?:\s|,|$))')


def clean_english_hint(text, min_len=3):
    """Strip a leading '<headword> [iast], [etymology] <headword> f. ...'
    prefix from an Apte English gloss, returning just the actual definition
    text (or '' if nothing usable remains). The etymology and any restated
    headword/variant forms must go, since they reuse the word's own root
    and would otherwise spoil a puzzle answer."""
    s = text.strip()

    prev = None
    while s != prev:
        prev = s
        s = s.lstrip(' ,;.')
        if s.startswith('('):
            end = s.find(')')
            if end != -1:
                s = s[end + 1:]
                continue
        if s.startswith('['):
            end = s.find(']')
            if end != -1:
                s = s[end + 1:]
                continue
        m3 = _RESTATED_HEADWORD.match(s)
        if m3:
            s = s[m3.end():]
            continue
        m2 = _POS_OR_NUM.match(s)
        if m2 and m2.end() > 0:
            s = s[m2.end():]
            continue

    s = s.strip(' ,;.')
    return s if len(s) >= min_len else ''


_QUOTED = re.compile(r'"([^"]+)"')


def clean_hindi_hint(text, min_len=2):
    """Return the Hindi gloss for use as a puzzle hint. parse_dictionaries.py
    already extracts just the gloss (dictionary codes and etymology are
    discarded at parse time -- see extract_hindi_gloss), so this mostly just
    trims. Any leftover quotes (from older/unrefreshed data) are unwrapped
    defensively."""
    s = text.strip()
    m = _QUOTED.fullmatch(s)
    if m:
        s = m.group(1).strip()
    return s if len(s) >= min_len else ''


def best_hint(meanings, cleaner):
    """Return the first usable cleaned hint from a list of raw meanings."""
    for m in meanings:
        cleaned = cleaner(m)
        if cleaned:
            return cleaned
    return ''


if __name__ == '__main__':
    tests = ['धर्म', 'कृष्ण', 'राम', 'गुरु', 'विद्या', 'संस्कृतम्', 'अ']
    for t in tests:
        print(t, '->', transliterate(t), '->', split_aksharas(t))
