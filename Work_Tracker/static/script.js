const socket = io(); // connect to Flask-SocketIO server

// Utility to create/update the daily summary chart
let dailyChartInstance = null;
function renderDailyChart(dailyData) {
  if (!dailyData || dailyData.length === 0) {
    document.getElementById('daily-activity-section').innerHTML = "<p>No daily summary data available.</p>";
    return;
  }

  const labels = dailyData.map(d => d.day).reverse();
  const activeHours = dailyData.map(d => (d.total_active_seconds / 3600).toFixed(2)).reverse();

  const ctx = document.getElementById('dailyChart').getContext('2d');

  if (dailyChartInstance) dailyChartInstance.destroy();

  dailyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Active Hours',
        data: activeHours,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        fill: true,
        tension: 0.2,
        pointRadius: 3,
        pointHoverRadius: 6,
        borderWidth: 3,
      }]
    },
    options: {
      responsive: true,
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Hours' }
        },
        x: {
          title: { display: true, text: 'Date' }
        }
      },
      plugins: {
        legend: { display: true, position: 'top' },
        tooltip: { enabled: true, mode: 'index', intersect: false }
      }
    }
  });
}

// Utility to create/update the app usage doughnut chart
let appChartInstance = null;
function renderAppUsageChart(appData) {
  if (!appData || appData.length === 0) {
    document.getElementById('app-usage-section').innerHTML = "<p>No app usage data available.</p>";
    return;
  }

  const appLabels = appData.map(a => a.app_name);
  const durations = appData.map(a => a.duration_seconds);
  const percentages = appData.map(a => a.percentage);

  const ctx = document.getElementById('appChart').getContext('2d');

  if (appChartInstance) appChartInstance.destroy();

  appChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: appLabels,
      datasets: [{
        data: durations,
        backgroundColor: [
          '#ef4444','#f97316','#eab308','#22c55e','#3b82f6',
          '#6366f1','#8b5cf6','#ec4899','#14b8a6','#f43f5e'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 16, padding: 12 } },
        tooltip: {
          callbacks: {
            label: context => {
              const label = context.label || '';
              const val = context.parsed || 0;
              const index = context.dataIndex;
              const percentage = percentages[index] ? percentages[index].toFixed(2) : '';
              let minutes = Math.floor(val / 60);
              let seconds = val % 60;
              return `${label}: ${minutes}m ${seconds}s (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

// Render activity events table
function renderActivityEvents(data) {
  const table = document.getElementById('activityTable');
  const tbody = table.querySelector('tbody');

  if (!data || data.length === 0) {
    tbody.innerHTML = "<tr><td colspan='3'>No recent activity events.</td></tr>";
  } else {
    tbody.innerHTML = data.map(event => `
      <tr>
        <td>${new Date(event.event_time).toLocaleString()}</td>
        <td>${event.event_type}</td>
        <td>${event.details || ""}</td>
      </tr>
    `).join('');
  }
  table.style.display = 'table';
  document.getElementById('loading-activity').style.display = 'none';
}

// Render activity timeline chart
let activityTimelineChartInstance = null;
function renderActivityTimeline(data) {
  document.getElementById('loading-timeline').style.display = 'none';

  if (!data || data.length === 0) {
    document.getElementById('activity-timeline-section').innerHTML = "<p>No activity timeline data available.</p>";
    return;
  }

  // Sort ascending by time
  data.sort((a,b) => new Date(a.event_time) - new Date(b.event_time));

  // Build intervals for active/inactive states
  const intervals = [];
  let lastEvent = null;

  for (const ev of data) {
    const type = ev.event_type.toUpperCase();
    const ts = new Date(ev.event_time);

    if (type === "UNLOCKED" || type === "LOGIN") {
      if (lastEvent && !lastEvent.end) {
        lastEvent.end = ts;
        intervals.push(lastEvent);
      }
      lastEvent = { start: ts, status: 1, end: null };
    } else if (type === "LOCKED" || type === "SHUTDOWN" || type === "SUSPEND") {
      if (lastEvent && lastEvent.status === 1) {
        lastEvent.end = ts;
        intervals.push(lastEvent);
        lastEvent = { start: ts, status: 0, end: null };
      } else if (!lastEvent) {
        lastEvent = { start: ts, status: 0, end: null };
      }
    }
  }
  if (lastEvent && !lastEvent.end) lastEvent.end = new Date();
  intervals.push(lastEvent);

  const labels = [];
  const activeData = [];

  intervals.forEach(interval => {
    labels.push(interval.start.toLocaleTimeString());
    activeData.push(interval.status);
    labels.push(interval.end.toLocaleTimeString());
    activeData.push(interval.status);
  });

  const ctx = document.getElementById('activityTimelineChart').getContext('2d');

  if (activityTimelineChartInstance) activityTimelineChartInstance.destroy();

  activityTimelineChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Active (1) / Inactive (0)',
        data: activeData,
        fill: true,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        stepped: true,
        tension: 0
      }]
    },
    options: {
      scales: {
        y: {
          min: 0,
          max: 1,
          ticks: {
            stepSize: 1,
            callback: val => val === 1 ? 'Active' : 'Inactive'
          }
        },
        x: {
          title: { display: true, text: 'Time' }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ctx.parsed.y === 1 ? "Active" : "Inactive"
          }
        }
      },
      responsive: true,
      animation: false,
    }
  });
}

// Hide loading placeholders initially
document.getElementById('loading-daily').style.display = 'block';
document.getElementById('loading-app').style.display = 'block';
document.getElementById('loading-activity').style.display = 'block';
document.getElementById('loading-timeline').style.display = 'block';

// Listen to socket.io events and update UI live
socket.on('daily_summary_update', data => {
  document.getElementById('loading-daily').style.display = 'none';
  renderDailyChart(data);
});

socket.on('app_usage_update', data => {
  document.getElementById('loading-app').style.display = 'none';
  renderAppUsageChart(data);
});

socket.on('activity_events_update', data => {
  document.getElementById('loading-activity').style.display = 'none';
  renderActivityEvents(data);
  renderActivityTimeline(data);  // reuse same data for timeline
});

// Fallback: On page load, fetch once in case no socket event yet
async function initialFetch() {
  try {
    const [dailyDataRes, appDataRes, activityEventsRes] = await Promise.all([
      fetch('/api/daily_summary'),
      fetch('/api/app_usage'),
      fetch('/api/activity_events')
    ]);

    const dailyData = await dailyDataRes.json();
    const appData = await appDataRes.json();
    const activityData = await activityEventsRes.json();

    document.getElementById('loading-daily').style.display = 'none';
    document.getElementById('loading-app').style.display = 'none';
    document.getElementById('loading-activity').style.display = 'none';
    document.getElementById('loading-timeline').style.display = 'none';

    renderDailyChart(dailyData);
    renderAppUsageChart(appData);
    renderActivityEvents(activityData);
    renderActivityTimeline(activityData);

  } catch (e) {
    console.error("Initial fetch error:", e);
  }
}

initialFetch();
