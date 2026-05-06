<script>
  import { onMount } from 'svelte';

  export let days = [];          // last 90 entries of daily_history
  export let weight_history = [];

  let canvas;
  let chart;

  function buildData() {
    const labels = days.map(d => d.date);

    // Weight map for exact measurement days
    const weightMap = {};
    for (const w of weight_history) weightMap[w.measured_at] = w.weight_kg;

    // Forward-fill: seed with most recent measurement before the window
    const cutoff = labels[0] ?? '';
    const older = weight_history.filter(w => w.measured_at < cutoff);
    let carry = older.length ? older[older.length - 1].weight_kg : null;

    const weightData = [];
    const pointRadii = [];
    for (const l of labels) {
      if (weightMap[l] !== undefined) carry = weightMap[l];
      weightData.push(carry);
      pointRadii.push(weightMap[l] !== undefined ? 3 : 0);
    }

    const activityData = days.map(d => d.stars);

    // Y-axis range tight around actual weight values
    const vals = Object.values(weightMap);
    if (carry !== null && !vals.includes(carry)) vals.push(carry);
    const wMin = vals.length ? Math.floor(Math.min(...vals)) - 1 : 60;
    const wMax = vals.length ? Math.ceil(Math.max(...vals))  + 1 : 100;

    // X month labels
    const tickLabels = labels.map(l => {
      const d = new Date(l + 'T00:00:00');
      return d.getDate() === 1
        ? d.toLocaleDateString('de-CH', { month: 'short' })
        : null;
    });

    return { labels, weightData, activityData, pointRadii, wMin, wMax, tickLabels };
  }

  onMount(async () => {
    const { default: Chart } = await import('chart.js/auto');
    const { labels, weightData, activityData, pointRadii, wMin, wMax, tickLabels } = buildData();

    chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            data: weightData,
            borderColor: '#60a5fa',
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: pointRadii,
            pointBackgroundColor: '#60a5fa',
            yAxisID: 'yW',
            tension: 0,
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
              label: item => {
                if (item.datasetIndex === 0) return item.raw != null ? `⚖️ ${item.raw} kg` : null;
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
              callback: (_, i) => tickLabels[i] ?? null,
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

    return () => chart?.destroy();
  });

  // Update chart when new weight or activity data arrives
  $: if (chart) {
    const { weightData, activityData, pointRadii } = buildData();
    chart.data.datasets[0].data = weightData;
    chart.data.datasets[0].pointRadius = pointRadii;
    chart.data.datasets[1].data = activityData;
    chart.update('none');
  }
</script>

<div class="h-28 relative">
  <canvas bind:this={canvas}></canvas>
</div>
