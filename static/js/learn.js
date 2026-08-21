document.addEventListener('DOMContentLoaded', function() {
    const card = document.getElementById('flashcard');
    const nextBtn = document.getElementById('nextBtn');
    const countEl = document.getElementById('learnCount');
    let count = 0;
    let flipped = false;

    card.addEventListener('click', function() {
        flipped = !flipped;
        card.classList.toggle('flipped', flipped);
    });

    nextBtn.addEventListener('click', loadNext);
    loadNext();

    async function loadNext() {
        try {
            const res = await fetch('/api/random?count=1');
            const data = await res.json();
            if (!data.success || !data.words.length) return;
            const word = data.words[0];

            flipped = false;
            card.classList.remove('flipped');

            document.getElementById('flashDeva').textContent = word.sanskrit;
            document.getElementById('flashRoman').textContent = word.roman || '';
            document.getElementById('flashDevaBack').textContent = word.sanskrit;
            const genderBadge = document.getElementById('flashGender');
            genderBadge.textContent = word.gender;
            genderBadge.className = `gender-badge gender-${word.gender.toLowerCase()}`;
            document.getElementById('flashEnglish').textContent = word.english_meaning;
            document.getElementById('flashHindi').textContent = word.hindi_meaning;

            count += 1;
            countEl.textContent = `Card ${count}`;
        } catch (e) {
            document.getElementById('flashDeva').textContent = 'त्रुटि';
        }
    }
});
