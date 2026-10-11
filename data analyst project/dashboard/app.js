/**
 * Analytics Command Center — Interactive Dashboard
 * Charts, counter animations, scroll-triggered reveals
 */

const ACCENT_CHURN = '#00d4aa';
const ACCENT_ATTRIBUTION = '#f59e0b';
const COLORS = [
  ACCENT_CHURN,
  '#00b894',
  '#55efc4',
  ACCENT_ATTRIBUTION,
  '#fbbf24',
  '#fcd34d',
];

// ----- Chart.js defaults -----
if (typeof Chart !== 'undefined') {
  Chart.defaults.color = '#8b9199';
  Chart.defaults.border.color = 'rgba(255,255,255,0.06)';
  Chart.defaults.font.family = '"Outfit", system-ui, sans-serif';
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(18, 22, 30, 0.95)';
  Chart.defaults.plugins.tooltip.titleColor = '#e8eaed';
  Chart.defaults.animation.duration = 1200;
}

// ----- Counter animation -----
function animateCounter(el, target, decimals = 0) {
  const duration = 1500;
  const start = 0;
  const startTime = performance.now();
  function step(now) {
    const t = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    const val = start + (target - start) * eased;
    el.textContent = val.toFixed(decimals);
    if (t < 1) requestAnimationFrame(step);
    else el.textContent = target.toFixed(decimals);
  }
  requestAnimationFrame(step);
}

// ----- Intersection Observer: reveal + count -----
const observerOptions = { rootMargin: '0px 0px -80px 0px', threshold: 0.1 };
const countObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    const card = entry.target;
    card.classList.add('visible');
    const counter = card.querySelector('.counter');
    if (counter && !counter.dataset.done) {
      counter.dataset.done = '1';
      const target = parseFloat(counter.dataset.target);
      const decimals = parseInt(counter.dataset.decimals, 10) || 0;
      animateCounter(counter, target, decimals);
    }
  });
}, observerOptions);

document.querySelectorAll('.kpi-card').forEach((el) => countObserver.observe(el));

const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
}, { rootMargin: '0px 0px -60px 0px', threshold: 0.05 });

document.querySelectorAll('.section-header, .chart-card, .impact-card').forEach((el) => sectionObserver.observe(el));

// ----- Header hide on scroll down -----
let lastY = window.scrollY;
const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
  const y = window.scrollY;
  if (y > 120) {
    if (y > lastY) header.classList.add('hidden');
    else header.classList.remove('hidden');
  } else header.classList.remove('hidden');
  lastY = y;
}, { passive: true });

// ----- Cohort retention (curves by cohort) -----
function initCohortHeatmap() {
  const ctx = document.getElementById('cohortHeatmap');
  if (!ctx) return;
  const periods = ['M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6'];
  const cohorts = ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05'];
  const retentionByCohort = cohorts.map((_, i) =>
    periods.map((_, j) => Math.round(100 - j * 11 - i * 1.5 - Math.random() * 5))
  );
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: periods,
      datasets: cohorts.map((cohort, i) => ({
        label: cohort,
        data: retentionByCohort[i],
        borderColor: COLORS[i % COLORS.length],
        backgroundColor: COLORS[i % COLORS.length] + '15',
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 8,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.04)' } },
      },
      plugins: {
        legend: { position: 'bottom' },
        tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${c.raw}% retention` } },
      },
    },
  });
}

// ----- Churn risk segments (doughnut) -----
function initChurnSegments() {
  const ctx = document.getElementById('churnSegments');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Low', 'Medium', 'High', 'Critical'],
      datasets: [{
        data: [3200, 1200, 450, 150],
        backgroundColor: [ACCENT_CHURN, '#55efc4', ACCENT_ATTRIBUTION, '#ef4444'],
        borderColor: 'transparent',
        hoverOffset: 12,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: (c) => `${c.label}: ${c.raw} customers (${((c.raw / 5000) * 100).toFixed(1)}%)`,
          },
        },
      },
    },
  });
}

// ----- MRR & Churn trend (line) -----
function initMrrTrend() {
  const ctx = document.getElementById('mrrTrend');
  if (!ctx) return;
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const mrr = [420, 445, 468, 455, 472, 488, 501, 495, 510, 528, 520, 535];
  const churn = [5.2, 4.8, 4.5, 4.9, 4.2, 4.0, 4.1, 4.4, 3.9, 3.8, 4.2, 4.2];
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'MRR ($K)',
          data: mrr,
          borderColor: ACCENT_CHURN,
          backgroundColor: ACCENT_CHURN + '20',
          fill: true,
          tension: 0.35,
          yAxisID: 'y',
        },
        {
          label: 'Churn %',
          data: churn,
          borderColor: ACCENT_ATTRIBUTION,
          backgroundColor: 'transparent',
          borderDash: [4, 2],
          tension: 0.35,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { type: 'linear', position: 'left', grid: { color: 'rgba(255,255,255,0.04)' } },
        y1: { type: 'linear', position: 'right', min: 0, max: 8, grid: { drawOnChartArea: false } },
      },
      plugins: {
        legend: { position: 'top' },
      },
    },
  });
}

// ----- Attribution by channel (bar) -----
function initAttributionChart() {
  const ctx = document.getElementById('attributionChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Google Paid', 'Meta', 'LinkedIn', 'Organic', 'Email'],
      datasets: [{
        label: 'Attributed conversions',
        data: [420, 380, 180, 520, 310],
        backgroundColor: [
          ACCENT_ATTRIBUTION,
          ACCENT_ATTRIBUTION + 'cc',
          ACCENT_ATTRIBUTION + '99',
          ACCENT_CHURN,
          ACCENT_CHURN + 'cc',
        ],
        borderColor: [ACCENT_ATTRIBUTION, ACCENT_ATTRIBUTION, ACCENT_ATTRIBUTION, ACCENT_CHURN, ACCENT_CHURN],
        borderWidth: 1,
        borderRadius: 6,
        hoverBackgroundColor: [ACCENT_ATTRIBUTION, ACCENT_ATTRIBUTION, ACCENT_ATTRIBUTION, ACCENT_CHURN, ACCENT_CHURN],
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' } },
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { afterLabel: (c) => `Share: ${((c.raw / 1810) * 100).toFixed(1)}%` } },
      },
    },
  });
}

// ----- Spend vs Revenue (grouped bar) -----
function initSpendRevenueChart() {
  const ctx = document.getElementById('spendRevenueChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Google', 'Meta', 'LinkedIn', 'Organic', 'Email'],
      datasets: [
        {
          label: 'Spend ($K)',
          data: [85, 62, 45, 0, 12],
          backgroundColor: ACCENT_ATTRIBUTION + '99',
          borderColor: ACCENT_ATTRIBUTION,
          borderWidth: 1,
          borderRadius: 6,
          yAxisID: 'y',
        },
        {
          label: 'Revenue ($K)',
          data: [280, 195, 98, 420, 145],
          backgroundColor: ACCENT_CHURN + '99',
          borderColor: ACCENT_CHURN,
          borderWidth: 1,
          borderRadius: 6,
          yAxisID: 'y',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' } },
      },
      plugins: {
        legend: { position: 'top' },
      },
    },
  });
}

// ----- Init all charts when DOM ready -----
function init() {
  initCohortHeatmap();
  initChurnSegments();
  initMrrTrend();
  initAttributionChart();
  initSpendRevenueChart();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
