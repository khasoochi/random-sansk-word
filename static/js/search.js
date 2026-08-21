document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('searchInput');
    const regexToggle = document.getElementById('regexToggle');
    const suggestions = document.getElementById('suggestions');
    const results = document.getElementById('results');
    const loading = document.getElementById('loading');
    const statsEl = document.getElementById('searchStats');

    let debounceTimer = null;
    let suggestDebounce = null;
    let activeSuggestion = -1;

    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        clearTimeout(suggestDebounce);
        const q = input.value.trim();

        if (!q) {
            results.innerHTML = '';
            suggestions.innerHTML = '';
            suggestions.classList.remove('open');
            statsEl.textContent = '';
            return;
        }

        suggestDebounce = setTimeout(() => fetchSuggestions(q), 150);
        debounceTimer = setTimeout(() => runSearch(q), 350);
    });

    regexToggle.addEventListener('change', function() {
        const q = input.value.trim();
        if (q) runSearch(q);
    });

    input.addEventListener('keydown', function(e) {
        const items = suggestions.querySelectorAll('.suggestion-item');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeSuggestion = Math.min(activeSuggestion + 1, items.length - 1);
            highlightSuggestion(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeSuggestion = Math.max(activeSuggestion - 1, -1);
            highlightSuggestion(items);
        } else if (e.key === 'Enter') {
            if (activeSuggestion >= 0 && items[activeSuggestion]) {
                input.value = items[activeSuggestion].dataset.word;
            }
            suggestions.classList.remove('open');
            runSearch(input.value.trim());
        } else if (e.key === 'Escape') {
            suggestions.classList.remove('open');
        }
    });

    document.addEventListener('click', function(e) {
        if (!suggestions.contains(e.target) && e.target !== input) {
            suggestions.classList.remove('open');
        }
    });

    function highlightSuggestion(items) {
        items.forEach((el, i) => el.classList.toggle('active', i === activeSuggestion));
    }

    async function fetchSuggestions(q) {
        try {
            const res = await fetch(`/api/suggest?q=${encodeURIComponent(q)}&limit=8`);
            const data = await res.json();
            activeSuggestion = -1;
            if (!data.success || !data.results.length) {
                suggestions.innerHTML = '';
                suggestions.classList.remove('open');
                return;
            }
            suggestions.innerHTML = data.results.map(r =>
                `<div class="suggestion-item" data-word="${escapeAttr(r.sanskrit)}">
                    <span class="sug-deva">${escapeHtml(r.sanskrit)}</span>
                    <span class="sug-roman">${escapeHtml(r.roman)}</span>
                </div>`
            ).join('');
            suggestions.classList.add('open');
            suggestions.querySelectorAll('.suggestion-item').forEach(el => {
                el.addEventListener('click', () => {
                    input.value = el.dataset.word;
                    suggestions.classList.remove('open');
                    runSearch(input.value);
                });
            });
        } catch (e) {
            // silently ignore suggestion failures
        }
    }

    async function runSearch(q) {
        if (!q) return;
        suggestions.classList.remove('open');
        loading.style.display = 'block';
        results.innerHTML = '';

        try {
            const params = new URLSearchParams({ q, regex: regexToggle.checked ? '1' : '0' });
            const res = await fetch(`/api/search?${params}`);
            const data = await res.json();

            if (!data.success) {
                statsEl.textContent = '';
                results.innerHTML = `<div class="error-box">${escapeHtml(data.error || 'Search failed')}</div>`;
                return;
            }

            statsEl.textContent = `${data.count} result${data.count === 1 ? '' : 's'}`;
            if (data.count === 0) {
                results.innerHTML = `<div class="empty-box">No matches found.</div>`;
                return;
            }

            results.innerHTML = data.results.map(word => `
                <div class="word-card">
                    <div class="word-header">
                        <div class="sanskrit-word">${escapeHtml(word.sanskrit)}</div>
                        <span class="gender-badge gender-${word.gender.toLowerCase()}">${escapeHtml(word.gender)}</span>
                    </div>
                    <div class="roman-word">${escapeHtml(word.roman || '')}</div>
                    <div class="meaning-section">
                        <div class="meaning-label">English Meaning</div>
                        <div class="meaning-text">${escapeHtml(word.english_meaning)}</div>
                    </div>
                    <div class="meaning-section">
                        <div class="meaning-label">हिन्दी अर्थ</div>
                        <div class="meaning-text hindi-text">${escapeHtml(word.hindi_meaning)}</div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            results.innerHTML = `<div class="error-box">Network error: ${escapeHtml(e.message)}</div>`;
        } finally {
            loading.style.display = 'none';
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    function escapeAttr(text) {
        return escapeHtml(text).replace(/"/g, '&quot;');
    }
});
