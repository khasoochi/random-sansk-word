#!/usr/bin/env python3
"""
Parser for Apte Sanskrit-English and Sanskrit-Hindi Babylon dictionaries.
Extracts Sanskrit words with their gender, English meanings, and Hindi meanings.
"""

import re
import json
import csv
from collections import defaultdict


def extract_gender(hindi_entry):
    """Extract gender information from Hindi dictionary entry."""
    gender_map = {
        'पुं*': 'masculine',
        'पुं': 'masculine',
        'स्त्री*': 'feminine',
        'स्त्री': 'feminine',
        'नपुं*': 'neuter',
        'नपुं': 'neuter',
        'वि*': 'adjective',
        'वि': 'adjective',
        'अव्य*': 'indeclinable',
        'अव्य': 'indeclinable',
        'क्रि*वि*': 'adverb',
    }

    for marker, gender in gender_map.items():
        if marker in hindi_entry:
            return gender
    return 'unknown'


def clean_text(text):
    """Remove HTML tags and clean text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_english_dictionary(filepath):
    """Parse the Sanskrit-English Babylon dictionary."""
    entries = defaultdict(list)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by double newlines to separate entries
    blocks = content.split('\n\n')

    current_headword = None

    for block in blocks:
        if not block.strip() or block.startswith('#'):
            continue

        lines = block.strip().split('\n')
        if not lines:
            continue

        # First line is the headword
        headword = lines[0].strip()

        # Skip if headword is empty or contains only special chars
        if not headword or headword in ['→', '-', '|']:
            continue

        # Get definition (rest of the lines)
        definition = ' '.join(lines[1:]) if len(lines) > 1 else ''
        definition = clean_text(definition)

        # Handle compound headwords (e.g., "आबाधः|आबाध")
        if '|' in headword:
            headword = headword.split('|')[-1].strip()

        if headword and definition:
            entries[headword].append(definition)

    return entries


def parse_hindi_dictionary(filepath):
    """Parse the Sanskrit-Hindi Babylon dictionary."""
    entries = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by double newlines to separate entries
    blocks = content.split('\n\n')

    for block in blocks:
        if not block.strip() or block.startswith('#'):
            continue

        lines = block.strip().split('\n')
        if not lines:
            continue

        # First line is the headword
        headword = lines[0].strip()

        # Skip if headword is empty
        if not headword:
            continue

        # Get full entry
        full_entry = ' '.join(lines[1:]) if len(lines) > 1 else ''

        # Handle compound headwords (e.g., "अः|अ")
        if '|' in headword:
            headword = headword.split('|')[-1].strip()

        # Extract gender
        gender = extract_gender(full_entry)

        # Extract Hindi meaning
        hindi_meaning = clean_text(full_entry)

        if headword:
            if headword not in entries:
                entries[headword] = {
                    'gender': gender,
                    'meanings': []
                }
            entries[headword]['meanings'].append(hindi_meaning)

    return entries


def merge_dictionaries(english_dict, hindi_dict):
    """Merge English and Hindi dictionaries."""
    merged = []

    # Get all unique headwords
    all_headwords = set(english_dict.keys()) | set(hindi_dict.keys())

    for headword in all_headwords:
        entry = {
            'sanskrit': headword,
            'gender': 'unknown',
            'english_meanings': [],
            'hindi_meanings': []
        }

        # Get Hindi data
        if headword in hindi_dict:
            entry['gender'] = hindi_dict[headword]['gender']
            entry['hindi_meanings'] = hindi_dict[headword]['meanings']

        # Get English data
        if headword in english_dict:
            entry['english_meanings'] = english_dict[headword]

        # Only include entries that have both English and Hindi meanings
        if entry['english_meanings'] and entry['hindi_meanings']:
            merged.append(entry)

    return merged


def save_to_json(data, filepath):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} entries to {filepath}")


def save_to_csv(data, filepath):
    """Save data to CSV file."""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Sanskrit', 'Gender', 'English Meaning', 'Hindi Meaning'])

        for entry in data:
            sanskrit = entry['sanskrit']
            gender = entry['gender']

            # Take first meaning from each
            english = entry['english_meanings'][0] if entry['english_meanings'] else ''
            hindi = entry['hindi_meanings'][0] if entry['hindi_meanings'] else ''

            # Limit length for readability
            english = (english[:200] + '...') if len(english) > 200 else english
            hindi = (hindi[:200] + '...') if len(hindi) > 200 else hindi

            writer.writerow([sanskrit, gender, english, hindi])

    print(f"Saved {len(data)} entries to {filepath}")


def main():
    print("Parsing Sanskrit-English dictionary...")
    english_dict = parse_english_dictionary('apte-sa.babylon')
    print(f"Found {len(english_dict)} unique headwords in English dictionary")

    print("\nParsing Sanskrit-Hindi dictionary...")
    hindi_dict = parse_hindi_dictionary('apte-hi.babylon')
    print(f"Found {len(hindi_dict)} unique headwords in Hindi dictionary")

    print("\nMerging dictionaries...")
    merged_data = merge_dictionaries(english_dict, hindi_dict)
    print(f"Merged {len(merged_data)} entries with both English and Hindi meanings")

    print("\nSaving to files...")
    save_to_json(merged_data, 'sanskrit_dictionary.json')
    save_to_csv(merged_data, 'sanskrit_dictionary.csv')

    print("\nDone! Dictionary data has been processed.")
    print(f"Total entries: {len(merged_data)}")


if __name__ == '__main__':
    main()
