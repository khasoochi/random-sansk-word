document.addEventListener('DOMContentLoaded', function() {
    const gridEl = document.getElementById('crosswordGrid');
    const acrossEl = document.getElementById('acrossClues');
    const downEl = document.getElementById('downClues');
    const message = document.getElementById('crosswordMessage');
    const keyboardEl = document.getElementById('devkeyboard');

    let puzzleId = null;
    let rows = 0, cols = 0, words = [];
    let activeCells = new Set();   // "r,c"
    let numberAt = {};             // "r,c" -> number
    let contents = {};             // "r,c" -> current buffer
    let cellStatus = {};           // "r,c" -> 'correct' | 'incorrect' | undefined
    let activeKey = null;
    let gameOver = false;

    DevKeyboard.mount(keyboardEl, {
        onKey: (ch) => {
            if (gameOver || !activeKey) return;
            contents[activeKey] = (contents[activeKey] || '') + ch;
            cellStatus[activeKey] = undefined;
            renderGrid();
        },
        onBackspace: () => {
            if (gameOver || !activeKey) return;
            contents[activeKey] = (contents[activeKey] || '').slice(0, -1);
            cellStatus[activeKey] = undefined;
            renderGrid();
        },
        onClear: () => {
            if (gameOver) return;
            contents = {};
            cellStatus = {};
            renderGrid();
        },
    });

    document.getElementById('checkCrossword').addEventListener('click', checkGrid);
    document.getElementById('giveUpCrossword').addEventListener('click', giveUp);
    document.getElementById('newCrossword').addEventListener('click', startNewGame);

    startNewGame();

    async function startNewGame() {
        message.textContent = '';
        message.className = 'game-message';
        gameOver = false;
        contents = {};
        cellStatus = {};
        activeKey = null;

        try {
            const res = await fetch('/api/games/crossword/new');
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Failed to load puzzle');

            puzzleId = data.id;
            rows = data.rows;
            cols = data.cols;
            words = data.words;

            activeCells = new Set();
            numberAt = {};
            words.forEach(w => {
                for (let k = 0; k < w.length; k++) {
                    const r = w.row + (w.direction === 'down' ? k : 0);
                    const c = w.col + (w.direction === 'across' ? k : 0);
                    activeCells.add(`${r},${c}`);
                }
                const startKey = `${w.row},${w.col}`;
                numberAt[startKey] = w.number;
            });

            const firstAcross = words.find(w => w.direction === 'across');
            activeKey = firstAcross ? `${firstAcross.row},${firstAcross.col}` : null;

            renderGrid();
            renderClues();
        } catch (e) {
            message.textContent = 'Could not load a puzzle: ' + e.message;
            message.className = 'game-message error';
        }
    }

    function renderGrid() {
        gridEl.innerHTML = '';
        gridEl.style.setProperty('--cw-cols', cols);
        gridEl.style.setProperty('--cw-rows', rows);

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const key = `${r},${c}`;
                const cell = document.createElement('div');

                if (!activeCells.has(key)) {
                    cell.className = 'crossword-cell blocked';
                    gridEl.appendChild(cell);
                    continue;
                }

                cell.className = 'crossword-cell active';
                if (key === activeKey) cell.classList.add('selected');
                if (cellStatus[key] === 'correct') cell.classList.add('correct');
                if (cellStatus[key] === 'incorrect') cell.classList.add('incorrect');

                if (numberAt[key]) {
                    const num = document.createElement('span');
                    num.className = 'cell-number';
                    num.textContent = numberAt[key];
                    cell.appendChild(num);
                }

                const text = document.createElement('span');
                text.className = 'cell-text';
                text.textContent = contents[key] || '';
                cell.appendChild(text);

                cell.addEventListener('click', () => {
                    if (gameOver) return;
                    activeKey = key;
                    renderGrid();
                });

                gridEl.appendChild(cell);
            }
        }
    }

    function renderClues() {
        const across = words.filter(w => w.direction === 'across').sort((a, b) => a.number - b.number);
        const down = words.filter(w => w.direction === 'down').sort((a, b) => a.number - b.number);

        acrossEl.innerHTML = across.map(clueItem).join('');
        downEl.innerHTML = down.map(clueItem).join('');

        [...acrossEl.querySelectorAll('li'), ...downEl.querySelectorAll('li')].forEach(li => {
            li.addEventListener('click', () => {
                activeKey = li.dataset.key;
                renderGrid();
            });
        });
    }

    function clueItem(w) {
        return `<li data-key="${w.row},${w.col}">
            <strong>${w.number}.</strong> ${escapeHtml(w.clue_en)}
            <span class="hindi-text clue-hi">${escapeHtml(w.clue_hi)}</span>
            <span class="clue-length">(${w.length} akshara${w.length > 1 ? 's' : ''})</span>
        </li>`;
    }

    async function checkGrid() {
        const cells = {};
        Object.entries(contents).forEach(([k, v]) => { if (v) cells[k] = v; });

        try {
            const res = await fetch('/api/games/crossword/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: puzzleId, cells }),
            });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Check failed');

            cellStatus = {};
            Object.entries(data.results).forEach(([k, ok]) => {
                cellStatus[k] = ok ? 'correct' : 'incorrect';
            });

            if (data.solved) {
                gameOver = true;
                message.textContent = 'शाबाश! (Well done!) Crossword solved.';
                message.className = 'game-message success';
            } else {
                message.textContent = 'Some aksharas are missing or incorrect.';
                message.className = 'game-message error';
            }
            renderGrid();
        } catch (e) {
            message.textContent = 'Error: ' + e.message;
            message.className = 'game-message error';
        }
    }

    async function giveUp() {
        if (!puzzleId) return;
        gameOver = true;
        try {
            const res = await fetch(`/api/games/crossword/${puzzleId}/reveal`);
            const data = await res.json();
            if (data.success) {
                contents = { ...data.cells };
                cellStatus = {};
                Object.keys(data.cells).forEach(k => cellStatus[k] = 'correct');
                message.textContent = 'Answers revealed.';
                message.className = 'game-message info';
                renderGrid();
            }
        } catch (e) {
            message.textContent = 'Could not reveal the answer.';
            message.className = 'game-message error';
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
});
