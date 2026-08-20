// Random word generator page

document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generateBtn');
    const wordCountInput = document.getElementById('wordCount');
    const resultsContainer = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');

    loadStats();
    generateBtn.addEventListener('click', generateWords);
    wordCountInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') generateWords();
    });
    generateWords();

    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            if (data.total_words) {
                document.getElementById('totalWords').textContent =
                    `${data.total_words.toLocaleString()} words available`;
            }
        } catch (error) {
            document.getElementById('totalWords').textContent = 'Stats unavailable';
        }
    }

    async function generateWords() {
        const count = parseInt(wordCountInput.value) || 5;
        if (count < 1 || count > 100) {
            alert('Please enter a number between 1 and 100');
            return;
        }

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
            resultsContainer.appendChild(createWordCard(word, index));
        });
    }

    function createWordCard(word, index) {
        const card = document.createElement('div');
        card.className = 'word-card';
        card.style.animationDelay = `${index * 0.06}s`;
        const genderClass = `gender-${word.gender.toLowerCase()}`;

        card.innerHTML = `
            <div class="word-header">
                <div class="sanskrit-word">${escapeHtml(word.sanskrit)}</div>
                <span class="gender-badge ${genderClass}">${escapeHtml(word.gender)}</span>
            </div>
            <div class="roman-word">${escapeHtml(word.roman || '')}</div>
            <div class="meaning-section">
                <div class="meaning-label">English Meaning</div>
                <div class="meaning-text">${escapeHtml(truncateText(word.english_meaning, 220))}</div>
            </div>
            <div class="meaning-section">
                <div class="meaning-label">हिन्दी अर्थ</div>
                <div class="meaning-text hindi-text">${escapeHtml(truncateText(word.hindi_meaning, 220))}</div>
            </div>
        `;

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
                const additionalDiv = document.createElement('div');
                additionalDiv.className = 'additional-meanings';
                additionalDiv.id = `additional-${index}`;

                if (word.all_english_meanings.length > 1) {
                    const engLabel = document.createElement('strong');
                    engLabel.textContent = 'All English Meanings:';
                    additionalDiv.appendChild(engLabel);
                    const engList = document.createElement('ul');
                    word.all_english_meanings.forEach(m => {
                        const li = document.createElement('li');
                        li.textContent = m;
                        engList.appendChild(li);
                    });
                    additionalDiv.appendChild(engList);
                }

                if (word.all_hindi_meanings.length > 1) {
                    const hindiLabel = document.createElement('strong');
                    hindiLabel.textContent = 'सभी हिन्दी अर्थ:';
                    additionalDiv.appendChild(hindiLabel);
                    const hindiList = document.createElement('ul');
                    hindiList.className = 'hindi-text';
                    word.all_hindi_meanings.forEach(m => {
                        const li = document.createElement('li');
                        li.textContent = m;
                        hindiList.appendChild(li);
                    });
                    additionalDiv.appendChild(hindiList);
                }

                card.appendChild(additionalDiv);
                expandBtn.textContent = '- Show less';
                expanded = true;
            } else {
                const additionalDiv = document.getElementById(`additional-${index}`);
                if (additionalDiv) additionalDiv.remove();
                expandBtn.textContent = '+ Show all meanings';
                expanded = false;
            }
        });

        card.appendChild(expandBtn);
    }

    function truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showError(message) {
        resultsContainer.innerHTML = `<div class="error-box">${escapeHtml(message)}</div>`;
    }
});
