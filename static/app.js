/* TSM Price Tracker - Frontend */

let allItems = [];
let currentCategory = "all";
let currentChartItemId = null;
let priceChart = null;
let dowChart = null;
let itemsCollapsed = false;
let ignoredItems = new Set(JSON.parse(localStorage.getItem("tsm_ignored_items") || "[]"));
let lastBuyRecs = [];
let lastSellRecs = [];

// --- Initialization ---

document.addEventListener("DOMContentLoaded", () => {
    loadMarketSummary();
    loadItems();
    loadRecommendations();
    loadSellRecommendations();
    loadMarketMovers();
    loadStats();
});

// --- Data Loading ---

async function loadItems() {
    const res = await fetch("/api/items");
    allItems = await res.json();
    document.getElementById("items-count").textContent = `(${allItems.length})`;
    renderItemGrid();
}

async function loadRecommendations() {
    const res = await fetch("/api/recommendations");
    const recs = await res.json();
    renderRecommendations(recs);
}

async function loadSellRecommendations() {
    const res = await fetch("/api/sell-recommendations");
    const recs = await res.json();
    renderSellRecommendations(recs);
}

async function loadMarketSummary() {
    const res = await fetch("/api/market-summary");
    const data = await res.json();
    renderMarketPulse(data);
}

async function loadMarketMovers() {
    const res = await fetch("/api/market-movers");
    const data = await res.json();
    renderMarketMovers(data);
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
        el.textContent = "No data yet.";
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

function renderMarketPulse(data) {
    const aboveEl = document.getElementById("pulse-above");
    const normalEl = document.getElementById("pulse-normal");
    const belowEl = document.getElementById("pulse-below");
    const barEl = document.getElementById("pulse-bar");

    aboveEl.innerHTML = `<span class="pulse-arrow up">&#9650;</span> ${data.above} above avg`;
    belowEl.innerHTML = `<span class="pulse-arrow down">&#9660;</span> ${data.below} below avg`;
    normalEl.textContent = `${data.normal} normal`;

    if (data.total > 0) {
        const abovePct = (data.above / data.total) * 100;
        const normalPct = (data.normal / data.total) * 100;
        const belowPct = (data.below / data.total) * 100;
        barEl.innerHTML = `
            <div class="pulse-segment above" style="width:${abovePct}%"></div>
            <div class="pulse-segment normal" style="width:${normalPct}%"></div>
            <div class="pulse-segment below" style="width:${belowPct}%"></div>
        `;
    }
}

function renderRecommendations(recs) {
    lastBuyRecs = recs;
    const container = document.getElementById("recommendations-list");
    const allBuyRecs = recs.filter(r => r.signal === "strong_buy" || r.signal === "buy");
    const buyRecs = allBuyRecs.filter(r => !ignoredItems.has(r.item_id));

    if (buyRecs.length === 0 && allBuyRecs.length === 0) {
        container.innerHTML = '<div class="no-data">No buy-low opportunities right now.</div>';
        return;
    }

    if (buyRecs.length === 0) {
        container.innerHTML = '<div class="no-data">All buy-low items are ignored.</div>' +
            renderIgnoredFooter(allBuyRecs, "buy-ignored");
        return;
    }

    const INITIAL_SHOW = 5;
    const renderBuyCard = r => {
        const profitGold = (r.avg_raid_day_gold || r.avg_7d_gold) - r.current_min_buyout_gold;
        return `
        <div class="compact-card buy ${r.signal}" onclick="openChart(${r.item_id})">
            ${r.icon_url ? `<img class="card-icon" src="${r.icon_url}" alt="" loading="lazy" onerror="this.style.display='none'">` : ''}
            <div class="card-body">
                <div class="card-top">
                    <span class="card-name">${r.name}</span>
                    <span class="signal-badge ${r.signal}">${r.signal.replace("_", " ")}</span>
                    <button class="card-dismiss" onclick="ignoreItem(${r.item_id}, event)" title="Ignore this item">&times;</button>
                </div>
                <div class="card-prices">
                    <span class="card-current">${formatGold(r.current_min_buyout_gold)}</span>
                    <span class="card-avg">avg ${formatGold(r.avg_7d_gold)}</span>
                </div>
                <div class="card-bar-wrap">
                    <div class="card-bar buy-bar" style="width:${Math.min(Math.abs(r.discount_pct) * 200, 100)}%"></div>
                    <span class="card-pct">-${(r.discount_pct * 100).toFixed(1)}%</span>
                    <span class="card-profit">+${formatGold(profitGold)}</span>
                </div>
            </div>
        </div>`;
    };

    const visible = buyRecs.slice(0, INITIAL_SHOW);
    const hidden = buyRecs.slice(INITIAL_SHOW);
    container.innerHTML = visible.map(renderBuyCard).join("") +
        (hidden.length > 0 ? `<div class="more-cards hidden" id="buy-more">${hidden.map(renderBuyCard).join("")}</div>
        <button class="show-more-btn" onclick="toggleMore('buy-more', this)">Show ${hidden.length} more</button>` : '') +
        renderIgnoredFooter(allBuyRecs, "buy-ignored");
}

function renderSellRecommendations(recs) {
    lastSellRecs = recs;
    const container = document.getElementById("sell-recommendations-list");
    const allSellRecs = recs.filter(r => r.signal === "strong_sell" || r.signal === "sell");
    const sellRecs = allSellRecs.filter(r => !ignoredItems.has(r.item_id));

    if (sellRecs.length === 0 && allSellRecs.length === 0) {
        container.innerHTML = '<div class="no-data">No sell-high opportunities right now.</div>';
        return;
    }

    if (sellRecs.length === 0) {
        container.innerHTML = '<div class="no-data">All sell-high items are ignored.</div>' +
            renderIgnoredFooter(allSellRecs, "sell-ignored");
        return;
    }

    const INITIAL_SHOW = 5;
    const renderSellCard = r => {
        const premiumGold = r.current_min_buyout_gold - (r.avg_7d_gold || 0);
        return `
        <div class="compact-card sell ${r.signal}" onclick="openChart(${r.item_id})">
            ${r.icon_url ? `<img class="card-icon" src="${r.icon_url}" alt="" loading="lazy" onerror="this.style.display='none'">` : ''}
            <div class="card-body">
                <div class="card-top">
                    <span class="card-name">${r.name}</span>
                    <span class="signal-badge ${r.signal}">${r.signal.replace("_", " ")}</span>
                    <button class="card-dismiss" onclick="ignoreItem(${r.item_id}, event)" title="Ignore this item">&times;</button>
                </div>
                <div class="card-prices">
                    <span class="card-current">${formatGold(r.current_min_buyout_gold)}</span>
                    <span class="card-avg">avg ${formatGold(r.avg_7d_gold)}</span>
                </div>
                <div class="card-bar-wrap">
                    <div class="card-bar sell-bar" style="width:${Math.min(r.premium_pct * 200, 100)}%"></div>
                    <span class="card-pct">+${(r.premium_pct * 100).toFixed(1)}%</span>
                    <span class="card-profit sell-profit">+${formatGold(premiumGold)}</span>
                </div>
            </div>
        </div>`;
    };

    const visible = sellRecs.slice(0, INITIAL_SHOW);
    const hidden = sellRecs.slice(INITIAL_SHOW);
    container.innerHTML = visible.map(renderSellCard).join("") +
        (hidden.length > 0 ? `<div class="more-cards hidden" id="sell-more">${hidden.map(renderSellCard).join("")}</div>
        <button class="show-more-btn" onclick="toggleMore('sell-more', this)">Show ${hidden.length} more</button>` : '') +
        renderIgnoredFooter(allSellRecs, "sell-ignored");
}

function renderMarketMovers(data) {
    const container = document.getElementById("movers-grid");

    if (data.gainers.length === 0 && data.losers.length === 0) {
        container.innerHTML = '<div class="no-data">Not enough data for market movers yet.</div>';
        return;
    }

    const renderMover = (m, isGainer) => `
        <div class="mover-card ${isGainer ? 'gainer' : 'loser'}" onclick="openChart(${m.item_id})">
            ${m.icon_url ? `<img class="mover-icon" src="${m.icon_url}" alt="" loading="lazy" onerror="this.style.display='none'">` : ''}
            <div class="mover-info">
                <span class="mover-name">${m.name}</span>
                <span class="mover-price">${formatGold(m.current_price_gold)}</span>
            </div>
            <span class="mover-change ${isGainer ? 'up' : 'down'}">
                ${isGainer ? '&#9650;' : '&#9660;'} ${(Math.abs(m.change_pct) * 100).toFixed(1)}%
            </span>
        </div>
    `;

    container.innerHTML =
        data.gainers.map(m => renderMover(m, true)).join("") +
        data.losers.map(m => renderMover(m, false)).join("");
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

// --- Show More Toggle ---

function toggleMore(id, btn) {
    const el = document.getElementById(id);
    if (el.classList.contains("hidden")) {
        el.classList.remove("hidden");
        btn.textContent = "Show less";
    } else {
        el.classList.add("hidden");
        const count = el.children.length;
        btn.textContent = `Show ${count} more`;
    }
}

// --- Collapsible Items ---

function toggleItems() {
    itemsCollapsed = !itemsCollapsed;
    const content = document.getElementById("items-collapsible");
    const arrow = document.getElementById("items-toggle-arrow");
    content.style.display = itemsCollapsed ? "none" : "block";
    arrow.innerHTML = itemsCollapsed ? "&#9654;" : "&#9660;";
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

    const [priceRes, tradeRes] = await Promise.all([
        fetch(`/api/prices/${itemId}?days=${days}`),
        fetch(`/api/trades/${itemId}?days=${days}`),
    ]);
    const data = await priceRes.json();
    const tradeData = await tradeRes.json();

    const labels = data.data.map(d => new Date(d.time * 1000));
    const minBuyout = data.data.map(d => d.minBuyout);
    const dbMarket = data.data.map(d => d.marketValue);

    const buyTrades = tradeData.trades
        .filter(t => t.type === "buy")
        .map(t => ({ x: new Date(t.time * 1000), y: t.priceGold }));
    const sellTrades = tradeData.trades
        .filter(t => t.type === "sell")
        .map(t => ({ x: new Date(t.time * 1000), y: t.priceGold }));

    if (priceChart) priceChart.destroy();

    const ctx = document.getElementById("price-chart").getContext("2d");

    const raidDayPlugin = {
        id: "raidDayHighlight",
        beforeDraw(chart) {
            const { ctx, chartArea, scales } = chart;
            if (!chartArea || !scales.x) return;

            ctx.save();
            ctx.fillStyle = "rgba(233, 69, 96, 0.08)";

            const min = scales.x.min;
            const max = scales.x.max;
            const dayMs = 86400000;

            let d = new Date(min);
            d.setHours(0, 0, 0, 0);

            while (d.getTime() <= max) {
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

// --- Ignore Items ---

function saveIgnoredItems() {
    localStorage.setItem("tsm_ignored_items", JSON.stringify([...ignoredItems]));
}

function ignoreItem(itemId, event) {
    event.stopPropagation();
    ignoredItems.add(itemId);
    saveIgnoredItems();
    renderRecommendations(lastBuyRecs);
    renderSellRecommendations(lastSellRecs);
}

function unignoreItem(itemId) {
    ignoredItems.delete(itemId);
    saveIgnoredItems();
    renderRecommendations(lastBuyRecs);
    renderSellRecommendations(lastSellRecs);
}

function toggleIgnoredPanel(panelId) {
    const panel = document.getElementById(panelId);
    panel.classList.toggle("hidden");
}

function renderIgnoredFooter(recs, panelId) {
    const ignoredRecs = recs.filter(r => ignoredItems.has(r.item_id));
    if (ignoredRecs.length === 0) return '';

    return `<button class="ignored-toggle" onclick="toggleIgnoredPanel('${panelId}')">${ignoredRecs.length} ignored</button>
        <div id="${panelId}" class="ignored-panel hidden">
            ${ignoredRecs.map(r => `
                <div class="ignored-item">
                    ${r.icon_url ? `<img class="ignored-icon" src="${r.icon_url}" alt="" onerror="this.style.display='none'">` : ''}
                    <span class="ignored-name">${r.name}</span>
                    <button class="restore-btn" onclick="unignoreItem(${r.item_id})">Restore</button>
                </div>
            `).join("")}
        </div>`;
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
        loadItems();
        loadRecommendations();
        loadSellRecommendations();
        loadMarketSummary();
        loadMarketMovers();
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
