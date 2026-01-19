const socket = io();

const latencyCtx = document.getElementById('latencyChart').getContext('2d');
const maxDataPoints = 60;
const latencyData = {
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
};

const latencyChart = new Chart(latencyCtx, {
    type: 'line',
    data: latencyData,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                display: false
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#94a3b8'
                }
            }
        },
        plugins: {
            legend: {
                display: false
            }
        },
        animation: {
            duration: 0
        }
    }
});

const startBtn = document.getElementById('start-btn');
const targetInput = document.getElementById('target');
const currLatency = document.getElementById('curr-latency');
const currLoss = document.getElementById('curr-loss');
const pktsSent = document.getElementById('pkts-sent');
const pktsRecv = document.getElementById('pkts-recv');
const tracerouteLog = document.getElementById('traceroute-log');

startBtn.addEventListener('click', () => {
    const target = targetInput.value.trim() || '8.8.8.8';
    
    // Reset UI
    latencyData.labels = [];
    latencyData.datasets[0].data = [];
    latencyChart.update();
    tracerouteLog.innerHTML = 'Starting traceroute...<br>';
    currLatency.innerText = '--';
    currLoss.innerText = '0';
    pktsSent.innerText = '0';
    pktsRecv.innerText = '0';

    socket.emit('start_test', { target: target });
});

socket.on('ping_result', (data) => {
    // Update stats
    pktsSent.innerText = data.total_sent;
    pktsRecv.innerText = data.total_received;
    currLoss.innerText = data.loss;
    
    if (data.latency !== null) {
        currLatency.innerText = data.latency;
        
        // Update Chart
        const now = new Date().toLocaleTimeString();
        latencyData.labels.push(now);
        latencyData.datasets[0].data.push(data.latency);
        
        if (latencyData.labels.length > maxDataPoints) {
            latencyData.labels.shift();
            latencyData.datasets[0].data.shift();
        }
        latencyChart.update();
    } else {
        currLatency.innerText = 'TIMEOUT';
        // Add a zero or null value to chart to show drop? 
        // Let's add null to create a gap
        latencyData.labels.push(new Date().toLocaleTimeString());
        latencyData.datasets[0].data.push(null);
        if (latencyData.labels.length > maxDataPoints) {
            latencyData.labels.shift();
            latencyData.datasets[0].data.shift();
        }
        latencyChart.update();
    }
});

socket.on('traceroute_result', (data) => {
    const div = document.createElement('div');
    div.innerText = data.raw;
    tracerouteLog.appendChild(div);
    tracerouteLog.scrollTop = tracerouteLog.scrollHeight;
});
