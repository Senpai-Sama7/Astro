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
      errorRate: m.tools.executions ? (m.tools.errors / m.tools.executions * 100).toFixed(2) + '%' : '0%',
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
<html><head><title>Astro Metrics</title>
<style>
  body { font-family: system-ui; background: #1a1a2e; color: #eee; padding: 20px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
  .card { background: #16213e; border-radius: 12px; padding: 20px; }
  .card h3 { margin: 0 0 15px; color: #0f4c75; }
  .stat { font-size: 2em; font-weight: bold; color: #3282b8; }
  .label { color: #888; font-size: 0.9em; }
  canvas { max-height: 200px; }
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head><body>
<h1>📊 Astro Metrics Dashboard</h1>
<div class="grid">
  <div class="card"><h3>Requests</h3><div class="stat" id="requests">-</div><div class="label">Total API Requests</div></div>
  <div class="card"><h3>Tool Executions</h3><div class="stat" id="tools">-</div><div class="label">Total Executions</div></div>
  <div class="card"><h3>Error Rate</h3><div class="stat" id="errors">-</div><div class="label">Tool Errors</div></div>
  <div class="card"><h3>Avg Latency</h3><div class="stat" id="latency">-</div><div class="label">Response Time</div></div>
  <div class="card"><h3>Uptime</h3><div class="stat" id="uptime">-</div><div class="label">Since Start</div></div>
  <div class="card"><h3>Memory</h3><div class="stat" id="memory">-</div><div class="label">Heap Usage</div></div>
</div>
<div class="card" style="margin-top:20px"><h3>Latency History</h3><canvas id="chart"></canvas></div>
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
  document.getElementById('errors').textContent = m.tools.executions ? (m.tools.errors/m.tools.executions*100).toFixed(1)+'%' : '0%';
  document.getElementById('latency').textContent = m.latency.avg.toFixed(1)+'ms';
  document.getElementById('uptime').textContent = Math.floor(m.system.uptime/1000)+'s';
  document.getElementById('memory').textContent = (m.system.memory.used/1024/1024).toFixed(1)+'MB';
  const labels = m.latency.history.map(p => new Date(p.timestamp).toLocaleTimeString());
  const data = m.latency.history.map(p => p.value);
  if (!chart) {
    chart = new Chart(document.getElementById('chart'), {
      type: 'line', data: { labels, datasets: [{ label: 'Latency (ms)', data, borderColor: '#3282b8', tension: 0.3 }] },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });
  } else { chart.data.labels = labels; chart.data.datasets[0].data = data; chart.update(); }
}
update(); setInterval(update, 5000);
</script></body></html>`;
