# Random Sanskrit Word Generator

A beautiful Flask web application that generates random Sanskrit words from the Apte Dictionary with their gender, English meanings, and Hindi meanings.

## Features

- 🎲 Generate random Sanskrit words (1-100 at a time)
- 🌐 Dual language support: English and Hindi meanings
- 📖 18,051 Sanskrit words from authentic Apte Dictionary
- 📊 Gender classification (Masculine, Feminine, Neuter, Adjective, etc.)
- 🎨 Beautiful, responsive UI with smooth animations
- 📱 Mobile-friendly design
- 🔍 Search functionality (coming soon)
- 📊 Dictionary statistics

## Dictionary Source

This application uses the Apte Sanskrit Dictionary in Babylon format:
- **apte-sa.babylon**: Sanskrit-English dictionary
- **apte-hi.babylon**: Sanskrit-Hindi dictionary

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd random-sansk-word
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Parse the dictionary files (first time only):
```bash
python3 parse_dictionaries.py
```

This will generate:
- `sanskrit_dictionary.json` - Complete dictionary in JSON format
- `sanskrit_dictionary.csv` - Dictionary in CSV format

## Running the Application

Start the Flask server:
```bash
python3 app.py
```

The application will be available at: `http://localhost:5000`

## Deployment

### Deploying to Vercel

This app is configured for easy deployment to Vercel:

1. **Push to GitHub** (already done if you cloned this repo)

2. **Import to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Select your GitHub repository
   - Vercel will automatically detect the Python/Flask setup

3. **Configuration**:
   - The `vercel.json` file is already configured
   - No environment variables needed
   - The dictionary JSON (20MB) is included in the repository

4. **Deploy**:
   - Click "Deploy"
   - Vercel will build and deploy your app
   - You'll get a live URL like: `your-app.vercel.app`

5. **Health Check**:
   - Visit `/health` endpoint to verify deployment
   - Check dictionary loaded status and file system info

**Note**: The `sanskrit_dictionary.json` file (20MB) is committed to the repository for Vercel deployment. If you need to regenerate it, run `python3 parse_dictionaries.py`.

### Troubleshooting Vercel Deployment

If the deployment fails:
1. Check the `/health` endpoint for diagnostic information
2. Review Vercel build logs for errors
3. Ensure the dictionary JSON file is present in the deployment
4. Verify Python version compatibility (Python 3.9+ recommended)

## Usage

1. Open your web browser and navigate to `http://localhost:5000`
2. Enter the number of random words you want to generate (1-100)
3. Click "Generate Random Words"
4. View the Sanskrit words with their:
   - Sanskrit script
   - Gender classification
   - English meaning
   - Hindi meaning (हिन्दी अर्थ)
5. Click "Show all meanings" to see additional definitions

## API Endpoints

### Get Random Words
```
GET /api/random?count=5
```

Returns random Sanskrit words with meanings.

**Parameters:**
- `count` (optional): Number of words to return (1-100, default: 1)

**Response:**
```json
{
  "success": true,
  "count": 5,
  "words": [
    {
      "sanskrit": "अग्नि",
      "gender": "masculine",
      "english_meaning": "Fire...",
      "hindi_meaning": "अग्नि...",
      "all_english_meanings": [...],
      "all_hindi_meanings": [...]
    }
  ]
}
```

### Get Statistics
```
GET /api/stats
```

Returns dictionary statistics.

**Response:**
```json
{
  "total_words": 18051,
  "gender_distribution": {
    "masculine": 8234,
    "feminine": 4123,
    "neuter": 3456,
    ...
  }
}
```

### Search Words
```
GET /api/search?q=अग्नि
```

Search for Sanskrit words by headword.

**Parameters:**
- `q` (required): Search query

## Project Structure

```
random-sansk-word/
├── app.py                      # Flask application
├── parse_dictionaries.py       # Dictionary parser script
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── apte-sa.babylon            # Sanskrit-English dictionary
├── apte-hi.babylon            # Sanskrit-Hindi dictionary
├── sanskrit_dictionary.json    # Processed dictionary (JSON)
├── sanskrit_dictionary.csv     # Processed dictionary (CSV)
├── templates/
│   └── index.html             # Main HTML template
└── static/
    ├── css/
    │   └── style.css          # Styles
    └── js/
        └── app.js             # Frontend JavaScript
```

## Technologies Used

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Fonts**:
  - Noto Sans Devanagari (for Sanskrit/Hindi text)
  - Poppins (for English text)
- **Data Format**: JSON, CSV

## Features Explanation

### Gender Classification

Words are classified by gender:
- **Masculine** (पुं) - Blue badge
- **Feminine** (स्त्री) - Red badge
- **Neuter** (नपुं) - Green badge
- **Adjective** (वि) - Orange badge
- **Indeclinable** (अव्य) - Purple badge
- **Adverb** (क्रि.वि) - Teal badge

### Dictionary Processing

The parser script (`parse_dictionaries.py`) performs:
1. Extracts headwords and definitions from Babylon format
2. Identifies gender markers in Hindi dictionary
3. Merges entries from both dictionaries
4. Filters entries to include only those with both English and Hindi meanings
5. Exports to JSON and CSV formats

## Data Statistics

- **Total Entries**: 18,051 Sanskrit words
- **Source**: Apte Dictionary (Babylon format)
- **Languages**: Sanskrit, English, Hindi
- **File Sizes**:
  - Sanskrit-English: ~19 MB
  - Sanskrit-Hindi: ~17 MB

## Development

To modify the application:

1. **Backend changes**: Edit `app.py`
2. **Frontend changes**:
   - HTML: Edit `templates/index.html`
   - CSS: Edit `static/css/style.css`
   - JavaScript: Edit `static/js/app.js`
3. **Dictionary parsing**: Edit `parse_dictionaries.py`

## License

This application uses the Apte Dictionary data. Please ensure compliance with the dictionary's usage terms.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Future Enhancements

- [ ] Advanced search functionality
- [ ] Filter by gender/word type
- [ ] Bookmark favorite words
- [ ] Export word lists to PDF
- [ ] Audio pronunciation
- [ ] Word of the day feature
- [ ] Etymology information
- [ ] Example sentences

## Support

For issues or questions, please open an issue on the GitHub repository.
