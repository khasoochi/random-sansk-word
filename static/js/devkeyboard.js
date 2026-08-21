// Reusable virtual Devanagari keyboard for building one akshara at a time.
// Devanagari is an abugida: a "letter" the player types is a consonant
// (optionally joined into a conjunct via halant) plus a vowel sign, or a
// standalone independent vowel. This widget exposes taps on those units;
// the calling page decides how to accumulate them into an akshara slot.

const DevKeyboard = (function() {
    const VOWELS = ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ'];
    const CONSONANT_ROWS = [
        ['क', 'ख', 'ग', 'घ', 'ङ'],
        ['च', 'छ', 'ज', 'झ', 'ञ'],
        ['ट', 'ठ', 'ड', 'ढ', 'ण'],
        ['त', 'थ', 'द', 'ध', 'न'],
        ['प', 'फ', 'ब', 'भ', 'म'],
        ['य', 'र', 'ल', 'व'],
        ['श', 'ष', 'स', 'ह', 'ळ'],
    ];
    const MATRAS = [
        { label: 'ा', value: 'ा' }, { label: 'ि', value: 'ि' }, { label: 'ी', value: 'ी' },
        { label: 'ु', value: 'ु' }, { label: 'ू', value: 'ू' }, { label: 'ृ', value: 'ृ' },
        { label: 'े', value: 'े' }, { label: 'ै', value: 'ै' }, { label: 'ो', value: 'ो' },
        { label: 'ौ', value: 'ौ' }, { label: 'ं', value: 'ं' }, { label: 'ः', value: 'ः' },
    ];

    function mount(container, { onKey, onBackspace, onClear }) {
        container.innerHTML = '';
        container.className = 'devkeyboard';

        const makeRow = (className) => {
            const row = document.createElement('div');
            row.className = `dk-row ${className}`;
            container.appendChild(row);
            return row;
        };

        const makeBtn = (row, label, value, extraClass) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `dk-key ${extraClass || ''}`;
            btn.textContent = label;
            btn.addEventListener('click', () => onKey(value));
            row.appendChild(btn);
        };

        const vowelRow = makeRow('dk-vowels');
        VOWELS.forEach(v => makeBtn(vowelRow, v, v));

        CONSONANT_ROWS.forEach(rowChars => {
            const row = makeRow('dk-consonants');
            rowChars.forEach(c => makeBtn(row, c, c));
        });

        const matraRow = makeRow('dk-matras');
        MATRAS.forEach(m => makeBtn(matraRow, m.label, m.value));
        makeBtn(matraRow, '्', '्', 'dk-halant');

        const controlRow = makeRow('dk-controls');
        const backBtn = document.createElement('button');
        backBtn.type = 'button';
        backBtn.className = 'dk-key dk-backspace';
        backBtn.textContent = '⌫ Backspace';
        backBtn.addEventListener('click', onBackspace);
        controlRow.appendChild(backBtn);

        if (onClear) {
            const clearBtn = document.createElement('button');
            clearBtn.type = 'button';
            clearBtn.className = 'dk-key dk-clear';
            clearBtn.textContent = 'Clear Row';
            clearBtn.addEventListener('click', onClear);
            controlRow.appendChild(clearBtn);
        }
    }

    return { mount };
})();
