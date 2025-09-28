<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Liverpool W/D/L — Sep 27, 2025 → Today</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />

  <!-- Chart.js (CDN) -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1"></script>

  <style>
    :root { font-family: system-ui, Arial, sans-serif; color-scheme: light dark; }
    .wrap { max-width: 900px; margin: 2.5rem auto; padding: 1rem; }
    h1 { margin: 0 0 .25rem; font-size: 1.6rem; }
    .muted { color: #666; margin-bottom: 1rem; }
    .grid { display: grid; gap: 1rem; grid-template-columns: 1fr; }
    @media (min-width: 860px) { .grid { grid-template-columns: 2fr 1fr; } }

    .card { border: 1px solid #e6e6e6; border-radius: 12px; padding: 1rem; background: #fff; }
    .controls label { display:block; font-size:.9rem; margin:.25rem 0 .4rem; }
    .controls input[type="file"] { width:100%; }
    .row { display:flex; gap:.5rem; align-items:center; flex-wrap:wrap; }
    .stat { display:flex; align-items:baseline; gap:.35rem; }
    .stat b { font-size:1.4rem; }
    .legend { display:flex; gap:1rem; margin-top:.5rem; font-size:.92rem; }
    .swatch { display:inline-block; width:.9rem; height:.9rem; border-radius:3px; margin-right:.35rem; vertical-align:middle; }
    .foot { margin-top:.75rem; color:#666; font-size:.9rem; }
    button { border:1px solid #ddd; background:#fafafa; border-radius:8px; padding:.5rem .75rem; cursor:pointer; }
    button:hover { background:#f0f0f0; }
    .full-width { width:100%; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>🔴 Liverpool W/D/L</h1>
    <div class="muted" id="window">Window: <b>2025-09-27</b> → <b id="today">today</b></div>

    <div class="grid">
      <!-- Chart card -->
      <div class="card">
        <canvas id="wdlChart" height="180"></canvas>

        <div class="legend">
          <span><span class="swatch" style="background:#0ea5a6"></span>Wins</span>
          <span><span class="swatch" style="background:#f59e0b"></span>Draws</span>
          <span><span class="swatch" style="background:#ef4444"></span>Losses</span>
        </div>

        <div class="row" style="margin-top:.75rem">
          <div class="stat">Wins: <b id="wins">–</b></div>
          <div class="stat">Draws: <b id="draws">–</b></div>
          <div class="stat">Losses: <b id="losses">–</b></div>
          <div class="stat">Matches: <b id="matches">–</b></div>
          <div class="stat">Win%: <b id="winpct">–</b></div>
          <button id="refresh">Refresh data</button>
        </div>

        <div class="foot" id="meta">Loading…</div>
      </div>

      <!-- Controls card -->
      <div class="card controls">
        <label><b>Apply a photo to the chart</b></label>
        <input id="imgInput" type="file" accept="image/*" />
        <label style="margin-top:.5rem">Where to apply:</label>
        <select id="applyWhere" class="full-width">
          <option value="all">All bars</option>
          <option value="wins">Wins only</option>
          <option value="draws">Draws only</option>
          <option value="losses">Losses only</option>
          <option value="bg">Background watermark</option>
        </select>
        <div class="foot">Tip: pick a small image for nicer tiling in bar fills. PNGs with transparency look great.</div>
      </div>
    </div>
  </div>

  <script>
    // ---- Settings
    const FROM = "2025-09-27";                 // fixed start date
    const DATA_URL = "./data/fixtures.json";   // written daily by your GitHub Action

    // ---- Utilities
    const pad = n => String(n).padStart(2, "0");
    const todayISO = () => {
      const d = new Date();
      return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
    };
    document.getElementById("today").textContent = todayISO();

    // ---- Base colors for bars (used when no image)
    const baseColors = {
      wins:   "#0ea5a6", // teal
      draws:  "#f59e0b", // amber
      losses: "#ef4444"  // red
    };

    // ---- Background plugin (optional image watermark)
    const bgPlugin = {
      id: "bgImage",
      img: null,
      beforeDraw(chart, args, opts) {
        if (!this.img) return;
        const { ctx, chartArea } = chart;
        if (!chartArea) return;
        const { left, top, width, height } = chartArea;
        ctx.save();
        ctx.globalAlpha = 0.12;
        // tile image
        const pattern = ctx.createPattern(this.img, "repeat");
        ctx.fillStyle = pattern;
        ctx.fillRect(left, top, width, height);
        ctx.restore();
      }
    };

    let chart; // Chart.js instance

    // ---- Create the chart
    function createChart(w, d, l) {
      const ctx = document.getElementById("wdlChart").getContext("2d");
      const data = {
        labels: ["Wins", "Draws", "Losses"],
        datasets: [{
          label: "Results",
          data: [w, d, l],
          borderColor: "#111827",
          borderWidth: 1,
          backgroundColor: [baseColors.wins, baseColors.draws, baseColors.losses],
          hoverBackgroundColor: [baseColors.wins, baseColors.draws, baseColors.losses]
        }]
      };
      const options = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, ticks: { precision:0 } }
        },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => `${ctx.raw} ${ctx.label.toLowerCase()}` } }
        }
      };
      chart = new Chart(ctx, { type: "bar", data, options, plugins: [bgPlugin] });
    }

    // ---- Apply image either to bars or to background
    function applyImageToChart(img, where) {
      if (!chart) return;
      const ctx = chart.ctx;
      const pat = ctx.createPattern(img, "repeat");

      if (where === "bg") {
        bgPlugin.img = img;
        chart.update();
        return;
      }

      // Start with base colors
      const fill = [baseColors.wins, baseColors.draws, baseColors.losses];

      if (where === "all") {
        fill[0] = fill[1] = fill[2] = pat;
      } else if (where === "wins") {
        fill[0] = pat;
      } else if (where === "draws") {
        fill[1] = pat;
      } else if (where === "losses") {
        fill[2] = pat;
      }

      chart.data.datasets[0].backgroundColor = fill;
      chart.data.datasets[0].hoverBackgroundColor = fill;
      chart.update();
    }

    // ---- Load JSON and render
    async function loadAndRender() {
      document.getElementById("meta").textContent = "Loading…";
      try {
        const res = await fetch(DATA_URL, { cache: "no-store" });
        if (!res.ok) throw new Error("fixtures.json not found (has the Action run?)");
        const data = await res.json();

        // Derive counts (use summary if present, else compute)
        let w, d, l;
        if (data.summary) {
          w = data.summary.wins ?? 0;
          d = data.summary.draws ?? 0;
          l = data.summary.losses ?? 0;
        } else if (Array.isArray(data.rows)) {
          w = data.rows.filter(r => r.result === "W").length;
          d = data.rows.filter(r => r.result === "D").length;
          l = data.rows.filter(r => r.result === "L").length;
        } else {
          w = d = l = 0;
        }

        // Update header + stats
        document.getElementById("wins").textContent = w;
        document.getElementById("draws").textContent = d;
        document.getElementById("losses").textContent = l;

        const matches = w + d + l;
        document.getElementById("matches").textContent = matches;
        document.getElementById("winpct").textContent = matches ? ((w / matches) * 100).toFixed(1) + "%" : "—";

        const from = data.from || FROM;
        const to = data.to   || todayISO();
        const gen = data.generated_at || "—";
        document.getElementById("window").innerHTML = `Window: <b>${from}</b> → <b>${to}</b>`;
        document.getElementById("meta").textContent = `Updated ${gen}. Source: ESPN results.`;

        // Build chart
        if (chart) chart.destroy();
        createChart(w, d, l);

      } catch (err) {
        document.getElementById("meta").textContent = "Error loading fixtures.json";
        console.error(err);
      }
    }

    // ---- Wire up controls
    document.getElementById("refresh").addEventListener("click", loadAndRender);

    const imgInput = document.getElementById("imgInput");
    const whereSel = document.getElementById("applyWhere");
    let lastImg = null;

    function handleImage(file) {
      if (!file) return;
      const img = new Image();
      img.onload = () => {
        lastImg = img;
        applyImageToChart(img, whereSel.value);
      };
      img.src = URL.createObjectURL(file);
    }
    imgInput.addEventListener("change", e => handleImage(e.target.files?.[0]));
    whereSel.addEventListener("change", () => {
      if (lastImg) applyImageToChart(lastImg, whereSel.value);
    });

    // Kick things off
    loadAndRender();
  </script>
</body>
</html>
