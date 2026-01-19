const socket = io();

const monitors = {};

const addBtn = document.getElementById('add-btn');
const targetInput = document.getElementById('target');
const container = document.getElementById('monitors-container');
const template = document.getElementById('monitor-template');

// Initialize: Load active targets from server
async function init() {
    try {
        const response = await fetch('/api/active-targets');
        const targets = await response.json();
        targets.forEach(target => {
            createMonitor(target);
            startTest(target);
        });
    } catch (err) {
        console.error('Failed to load active targets:', err);
    }
}

addBtn.addEventListener('click', () => {
    const target = targetInput.value.trim();
    if (!target) return;
    
    console.log('Adding target:', target);
    
    if (monitors[target]) {
        alert('This target is already being monitored.');
        return;
    }

    createMonitor(target);
    targetInput.value = '';
    startTest(target);
});

function startTest(target) {
    if (socket.connected) {
        socket.emit('start_test', { target: target });
    } else {
        socket.on('connect', () => {
            socket.emit('start_test', { target: target });
        });
    }
}

async function createMonitor(target) {
    try {
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.monitor-card');
        
        card.querySelector('.target-display').innerText = target;
        
        const elements = {
            latency: card.querySelector('.curr-latency'),
            loss: card.querySelector('.curr-loss'),
            sent: card.querySelector('.pkts-sent'),
            recv: card.querySelector('.pkts-recv'),
            hopList: card.querySelector('.hop-list'),
            hops: {}, 
            canvas: card.querySelector('.latencyChart'),
            data: {
                labels: [],
                datasets: [{
                    label: 'Latency (ms)',
                    data: [],
                    borderColor: '#60a5fa',
                    backgroundColor: 'rgba(96, 165, 250, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            }
        };

        // Load history before showing chart
        try {
            const histResp = await fetch(`/api/history/${encodeURIComponent(target)}?hours=1`);
            const history = await histResp.json();
            history.forEach(point => {
                const time = new Date(point.timestamp + 'Z').toLocaleTimeString();
                elements.data.labels.push(time);
                elements.data.datasets[0].data.push(point.latency);
            });
        } catch (err) {
            console.error(`Failed to load history for ${target}:`, err);
        }

        container.prepend(clone);
        const attachedCard = container.firstElementChild;
        
        elements.chart = new Chart(elements.canvas.getContext('2d'), {
            type: 'line',
            data: elements.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { display: false },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: { legend: { display: false } },
                animation: { duration: 0 }
            }
        });

        attachedCard.querySelector('.stop-btn').addEventListener('click', () => {
            socket.emit('stop_test', { target: target });
            attachedCard.remove();
            delete monitors[target];
        });

        attachedCard.querySelector('.clear-btn').addEventListener('click', async () => {
            if (confirm(`Clear all history for ${target}?`)) {
                await fetch(`/api/clear-history/${encodeURIComponent(target)}`, { method: 'POST' });
                elements.data.labels = [];
                elements.data.datasets[0].data = [];
                elements.chart.update();
            }
        });

        monitors[target] = elements;
    } catch (err) {
        console.error('Error creating monitor:', err);
    }
}

socket.on('ping_result', (data) => {
    const m = monitors[data.target];
    if (!m) return;

    m.sent.innerText = data.total_sent;
    m.recv.innerText = data.total_received;
    m.loss.innerText = data.loss;
    
    const now = new Date().toLocaleTimeString();
    m.data.labels.push(now);
    
    if (data.latency !== null) {
        m.latency.innerText = data.latency;
        m.data.datasets[0].data.push(data.latency);
    } else {
        m.latency.innerText = 'TIMEOUT';
        m.data.datasets[0].data.push(null);
    }

    if (m.data.labels.length > 200) { // Increased for better history view
        m.data.labels.shift();
        m.data.datasets[0].data.shift();
    }
    m.chart.update();
});

socket.on('hop_update', (data) => {
    const m = monitors[data.target];
    if (!m) return;

    let hopRow = m.hops[data.ip];
    if (!hopRow) {
        hopRow = document.createElement('tr');
        hopRow.innerHTML = `
            <td class="px-2 py-1 text-slate-500">${data.num}</td>
            <td class="px-2 py-1 font-mono">${data.ip}</td>
            <td class="px-2 py-1 loss-val">0%</td>
            <td class="px-2 py-1 lat-val">0ms</td>
        `;
        m.hopList.appendChild(hopRow);
        m.hops[data.ip] = hopRow;
    }

    const lossEl = hopRow.querySelector('.loss-val');
    const latEl = hopRow.querySelector('.lat-val');

    lossEl.innerText = `${data.loss}%`;
    latEl.innerText = `${data.avg_latency}ms`;

    if (data.loss > 0) {
        lossEl.classList.add('text-red-400', 'font-bold');
        hopRow.classList.add('bg-red-500/10');
    } else {
        lossEl.classList.remove('text-red-400', 'font-bold');
        hopRow.classList.remove('bg-red-500/10');
    }
});

// Run init
init();
