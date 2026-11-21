/**
 * AIS Inventory Management & Valuation System — Application Controller
 * Enhanced with GSAP 3.12 soft glassmorphic animations, KPI counter tweens,
 * ambient motion, and clean modal/toast transitions.
 */

/* ── Global State ── */
const state = {
  currentTab: 'dashboard',
  valuationMethod: 'FIFO',
  valuationSystem: 'PERPETUAL',
  items: [],
  pendingDelete: null,
};

const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** Crash-proof DOM text setter */
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

/** Smooth GSAP number count-up for KPI metrics */
function animateMetric(id, targetValue, formatter) {
  const el = document.getElementById(id);
  if (!el) return;
  const num = Number(targetValue) || 0;
  if (typeof gsap === 'undefined' || prefersReducedMotion) {
    el.textContent = formatter(num);
    return;
  }
  const current = parseFloat(el.dataset.val || '0') || 0;
  const proxy = { val: current };
  el.dataset.val = String(num);
  gsap.to(proxy, {
    val: num,
    duration: 0.78,
    ease: 'power2.out',
    onUpdate: () => {
      el.textContent = formatter(proxy.val);
    }
  });
}

/* ═══════════════════ GSAP Motion Choreography ═══════════════════ */
function initGSAPMotion() {
  if (typeof gsap === 'undefined' || prefersReducedMotion) return;

  // 1. Slow breathing ambient orbs
  gsap.to('.orb-1', { x: -45, y: 38, scale: 1.08, duration: 15, ease: 'sine.inOut', repeat: -1, yoyo: true });
  gsap.to('.orb-2', { x: 52, y: -32, scale: 1.1, duration: 18, ease: 'sine.inOut', repeat: -1, yoyo: true });
  gsap.to('.orb-3', { x: -30, y: -26, scale: 0.94, duration: 13, ease: 'sine.inOut', repeat: -1, yoyo: true });

  // 2. Initial entrance choreography
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  tl.from('.sidebar', { x: -26, opacity: 0, duration: 0.65 })
    .from('.sidebar .nav-link', { x: -12, opacity: 0, duration: 0.4, stagger: 0.045 }, '-=0.38')
    .from('.sidebar-footer', { y: 12, opacity: 0, duration: 0.45 }, '-=0.25');

  animateActivePane(document.querySelector('.tab-pane.active'));
}

function animateActivePane(pane) {
  if (!pane || typeof gsap === 'undefined' || prefersReducedMotion) return;
  const targets = pane.querySelectorAll('.page-header, .kpi, .quick-actions, .chart-box, .g-card');
  gsap.killTweensOf(targets);
  gsap.fromTo(
    targets,
    { opacity: 0, y: 16, filter: 'blur(7px)' },
    { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.56, stagger: 0.055, ease: 'power3.out', clearProps: 'filter,transform' }
  );
}

function animateTableRows(tbody) {
  if (!tbody || typeof gsap === 'undefined' || prefersReducedMotion) return;
  const rows = tbody.querySelectorAll('tr');
  if (!rows.length) return;
  gsap.fromTo(
    rows,
    { opacity: 0, y: 8 },
    { opacity: 1, y: 0, duration: 0.34, stagger: 0.025, ease: 'power2.out', clearProps: 'transform' }
  );
}

/* ── Bootstrap ── */
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
  initMobileSidebar();
  initTabs();
  initGSAPMotion();
  checkHealth();
  loadDashboard();
  loadItems();
  loadPurchases();
  loadSales();
  loadValuationReport();
  loadControls();
  setupEventListeners();
});

/* ═══════════════════ Mobile Sidebar ═══════════════════ */
function initMobileSidebar() {
  const toggleBtn = document.getElementById('mobile-toggle-btn');
  const sidebar = document.getElementById('app-sidebar');
  const scrim = document.getElementById('sidebar-scrim');

  const closeSidebar = () => {
    sidebar?.classList.remove('open');
    scrim?.classList.remove('visible');
  };

  toggleBtn?.addEventListener('click', () => {
    const isOpen = sidebar?.classList.toggle('open');
    scrim?.classList.toggle('visible', !!isOpen);
  });

  scrim?.addEventListener('click', closeSidebar);
}

/* ═══════════════════ Sidebar Navigation ═══════════════════ */
function initTabs() {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      if (targetId === state.currentTab) return;

      navLinks.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
        state.currentTab = targetId;
        animateActivePane(targetPane);

        if (targetId === 'dashboard')      loadDashboard();
        else if (targetId === 'items')     loadItems();
        else if (targetId === 'purchases') loadPurchases();
        else if (targetId === 'sales')     loadSales();
        else if (targetId === 'valuation') loadValuationReport();
        else if (targetId === 'controls')  loadControls();
      }

      document.getElementById('app-sidebar')?.classList.remove('open');
      document.getElementById('sidebar-scrim')?.classList.remove('visible');
    });
  });
}

/* ═══════════════════ System Health ═══════════════════ */
async function checkHealth() {
  try {
    const res = await fetch('/api/health');
    if (res.ok) {
      const data = await res.json();
      setText('db-badge-text', data.database_type);
      setText('operator-name-header', data.operator);
    }
  } catch {
    setText('db-badge-text', 'Offline / Local');
  }
}

/* ═══════════════════ Dashboard ═══════════════════ */
async function loadDashboard() {
  try {
    const [summaryRes, chartRes] = await Promise.all([
      fetch('/api/dashboard/summary'),
      fetch('/api/dashboard/charts')
    ]);

    if (summaryRes.ok) {
      const s = await summaryRes.json();
      animateMetric('kpi-valuation', s.total_valuation_wac, v => `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
      animateMetric('kpi-skus', s.active_skus, v => Math.round(v).toLocaleString('en-US'));
      setText('kpi-units', `${s.total_units_in_stock} Units on Hand`);
      animateMetric('kpi-low-stock', s.low_stock_count, v => Math.round(v).toLocaleString('en-US'));
      animateMetric('kpi-turnover', s.turnover_rate, v => `${v.toFixed(1)}x`);
      setText('kpi-dsi', `${s.days_in_inventory} Days in Inventory`);

      const badge = document.getElementById('tab-alert-badge');
      if (badge) {
        badge.textContent = s.low_stock_count;
        badge.style.display = s.low_stock_count > 0 ? 'inline-block' : 'none';
      }
    }

    if (chartRes.ok) {
      const c = await chartRes.json();
      renderValuationComparisonChart('valuationMethodChart', c.methods_comparison);
      renderCategoryBreakdownChart('categoryChart', c.categories);
      renderRecentFeed(c.recent_feed);
    }
  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

function renderRecentFeed(feed) {
  const container = document.getElementById('recent-transactions-list');
  if (!container) return;

  if (!feed || feed.length === 0) {
    container.innerHTML = '<div style="padding:1.5rem;text-align:center;color:var(--text-muted);font-size:0.85rem;">No recent transactions</div>';
    return;
  }

  container.innerHTML = feed.map(tx => {
    const isPurchase = tx.type === 'PURCHASE';
    const tagClass = isPurchase ? 'tag-blue' : 'tag-green';
    const label = isPurchase ? 'Purchase' : 'Sale';
    return `
      <div class="feed-item">
        <div class="feed-left">
          <span class="tag ${tagClass}">${label}</span>
          <strong style="font-size:0.86rem;">${tx.sku}</strong>
          <span style="font-size:0.82rem;color:var(--text-muted);">${tx.quantity} units</span>
        </div>
        <div class="feed-right">
          <div class="feed-amount">$${Number(tx.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          <div class="feed-time">${tx.timestamp}</div>
        </div>
      </div>
    `;
  }).join('');

  if (typeof gsap !== 'undefined' && !prefersReducedMotion) {
    gsap.fromTo(container.querySelectorAll('.feed-item'), { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.35, stagger: 0.04, ease: 'power2.out' });
  }
}

/* ═══════════════════ Item Master ═══════════════════ */
async function loadItems() {
  try {
    const res = await fetch('/api/items');
    if (!res.ok) throw new Error('Failed to load items');
    state.items = await res.json();
    renderItemsTable();
    populateItemDropdowns();
  } catch (err) {
    console.error(err);
    showToast('Failed to load items catalogue', 'error');
  }
}

function renderItemsTable() {
  const tbody = document.getElementById('items-table-body');
  const search = (document.getElementById('item-search-input')?.value || '').toLowerCase();
  const categoryFilter = document.getElementById('item-category-filter')?.value || 'ALL';
  if (!tbody) return;

  const filtered = state.items.filter(item => {
    const matchesSearch = item.sku.toLowerCase().includes(search) || item.name.toLowerCase().includes(search);
    const matchesCat = categoryFilter === 'ALL' || item.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;padding:2rem;color:var(--text-muted);">No matching items found.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(item => {
    const isLow = item.current_stock <= item.reorder_level;
    const statusTag = isLow
      ? `<span class="tag tag-red">Low Stock (${item.current_stock})</span>`
      : `<span class="tag tag-green">Normal</span>`;

    return `
      <tr>
        <td><strong>${item.sku}</strong></td>
        <td>${item.name}</td>
        <td><span class="tag tag-slate">${item.category}</span></td>
        <td>${item.unit_of_measure}</td>
        <td>${item.reorder_level}</td>
        <td>$${item.selling_price.toFixed(2)}</td>
        <td style="font-weight:700;">${item.current_stock}</td>
        <td>$${item.moving_avg_cost.toFixed(2)}</td>
        <td style="font-weight:700;color:var(--blue-deep);">$${item.wac_value.toFixed(2)}</td>
        <td>${statusTag}</td>
        <td>
          <div style="display:flex;gap:0.35rem;">
            <button class="btn btn-secondary btn-sm" onclick="viewCostLayers(${item.id},'${item.sku}')" title="Inspect Cost Layers">Lots</button>
            <button class="btn btn-danger btn-sm" onclick="requestDeleteItem(${item.id},'${item.sku}')" title="Delete SKU">Delete</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  animateTableRows(tbody);
  populateCategoryFilter();
}

function populateCategoryFilter() {
  const select = document.getElementById('item-category-filter');
  if (!select || select.children.length > 1) return;
  const categories = [...new Set(state.items.map(i => i.category))];
  categories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = cat;
    select.appendChild(opt);
  });
}

function populateItemDropdowns() {
  const selects = ['goods-in-item-select', 'goods-out-item-select', 'reconcile-item-select'];
  const optionsHtml = '<option value="">-- Choose SKU / Item --</option>' +
    state.items.map(i =>
      `<option value="${i.id}" data-stock="${i.current_stock}" data-price="${i.selling_price}" data-cost="${i.moving_avg_cost}" data-unit="${i.unit_of_measure}">${i.sku} - ${i.name} (Stock: ${i.current_stock})</option>`
    ).join('');

  selects.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = optionsHtml;
  });
}

/* ═══════════════════ Goods In (Purchases) ═══════════════════ */
async function loadPurchases() {
  try {
    const res = await fetch('/api/goods-in');
    if (!res.ok) throw new Error('Failed');
    const purchases = await res.json();
    const tbody = document.getElementById('purchases-table-body');
    if (!tbody) return;

    if (purchases.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:2rem;color:var(--text-muted);">No purchases recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = purchases.map(p => `
      <tr>
        <td>${new Date(p.timestamp).toLocaleDateString()} ${new Date(p.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
        <td><strong>${p.item_sku}</strong></td>
        <td>${p.item_name}</td>
        <td>${p.party}</td>
        <td style="font-weight:700;">${p.quantity}</td>
        <td>$${p.unit_price.toFixed(2)}</td>
        <td style="font-weight:700;color:var(--blue-deep);">$${p.total_amount.toFixed(2)}</td>
        <td><span class="tag tag-slate">${p.reference}</span></td>
      </tr>
    `).join('');
    animateTableRows(tbody);
  } catch (err) {
    console.error(err);
  }
}

/* ═══════════════════ Goods Out (Sales) ═══════════════════ */
async function loadSales() {
  try {
    const res = await fetch('/api/goods-out');
    if (!res.ok) throw new Error('Failed');
    const sales = await res.json();
    const tbody = document.getElementById('sales-table-body');
    if (!tbody) return;

    if (sales.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--text-muted);">No sales recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = sales.map(s => {
      const margin = s.total_amount - s.cogs_fifo;
      return `
        <tr>
          <td>${new Date(s.timestamp).toLocaleDateString()} ${new Date(s.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
          <td><strong>${s.item_sku}</strong></td>
          <td>${s.item_name}</td>
          <td>${s.party}</td>
          <td style="font-weight:700;">${s.quantity}</td>
          <td>$${s.unit_price.toFixed(2)}</td>
          <td style="font-weight:700;color:var(--emerald-deep);">$${s.total_amount.toFixed(2)}</td>
          <td style="color:var(--rose);font-weight:600;">$${s.cogs_fifo.toFixed(2)}</td>
          <td style="font-weight:700;color:var(--blue-deep);">$${margin.toFixed(2)}</td>
        </tr>
      `;
    }).join('');
    animateTableRows(tbody);
  } catch (err) {
    console.error(err);
  }
}

/* ═══════════════════ Valuation Engine ═══════════════════ */
async function loadValuationReport() {
  try {
    const { valuationMethod: method, valuationSystem: system } = state;
    const res = await fetch(`/api/valuation/report?method=${method}&system=${system}`);
    if (!res.ok) throw new Error(`Server responded ${res.status}`);
    const report = await res.json();

    const notice = document.getElementById('lifo-academic-notice');
    if (notice) {
      if (report.compliance_note) {
        notice.style.display = 'flex';
        setText('lifo-notice-text', report.compliance_note);
        if (typeof gsap !== 'undefined' && !prefersReducedMotion) {
          gsap.fromTo(notice, { opacity: 0, y: -8 }, { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out' });
        }
      } else {
        notice.style.display = 'none';
      }
    }

    const fmtMoney = v => `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    animateMetric('val-goods-avail', report.total_goods_available_cost, fmtMoney);
    animateMetric('val-ending-stock', report.total_ending_inventory_value, fmtMoney);
    animateMetric('val-cogs', report.total_cogs, fmtMoney);
    animateMetric('val-revenue', report.total_revenue, fmtMoney);
    animateMetric('val-gross-margin', report.total_gross_margin, fmtMoney);
    setText('val-gross-margin-pct', `${report.overall_gross_margin_pct.toFixed(2)}%`);
    setText('val-turnover-days', `${report.overall_days_in_inventory} Days`);

    const tbody = document.getElementById('valuation-table-body');
    if (tbody) {
      if (!report.items || report.items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--text-muted);">No valuation records available.</td></tr>`;
      } else {
        tbody.innerHTML = report.items.map(i => `
          <tr>
            <td><strong>${i.sku}</strong></td>
            <td>${i.name}</td>
            <td><span class="tag tag-slate">${i.current_stock} ${i.unit}</span></td>
            <td>$${i.goods_available_cost.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td style="font-weight:700;color:var(--blue-deep);">$${i.ending_inventory_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td style="font-weight:600;color:var(--rose);">$${i.cogs.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td style="font-weight:700;color:var(--emerald-deep);">$${i.revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td><strong>$${i.gross_margin.toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong> <span class="tag tag-green" style="font-size:0.71rem;margin-left:0.3rem;">${i.gross_margin_pct.toFixed(1)}%</span></td>
            <td><span class="tag tag-violet">${i.days_in_inventory} d</span></td>
          </tr>
        `).join('');
        animateTableRows(tbody);
      }
    }
  } catch (err) {
    console.error('Valuation report error:', err);
    showToast('Failed to load valuation report: ' + (err.message || 'Error'), 'error');
  }
}

/* ═══════════════════ Internal Controls & Analysis ═══════════════════ */
async function loadControls() {
  try {
    const [alertsRes, abcRes, recRes, auditRes] = await Promise.all([
      fetch('/api/controls/reorder-alerts'),
      fetch('/api/controls/abc-analysis'),
      fetch('/api/controls/reconciliations'),
      fetch('/api/controls/audit-trail')
    ]);

    if (alertsRes.ok) {
      const alerts = await alertsRes.json();
      const tbody = document.getElementById('reorder-table-body');
      if (tbody) {
        if (alerts.length === 0) {
          tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:1.5rem;color:var(--emerald-deep);">All items are above replenishment thresholds.</td></tr>`;
        } else {
          tbody.innerHTML = alerts.map(a => `
            <tr>
              <td><strong>${a.sku}</strong></td>
              <td>${a.name}</td>
              <td style="color:var(--rose);font-weight:700;">${a.current_stock} ${a.unit_of_measure}</td>
              <td>${a.reorder_level} ${a.unit_of_measure}</td>
              <td><span class="tag tag-red">Replenishment Required</span></td>
              <td><button class="btn btn-primary btn-sm" onclick="openGoodsInForSku(${a.id})">Order Stock</button></td>
            </tr>
          `).join('');
          animateTableRows(tbody);
        }
      }
    }

    if (abcRes.ok) {
      const abc = await abcRes.json();
      const tbody = document.getElementById('abc-table-body');
      if (tbody) {
        tbody.innerHTML = abc.map(item => {
          let tagClass = 'tag-slate';
          if (item.abc_category === 'A') tagClass = 'tag-red';
          else if (item.abc_category === 'B') tagClass = 'tag-amber';

          return `
            <tr>
              <td><span class="tag ${tagClass}" style="font-size:0.78rem;font-weight:700;">Class ${item.abc_category}</span></td>
              <td><strong>${item.sku}</strong></td>
              <td>${item.name}</td>
              <td>${item.total_sold_units}</td>
              <td style="font-weight:700;">$${item.usage_value.toFixed(2)}</td>
              <td>${item.value_share_pct.toFixed(1)}%</td>
              <td style="font-weight:700;">${item.cumulative_share_pct.toFixed(1)}%</td>
              <td style="font-size:0.8rem;color:var(--text-secondary);">${item.recommended_control}</td>
            </tr>
          `;
        }).join('');
        animateTableRows(tbody);
      }
    }

    if (recRes.ok) {
      const recs = await recRes.json();
      const tbody = document.getElementById('reconciliation-table-body');
      if (tbody) {
        if (recs.length === 0) {
          tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:1.5rem;color:var(--text-muted);">No reconciliations performed yet.</td></tr>`;
        } else {
          tbody.innerHTML = recs.map(r => {
            const thresholdTag = r.exceeds_threshold
              ? `<span class="tag tag-red">&gt; 2% Shrinkage</span>`
              : `<span class="tag tag-green">Within Tolerance</span>`;

            return `
              <tr>
                <td>${new Date(r.timestamp).toLocaleDateString()}</td>
                <td><strong>${r.item_sku}</strong></td>
                <td>${r.book_stock}</td>
                <td>${r.physical_count}</td>
                <td style="font-weight:700;color:${r.variance < 0 ? 'var(--rose)' : 'var(--emerald-deep)'};">${r.variance > 0 ? '+' : ''}${r.variance} (${r.variance_pct.toFixed(2)}%)</td>
                <td>${thresholdTag}</td>
                <td>${r.adjusted ? '<span class="tag tag-blue">Synced</span>' : '<span class="tag tag-slate">Unadjusted</span>'}</td>
                <td style="font-size:0.8rem;color:var(--text-secondary);">${r.notes || '-'}</td>
              </tr>
            `;
          }).join('');
          animateTableRows(tbody);
        }
      }
    }

    if (auditRes.ok) {
      const logs = await auditRes.json();
      const tbody = document.getElementById('audit-table-body');
      if (tbody) {
        tbody.innerHTML = logs.map(l => `
          <tr>
            <td>${new Date(l.timestamp).toLocaleString()}</td>
            <td><span class="tag tag-slate">${l.action}</span></td>
            <td>${l.entity_name}</td>
            <td><strong>${l.operator}</strong></td>
            <td style="font-size:0.82rem;">${l.details}</td>
          </tr>
        `).join('');
        animateTableRows(tbody);
      }
    }
  } catch (err) {
    console.error('Controls load error:', err);
  }
}

/* ═══════════════════ Event Listeners ═══════════════════ */
function setupEventListeners() {
  document.getElementById('item-search-input')?.addEventListener('input', renderItemsTable);
  document.getElementById('item-category-filter')?.addEventListener('change', renderItemsTable);

  document.querySelectorAll('[data-val-method]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-val-method]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.valuationMethod = btn.getAttribute('data-val-method');
      loadValuationReport();
    });
  });

  document.querySelectorAll('[data-val-system]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-val-system]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.valuationSystem = btn.getAttribute('data-val-system');
      loadValuationReport();
    });
  });

  document.getElementById('goods-out-item-select')?.addEventListener('change', (e) => {
    const opt = e.target.selectedOptions[0];
    const preview = document.getElementById('goods-out-stock-preview');
    const priceInput = document.getElementById('goods-out-price');

    if (opt && opt.value) {
      const stock = parseFloat(opt.getAttribute('data-stock') || '0');
      const price = parseFloat(opt.getAttribute('data-price') || '0');
      const unit = opt.getAttribute('data-unit') || 'Units';
      preview.style.display = 'block';
      preview.innerHTML = `Available Stock on Hand: <strong>${stock} ${unit}</strong>`;
      if (priceInput && !priceInput.value) priceInput.value = price.toFixed(2);
    } else {
      preview.style.display = 'none';
    }
  });

  document.getElementById('reconcile-count')?.addEventListener('input', calculateLiveVariance);
  document.getElementById('reconcile-item-select')?.addEventListener('change', calculateLiveVariance);

  document.getElementById('create-item-form')?.addEventListener('submit', handleCreateItem);
  document.getElementById('goods-in-form')?.addEventListener('submit', handleGoodsIn);
  document.getElementById('goods-out-form')?.addEventListener('submit', handleGoodsOut);
  document.getElementById('reconcile-form')?.addEventListener('submit', handleReconcile);

  document.getElementById('confirm-delete-btn')?.addEventListener('click', () => {
    if (state.pendingDelete) {
      const { id, sku } = state.pendingDelete;
      state.pendingDelete = null;
      closeModal('modal-confirm-delete');
      deleteItem(id, sku);
    }
  });

  // Close modal when clicking backdrop or pressing Escape
  document.querySelectorAll('.modal-bg').forEach(bg => {
    bg.addEventListener('click', (e) => {
      if (e.target === bg) closeModal(bg.id);
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-bg.open').forEach(m => closeModal(m.id));
    }
  });
}

function calculateLiveVariance() {
  const itemSelect = document.getElementById('reconcile-item-select');
  const countInput = document.getElementById('reconcile-count');
  const preview = document.getElementById('reconcile-preview-box');

  const opt = itemSelect?.selectedOptions[0];
  if (!opt || !opt.value || countInput.value === '') {
    preview.style.display = 'none';
    return;
  }

  const bookStock = parseFloat(opt.getAttribute('data-stock') || '0');
  const physicalCount = parseFloat(countInput.value || '0');
  const variance = physicalCount - bookStock;
  const variancePct = bookStock > 0 ? (Math.abs(variance) / bookStock) * 100 : 0;
  const exceeds = variancePct > 2.0;

  preview.style.display = 'block';
  preview.style.background = exceeds ? 'var(--rose-soft)' : 'var(--emerald-soft)';
  preview.style.borderColor = exceeds ? 'rgba(214,83,109,0.28)' : 'rgba(15,157,138,0.28)';
  preview.style.color = exceeds ? '#9c2440' : '#0b6659';

  preview.innerHTML = `
    <div style="font-weight:700;font-size:0.86rem;">
      Book Stock: ${bookStock} | Physical Count: ${physicalCount}
    </div>
    <div style="margin-top:0.25rem;">
      Variance: <strong>${variance > 0 ? '+' : ''}${variance} (${variancePct.toFixed(2)}%)</strong>
      ${exceeds ? '— <strong>Exceeds 2% Tolerance Limit!</strong> Flagged for review.' : '— Within 2% acceptable threshold.'}
    </div>
  `;
}

/* ═══════════════════ GSAP Modal Actions ═══════════════════ */
function openModal(modalId) {
  const bg = document.getElementById(modalId);
  if (!bg) return;
  const box = bg.querySelector('.modal-box');
  bg.classList.add('open');

  if (typeof gsap !== 'undefined' && !prefersReducedMotion) {
    gsap.fromTo(bg, { opacity: 0 }, { opacity: 1, duration: 0.24, ease: 'power2.out' });
    if (box) {
      gsap.fromTo(
        box,
        { opacity: 0, scale: 0.94, y: 18, filter: 'blur(6px)' },
        { opacity: 1, scale: 1, y: 0, filter: 'blur(0px)', duration: 0.36, ease: 'power3.out', clearProps: 'filter' }
      );
    }
  }
}

function closeModal(modalId) {
  const bg = document.getElementById(modalId);
  if (!bg || !bg.classList.contains('open')) return;
  const box = bg.querySelector('.modal-box');

  if (typeof gsap !== 'undefined' && !prefersReducedMotion) {
    gsap.to(box, { opacity: 0, scale: 0.96, y: 10, duration: 0.2, ease: 'power2.in' });
    gsap.to(bg, {
      opacity: 0,
      duration: 0.22,
      ease: 'power2.in',
      onComplete: () => {
        bg.classList.remove('open');
        gsap.set([bg, box], { clearProps: 'all' });
      }
    });
  } else {
    bg.classList.remove('open');
  }
}

function openGoodsInForSku(itemId) {
  const select = document.getElementById('goods-in-item-select');
  if (select) select.value = itemId;
  openModal('modal-goods-in');
}

function requestDeleteItem(itemId, sku) {
  state.pendingDelete = { id: itemId, sku };
  setText('confirm-delete-message', `Delete SKU '${sku}'? Internal controls will block deletion if transaction history exists.`);
  openModal('modal-confirm-delete');
}

async function viewCostLayers(itemId, sku) {
  try {
    const res = await fetch(`/api/items/${itemId}/layers`);
    if (!res.ok) throw new Error('Failed');
    const layers = await res.json();

    const titleEl = document.getElementById('cost-layer-modal-title');
    if (titleEl) titleEl.textContent = `Cost Layers (Lots) for ${sku}`;
    const tbody = document.getElementById('cost-layer-table-body');

    if (layers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:1.5rem;color:var(--text-muted);">No active cost layers for this SKU.</td></tr>`;
    } else {
      tbody.innerHTML = layers.map(l => `
        <tr>
          <td>${new Date(l.purchase_date).toLocaleDateString()}</td>
          <td>${l.supplier}</td>
          <td>${l.original_quantity}</td>
          <td style="font-weight:700;color:var(--blue-deep);">${l.remaining_quantity}</td>
          <td>$${l.unit_cost.toFixed(2)}</td>
          <td><span class="tag tag-slate">${l.reference}</span></td>
        </tr>
      `).join('');
    }
    openModal('modal-cost-layers');
  } catch {
    showToast('Failed to load cost layers', 'error');
  }
}

async function deleteItem(itemId, sku) {
  try {
    const res = await fetch(`/api/items/${itemId}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Deletion failed', 'error');
    } else {
      showToast(`SKU ${sku} deleted successfully`, 'success');
      loadItems();
      loadDashboard();
    }
  } catch {
    showToast('Network error while deleting item', 'error');
  }
}

/* ═══════════════════ Form Handlers ═══════════════════ */
async function handleCreateItem(e) {
  e.preventDefault();
  const f = e.target;
  const payload = {
    sku: f.sku.value.trim(),
    name: f.name.value.trim(),
    category: f.category.value.trim() || 'General',
    unit_of_measure: f.unit_of_measure.value.trim() || 'Unit',
    reorder_level: parseFloat(f.reorder_level.value || '10'),
    selling_price: parseFloat(f.selling_price.value || '0'),
    initial_stock: parseFloat(f.initial_stock.value || '0'),
    initial_cost: parseFloat(f.initial_cost.value || '0')
  };

  try {
    const res = await fetch('/api/items', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Failed to create item', 'error');
    } else {
      showToast(`Item '${data.sku}' created successfully`, 'success');
      f.reset();
      closeModal('modal-create-item');
      loadItems();
      loadDashboard();
    }
  } catch {
    showToast('Error communicating with server', 'error');
  }
}

async function handleGoodsIn(e) {
  e.preventDefault();
  const f = e.target;
  const payload = {
    item_id: parseInt(f.item_id.value),
    quantity: parseFloat(f.quantity.value),
    unit_cost: parseFloat(f.unit_cost.value),
    supplier: f.supplier.value.trim(),
    reference: f.reference.value.trim() || 'PO-Auto'
  };

  try {
    const res = await fetch('/api/goods-in', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Purchase recording failed', 'error');
    } else {
      showToast(`Goods In logged for ${data.item_sku}`, 'success');
      f.reset();
      closeModal('modal-goods-in');
      loadDashboard();
      loadItems();
      loadPurchases();
    }
  } catch {
    showToast('Error recording purchase', 'error');
  }
}

async function handleGoodsOut(e) {
  e.preventDefault();
  const f = e.target;
  const payload = {
    item_id: parseInt(f.item_id.value),
    quantity: parseFloat(f.quantity.value),
    selling_price: parseFloat(f.selling_price.value),
    customer: f.customer.value.trim(),
    reference: f.reference.value.trim() || 'INV-Auto'
  };

  try {
    const res = await fetch('/api/goods-out', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Sale rejected by internal controls', 'error');
    } else {
      showToast(`Sale recorded for ${data.item_sku} (COGS: $${data.cogs_fifo.toFixed(2)})`, 'success');
      f.reset();
      closeModal('modal-goods-out');
      loadDashboard();
      loadItems();
      loadSales();
      loadValuationReport();
    }
  } catch {
    showToast('Error recording sale', 'error');
  }
}

async function handleReconcile(e) {
  e.preventDefault();
  const f = e.target;
  const payload = {
    item_id: parseInt(f.item_id.value),
    physical_count: parseFloat(f.physical_count.value),
    adjust_book_stock: f.adjust_book_stock.checked,
    notes: f.notes.value.trim()
  };

  try {
    const res = await fetch('/api/controls/reconcile', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Audit submission failed', 'error');
    } else {
      const msg = data.exceeds_threshold
        ? `Audit logged: variance (${data.variance_pct.toFixed(2)}%) exceeds 2% threshold.`
        : `Audit logged: variance within tolerance.`;
      showToast(msg, data.exceeds_threshold ? 'error' : 'success');
      f.reset();
      document.getElementById('reconcile-preview-box').style.display = 'none';
      closeModal('modal-reconcile');
      loadControls();
      loadItems();
      loadDashboard();
    }
  } catch {
    showToast('Error recording physical count audit', 'error');
  }
}

/* ═══════════════════ GSAP Toast Notifications ═══════════════════ */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const cls = type === 'success' ? 'toast-ok' : type === 'error' ? 'toast-err' : 'toast-inf';
  toast.className = `toast ${cls}`;

  const dotColor = type === 'success' ? 'var(--emerald)' : type === 'error' ? 'var(--rose)' : 'var(--blue)';
  toast.innerHTML = `<span style="width:9px;height:9px;border-radius:50%;background:${dotColor};flex-shrink:0;"></span><span>${message}</span>`;
  container.appendChild(toast);

  if (typeof gsap !== 'undefined' && !prefersReducedMotion) {
    gsap.fromTo(toast, { opacity: 0, x: 40, scale: 0.96 }, { opacity: 1, x: 0, scale: 1, duration: 0.36, ease: 'power3.out' });
  }

  setTimeout(() => {
    if (typeof gsap !== 'undefined' && !prefersReducedMotion) {
      gsap.to(toast, { opacity: 0, x: 36, duration: 0.28, ease: 'power2.in', onComplete: () => toast.remove() });
    } else {
      toast.remove();
    }
  }, 4000);
}
