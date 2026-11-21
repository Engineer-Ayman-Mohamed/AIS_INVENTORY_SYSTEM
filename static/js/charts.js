/**
 * Chart.js Integration — Calm Glassmorphic Palette
 * Renders:
 * 1. Inventory Valuation by Cost-Flow Method (FIFO vs WAC vs LIFO)
 * 2. Inventory Value Distribution by Category
 */

let valuationChartInstance = null;
let categoryChartInstance = null;

function renderValuationComparisonChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (valuationChartInstance) {
    valuationChartInstance.destroy();
  }

  valuationChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Closing Inventory Value ($)',
        data: data.values,
        backgroundColor: [
          'rgba(79, 109, 245, 0.78)',  // FIFO: Calm Indigo-Blue
          'rgba(15, 157, 138, 0.78)',  // WAC: Soft Sage-Teal
          'rgba(217, 130, 43, 0.76)'   // LIFO: Warm Sand-Amber
        ],
        hoverBackgroundColor: [
          'rgba(79, 109, 245, 0.94)',
          'rgba(15, 157, 138, 0.94)',
          'rgba(217, 130, 43, 0.92)'
        ],
        borderColor: ['#4f6df5', '#0f9d8a', '#d9822b'],
        borderWidth: 1.5,
        borderRadius: 10,
        borderSkipped: false,
        maxBarThickness: 58
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 850,
        easing: 'easeOutQuart'
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(20, 33, 61, 0.88)',
          titleColor: '#f8fafc',
          bodyColor: '#e2e8f0',
          padding: 12,
          cornerRadius: 10,
          displayColors: true,
          callbacks: {
            label: function (context) {
              return ' Value: $' + Number(context.raw).toLocaleString('en-US', { minimumFractionDigits: 2 });
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          border: { display: false },
          ticks: {
            color: '#7687a0',
            font: { family: "'Inter', sans-serif", size: 11 },
            callback: function (value) {
              return '$' + Number(value).toLocaleString();
            }
          },
          grid: {
            color: 'rgba(148, 163, 184, 0.14)'
          }
        },
        x: {
          border: { display: false },
          ticks: {
            color: '#4a5b75',
            font: { family: "'Inter', sans-serif", size: 12, weight: '600' }
          },
          grid: { display: false }
        }
      }
    }
  });
}

function renderCategoryBreakdownChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  const palette = [
    '#4f6df5',
    '#0f9d8a',
    '#7c6ae6',
    '#38a3c7',
    '#d9822b',
    '#d6536d',
    '#64748b'
  ];

  categoryChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.values,
        backgroundColor: palette.slice(0, data.labels.length),
        borderWidth: 3,
        borderColor: 'rgba(255, 255, 255, 0.88)',
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 900,
        easing: 'easeOutQuart'
      },
      plugins: {
        legend: {
          position: 'right',
          labels: {
            boxWidth: 11,
            boxHeight: 11,
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 14,
            color: '#4a5b75',
            font: { family: "'Inter', sans-serif", size: 12, weight: '500' }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(20, 33, 61, 0.88)',
          titleColor: '#f8fafc',
          bodyColor: '#e2e8f0',
          padding: 12,
          cornerRadius: 10,
          callbacks: {
            label: function (context) {
              const label = context.label || '';
              const val = context.raw || 0;
              return ` ${label}: $${Number(val).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            }
          }
        }
      },
      cutout: '66%'
    }
  });
}
