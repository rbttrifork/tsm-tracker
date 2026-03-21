/* TSM Price Tracker - Frontend */

let allItems = [];
let currentCategory = "all";
let currentChartItemId = null;
let priceChart = null;
let dowChart = null;

// --- Initialization ---

document.addEventListener("DOMContentLoaded", () => {
    loadItems();
    loadRecommendations();
    loadStats();
});

// --- Data Loading ---

async function loadItems() {
    const res = await fetch("/api/items");
    allItems = await res.json();
    renderItemGrid();
}

async function loadRecommendations() {
    const res = await fetch("/api/recommendations");
    const recs = await res.json();
    renderRecommendations(recs);
}

async function loadStats() {
    const res = await fetch("/api/stats");
    const stats = await res.json();
    const el = document.getElementById("stats-info");
    if (stats.latest_snapshot) {
        const d = new Date(stats.latest_snapshot * 1000);
        const date = d.toLocaleDateString();
        const time = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        el.textContent = `Last updated: ${date} ${time}`;
    } else {
        el.textContent = "No data yet. Import backups or collect a snapshot.";
    }
}

// --- Rendering ---

function formatGold(value) {
    if (value === null || value === undefined) return "N/A";
    const g = Math.floor(value);
    const s = Math.floor((value - g) * 100);
    const c = Math.round(((value - g) * 100 - s) * 100);
    let parts = [];
    if (g > 0) parts.push(`${g}g`);
    if (s > 0) parts.push(`${s}s`);
    if (c > 0 && g === 0) parts.push(`${c}c`);
    return parts.length > 0 ? parts.join(" ") : "0c";
}

function renderItemGrid() {
    const grid = document.getElementById("item-grid");
    const filtered = currentCategory === "all"
        ? allItems
        : allItems.filter(i => i.category === currentCategory);

    grid.innerHTML = filtered.map(item => `
        <div class="item-card" onclick="openChart(${item.item_id})">
            ${item.icon_url ? `<img class="item-icon" src="${item.icon_url}" alt="" loading="lazy" onerror="this.style.display='none'">` : ''}
            <div class="item-info">
                <div class="item-category">${item.category}</div>
                <div class="item-name">${item.name}</div>
                <div class="item-price" id="price-${item.item_id}">Loading...</div>
            </div>
        </div>
    `).join("");

    // Load latest prices for visible items
    loadLatestPrices(filtered.map(i => i.item_id));
}

async function loadLatestPrices(itemIds) {
    if (itemIds.length === 0) return;
    const res = await fetch(`/api/prices/multi?ids=${itemIds.join(",")}&days=2`);
    const data = await res.json();

    for (const item of data) {
        const el = document.getElementById(`price-${item.item_id}`);
        if (!el) continue;
        if (item.data.length > 0) {
            const latest = item.data[item.data.length - 1];
            const price = latest.marketValue || latest.minBuyout;
            el.innerHTML = `${formatGold(price)} <small>${latest.numAuctions || 0} auctions</small>`;
        } else {
            el.textContent = "No data";
        }
    }
}

function renderRecommendations(recs) {
    const container = document.getElementById("recommendations-list");
    const buyRecs = recs.filter(r => r.signal === "strong_buy" || r.signal === "buy");

    if (buyRecs.length === 0) {
        container.innerHTML = '<div style="color: var(--text-dim); padding: 1rem;">No buy-low opportunities detected right now. Prices are near or above average.</div>';
        return;
    }

    container.innerHTML = buyRecs.map(r => `
        <div class="rec-card ${r.signal}" onclick="openChart(${r.item_id})">
            <div class="rec-header">
                ${r.icon_url ? `<img class="rec-icon" src="${r.icon_url}" alt="" loading="lazy" onerror="this.style.display='none'">` : ''}
                <span class="rec-name">${r.name}</span>
                <span class="rec-signal ${r.signal}">${r.signal.replace("_", " ")}</span>
            </div>
            <div class="rec-details">
                <span>Current: <span class="gold-value">${formatGold(r.current_min_buyout_gold)}</span></span>
                <span>7d Avg: <span class="value">${formatGold(r.avg_7d_gold)}</span></span>
                <span>Discount: <span class="discount">${(r.discount_pct * 100).toFixed(1)}%</span></span>
                <span>Exp. Profit: <span class="profit">+${(r.expected_profit_pct * 100).toFixed(1)}%</span></span>
                <span>Raid Day Avg: <span class="value">${formatGold(r.avg_raid_day_gold)}</span></span>
                <span>Confidence: <span class="value">${(r.confidence * 100).toFixed(0)}%</span></span>
            </div>
        </div>
    `).join("");
}

// --- Category Filter ---

function filterCategory(category) {
    currentCategory = category;
    document.querySelectorAll(".tab").forEach(t => {
        t.classList.toggle("active", t.dataset.category === category);
    });
    renderItemGrid();
}

// --- Chart ---

async function openChart(itemId) {
    currentChartItemId = itemId;
    const modal = document.getElementById("chart-modal");
    modal.classList.remove("hidden");

    // Find item name
    const item = allItems.find(i => i.item_id === itemId);
    const titleEl = document.getElementById("chart-title");
    const iconHtml = item && item.icon_url ? `<img class="chart-title-icon" src="${item.icon_url}" alt="">` : '';
    titleEl.innerHTML = iconHtml + (item ? item.name : `Item ${itemId}`);

    await loadChartData(itemId);
    await loadDowData(itemId);
}

function closeChart() {
    document.getElementById("chart-modal").classList.add("hidden");
    if (priceChart) { priceChart.destroy(); priceChart = null; }
    if (dowChart) { dowChart.destroy(); dowChart = null; }
    currentChartItemId = null;
}

function reloadChart() {
    if (currentChartItemId) {
        loadChartData(currentChartItemId);
        loadDowData(currentChartItemId);
    }
}

async function loadChartData(itemId) {
    const days = document.getElementById("chart-days").value;

    // Fetch price snapshots and trade history in parallel
    const [priceRes, tradeRes] = await Promise.all([
        fetch(`/api/prices/${itemId}?days=${days}`),
        fetch(`/api/trades/${itemId}?days=${days}`),
    ]);
    const data = await priceRes.json();
    const tradeData = await tradeRes.json();

    const labels = data.data.map(d => new Date(d.time * 1000));
    const minBuyout = data.data.map(d => d.minBuyout);
    const dbMarket = data.data.map(d => d.marketValue);

    // Build scatter datasets for buy/sell trades
    const buyTrades = tradeData.trades
        .filter(t => t.type === "buy")
        .map(t => ({ x: new Date(t.time * 1000), y: t.priceGold }));
    const sellTrades = tradeData.trades
        .filter(t => t.type === "sell")
        .map(t => ({ x: new Date(t.time * 1000), y: t.priceGold }));

    if (priceChart) priceChart.destroy();

    const ctx = document.getElementById("price-chart").getContext("2d");

    // Create raid day highlight bands
    const raidDayPlugin = {
        id: "raidDayHighlight",
        beforeDraw(chart) {
            const { ctx, chartArea, scales } = chart;
            if (!chartArea || !scales.x) return;

            ctx.save();
            ctx.fillStyle = "rgba(233, 69, 96, 0.08)";

            // Find raid day ranges
            const min = scales.x.min;
            const max = scales.x.max;
            const dayMs = 86400000;

            let d = new Date(min);
            d.setHours(0, 0, 0, 0);

            while (d.getTime() <= max) {
                // d.getDay(): 0=Sun, 1=Mon, ... convert to our format: 0=Mon
                const ourDow = (d.getDay() + 6) % 7;
                if (window.RAID_DAYS.includes(ourDow)) {
                    const x1 = scales.x.getPixelForValue(d.getTime());
                    const x2 = scales.x.getPixelForValue(d.getTime() + dayMs);
                    const clampX1 = Math.max(x1, chartArea.left);
                    const clampX2 = Math.min(x2, chartArea.right);
                    if (clampX2 > clampX1) {
                        ctx.fillRect(clampX1, chartArea.top, clampX2 - clampX1, chartArea.bottom - chartArea.top);
                    }
                }
                d = new Date(d.getTime() + dayMs);
            }
            ctx.restore();
        }
    };

    priceChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Min Buyout",
                    data: minBuyout,
                    borderColor: "#ffd700",
                    backgroundColor: "rgba(255, 215, 0, 0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                    borderWidth: 2,
                },
                {
                    label: "DBMarket",
                    data: dbMarket,
                    borderColor: "#60a5fa",
                    backgroundColor: "rgba(96, 165, 250, 0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                    borderWidth: 2,
                },
                {
                    label: "Your Buys",
                    data: buyTrades,
                    type: "scatter",
                    borderColor: "#4ade80",
                    backgroundColor: "rgba(74, 222, 128, 0.7)",
                    pointRadius: 5,
                    pointStyle: "triangle",
                    showLine: false,
                },
                {
                    label: "Your Sales",
                    data: sellTrades,
                    type: "scatter",
                    borderColor: "#fb923c",
                    backgroundColor: "rgba(251, 146, 60, 0.7)",
                    pointRadius: 5,
                    pointStyle: "rectRot",
                    showLine: false,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: { labels: { color: "#e0e0e0" } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${formatGold(ctx.parsed.y)}`,
                        title: (items) => {
                            const d = new Date(items[0].parsed.x);
                            const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
                            const ourDow = (d.getDay() + 6) % 7;
                            const isRaid = window.RAID_DAYS.includes(ourDow);
                            return `${d.toLocaleString()} (${days[ourDow]}${isRaid ? " - RAID DAY" : ""})`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    type: "time",
                    time: { unit: days <= 7 ? "hour" : "day" },
                    ticks: { color: "#8899aa" },
                    grid: { color: "rgba(255,255,255,0.05)" },
                },
                y: {
                    ticks: {
                        color: "#8899aa",
                        callback: (v) => formatGold(v),
                    },
                    grid: { color: "rgba(255,255,255,0.05)" },
                },
            },
        },
        plugins: [raidDayPlugin],
    });
}

async function loadDowData(itemId) {
    const days = document.getElementById("chart-days").value;
    const res = await fetch(`/api/dow/${itemId}?days=${days}`);
    const data = await res.json();

    const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const values = [];
    const colors = [];

    for (let i = 0; i < 7; i++) {
        const dow = data.day_of_week[i];
        values.push(dow ? dow.avg_price_gold : 0);
        colors.push(window.RAID_DAYS.includes(i) ? "#e94560" : "#0f3460");
    }

    if (dowChart) dowChart.destroy();

    const ctx = document.getElementById("dow-chart").getContext("2d");
    dowChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: dayNames,
            datasets: [{
                label: "Avg Min Buyout",
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(c => c === "#e94560" ? "#e94560" : "#1a4080"),
                borderWidth: 1,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => formatGold(ctx.parsed.y),
                    },
                },
            },
            scales: {
                x: { ticks: { color: "#8899aa" }, grid: { display: false } },
                y: {
                    ticks: {
                        color: "#8899aa",
                        callback: (v) => formatGold(v),
                    },
                    grid: { color: "rgba(255,255,255,0.05)" },
                },
            },
        },
    });
}

// --- Actions ---

async function collectSnapshot() {
    const btn = document.getElementById("btn-collect");
    btn.textContent = "Collecting...";
    btn.disabled = true;
    try {
        const res = await fetch("/api/snapshot", { method: "POST" });
        const data = await res.json();
        btn.textContent = `Collected ${data.items_collected} items`;
        setTimeout(() => {
            btn.textContent = "Collect Snapshot";
            btn.disabled = false;
        }, 3000);
        // Refresh
        loadItems();
        loadRecommendations();
        loadStats();
    } catch (e) {
        btn.textContent = "Error!";
        setTimeout(() => {
            btn.textContent = "Collect Snapshot";
            btn.disabled = false;
        }, 3000);
    }
}

// Close modal on ESC or backdrop click
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeChart();
});
document.getElementById("chart-modal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeChart();
});
