document.addEventListener('DOMContentLoaded', function() {
    const board = document.getElementById('wordleBoard');
    const message = document.getElementById('wordleMessage');
    const hintEn = document.getElementById('hintEn');
    const hintHi = document.getElementById('hintHi');
    const submitBtn = document.getElementById('submitGuess');
    const giveUpBtn = document.getElementById('giveUp');
    const newBtn = document.getElementById('newWordle');
    const keyboardEl = document.getElementById('devkeyboard');

    let puzzleId = null;
    let length = 0;
    let maxAttempts = 6;
    let history = [];       // [{guess:[...], feedback:[...]}]
    let slots = [];         // current row buffers
    let activeSlot = 0;
    let gameOver = false;

    DevKeyboard.mount(keyboardEl, {
        onKey: (ch) => {
            if (gameOver) return;
            slots[activeSlot] = (slots[activeSlot] || '') + ch;
            renderBoard();
        },
        onBackspace: () => {
            if (gameOver) return;
            const cur = slots[activeSlot] || '';
            slots[activeSlot] = cur.slice(0, -1);
            renderBoard();
        },
    });

    submitBtn.addEventListener('click', submitGuess);
    giveUpBtn.addEventListener('click', giveUp);
    newBtn.addEventListener('click', startNewGame);

    startNewGame();

    async function startNewGame() {
        message.textContent = '';
        message.className = 'game-message';
        gameOver = false;
        history = [];

        try {
            const res = await fetch('/api/games/wordle/new');
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Failed to load puzzle');

            puzzleId = data.id;
            length = data.length;
            maxAttempts = Math.max(6, length + 2);
            slots = new Array(length).fill('');
            activeSlot = 0;

            hintEn.textContent = data.hint_en;
            hintHi.textContent = data.hint_hi;
            renderBoard();
        } catch (e) {
            message.textContent = 'Could not load a puzzle: ' + e.message;
            message.className = 'game-message error';
        }
    }

    function renderBoard() {
        board.innerHTML = '';
        board.style.setProperty('--wordle-cols', length);

        for (let row = 0; row < maxAttempts; row++) {
            const rowEl = document.createElement('div');
            rowEl.className = 'wordle-row';

            if (row < history.length) {
                const { guess, feedback } = history[row];
                guess.forEach((ak, i) => {
                    const cell = document.createElement('div');
                    cell.className = `wordle-cell filled ${feedback[i]}`;
                    cell.textContent = ak;
                    rowEl.appendChild(cell);
                });
            } else if (row === history.length && !gameOver) {
                for (let i = 0; i < length; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'wordle-cell editable' + (i === activeSlot ? ' active' : '');
                    cell.textContent = slots[i] || '';
                    cell.addEventListener('click', () => { activeSlot = i; renderBoard(); });
                    rowEl.appendChild(cell);
                }
            } else {
                for (let i = 0; i < length; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'wordle-cell';
                    rowEl.appendChild(cell);
                }
            }
            board.appendChild(rowEl);
        }
    }

    async function submitGuess() {
        if (gameOver) return;
        if (slots.some(s => !s)) {
            message.textContent = 'Fill in every akshara before submitting.';
            message.className = 'game-message error';
            return;
        }

        try {
            const res = await fetch('/api/games/wordle/guess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: puzzleId, guess: slots }),
            });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Guess failed');

            history.push({ guess: slots.slice(), feedback: data.feedback });
            slots = new Array(length).fill('');
            activeSlot = 0;

            if (data.solved) {
                gameOver = true;
                message.textContent = `सही! (Correct!) ${data.word} — ${data.english_meaning}`;
                message.className = 'game-message success';
            } else if (history.length >= maxAttempts) {
                gameOver = true;
                giveUp();
                return;
            }
            renderBoard();
        } catch (e) {
            message.textContent = 'Error: ' + e.message;
            message.className = 'game-message error';
        }
    }

    async function giveUp() {
        if (!puzzleId) return;
        gameOver = true;
        try {
            const res = await fetch(`/api/games/wordle/${puzzleId}/reveal`);
            const data = await res.json();
            if (data.success) {
                message.textContent = `Answer: ${data.word} (${data.roman}) — ${data.english_meaning}`;
                message.className = 'game-message info';
            }
        } catch (e) {
            message.textContent = 'Could not reveal the answer.';
            message.className = 'game-message error';
        }
        renderBoard();
    }
});
