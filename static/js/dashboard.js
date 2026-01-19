const socket = io();

const verticalLinePlugin = {
    id: 'verticalLine',
    afterDraw: (chart) => {
        if (chart.tooltip?._active?.length) {
            const activePoint = chart.tooltip._active[0];
            const ctx = chart.ctx;
            const x = activePoint.element.x;
            const topY = chart.scales.y.top;
            const bottomY = chart.scales.y.bottom;

            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x, topY);
            ctx.lineTo(x, bottomY);
            ctx.lineWidth = 1;
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.stroke();
            ctx.restore();
        }
    }
};
Chart.register(verticalLinePlugin);

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
            timelineLabels: [], // Shared timeline for all charts in this card
            canvas: card.querySelector('.latencyChart'),
            data: {
                labels: [], // Will point to timelineLabels
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
        elements.data.labels = elements.timelineLabels;

        // Load history before showing chart
        try {
            const histResp = await fetch(`/api/history/${encodeURIComponent(target)}?hours=1`);
            const history = await histResp.json();
            history.forEach(point => {
                const time = new Date(point.timestamp + 'Z').toLocaleTimeString();
                elements.timelineLabels.push(time);
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
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                onHover: (evt, activeElements) => {
                    if (activeElements.length > 0) {
                        const index = activeElements[0].index;
                        syncHovers(target, index);
                    }
                },
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
                elements.timelineLabels.length = 0;
                elements.data.datasets[0].data = [];
                elements.chart.update();
                Object.values(elements.hops).forEach(hopObj => {
                    hopObj.data.datasets[0].data = [];
                    hopObj.chart.update();
                });
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
    m.timelineLabels.push(now);
    
    // Update Destination Chart
    if (data.latency !== null) {
        m.latency.innerText = data.latency;
        m.data.datasets[0].data.push(data.latency);
    } else {
        m.latency.innerText = 'TIMEOUT';
        m.data.datasets[0].data.push(null);
    }

    // Shifting logic (Master Tick)
    if (m.timelineLabels.length > 200) { 
        m.timelineLabels.shift();
        m.data.datasets[0].data.shift();
    }

    // Update all Hop Sparklines with their latest known value to keep them synced
    Object.values(m.hops).forEach(hopObj => {
        // Use the last known latency for this hop, or null if never seen
        const lastVal = hopObj.lastLatency !== undefined ? hopObj.lastLatency : null;
        hopObj.data.datasets[0].data.push(lastVal);
        
        // Don't shift labels here, they are shared!
        if (hopObj.data.datasets[0].data.length > 200) {
            hopObj.data.datasets[0].data.shift();
        }
        hopObj.chart.update();
    });

    m.chart.update();
});

socket.on('hop_update', (data) => {
    const m = monitors[data.target];
    if (!m) return;

    let hopObj = m.hops[data.ip];
    if (!hopObj) {
        const hopRow = document.createElement('tr');
        hopRow.innerHTML = `
            <td class="px-2 py-1 text-slate-500">${data.num}</td>
            <td class="px-2 py-1 font-mono">${data.ip}</td>
            <td class="px-2 py-1 loss-val">0%</td>
            <td class="px-2 py-1 lat-val">0ms</td>
            <td class="px-2 py-1">
                <div class="h-8 w-full">
                    <canvas class="hopSparkline"></canvas>
                </div>
            </td>
        `;
        m.hopList.appendChild(hopRow);

        const canvas = hopRow.querySelector('.hopSparkline');
        const sparklineData = {
            labels: m.timelineLabels, // Use shared labels
            datasets: [{
                data: new Array(m.timelineLabels.length).fill(null),
                borderColor: '#10b981',
                borderWidth: 1,
                fill: false,
                tension: 0.4,
                pointRadius: 0
            }]
        };

        const sparklineChart = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: sparklineData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                onHover: (evt, activeElements) => {
                    if (activeElements.length > 0) {
                        const index = activeElements[0].index;
                        syncHovers(data.target, index);
                    }
                },
                scales: {
                    x: { display: false },
                    y: { display: false, beginAtZero: true }
                },
                plugins: { legend: { display: false } },
                animation: { duration: 0 }
            }
        });

        hopObj = {
            row: hopRow,
            chart: sparklineChart,
            data: sparklineData,
            lastLatency: data.avg_latency
        };
        m.hops[data.ip] = hopObj;
    }

    hopObj.lastLatency = data.avg_latency;
    const lossEl = hopObj.row.querySelector('.loss-val');
    const latEl = hopObj.row.querySelector('.lat-val');

    lossEl.innerText = `${data.loss}%`;
    latEl.innerText = `${data.avg_latency}ms`;

    if (data.loss > 0) {
        lossEl.classList.add('text-red-400', 'font-bold');
        hopObj.row.classList.add('bg-red-500/10');
    } else {
        lossEl.classList.remove('text-red-400', 'font-bold');
        hopObj.row.classList.remove('bg-red-500/10');
    }
});

socket.on('hop_update', (data) => {
    const m = monitors[data.target];
    if (!m) return;

    if (!hopRow) {
        hopRow = document.createElement('tr');
        hopRow.innerHTML = `
            <td class="px-2 py-1 text-slate-500">${data.num}</td>
            <td class="px-2 py-1 font-mono">${data.ip}</td>
            <td class="px-2 py-1 loss-val">0%</td>
            <td class="px-2 py-1 lat-val">0ms</td>
            <td class="px-2 py-1">
                <div class="h-8 w-full">
                    <canvas class="hopSparkline"></canvas>
                </div>
            </td>
        `;
        m.hopList.appendChild(hopRow);

        const canvas = hopRow.querySelector('.hopSparkline');
        const sparklineData = {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#10b981',
                borderWidth: 1,
                fill: false,
                tension: 0.4,
                pointRadius: 0
            }]
        };

        const sparklineChart = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: sparklineData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { display: false },
                    y: { display: false, beginAtZero: true }
                },
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                animation: { duration: 0 }
            }
        });

        m.hops[data.ip] = {
            row: hopRow,
            chart: sparklineChart,
            data: sparklineData
        };
    }

    const hopObj = m.hops[data.ip];
    const lossEl = hopObj.row.querySelector('.loss-val');
    const latEl = hopObj.row.querySelector('.lat-val');

    lossEl.innerText = `${data.loss}%`;
    latEl.innerText = `${data.avg_latency}ms`;

    // Update Sparkline
    const now = new Date().toLocaleTimeString();
    hopObj.data.labels.push(now);
    hopObj.data.datasets[0].data.push(data.avg_latency);

    if (hopObj.data.labels.length > 60) {
        hopObj.data.labels.shift();
        hopObj.data.datasets[0].data.shift();
    }
    hopObj.chart.update();

    if (data.loss > 0) {
        lossEl.classList.add('text-red-400', 'font-bold');
        hopObj.row.classList.add('bg-red-500/10');
    } else {
        lossEl.classList.remove('text-red-400', 'font-bold');
        hopObj.row.classList.remove('bg-red-500/10');
    }
});

function syncHovers(target, index) {
    const m = monitors[target];
    if (!m) return;

    // Sync destination chart
    m.chart.setActiveElements([{ datasetIndex: 0, index: index }]);
    m.chart.tooltip.setActiveElements([{ datasetIndex: 0, index: index }], { x: 0, y: 0 });
    m.chart.update();

    // Sync all hop sparklines
    Object.values(m.hops).forEach(hopObj => {
        hopObj.chart.setActiveElements([{ datasetIndex: 0, index: index }]);
        // Sparklines don't have tooltips enabled usually, but we can set active elements
        hopObj.chart.update();
    });
}

// Run init
init();
