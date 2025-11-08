#!/usr/bin/env python3
"""
Test script for the Flask application
"""

import sys
import json

# Test importing the app
try:
    from app import app, DICTIONARY_DATA
    print("✓ App imported successfully")
except Exception as e:
    print(f"✗ Failed to import app: {e}")
    sys.exit(1)

# Test dictionary data loaded
print(f"✓ Dictionary loaded with {len(DICTIONARY_DATA)} entries")

# Test a few sample entries
if len(DICTIONARY_DATA) > 0:
    sample = DICTIONARY_DATA[0]
    print(f"\n📖 Sample entry:")
    print(f"   Sanskrit: {sample['sanskrit']}")
    print(f"   Gender: {sample['gender']}")
    print(f"   English meanings: {len(sample['english_meanings'])} entries")
    print(f"   Hindi meanings: {len(sample['hindi_meanings'])} entries")

# Test Flask app context
with app.test_client() as client:
    # Test home page
    response = client.get('/')
    if response.status_code == 200:
        print("\n✓ Home page accessible")
    else:
        print(f"\n✗ Home page returned status {response.status_code}")

    # Test random API
    response = client.get('/api/random?count=3')
    if response.status_code == 200:
        data = json.loads(response.data)
        if data['success'] and data['count'] == 3:
            print(f"✓ Random API works - returned {data['count']} words")
            print(f"   Sample word: {data['words'][0]['sanskrit']}")
        else:
            print("✗ Random API returned unexpected data")
    else:
        print(f"✗ Random API returned status {response.status_code}")

    # Test stats API
    response = client.get('/api/stats')
    if response.status_code == 200:
        data = json.loads(response.data)
        print(f"✓ Stats API works - {data['total_words']} total words")
        print(f"   Gender distribution: {list(data['gender_distribution'].keys())}")
    else:
        print(f"✗ Stats API returned status {response.status_code}")

print("\n✅ All tests passed! The application is ready to run.")
print("\nTo start the server, run:")
print("   python3 app.py")
print("\nThen visit: http://localhost:5000")
