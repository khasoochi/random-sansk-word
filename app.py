"""
Flask application for the Sanskrit dictionary: random word generator,
search (Devanagari + transliteration + regex), flashcard learning, and
Devanagari word games (Wordle, Scramble, Crossword) built on aksharas
(syllables) rather than raw Unicode characters.
"""

import json
import os
import random
import re

from flask import Flask, render_template, jsonify, request

from devanagari_utils import is_devanagari

app = Flask(__name__)

MAX_SEARCH_RESULTS = 60
MAX_SUGGESTIONS = 10


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def _resolve_path(filename):
    for path in (filename, os.path.join(os.path.dirname(__file__), filename)):
        if os.path.exists(path):
            return path
    return None


def load_dictionary():
    path = _resolve_path('sanskrit_dictionary.json')
    if not path:
        print('ERROR: Could not find sanskrit_dictionary.json')
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f'Loaded {len(data)} Sanskrit words from {path}')
    return data


def load_puzzle_set(name):
    path = _resolve_path(os.path.join('puzzles', f'{name}.json'))
    if not path:
        print(f'WARNING: puzzles/{name}.json not found')
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f'Loaded {len(data)} {name} puzzles')
    return data


DICTIONARY_DATA = load_dictionary()
DICTIONARY_INDEX = {e['sanskrit']: e for e in DICTIONARY_DATA}

WORDLE_PUZZLES = load_puzzle_set('wordle')
SCRAMBLE_PUZZLES = load_puzzle_set('scramble')
CROSSWORD_PUZZLES = load_puzzle_set('crossword')

WORDLE_INDEX = {p['id']: p for p in WORDLE_PUZZLES}
SCRAMBLE_INDEX = {p['id']: p for p in SCRAMBLE_PUZZLES}
CROSSWORD_INDEX = {p['id']: p for p in CROSSWORD_PUZZLES}


# --------------------------------------------------------------------------
# Page routes
# --------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html', active='home')


@app.route('/random')
def random_page():
    return render_template('random.html', active='random')


@app.route('/search')
def search_page():
    return render_template('search.html', active='search')


@app.route('/learn')
def learn_page():
    return render_template('learn.html', active='learn')


@app.route('/games/wordle')
def wordle_page():
    return render_template('wordle.html', active='wordle')


@app.route('/games/scramble')
def scramble_page():
    return render_template('scramble.html', active='scramble')


@app.route('/games/crossword')
def crossword_page():
    return render_template('crossword.html', active='crossword')


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'dictionary_loaded': len(DICTIONARY_DATA) > 0,
        'word_count': len(DICTIONARY_DATA),
        'wordle_puzzles': len(WORDLE_PUZZLES),
        'scramble_puzzles': len(SCRAMBLE_PUZZLES),
        'crossword_puzzles': len(CROSSWORD_PUZZLES),
        'working_directory': os.getcwd(),
    })


# --------------------------------------------------------------------------
# Dictionary API
# --------------------------------------------------------------------------

def format_word(entry):
    return {
        'sanskrit': entry['sanskrit'],
        'roman': entry.get('roman', ''),
        'gender': entry['gender'],
        'english_meaning': entry['english_meanings'][0] if entry['english_meanings'] else 'N/A',
        'hindi_meaning': entry['hindi_meanings'][0] if entry['hindi_meanings'] else 'N/A',
        'all_english_meanings': entry['english_meanings'],
        'all_hindi_meanings': entry['hindi_meanings'],
    }


@app.route('/api/random', methods=['GET'])
def get_random_words():
    try:
        count = int(request.args.get('count', 1))
        count = min(max(1, count), 100)

        if count >= len(DICTIONARY_DATA):
            sample = DICTIONARY_DATA
        else:
            sample = random.sample(DICTIONARY_DATA, count)

        return jsonify({
            'success': True,
            'count': len(sample),
            'words': [format_word(w) for w in sample],
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/stats', methods=['GET'])
def get_stats():
    gender_counts = {}
    for word in DICTIONARY_DATA:
        gender_counts[word['gender']] = gender_counts.get(word['gender'], 0) + 1
    return jsonify({'total_words': len(DICTIONARY_DATA), 'gender_distribution': gender_counts})


@app.route('/api/search', methods=['GET'])
def search_words():
    query = request.args.get('q', '').strip()
    use_regex = request.args.get('regex', '0') in ('1', 'true', 'True')

    if not query:
        return jsonify({'success': False, 'error': 'Search query is required'}), 400

    if use_regex:
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error as e:
            return jsonify({'success': False, 'error': f'Invalid regex: {e}'}), 400
        matcher = lambda e: bool(pattern.search(e['sanskrit'])) or bool(pattern.search(e.get('roman', '')))
    else:
        q_lower = query.lower()
        matcher = lambda e: query in e['sanskrit'] or q_lower in e.get('roman', '').lower()

    results = []
    for entry in DICTIONARY_DATA:
        if matcher(entry):
            results.append(format_word(entry))
            if len(results) >= MAX_SEARCH_RESULTS:
                break

    return jsonify({'success': True, 'count': len(results), 'results': results})


@app.route('/api/suggest', methods=['GET'])
def suggest_words():
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', MAX_SUGGESTIONS)), 25)

    if not query:
        return jsonify({'success': True, 'count': 0, 'results': []})

    q_lower = query.lower()
    prefix_matches = []
    substring_matches = []

    for entry in DICTIONARY_DATA:
        sanskrit = entry['sanskrit']
        roman = entry.get('roman', '')
        roman_lower = roman.lower()

        if sanskrit.startswith(query) or roman_lower.startswith(q_lower):
            prefix_matches.append(entry)
        elif query in sanskrit or q_lower in roman_lower:
            substring_matches.append(entry)

        if len(prefix_matches) >= limit:
            break

    combined = (prefix_matches + substring_matches)[:limit]
    results = [{'sanskrit': e['sanskrit'], 'roman': e.get('roman', '')} for e in combined]
    return jsonify({'success': True, 'count': len(results), 'results': results})


# --------------------------------------------------------------------------
# Word game helpers
# --------------------------------------------------------------------------

def score_aksharas(guess, answer):
    """Standard Wordle-style scoring, generalized to akshara units instead
    of single characters (handles duplicate aksharas correctly)."""
    n = len(answer)
    result = ['absent'] * len(guess)
    used = [False] * n

    for i in range(min(len(guess), n)):
        if guess[i] == answer[i]:
            result[i] = 'correct'
            used[i] = True

    for i in range(len(guess)):
        if result[i] == 'correct':
            continue
        for j in range(n):
            if not used[j] and guess[i] == answer[j]:
                result[i] = 'present'
                used[j] = True
                break

    return result


def public_word_fields(sanskrit):
    """Full reveal info for a headword, pulled from the main dictionary."""
    entry = DICTIONARY_INDEX.get(sanskrit)
    if not entry:
        return {}
    return {
        'english_meaning': entry['english_meanings'][0] if entry['english_meanings'] else '',
        'hindi_meaning': entry['hindi_meanings'][0] if entry['hindi_meanings'] else '',
        'gender': entry['gender'],
    }


# --------------------------------------------------------------------------
# Wordle API
# --------------------------------------------------------------------------

@app.route('/api/games/wordle/new', methods=['GET'])
def wordle_new():
    if not WORDLE_PUZZLES:
        return jsonify({'success': False, 'error': 'No Wordle puzzles available'}), 500
    length = request.args.get('length', type=int)
    pool = [p for p in WORDLE_PUZZLES if p['length'] == length] if length else WORDLE_PUZZLES
    if not pool:
        pool = WORDLE_PUZZLES
    p = random.choice(pool)
    return jsonify({
        'success': True,
        'id': p['id'],
        'length': p['length'],
        'gender': p['gender'],
        'hint_en': p['hint_en'],
        'hint_hi': p['hint_hi'],
    })


@app.route('/api/games/wordle/guess', methods=['POST'])
def wordle_guess():
    data = request.get_json(force=True, silent=True) or {}
    puzzle = WORDLE_INDEX.get(data.get('id'))
    guess = data.get('guess')

    if not puzzle or not isinstance(guess, list):
        return jsonify({'success': False, 'error': 'Invalid puzzle id or guess'}), 400
    if len(guess) != puzzle['length']:
        return jsonify({'success': False, 'error': 'Guess length mismatch'}), 400

    answer = puzzle['aksharas']
    feedback = score_aksharas(guess, answer)
    solved = feedback == ['correct'] * len(answer)

    response = {'success': True, 'feedback': feedback, 'solved': solved}
    if solved:
        response.update({'word': puzzle['word'], 'roman': puzzle['roman']})
        response.update(public_word_fields(puzzle['word']))
    return jsonify(response)


@app.route('/api/games/wordle/<puzzle_id>/reveal', methods=['GET'])
def wordle_reveal(puzzle_id):
    puzzle = WORDLE_INDEX.get(puzzle_id)
    if not puzzle:
        return jsonify({'success': False, 'error': 'Unknown puzzle id'}), 404
    result = {
        'success': True,
        'word': puzzle['word'],
        'roman': puzzle['roman'],
        'aksharas': puzzle['aksharas'],
    }
    result.update(public_word_fields(puzzle['word']))
    return jsonify(result)


# --------------------------------------------------------------------------
# Scramble API
# --------------------------------------------------------------------------

@app.route('/api/games/scramble/new', methods=['GET'])
def scramble_new():
    if not SCRAMBLE_PUZZLES:
        return jsonify({'success': False, 'error': 'No Scramble puzzles available'}), 500
    p = random.choice(SCRAMBLE_PUZZLES)
    return jsonify({
        'success': True,
        'id': p['id'],
        'scrambled': p['scrambled'],
        'hint_en': p['hint_en'],
        'hint_hi': p['hint_hi'],
    })


@app.route('/api/games/scramble/check', methods=['POST'])
def scramble_check():
    data = request.get_json(force=True, silent=True) or {}
    puzzle = SCRAMBLE_INDEX.get(data.get('id'))
    order = data.get('order')

    if not puzzle or not isinstance(order, list):
        return jsonify({'success': False, 'error': 'Invalid puzzle id or order'}), 400

    correct = order == puzzle['aksharas']
    response = {'success': True, 'correct': correct}
    if correct:
        response.update({'word': puzzle['word'], 'roman': puzzle['roman']})
        response.update(public_word_fields(puzzle['word']))
    return jsonify(response)


@app.route('/api/games/scramble/<puzzle_id>/reveal', methods=['GET'])
def scramble_reveal(puzzle_id):
    puzzle = SCRAMBLE_INDEX.get(puzzle_id)
    if not puzzle:
        return jsonify({'success': False, 'error': 'Unknown puzzle id'}), 404
    result = {
        'success': True,
        'word': puzzle['word'],
        'roman': puzzle['roman'],
        'aksharas': puzzle['aksharas'],
    }
    result.update(public_word_fields(puzzle['word']))
    return jsonify(result)


# --------------------------------------------------------------------------
# Crossword API
# --------------------------------------------------------------------------

def crossword_public_words(puzzle):
    return [{
        'number': w['number'],
        'direction': w['direction'],
        'row': w['row'],
        'col': w['col'],
        'length': w['length'],
        'clue_en': w['clue_en'],
        'clue_hi': w['clue_hi'],
    } for w in puzzle['words']]


@app.route('/api/games/crossword/new', methods=['GET'])
def crossword_new():
    if not CROSSWORD_PUZZLES:
        return jsonify({'success': False, 'error': 'No Crossword puzzles available'}), 500
    p = random.choice(CROSSWORD_PUZZLES)
    return jsonify({
        'success': True,
        'id': p['id'],
        'rows': p['rows'],
        'cols': p['cols'],
        'words': crossword_public_words(p),
    })


@app.route('/api/games/crossword/check', methods=['POST'])
def crossword_check():
    data = request.get_json(force=True, silent=True) or {}
    puzzle = CROSSWORD_INDEX.get(data.get('id'))
    cells = data.get('cells')

    if not puzzle or not isinstance(cells, dict):
        return jsonify({'success': False, 'error': 'Invalid puzzle id or cells'}), 400

    solution = {}
    for w in puzzle['words']:
        for k, ak in enumerate(w['aksharas']):
            r = w['row'] + (k if w['direction'] == 'down' else 0)
            c = w['col'] + (k if w['direction'] == 'across' else 0)
            solution[f'{r},{c}'] = ak

    results = {key: (solution.get(key) == val) for key, val in cells.items()}
    all_correct = len(solution) == len(cells) and all(results.values())

    response = {'success': True, 'results': results, 'solved': all_correct}
    if all_correct:
        response['words'] = [{'word': w['word'], 'roman': w['roman'], 'clue_en': w['clue_en']}
                              for w in puzzle['words']]
    return jsonify(response)


@app.route('/api/games/crossword/<puzzle_id>/reveal', methods=['GET'])
def crossword_reveal(puzzle_id):
    puzzle = CROSSWORD_INDEX.get(puzzle_id)
    if not puzzle:
        return jsonify({'success': False, 'error': 'Unknown puzzle id'}), 404

    cells = {}
    for w in puzzle['words']:
        for k, ak in enumerate(w['aksharas']):
            r = w['row'] + (k if w['direction'] == 'down' else 0)
            c = w['col'] + (k if w['direction'] == 'across' else 0)
            cells[f'{r},{c}'] = ak

    return jsonify({
        'success': True,
        'cells': cells,
        'words': [{'word': w['word'], 'roman': w['roman'], 'direction': w['direction'],
                   'number': w['number'], 'clue_en': w['clue_en']} for w in puzzle['words']],
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
