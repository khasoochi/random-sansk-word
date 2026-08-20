document.addEventListener('DOMContentLoaded', function() {
    const answerEl = document.getElementById('scrambleAnswer');
    const bankEl = document.getElementById('scrambleBank');
    const message = document.getElementById('scrambleMessage');
    const hintEn = document.getElementById('hintEn');
    const hintHi = document.getElementById('hintHi');

    let puzzleId = null;
    let bank = [];     // [{ak, used}]
    let answer = [];   // indices into bank, in chosen order
    let gameOver = false;

    document.getElementById('checkScramble').addEventListener('click', checkAnswer);
    document.getElementById('resetScramble').addEventListener('click', resetAnswer);
    document.getElementById('giveUpScramble').addEventListener('click', giveUp);
    document.getElementById('newScramble').addEventListener('click', startNewGame);

    startNewGame();

    async function startNewGame() {
        message.textContent = '';
        message.className = 'game-message';
        gameOver = false;

        try {
            const res = await fetch('/api/games/scramble/new');
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Failed to load puzzle');

            puzzleId = data.id;
            bank = data.scrambled.map(ak => ({ ak, used: false }));
            answer = [];
            hintEn.textContent = data.hint_en;
            hintHi.textContent = data.hint_hi;
            render();
        } catch (e) {
            message.textContent = 'Could not load a puzzle: ' + e.message;
            message.className = 'game-message error';
        }
    }

    function render() {
        answerEl.innerHTML = '';
        answer.forEach((idx) => {
            const tile = document.createElement('div');
            tile.className = 'scramble-tile answer-tile';
            tile.textContent = bank[idx].ak;
            tile.addEventListener('click', () => {
                if (gameOver) return;
                answer = answer.filter(i => i !== idx);
                bank[idx].used = false;
                render();
            });
            answerEl.appendChild(tile);
        });
        for (let i = answer.length; i < bank.length; i++) {
            const placeholder = document.createElement('div');
            placeholder.className = 'scramble-tile placeholder';
            answerEl.appendChild(placeholder);
        }

        bankEl.innerHTML = '';
        bank.forEach((item, idx) => {
            const tile = document.createElement('div');
            tile.className = 'scramble-tile bank-tile' + (item.used ? ' used' : '');
            tile.textContent = item.ak;
            if (!item.used) {
                tile.addEventListener('click', () => {
                    if (gameOver) return;
                    item.used = true;
                    answer.push(idx);
                    render();
                });
            }
            bankEl.appendChild(tile);
        });
    }

    function resetAnswer() {
        if (gameOver) return;
        answer = [];
        bank.forEach(b => b.used = false);
        render();
    }

    async function checkAnswer() {
        if (gameOver || answer.length !== bank.length) {
            message.textContent = 'Use all the aksharas before checking.';
            message.className = 'game-message error';
            return;
        }
        const order = answer.map(idx => bank[idx].ak);

        try {
            const res = await fetch('/api/games/scramble/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: puzzleId, order }),
            });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Check failed');

            if (data.correct) {
                gameOver = true;
                message.textContent = `सही! (Correct!) ${data.word} — ${data.english_meaning}`;
                message.className = 'game-message success';
            } else {
                message.textContent = 'Not quite — try rearranging.';
                message.className = 'game-message error';
            }
        } catch (e) {
            message.textContent = 'Error: ' + e.message;
            message.className = 'game-message error';
        }
    }

    async function giveUp() {
        if (!puzzleId) return;
        gameOver = true;
        try {
            const res = await fetch(`/api/games/scramble/${puzzleId}/reveal`);
            const data = await res.json();
            if (data.success) {
                message.textContent = `Answer: ${data.word} (${data.roman}) — ${data.english_meaning}`;
                message.className = 'game-message info';
            }
        } catch (e) {
            message.textContent = 'Could not reveal the answer.';
            message.className = 'game-message error';
        }
    }
});
