<script>
  import { onMount } from 'svelte';

  export let ninety_days = [];
  export let weight_history = [];

  let canvas;

  onMount(async () => {
    const { default: Chart } = await import('chart.js/auto');

    // Activity map: dateStr → stars
    const activityMap = {};
    for (const d of ninety_days) activityMap[d.date] = d.stars;

    // Weight map: dateStr → kg (only entries within last 90 days)
    const cutoff = ninety_days[0]?.date ?? '';
    const weightMap = {};
    for (const w of weight_history) {
      if (w.measured_at >= cutoff) weightMap[w.measured_at] = w.weight_kg;
    }

    // Build parallel arrays over 90 days
    const labels = ninety_days.map(d => d.date);
    const activityData = labels.map(l => activityMap[l] ?? 0);
    const weightData = labels.map(l => weightMap[l] ?? null);

    // Weight axis range: tight around actual values
    const vals = weightData.filter(v => v !== null);
    const wMin = vals.length ? Math.floor(Math.min(...vals)) - 1 : 60;
    const wMax = vals.length ? Math.ceil(Math.max(...vals))  + 1 : 100;

    // X-tick labels: ~monthly markers
    const tickLabels = labels.map((l, i) => {
      const d = new Date(l + 'T00:00:00');
      return d.getDate() === 1 ? d.toLocaleDateString('de-CH', { month: 'short' }) : '';
    });

    const chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            data: weightData,
            borderColor: '#60a5fa',
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: weightData.map(v => v !== null ? 3 : 0),
            pointBackgroundColor: '#60a5fa',
            spanGaps: true,
            yAxisID: 'yW',
            tension: 0.3,
            order: 1,
          },
          {
            data: activityData,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16,185,129,0.12)',
            borderWidth: 1.5,
            pointRadius: 0,
            fill: true,
            yAxisID: 'yA',
            tension: 0.2,
            order: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#1f2937',
            titleColor: '#9ca3af',
            bodyColor: '#e5e7eb',
            callbacks: {
              title: ([item]) => new Date(item.label + 'T00:00:00')
                .toLocaleDateString('de-CH', { day: 'numeric', month: 'short' }),
              label: (item) => {
                if (item.datasetIndex === 0)
                  return item.raw != null ? `⚖️ ${item.raw} kg` : null;
                return item.raw > 0 ? `🏋️ ${item.raw}` : null;
              },
            },
            filter: item => item.datasetIndex === 0 ? item.raw != null : item.raw > 0,
          },
        },
        scales: {
          x: {
            display: true,
            grid: { display: false },
            ticks: {
              color: '#6b7280',
              font: { size: 9 },
              maxRotation: 0,
              callback: (_, i) => tickLabels[i] || null,
            },
          },
          yW: {
            position: 'left',
            min: wMin,
            max: wMax,
            grid: { color: '#1f2937' },
            ticks: { color: '#60a5fa', font: { size: 9 }, maxTicksLimit: 4 },
          },
          yA: {
            position: 'right',
            min: 0,
            max: 3,
            grid: { display: false },
            ticks: { color: '#10b981', font: { size: 9 }, stepSize: 1 },
          },
        },
      },
    });

    return () => chart.destroy();
  });
</script>

<div class="h-28 relative">
  <canvas bind:this={canvas}></canvas>
</div>
