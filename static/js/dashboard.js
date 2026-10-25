// Dashboard logic: load assets, draw the chart with Chart.js, handle refresh.
(function () {
  "use strict";

  var state = { symbol: null, days: 30, chart: null };
  var TREND_TEXT = { up: "صعودی", down: "نزولی", flat: "بدون روند مشخص" };
  var nf = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 2 });

  function $(id) { return document.getElementById(id); }
  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : "";
  }
  function fmt(n) { return n === null || n === undefined ? "—" : nf.format(n); }
  function pct(n) { return n === null || n === undefined ? "—" : nf.format(n) + "٪"; }
  function trendClass(change) { return change > 0 ? "up" : change < 0 ? "down" : "flat"; }

  function getJSON(url, options) {
    return fetch(url, options).then(function (r) {
      if (!r.ok) { throw new Error("HTTP " + r.status); }
      return r.json();
    });
  }

  function renderCards(assets) {
    var box = $("cards");
    box.textContent = "";
    assets.forEach(function (a) {
      var s = a.summary;
      var card = document.createElement("button");
      card.className = "card" + (a.symbol === state.symbol ? " active" : "");
      card.dataset.symbol = a.symbol;

      var name = document.createElement("div");
      name.className = "name"; name.textContent = a.name;

      var price = document.createElement("div");
      price.className = "price";
      price.textContent = s ? fmt(s.latest) : "—";
      var unit = document.createElement("span");
      unit.className = "unit"; unit.textContent = " " + a.unit;
      price.appendChild(unit);

      var change = document.createElement("div");
      change.className = "change " + trendClass(s && s.change_percent);
      change.textContent = s ? pct(s.change_percent) + " در ۳۰ روز" : "";

      card.append(name, price, change);
      card.addEventListener("click", function () { selectAsset(a.symbol); });
      box.appendChild(card);
    });
  }

  function renderStats(summary, unit) {
    var dl = $("stats");
    dl.textContent = "";
    if (!summary) { return; }
    var rows = [
      ["آخرین قیمت", fmt(summary.latest) + " " + unit],
      ["کمترین", fmt(summary.min)],
      ["بیشترین", fmt(summary.max)],
      ["میانگین", fmt(summary.average)],
      ["تغییر در بازه", pct(summary.change_percent)],
      ["نوسان (انحراف معیار)", pct(summary.volatility)],
      ["روند", TREND_TEXT[summary.trend] || "—"],
      ["تعداد نقاط", fmt(summary.points)]
    ];
    rows.forEach(function (r) {
      var wrap = document.createElement("div");
      var dt = document.createElement("dt"); dt.textContent = r[0];
      var dd = document.createElement("dd"); dd.textContent = r[1];
      wrap.append(dt, dd);
      dl.appendChild(wrap);
    });
  }

  // Turn [{t}] + [values] into Chart.js points on a real time axis.
  function toPoints(times, values) {
    return values.map(function (v, i) { return { x: times[i], y: v }; });
  }

  // Y axis: never zoom in tighter than +-0.5% of the price, so a tiny move
  // (like 0.02%) does not look like a crash.
  function yBounds(prices) {
    if (!prices.length) { return {}; }
    var min = Math.min.apply(null, prices), max = Math.max.apply(null, prices);
    var pad = Math.max((max - min) * 0.1, Math.abs(max) * 0.005);
    return { min: min - pad, max: max + pad };
  }

  function drawChart(data) {
    var times = data.labels.map(function (t) { return Date.parse(t); });
    var spanMs = times.length > 1 ? times[times.length - 1] - times[0] : 0;
    var showTime = spanMs < 3 * 24 * 3600 * 1000;   // short range -> show hours too
    var tickOpts = showTime
      ? { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }
      : { month: "short", day: "numeric" };
    var bounds = yBounds(data.prices);

    $("empty-msg").hidden = data.prices.length > 0;
    if (state.chart) { state.chart.destroy(); }
    state.chart = new Chart($("price-chart"), {
      type: "line",
      data: {
        datasets: [
          { label: "قیمت", data: toPoints(times, data.prices), borderColor: "#2563eb",
            backgroundColor: "#2563eb", borderWidth: 2, pointRadius: data.prices.length < 12 ? 3 : 0 },
          { label: "میانگین ۷ نقطه", data: toPoints(times, data.ma7), borderColor: "#d97706",
            backgroundColor: "#d97706", borderWidth: 1.5, borderDash: [6, 4], pointRadius: 0 },
          { label: "میانگین ۲۱ نقطه", data: toPoints(times, data.ma21), borderColor: "#7c3aed",
            backgroundColor: "#7c3aed", borderWidth: 1.5, borderDash: [2, 3], pointRadius: 0 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { rtl: true, labels: { usePointStyle: true } },
          tooltip: {
            callbacks: {
              title: function (items) {
                return new Date(items[0].parsed.x).toLocaleString("fa-IR",
                  { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
              },
              label: function (item) {
                return item.dataset.label + ": " + nf.format(item.parsed.y);
              }
            }
          }
        },
        scales: {
          x: {
            type: "linear",
            ticks: {
              maxTicksLimit: 7, maxRotation: 0,
              callback: function (v) { return new Date(v).toLocaleString("fa-IR", tickOpts); }
            }
          },
          y: {
            min: bounds.min, max: bounds.max,
            ticks: { callback: function (v) { return nf.format(v); } }
          }
        }
      }
    });
  }

  function loadHistory() {
    if (!state.symbol) { return Promise.resolve(); }
    return getJSON("/api/history/" + state.symbol + "/?days=" + state.days).then(function (data) {
      $("chart-title").textContent = "نمودار " + data.name + " (" + data.unit + ")";
      $("demo-banner").hidden = !data.is_demo;
      drawChart(data);
      renderStats(data.summary, data.unit);
    });
  }

  function loadAssets() {
    return getJSON("/api/assets/").then(function (assets) {
      if (!state.symbol && assets.length) { state.symbol = assets[0].symbol; }
      renderCards(assets);
    });
  }

  function selectAsset(symbol) {
    state.symbol = symbol;
    document.querySelectorAll(".card").forEach(function (c) {
      c.classList.toggle("active", c.dataset.symbol === symbol);
    });
    loadHistory().catch(showError);
  }

  function showError(err) { $("status").textContent = "خطا: " + err.message; }

  function refresh() {
    var btn = $("refresh-btn");
    btn.disabled = true;
    $("status").textContent = "در حال دریافت قیمت‌ها…";
    getJSON("/api/refresh/", { method: "POST", headers: { "X-CSRFToken": csrfToken() } })
      .then(function (res) {
        var failedItems = res.results.filter(function (r) { return !r.ok; });
        var failed = failedItems.map(function (r) { return r.symbol; });
        var reasons = failedItems.map(function (r) { return r.error; })
          .filter(function (e, i, all) { return e && all.indexOf(e) === i; });
        $("status").textContent = fmt(res.updated) + " مورد به‌روز شد" +
          (failed.length ? " | ناموفق: " + failed.join("، ") +
            (reasons.length ? " (" + reasons.join(" ; ") + ")" : "") : "");
        return loadAssets().then(loadHistory);
      })
      .catch(showError)
      .then(function () { btn.disabled = false; });
  }

  document.querySelectorAll("#ranges .chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      document.querySelectorAll("#ranges .chip").forEach(function (c) { c.classList.remove("active"); });
      chip.classList.add("active");
      state.days = parseInt(chip.dataset.days, 10);
      loadHistory().catch(showError);
    });
  });
  $("refresh-btn").addEventListener("click", refresh);

  loadAssets().then(loadHistory).catch(showError);
})();
