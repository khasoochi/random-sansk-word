"""
Flask application for serving random Sanskrit words from Apte dictionary.
"""

from flask import Flask, render_template, jsonify, request
import json
import random
import os

app = Flask(__name__)

# Load dictionary data with proper path handling
def load_dictionary():
    """Load dictionary data from JSON file."""
    # Try different paths for local and Vercel deployment
    possible_paths = [
        'sanskrit_dictionary.json',
        os.path.join(os.path.dirname(__file__), 'sanskrit_dictionary.json'),
        '/var/task/sanskrit_dictionary.json'
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Loaded {len(data)} Sanskrit words from {path}")
                    return data
            except Exception as e:
                print(f"Error loading from {path}: {e}")
                continue

    # If no file found, return empty list with error
    print("ERROR: Could not find sanskrit_dictionary.json")
    return []

DICTIONARY_DATA = load_dictionary()


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for debugging."""
    return jsonify({
        'status': 'ok',
        'dictionary_loaded': len(DICTIONARY_DATA) > 0,
        'word_count': len(DICTIONARY_DATA),
        'working_directory': os.getcwd(),
        'file_exists': os.path.exists('sanskrit_dictionary.json'),
        'files_in_directory': os.listdir('.')[:20]  # First 20 files
    })


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
