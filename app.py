"""
Flask application for serving random Sanskrit words from Apte dictionary.
"""

from flask import Flask, render_template, jsonify, request
import json
import random

app = Flask(__name__)

# Load dictionary data
with open('sanskrit_dictionary.json', 'r', encoding='utf-8') as f:
    DICTIONARY_DATA = json.load(f)

print(f"Loaded {len(DICTIONARY_DATA)} Sanskrit words")


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/random', methods=['GET'])
def get_random_words():
    """
    Get random Sanskrit words.
    Query parameter: count (default: 1, max: 100)
    """
    try:
        count = int(request.args.get('count', 1))
        count = min(max(1, count), 100)  # Limit between 1 and 100

        # Get random sample
        if count >= len(DICTIONARY_DATA):
            random_words = DICTIONARY_DATA
        else:
            random_words = random.sample(DICTIONARY_DATA, count)

        # Format the response
        formatted_words = []
        for word in random_words:
            formatted_words.append({
                'sanskrit': word['sanskrit'],
                'gender': word['gender'],
                'english_meaning': word['english_meanings'][0] if word['english_meanings'] else 'N/A',
                'hindi_meaning': word['hindi_meanings'][0] if word['hindi_meanings'] else 'N/A',
                'all_english_meanings': word['english_meanings'],
                'all_hindi_meanings': word['hindi_meanings']
            })

        return jsonify({
            'success': True,
            'count': len(formatted_words),
            'words': formatted_words
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the dictionary."""
    gender_counts = {}
    for word in DICTIONARY_DATA:
        gender = word['gender']
        gender_counts[gender] = gender_counts.get(gender, 0) + 1

    return jsonify({
        'total_words': len(DICTIONARY_DATA),
        'gender_distribution': gender_counts
    })


@app.route('/api/search', methods=['GET'])
def search_words():
    """
    Search for Sanskrit words.
    Query parameter: q (search query)
    """
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400

    # Search in Sanskrit headwords
    results = []
    for word in DICTIONARY_DATA:
        if query in word['sanskrit']:
            results.append({
                'sanskrit': word['sanskrit'],
                'gender': word['gender'],
                'english_meaning': word['english_meanings'][0] if word['english_meanings'] else 'N/A',
                'hindi_meaning': word['hindi_meanings'][0] if word['hindi_meanings'] else 'N/A'
            })

            if len(results) >= 50:  # Limit results
                break

    return jsonify({
        'success': True,
        'count': len(results),
        'results': results
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
