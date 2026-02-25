import { Router } from 'express';
import { authenticateRequest } from '../middleware/auth';

export interface MetricPoint {
  timestamp: number;
  value: number;
}

export interface Metrics {
  requests: { total: number; byEndpoint: Record<string, number> };
  tools: { executions: number; byTool: Record<string, number>; errors: number };
  latency: { avg: number; p95: number; p99: number; history: MetricPoint[] };
  system: { uptime: number; memory: { used: number; total: number }; startTime: number };
}

class MetricsCollector {
  private data: Metrics;
  private latencies: number[] = [];
  private maxHistory = 100;

  constructor() {
    this.data = {
      requests: { total: 0, byEndpoint: {} },
      tools: { executions: 0, byTool: {}, errors: 0 },
      latency: { avg: 0, p95: 0, p99: 0, history: [] },
      system: { uptime: 0, memory: { used: 0, total: 0 }, startTime: Date.now() },
    };
  }

  recordRequest(endpoint: string): void {
    this.data.requests.total++;
    this.data.requests.byEndpoint[endpoint] = (this.data.requests.byEndpoint[endpoint] || 0) + 1;
  }

  recordToolExecution(tool: string, latencyMs: number, error?: boolean): void {
    this.data.tools.executions++;
    this.data.tools.byTool[tool] = (this.data.tools.byTool[tool] || 0) + 1;
    if (error) this.data.tools.errors++;

    this.latencies.push(latencyMs);
    if (this.latencies.length > 1000) this.latencies.shift();

    // Update latency stats
    const sorted = [...this.latencies].sort((a, b) => a - b);
    this.data.latency.avg = sorted.reduce((a, b) => a + b, 0) / sorted.length;
    this.data.latency.p95 = sorted[Math.floor(sorted.length * 0.95)] || 0;
    this.data.latency.p99 = sorted[Math.floor(sorted.length * 0.99)] || 0;

    // Add to history
    this.data.latency.history.push({ timestamp: Date.now(), value: latencyMs });
    if (this.data.latency.history.length > this.maxHistory) this.data.latency.history.shift();
  }

  getMetrics(): Metrics {
    const mem = process.memoryUsage();
    this.data.system.uptime = Date.now() - this.data.system.startTime;
    this.data.system.memory = { used: mem.heapUsed, total: mem.heapTotal };
    return this.data;
  }

  reset(): void {
    this.data.requests = { total: 0, byEndpoint: {} };
    this.data.tools = { executions: 0, byTool: {}, errors: 0 };
    this.latencies = [];
    this.data.latency = { avg: 0, p95: 0, p99: 0, history: [] };
  }
}

export const metricsCollector = new MetricsCollector();

export function createMetricsRouter(): Router {
  const router = Router();
  router.use(authenticateRequest);

  router.get('/', (_, res) => res.json(metricsCollector.getMetrics()));
  router.get('/summary', (_, res) => {
    const m = metricsCollector.getMetrics();
    res.json({
      requests: m.requests.total,
      toolExecutions: m.tools.executions,
      errorRate: m.tools.executions
        ? ((m.tools.errors / m.tools.executions) * 100).toFixed(2) + '%'
        : '0%',
      avgLatency: m.latency.avg.toFixed(2) + 'ms',
      uptime: Math.floor(m.system.uptime / 1000) + 's',
    });
  });
  router.post('/reset', (_, res) => {
    metricsCollector.reset();
    res.json({ success: true });
  });

  return router;
}

// Dashboard HTML
export const dashboardHtml = `<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>Astro Metrics</title>
<style>
  body { font-family: system-ui; background: #1a1a2e; color: #eee; padding: 20px; line-height: 1.5; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
  .card { background: #16213e; border-radius: 12px; padding: 20px; border: 1px solid #27365d; }
  .card h2 { margin: 0 0 15px; color: #8bd3ff; font-size: 1.1rem; }
  .stat { font-size: 2em; font-weight: bold; color: #90e0ef; }
  .label { color: #c9d6df; font-size: 0.95em; }
  .error { color: #ffb4a2; }
  canvas { max-height: 220px; }
  .sr-only { position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0; border: 0; overflow: hidden; clip: rect(0, 0, 0, 0); }
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head><body>
<main>
  <h1>Astro Metrics Dashboard</h1>
  <p id="status" role="status" aria-live="polite">Loading metrics…</p>
  <div class="grid" role="list" aria-label="System metrics">
    <section class="card" role="listitem" aria-labelledby="requests-title"><h2 id="requests-title">Requests</h2><div class="stat" id="requests" aria-live="polite">-</div><div class="label">Total API Requests</div></section>
    <section class="card" role="listitem" aria-labelledby="tools-title"><h2 id="tools-title">Tool Executions</h2><div class="stat" id="tools" aria-live="polite">-</div><div class="label">Total Executions</div></section>
    <section class="card" role="listitem" aria-labelledby="errors-title"><h2 id="errors-title">Error Rate</h2><div class="stat" id="errors" aria-live="polite">-</div><div class="label">Tool Errors</div></section>
    <section class="card" role="listitem" aria-labelledby="latency-title"><h2 id="latency-title">Avg Latency</h2><div class="stat" id="latency" aria-live="polite">-</div><div class="label">Response Time</div></section>
    <section class="card" role="listitem" aria-labelledby="uptime-title"><h2 id="uptime-title">Uptime</h2><div class="stat" id="uptime" aria-live="polite">-</div><div class="label">Since Start</div></section>
    <section class="card" role="listitem" aria-labelledby="memory-title"><h2 id="memory-title">Memory</h2><div class="stat" id="memory" aria-live="polite">-</div><div class="label">Heap Usage</div></section>
  </div>
  <section class="card" style="margin-top:20px" aria-labelledby="latency-history-title">
    <h2 id="latency-history-title">Latency History</h2>
    <p class="sr-only" id="chart-description">Line chart showing recent API latency measurements in milliseconds.</p>
    <canvas id="chart" role="img" aria-describedby="chart-description"></canvas>
  </section>
</main>
<script>
let chart;
function getToken(): string | null {
  let token = localStorage.getItem('astro_jwt');
  if (!token) {
    token = window.prompt('Enter JWT token to view metrics') || null;
    if (token) {
      localStorage.setItem('astro_jwt', token);
    }
  }
  return token;
}

async function update() {
  const token = getToken();
  if (!token) {
    return;
  }
  const res = await fetch('/api/v1/metrics', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 401 || res.status === 403) {
    localStorage.removeItem('astro_jwt');
    document.getElementById('requests').textContent = 'Auth required';
    return;
  }
  const m = await res.json();
  document.getElementById('requests').textContent = m.requests.total;
  document.getElementById('tools').textContent = m.tools.executions;
  document.getElementById('errors').textContent = m.tools.executions ? (m.tools.errors/m.tools.executions*100).toFixed(2)+'%' : '0%';
  document.getElementById('latency').textContent = m.latency.avg.toFixed(1)+'ms';
  document.getElementById('uptime').textContent = Math.floor(m.system.uptime/1000)+'s';
  document.getElementById('memory').textContent = (m.system.memory.used/1024/1024).toFixed(1)+'MB';

  const labels = m.latency.history.map(p => new Date(p.timestamp).toLocaleTimeString());
  const data = m.latency.history.map(p => p.value);

  if (!chart) {
    chart = new Chart(document.getElementById('chart'), {
      type: 'line',
      data: { labels, datasets: [{ label: 'Latency (ms)', data, borderColor: '#90e0ef', tension: 0.3 }] },
      options: {
        responsive: true,
        animation: false,
        scales: { y: { beginAtZero: true } },
      }
    });
  } else {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
  }
}

async function update() {
  try {
    const res = await fetch('/api/v1/metrics', { headers: { 'Accept': 'application/json' } });
    if (!res.ok) {
      throw new Error('Unable to fetch metrics (' + res.status + ')');
    }
    const m = await res.json();
    updateDom(m);
    setStatus('Metrics updated at ' + new Date().toLocaleTimeString());
  } catch (error) {
    setStatus(error instanceof Error ? error.message : 'Failed to update metrics.', true);
  }
}

update();
setInterval(update, 5000);
</script></body></html>`;
