const API_URL = 'http://localhost:5001/api/health';

let myChart;

// FETCH DATA
async function fetchHistory() {
    const res = await fetch(API_URL);
    const data = await res.json();
    updateDashboard(data);
}

// UPDATE UI
function updateDashboard(data) {
    const tableBody = document.querySelector('#historyTable tbody');
    tableBody.innerHTML = '';

    if (data.length > 0) {
        const latest = data[0];
        document.getElementById('lastBP').innerText =
            `${latest.bp.systolic}/${latest.bp.diastolic}`;
        document.getElementById('lastSugarB').innerText =
            `${latest.sugar.beforeMeal} mg/dL`;
        document.getElementById('lastSugarA').innerText =
            `${latest.sugar.afterMeal} mg/dL`;
    }

    data.forEach(entry => {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${new Date(entry.timestamp).toLocaleDateString()}</td>
            <td>${entry.bp.systolic}/${entry.bp.diastolic}</td>
            <td>${entry.sugar.beforeMeal} / ${entry.sugar.afterMeal}</td>
            <td>${getStatus(entry)}</td>
            <td>${entry.notes || '-'}</td>
        `;

        tableBody.appendChild(row);
    });

    updateChart(data);
}

// STATUS
function getStatus(entry) {
    const sys = entry.bp.systolic;
    const dia = entry.bp.diastolic;

    if (sys >= 180 || dia >= 120) return "🚨 Severe";
    if (sys >= 140 || dia >= 90) return "High";
    if (sys >= 130) return "Warning";
    return "Normal";
}

// SAVE
async function saveEntry() {
    const sys = parseInt(document.getElementById('sys').value);
    const dia = parseInt(document.getElementById('dia').value);
    const sugarBefore = parseInt(document.getElementById('sugarBefore').value);
    const sugarAfter = parseInt(document.getElementById('sugarAfter').value);
    const notes = document.getElementById('notes').value;

    if (!sys || !dia || !sugarBefore || !sugarAfter) {
        alert("Fill all fields");
        return;
    }

    const payload = {
        bp: { systolic: sys, diastolic: dia },
        sugar: { beforeMeal: sugarBefore, afterMeal: sugarAfter },
        notes
    };

    await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    fetchHistory();

    document.getElementById('sys').value = '';
    document.getElementById('dia').value = '';
    document.getElementById('sugarBefore').value = '';
    document.getElementById('sugarAfter').value = '';
    document.getElementById('notes').value = '';
}

// GRAPH
function updateChart(data) {
    const ctx = document.getElementById('healthChart').getContext('2d');

    const last10 = data.slice(0, 10).reverse();

    const labels = last10.map(e =>
        new Date(e.timestamp).toLocaleDateString()
    );

    const bpData = last10.map(e => e.bp.systolic);

    if (myChart) myChart.destroy();

    myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'BP Trend',
                data: bpData
            }]
        }
    });
}

fetchHistory();