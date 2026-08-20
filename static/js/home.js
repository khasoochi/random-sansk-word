document.addEventListener('DOMContentLoaded', async function() {
    const strip = document.getElementById('statsStrip');
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        const genders = Object.entries(data.gender_distribution || {})
            .sort((a, b) => b[1] - a[1])
            .map(([g, n]) => `${g}: ${n.toLocaleString()}`)
            .join(' · ');
        strip.textContent = `${data.total_words.toLocaleString()} words in the dictionary — ${genders}`;
    } catch (e) {
        strip.textContent = '';
    }
});
