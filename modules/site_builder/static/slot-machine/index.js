// ==========================================
// 수요일 다이어트 심판대 - Main JavaScript
// ==========================================

// ==========================================
// State Management
// ==========================================
const state = {
    penalties: [],
    rewards: [],
    history: [],
    selectedPerson: null,
    soundEnabled: true,
    isSpinning: false
};

// Get the most recent Wednesday (before or equal to today) in Korean timezone
function getLastWednesday() {
    // Get current time in Korean timezone (UTC+9)
    const now = new Date();
    const koreaOffset = 9 * 60; // UTC+9 in minutes
    const localOffset = now.getTimezoneOffset(); // local offset in minutes (negative for east)
    const koreaTime = new Date(now.getTime() + (koreaOffset + localOffset) * 60 * 1000);

    const dayOfWeek = koreaTime.getDay(); // 0=Sun, 1=Mon, ..., 3=Wed, ..., 6=Sat

    // Calculate days to subtract to get to the most recent Wednesday
    let daysToSubtract;
    if (dayOfWeek === 3) {
        daysToSubtract = 0; // Today is Wednesday
    } else if (dayOfWeek > 3) {
        daysToSubtract = dayOfWeek - 3; // After Wednesday (Thu=1, Fri=2, Sat=3)
    } else {
        daysToSubtract = dayOfWeek + 4; // Before Wednesday (Sun=4, Mon=5, Tue=6)
    }

    const lastWednesday = new Date(koreaTime);
    lastWednesday.setDate(koreaTime.getDate() - daysToSubtract);

    // Format as YYYY-MM-DD
    const year = lastWednesday.getFullYear();
    const month = String(lastWednesday.getMonth() + 1).padStart(2, '0');
    const day = String(lastWednesday.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Format date for display (M/D (요일))
function formatDateForDisplay(dateStr) {
    if (!dateStr) return '날짜없음';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;

    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10);
    const day = parseInt(parts[2], 10);

    const date = new Date(year, month - 1, day);
    const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
    const weekday = weekdays[date.getDay()];

    return `${month}/${day}(${weekday})`;
}

// ==========================================
// DOM Elements
// ==========================================
const elements = {
    // Sound
    soundToggle: document.getElementById('sound-toggle'),

    // Options
    penaltyInput: document.getElementById('penalty-input'),
    addPenaltyBtn: document.getElementById('add-penalty'),
    penaltyList: document.getElementById('penalty-list'),
    rewardInput: document.getElementById('reward-input'),
    addRewardBtn: document.getElementById('add-reward'),
    rewardList: document.getElementById('reward-list'),

    // Person Selection
    husbandBtn: document.getElementById('select-husband'),
    wifeBtn: document.getElementById('select-wife'),
    selectedPersonText: document.getElementById('selected-person'),

    // Slot Machine
    spinBtn: document.getElementById('spin-btn'),
    reel: document.getElementById('reel-main'),
    reelInner: document.getElementById('reel-inner'),

    // Modal
    modal: document.getElementById('result-modal'),
    resultEmoji: document.getElementById('result-emoji'),
    resultTitle: document.getElementById('result-title'),
    resultDescription: document.getElementById('result-description'),
    resultTarget: document.getElementById('result-target'),
    closeModalBtn: document.getElementById('close-modal'),
    resultContent: document.getElementById('result-content'),

    // D-Day & Motivation
    ddayCount: document.getElementById('dday-count'),
    successCount: document.getElementById('success-count'),
    motivationMessage: document.getElementById('motivation-message'),

    // History
    historyList: document.getElementById('history-list'),
    clearHistoryBtn: document.getElementById('clear-history'),

    // Confetti
    confettiContainer: document.getElementById('confetti-container')
};

// ==========================================
// Sound System (Web Audio API)
// ==========================================
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

const sounds = {
    spin: () => {
        if (!state.soundEnabled) return;
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.setValueAtTime(200, audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(800, audioContext.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    },

    tick: () => {
        if (!state.soundEnabled) return;
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.setValueAtTime(400 + Math.random() * 200, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.06, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.03);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.03);
    },

    win: () => {
        if (!state.soundEnabled) return;
        const notes = [523.25, 659.25, 783.99, 1046.50];
        notes.forEach((freq, i) => {
            setTimeout(() => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                oscillator.frequency.setValueAtTime(freq, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.3);
            }, i * 100);
        });
    },

    penalty: () => {
        if (!state.soundEnabled) return;
        const notes = [392, 349.23, 311.13, 293.66];
        notes.forEach((freq, i) => {
            setTimeout(() => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                oscillator.type = 'sawtooth';
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                oscillator.frequency.setValueAtTime(freq, audioContext.currentTime);
                gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.4);
            }, i * 200);
        });
    },

    click: () => {
        if (!state.soundEnabled) return;
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.setValueAtTime(1000, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.03);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.03);
    }
};

// ==========================================
// Local Storage
// ==========================================
const storage = {
    save: () => {
        localStorage.setItem('dietSlotMachine', JSON.stringify({
            penalties: state.penalties,
            rewards: state.rewards,
            history: state.history,
            soundEnabled: state.soundEnabled
        }));
    },

    load: () => {
        const saved = localStorage.getItem('dietSlotMachine');
        if (saved) {
            const data = JSON.parse(saved);
            state.penalties = data.penalties || [];
            state.rewards = data.rewards || [];
            state.history = data.history || [];
            state.soundEnabled = data.soundEnabled !== false;
        }
    }
};

// ==========================================
// Render Functions
// ==========================================
function renderOptions(type) {
    const list = type === 'penalty' ? elements.penaltyList : elements.rewardList;
    const items = type === 'penalty' ? state.penalties : state.rewards;

    if (items.length === 0) {
        list.innerHTML = `<li class="empty-message">${type === 'penalty' ? '무시무시한 벌칙을 추가하세요! 😈' : '달콤한 보상을 추가하세요! 🎁'}</li>`;
        return;
    }

    list.innerHTML = items.map((item, index) => `
        <li class="option-item">
            <span>${type === 'penalty' ? '💀' : '⭐'} ${item}</span>
            <button class="delete-btn" data-type="${type}" data-index="${index}">×</button>
        </li>
    `).join('');
}

function renderHistory() {
    if (state.history.length === 0) {
        elements.historyList.innerHTML = '<li class="empty-history">아직 심판 기록이 없어요! 💪</li>';
        return;
    }

    elements.historyList.innerHTML = state.history.map((item, index) => `
        <li class="history-item ${item.completed ? 'completed' : ''}">
            <input type="checkbox" class="history-checkbox" data-index="${index}" ${item.completed ? 'checked' : ''}>
            <span class="history-type">${item.type === 'penalty' ? '😈' : '🎁'}</span>
            <span class="history-text">${item.person} → ${item.option}</span>
            <span class="history-date">
                <span class="history-date-text" data-index="${index}" title="클릭해서 날짜 변경">${formatDateForDisplay(item.rawDate)}</span>
            </span>
            <button class="history-delete-btn" data-index="${index}" title="삭제">🗑️</button>
        </li>
    `).join('');
}

// ==========================================
// Motivational Messages
// ==========================================
const motivationalMessages = [
    "오늘 하루도 건강한 선택을 했다면, 그게 바로 성공이에요! 💪",
    "체중계 숫자보다 중요한 건 꾸준함이에요! 🔥",
    "부부가 함께하는 다이어트, 성공 확률 2배! 👫",
    "오늘 운동 안 해도 괜찮아요. 내일 하면 되니까! 🌟",
    "작은 변화가 큰 결과를 만들어요! ✨",
    "치팅데이도 다이어트의 일부예요! 🍕",
    "서로를 응원하는 것만으로도 이미 절반은 성공! 💕",
    "건강해지는 게 목표지, 숫자가 목표가 아니에요! 🎯",
    "오늘 샐러드 먹은 당신, 정말 대단해요! 🥗",
    "매주 수요일, 함께 성장하는 우리! 💪",
    "다이어트는 마라톤이에요. 천천히 가도 괜찮아요! 🏃",
    "오늘도 건강한 하루 보내세요! ☀️",
    "실패해도 괜찮아요. 다시 시작하면 되니까! 🌈",
    "부부가 함께면 못할 게 없어요! 👨‍❤️‍👩",
    "건강한 식단 = 행복한 내일! 🥦",
    "운동 후의 뿌듯함을 기억하세요! 💪",
    "오늘의 노력이 내일의 몸을 만들어요! 🏆",
    "물 한 잔 더 마셨다면 오늘도 성공! 💧",
    "계단 오르기도 훌륭한 운동이에요! 🏃‍♀️",
    "당신의 노력을 응원해요! 📣",
    "건강한 몸에 건강한 마음이 깃들어요! 🧘",
    "오늘 야식 참았다면 스스로 칭찬해주세요! 🌙",
    "작은 목표 달성이 큰 자신감을 만들어요! 🎖️",
    "함께라서 더 즐거운 다이어트! 😊",
    "지금 이 순간에도 변화하고 있어요! 🔄",
    "포기하지 않는 것이 가장 중요해요! 💎",
    "건강한 습관이 건강한 인생을 만들어요! 🌿",
    "오늘 하루도 최선을 다한 당신, 멋져요! ⭐",
    "몸이 가벼워지면 마음도 가벼워져요! 🕊️",
    "서로에게 좋은 영향을 주는 부부! 👏",
    "다이어트는 사랑이에요. 자신을 사랑하세요! ❤️",
    "조금씩, 하지만 꾸준히! 이게 비결이에요! 🐢",
    "오늘의 절제가 내일의 자유를 만들어요! 🦅",
    "건강한 body, 건강한 mind! 🧠",
    "당신은 이미 충분히 잘하고 있어요! 👍",
    "수요일마다 점검하는 우리, 정말 대단해요! 📅",
    "실패는 성공의 어머니! 다시 도전! 🔂",
    "오늘 먹은 건강식이 내일의 에너지예요! ⚡",
    "부부 동반 다이어트, 이혼율도 낮춰요! 😄",
    "스트레스 받지 마세요. 다이어트도 즐겁게! 🎈",
    "건강한 식사는 맛있어도 돼요! 🍽️",
    "오늘 조금 덜 먹었다면 대성공! 🎉",
    "운동은 선택, 건강은 필수! 🏋️",
    "당신의 의지력에 박수를! 👏",
    "함께 걷는 산책도 훌륭한 운동! 🚶‍♂️🚶‍♀️",
    "매일 조금씩 나아지고 있어요! 📈",
    "건강한 당신이 가장 아름다워요! 🌷",
    "오늘도 화이팅! 내일도 화이팅! 🔥🔥",
    "다이어트 파트너가 있다는 건 행운이에요! 🍀",
    "1kg 빠지면 파티하기로 해요! 🎊"
];

function getRandomMotivation() {
    return motivationalMessages[Math.floor(Math.random() * motivationalMessages.length)];
}

// ==========================================
// D-Day & Success Calculation
// ==========================================
const DIET_START_DATE = '2026-01-07'; // 다이어트 시작일

function calculateDday() {
    const startDate = new Date(DIET_START_DATE);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    startDate.setHours(0, 0, 0, 0);

    const diffTime = today - startDate;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(0, diffDays);
}

function getWednesdaysBetween(startDate, endDate) {
    const wednesdays = [];
    const current = new Date(startDate);
    current.setHours(0, 0, 0, 0);

    // Move to first Wednesday
    while (current.getDay() !== 3) {
        current.setDate(current.getDate() + 1);
    }

    // Collect all Wednesdays
    while (current <= endDate) {
        wednesdays.push(current.toISOString().split('T')[0]);
        current.setDate(current.getDate() + 7);
    }

    return wednesdays;
}

function calculateRemainingWednesdays() {
    const endDate = new Date('2026-04-12'); // 다이어트 종료일
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    endDate.setHours(0, 0, 0, 0);

    // Start from tomorrow if today is Wednesday, otherwise start from today
    const startDate = new Date(today);
    if (startDate.getDay() === 3) {
        startDate.setDate(startDate.getDate() + 1); // Exclude today if Wednesday
    }

    let count = 0;
    const current = new Date(startDate);

    // Move to next Wednesday
    while (current.getDay() !== 3) {
        current.setDate(current.getDate() + 1);
    }

    // Count remaining Wednesdays
    while (current <= endDate) {
        count++;
        current.setDate(current.getDate() + 7);
    }

    return count;
}

function renderMotivation() {
    // Update D-Day
    const dday = calculateDday();
    elements.ddayCount.textContent = dday;

    // Update Remaining Wednesdays
    const remaining = calculateRemainingWednesdays();
    elements.successCount.textContent = remaining;

    // Update Motivation Message (random on each render)
    elements.motivationMessage.textContent = getRandomMotivation();
}

function updateSpinButton() {
    const hasOptions = state.penalties.length > 0 || state.rewards.length > 0;
    const hasSelection = state.selectedPerson !== null;
    elements.spinBtn.disabled = !hasOptions || !hasSelection || state.isSpinning;
}

// ==========================================
// Option Management
// ==========================================
function addOption(type) {
    const input = type === 'penalty' ? elements.penaltyInput : elements.rewardInput;
    const value = input.value.trim();

    if (!value) return;

    if (type === 'penalty') {
        state.penalties.push(value);
    } else {
        state.rewards.push(value);
    }

    input.value = '';
    sounds.click();
    renderOptions(type);
    updateSpinButton();
    populateReel();
    storage.save();
}

function deleteOption(type, index) {
    if (type === 'penalty') {
        state.penalties.splice(index, 1);
    } else {
        state.rewards.splice(index, 1);
    }

    sounds.click();
    renderOptions(type);
    updateSpinButton();
    populateReel();
    storage.save();
}

// ==========================================
// Person Selection
// ==========================================
function selectPerson(person) {
    state.selectedPerson = person;

    elements.husbandBtn.classList.toggle('selected', person === '남편');
    elements.wifeBtn.classList.toggle('selected', person === '아내');

    const emoji = person === '남편' ? '🧔' : '👩';
    elements.selectedPersonText.textContent = `⚠️ ${emoji} ${person}이(가) 이번 주 다이어트에 실패했습니다!`;

    sounds.click();
    updateSpinButton();
}

// ==========================================
// Slot Machine - Smooth Animation
// ==========================================
function getAllOptions() {
    return [
        ...state.penalties.map(p => ({ type: 'penalty', value: p })),
        ...state.rewards.map(r => ({ type: 'reward', value: r }))
    ];
}

function populateReel() {
    const allOptions = getAllOptions();

    if (allOptions.length === 0) {
        elements.reelInner.innerHTML = '<div class="reel-item">옵션을 추가해주세요!</div>';
        return;
    }

    // Create enough copies for smooth spinning
    let html = '';
    const copies = Math.max(50, allOptions.length * 8);
    for (let i = 0; i < copies; i++) {
        const option = allOptions[i % allOptions.length];
        const typeClass = option.type === 'penalty' ? 'penalty' : 'reward';
        const emoji = option.type === 'penalty' ? '😈' : '🎁';
        html += `<div class="reel-item ${typeClass}">${emoji} ${option.value}</div>`;
    }
    elements.reelInner.innerHTML = html;
    elements.reelInner.style.transform = 'translateY(0)';
}

async function spin() {
    if (state.isSpinning) return;

    const allOptions = getAllOptions();
    if (allOptions.length === 0) return;

    state.isSpinning = true;
    elements.spinBtn.classList.add('spinning');
    updateSpinButton();

    // Random result
    const resultIndex = Math.floor(Math.random() * allOptions.length);
    const result = allOptions[resultIndex];

    // Populate reel
    populateReel();

    const itemHeight = 60;
    const spinDuration = 3500;
    const totalSpins = 5; // Number of full rotations
    const finalPosition = (totalSpins * allOptions.length + resultIndex) * itemHeight;

    sounds.spin();

    const startTime = performance.now();
    let lastTickTime = 0;

    const animate = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / spinDuration, 1);

        // Cubic ease-out for natural deceleration
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentPosition = easeOut * finalPosition;

        elements.reelInner.style.transform = `translateY(-${currentPosition}px)`;

        // Play tick sound with decreasing frequency
        const tickInterval = 50 + (progress * 150); // Starts fast, slows down
        if (elapsed - lastTickTime > tickInterval && progress < 0.95) {
            sounds.tick();
            lastTickTime = elapsed;
        }

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            // Ensure exact final position
            const exactPosition = (resultIndex % allOptions.length) * itemHeight;
            elements.reelInner.style.transform = `translateY(-${exactPosition}px)`;

            setTimeout(() => showResult(result), 200);
        }
    };

    requestAnimationFrame(animate);
}

// ==========================================
// Result Display
// ==========================================
function showResult(result) {
    const isPenalty = result.type === 'penalty';
    const targetPerson = isPenalty ? state.selectedPerson : (state.selectedPerson === '남편' ? '아내' : '남편');

    elements.resultEmoji.textContent = isPenalty ? '😈💀' : '🎁✨';
    elements.resultTitle.textContent = isPenalty ? '벌칙이다!' : '보상이다!';
    elements.resultTitle.style.color = isPenalty ? 'var(--penalty-color)' : 'var(--reward-color)';
    elements.resultDescription.textContent = result.value;

    // Dynamic button text based on result type
    if (isPenalty) {
        elements.resultTarget.textContent = `👉 ${targetPerson}! 실패의 대가를 치러라! 😈`;
        elements.closeModalBtn.textContent = '알겠어요... 😭';
        elements.closeModalBtn.className = 'modal-btn close-btn penalty-style';
    } else {
        elements.resultTarget.textContent = `👉 ${targetPerson}! 성공의 보상을 받아라! 🎉`;
        elements.closeModalBtn.textContent = '신난다! 🥳';
        elements.closeModalBtn.className = 'modal-btn close-btn reward-style';
    }

    elements.modal.classList.remove('hidden');

    if (isPenalty) {
        sounds.penalty();
        createConfetti('😈', 20);
    } else {
        sounds.win();
        createConfetti('🎉', 50);
    }

    // Add to history with last Wednesday date
    const lastWed = getLastWednesday();
    const historyItem = {
        type: result.type,
        option: result.value,
        person: targetPerson,
        rawDate: lastWed, // Store raw date for editing
        completed: false
    };

    state.history.unshift(historyItem);
    if (state.history.length > 50) state.history.pop();

    renderHistory();
    renderMotivation();
    storage.save();

    state.isSpinning = false;
    elements.spinBtn.classList.remove('spinning');
    updateSpinButton();
}

function closeModal() {
    elements.modal.classList.add('hidden');
    sounds.click();
}

// ==========================================
// Confetti Effect
// ==========================================
function createConfetti(emoji, count) {
    elements.confettiContainer.innerHTML = '';

    const emojis = emoji === '🎉'
        ? ['🎉', '✨', '💫', '⭐', '🌟', '💪', '🏆']
        : ['😈', '💀', '🔥', '⚡', '💣'];

    for (let i = 0; i < count; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.textContent = emojis[Math.floor(Math.random() * emojis.length)];
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.animationDelay = Math.random() * 2 + 's';
        confetti.style.fontSize = (Math.random() * 20 + 15) + 'px';
        elements.confettiContainer.appendChild(confetti);
    }

    setTimeout(() => {
        elements.confettiContainer.innerHTML = '';
    }, 5000);
}

// ==========================================
// History Date Editing
// ==========================================
function showDatePicker(index, element) {
    // Create inline date input
    const currentDate = state.history[index].rawDate;
    const input = document.createElement('input');
    input.type = 'date';
    input.className = 'history-date-input';
    input.value = currentDate;

    // Replace text with input
    element.replaceWith(input);
    input.focus();

    // Handle date change
    input.addEventListener('change', (e) => {
        state.history[index].rawDate = e.target.value;
        storage.save();
        renderHistory();
        sounds.click();
    });

    // Handle blur (click outside)
    input.addEventListener('blur', () => {
        renderHistory();
    });

    // Handle escape key
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            renderHistory();
        }
    });
}

// ==========================================
// History Management
// ==========================================
function toggleHistoryItem(index) {
    state.history[index].completed = !state.history[index].completed;
    sounds.click();
    renderHistory();
    storage.save();
}

function deleteHistoryItem(index) {
    const item = state.history[index];
    const message = `이 기록을 삭제하시겠습니까?\n\n${item.type === 'penalty' ? '😈 벌칙' : '🎁 보상'}: ${item.option}\n대상: ${item.person}\n날짜: ${formatDateForDisplay(item.rawDate)}`;

    if (confirm(message)) {
        state.history.splice(index, 1);
        sounds.click();
        renderHistory();
        renderMotivation();
        storage.save();
    }
}

function clearHistory() {
    if (confirm('정말로 모든 기록을 삭제하시겠습니까?\n새로운 다이어트의 시작! 💪')) {
        state.history = [];
        sounds.click();
        renderHistory();
        renderMotivation();
        storage.save();
    }
}

// ==========================================
// Sound Toggle
// ==========================================
function toggleSound() {
    state.soundEnabled = !state.soundEnabled;
    elements.soundToggle.textContent = state.soundEnabled ? '🔊' : '🔇';
    elements.soundToggle.classList.toggle('muted', !state.soundEnabled);
    storage.save();

    if (state.soundEnabled) {
        sounds.click();
    }
}

// ==========================================
// Event Listeners
// ==========================================
function initEventListeners() {
    // Sound toggle
    elements.soundToggle.addEventListener('click', toggleSound);

    // Add options
    elements.addPenaltyBtn.addEventListener('click', () => addOption('penalty'));
    elements.addRewardBtn.addEventListener('click', () => addOption('reward'));

    // Enter key for inputs
    elements.penaltyInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addOption('penalty');
    });
    elements.rewardInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addOption('reward');
    });

    // Delete options (event delegation)
    elements.penaltyList.addEventListener('click', (e) => {
        if (e.target.classList.contains('delete-btn')) {
            deleteOption('penalty', parseInt(e.target.dataset.index));
        }
    });
    elements.rewardList.addEventListener('click', (e) => {
        if (e.target.classList.contains('delete-btn')) {
            deleteOption('reward', parseInt(e.target.dataset.index));
        }
    });

    // Person selection
    elements.husbandBtn.addEventListener('click', () => selectPerson('남편'));
    elements.wifeBtn.addEventListener('click', () => selectPerson('아내'));

    // Spin
    elements.spinBtn.addEventListener('click', spin);

    // Modal
    elements.closeModalBtn.addEventListener('click', closeModal);
    elements.modal.addEventListener('click', (e) => {
        if (e.target === elements.modal) closeModal();
    });

    // History checkbox and date editing
    elements.historyList.addEventListener('change', (e) => {
        if (e.target.classList.contains('history-checkbox')) {
            toggleHistoryItem(parseInt(e.target.dataset.index));
        }
    });

    // Date click to edit
    elements.historyList.addEventListener('click', (e) => {
        if (e.target.classList.contains('history-date-text')) {
            showDatePicker(parseInt(e.target.dataset.index), e.target);
        }
        if (e.target.classList.contains('history-delete-btn')) {
            deleteHistoryItem(parseInt(e.target.dataset.index));
        }
    });

    elements.clearHistoryBtn.addEventListener('click', clearHistory);
}

// ==========================================
// Initialize
// ==========================================
function init() {
    storage.load();

    renderOptions('penalty');
    renderOptions('reward');
    renderHistory();
    renderMotivation();
    updateSpinButton();
    populateReel();

    elements.soundToggle.textContent = state.soundEnabled ? '🔊' : '🔇';
    elements.soundToggle.classList.toggle('muted', !state.soundEnabled);

    initEventListeners();

    console.log('💪 수요일 다이어트 심판대가 로드되었습니다!');
}

// Start the app
init();
