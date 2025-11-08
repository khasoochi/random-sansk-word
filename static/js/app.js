// Main application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generateBtn');
    const wordCountInput = document.getElementById('wordCount');
    const resultsContainer = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const statsDiv = document.getElementById('stats');

    // Load stats on page load
    loadStats();

    // Generate button click handler
    generateBtn.addEventListener('click', generateWords);

    // Allow Enter key to generate
    wordCountInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            generateWords();
        }
    });

    // Load initial words
    generateWords();

    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();

            if (data.total_words) {
                document.getElementById('totalWords').textContent =
                    `${data.total_words.toLocaleString()} words available`;
                document.getElementById('dbCount').textContent =
                    data.total_words.toLocaleString();

                // Display gender distribution
                if (data.gender_distribution) {
                    const genderInfo = Object.entries(data.gender_distribution)
                        .map(([gender, count]) => `${gender}: ${count}`)
                        .join(', ');
                    console.log('Gender distribution:', genderInfo);
                }
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            document.getElementById('totalWords').textContent = 'Error loading stats';
        }
    }

    async function generateWords() {
        const count = parseInt(wordCountInput.value) || 5;

        // Validate input
        if (count < 1 || count > 100) {
            alert('Please enter a number between 1 and 100');
            return;
        }

        // Show loading state
        loadingDiv.style.display = 'block';
        resultsContainer.innerHTML = '';
        generateBtn.disabled = true;

        try {
            const response = await fetch(`/api/random?count=${count}`);
            const data = await response.json();

            if (data.success) {
                displayWords(data.words);
            } else {
                showError(data.error || 'Failed to fetch words');
            }
        } catch (error) {
            showError('Network error: ' + error.message);
        } finally {
            loadingDiv.style.display = 'none';
            generateBtn.disabled = false;
        }
    }

    function displayWords(words) {
        resultsContainer.innerHTML = '';

        words.forEach((word, index) => {
            const card = createWordCard(word, index);
            resultsContainer.appendChild(card);
        });

        // Scroll to results smoothly
        if (words.length > 0) {
            setTimeout(() => {
                resultsContainer.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }, 100);
        }
    }

    function createWordCard(word, index) {
        const card = document.createElement('div');
        card.className = 'word-card';
        card.style.animationDelay = `${index * 0.1}s`;

        const genderClass = `gender-${word.gender.toLowerCase()}`;

        // Truncate meanings for initial display
        const englishMeaning = truncateText(word.english_meaning, 200);
        const hindiMeaning = truncateText(word.hindi_meaning, 200);

        card.innerHTML = `
            <div class="word-header">
                <div class="sanskrit-word">${escapeHtml(word.sanskrit)}</div>
                <span class="gender-badge ${genderClass}">${escapeHtml(word.gender)}</span>
            </div>

            <div class="meaning-section">
                <div class="meaning-label">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    English Meaning
                </div>
                <div class="meaning-text" id="english-${index}">
                    ${escapeHtml(englishMeaning)}
                </div>
            </div>

            <div class="meaning-section">
                <div class="meaning-label">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    हिन्दी अर्थ
                </div>
                <div class="meaning-text hindi-text" id="hindi-${index}">
                    ${escapeHtml(hindiMeaning)}
                </div>
            </div>
        `;

        // Add expand functionality if there are multiple meanings
        if (word.all_english_meanings && word.all_english_meanings.length > 1) {
            addExpandButton(card, word, index);
        }

        return card;
    }

    function addExpandButton(card, word, index) {
        const expandBtn = document.createElement('button');
        expandBtn.className = 'expand-btn';
        expandBtn.textContent = '+ Show all meanings';
        let expanded = false;

        expandBtn.addEventListener('click', function() {
            if (!expanded) {
                // Show all meanings
                const additionalDiv = document.createElement('div');
                additionalDiv.className = 'additional-meanings';
                additionalDiv.id = `additional-${index}`;

                if (word.all_english_meanings.length > 1) {
                    const engList = document.createElement('ul');
                    word.all_english_meanings.forEach(meaning => {
                        const li = document.createElement('li');
                        li.textContent = meaning;
                        engList.appendChild(li);
                    });

                    const engLabel = document.createElement('strong');
                    engLabel.textContent = 'All English Meanings:';
                    additionalDiv.appendChild(engLabel);
                    additionalDiv.appendChild(engList);
                }

                if (word.all_hindi_meanings.length > 1) {
                    const hindiList = document.createElement('ul');
                    hindiList.className = 'hindi-text';
                    word.all_hindi_meanings.forEach(meaning => {
                        const li = document.createElement('li');
                        li.textContent = meaning;
                        hindiList.appendChild(li);
                    });

                    const hindiLabel = document.createElement('strong');
                    hindiLabel.textContent = 'सभी हिन्दी अर्थ:';
                    additionalDiv.appendChild(hindiLabel);
                    additionalDiv.appendChild(hindiList);
                }

                card.appendChild(additionalDiv);
                expandBtn.textContent = '- Show less';
                expanded = true;
            } else {
                // Hide additional meanings
                const additionalDiv = document.getElementById(`additional-${index}`);
                if (additionalDiv) {
                    additionalDiv.remove();
                }
                expandBtn.textContent = '+ Show all meanings';
                expanded = false;
            }
        });

        card.appendChild(expandBtn);
    }

    function truncateText(text, maxLength) {
        if (text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength) + '...';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showError(message) {
        resultsContainer.innerHTML = `
            <div style="
                padding: 30px;
                background: #fee;
                border-left: 5px solid #e74c3c;
                border-radius: 10px;
                color: #c0392b;
                font-weight: 500;
                text-align: center;
                grid-column: 1 / -1;
            ">
                <strong>Error:</strong> ${escapeHtml(message)}
            </div>
        `;
    }
});
