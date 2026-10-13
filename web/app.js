/* Techcombank Wealth — the page. It only calls the services (app/main.py) and draws what they return. */
(function () {
  "use strict";
  const {vnd, pct, months: monthsText, monthName, esc} = window.Fmt;
  const C = window.Charts;
  const $ = (s, root) => (root || document).querySelector(s);

  const state = {clients: [], client: null, scope: "personal", months: 12, tab: "overview", board: null, seq: 0,
                 reads: {}, chat: {}, busy: false, risk: {}, alerts: null, alertFilter: "all",
                 catalog: [], plan: {}, goals: null, simBusy: false, queue: [], advisory: null, lastTab: {},
                 viewer: "client", closed: {}, views: null, srcOpen: null, viewsAll: false, advisoryAll: null};
  const EXAMPLES = ["Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ", "Nhà tôi có 10 lượng vàng",
                    "Tôi có 2 con, 14 tuổi và 10 tuổi", "Tôi có 20% cổ phần công ty Hoa Sen trị giá 5 tỷ"];

  // colour follows the asset class, never its rank
  const GROUP_COLOR = {
    "Bất động sản": "var(--s1)", "Cổ phiếu": "var(--s2)", "Tiền & tiền gửi": "var(--s3)", "Vàng": "var(--s4)",
    "Chứng chỉ quỹ": "var(--s5)", "Cổ phần DN": "var(--s6)", "Trái phiếu": "var(--s7)", "Tài sản số": "var(--s8)",
  };
  const TRUST_LABEL = {verified: "Đã xác thực", statement: "Từ sao kê", declared: "Bạn tự khai"};
  const STATUS = {
    ok: {color: "var(--good)", icon: "●", text: "An toàn"},
    near: {color: "var(--warning)", icon: "▲", text: "Gần ngưỡng"},
    over: {color: "var(--critical)", icon: "■", text: "Vượt ngưỡng"},
    low: {color: "var(--warning)", icon: "▲", text: "Thấp"},
    critical: {color: "var(--critical)", icon: "■", text: "Rất thấp"},
  };
  const CLASS_LABEL = {
    cash: "Tiền mặt & thanh toán", deposit: "Tiền gửi", stock: "Cổ phiếu", bond: "Trái phiếu", fund: "Chứng chỉ quỹ",
    real_estate: "Bất động sản", gold: "Vàng", business: "Cổ phần DN", insurance: "Bảo hiểm", crypto: "Tài sản số",
    loan: "Khoản vay", card: "Dư nợ thẻ",
  };

  async function api(path, body) {
    const r = await fetch(path, body === undefined ? {} : {method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(body)});
    if (!r.ok) throw new Error(`${path}: ${r.status}`);
    return r.json();
  }

  function status(key) {
    const s = STATUS[key] || STATUS.ok;
    return `<span class="status"><span class="dot" style="background:${s.color}" aria-hidden="true"></span>${s.text}</span>`;
  }

  // ── the overview ────────────────────────────────────────────────────
  function renderOverview(d) {
    const box = $("#tab-overview");
    const nw = d.net_worth, pf = d.performance, rk = d.risk, lq = d.liquidity, cf = d.cashflow;
    const up = nw.month_change >= 0;
    const who = d.members.map(m => `<span class="chip">${esc(m.name)} · ${esc(m.relation)}</span>`).join("")
      + d.waiting.map(m => `<span class="chip wait" title="Chưa đồng ý chia sẻ dữ liệu">${esc(m.name)} · chưa đồng ý chia sẻ</span>`).join("");
    box.innerHTML = `
      <div class="card hero">
        <div>
          <div class="label">Tài sản ròng ${d.scope === "family" ? "· gia đình" : "· cá nhân"}</div>
          <div class="figure">${vnd(nw.value)}</div>
          <div><span class="delta ${up ? "up" : "down"}">${up ? "▲" : "▼"} ${pct(nw.month_change_pct, true)}</span>
            <span class="muted">so với tháng trước (${vnd(nw.month_change, true)})</span></div>
          <div class="muted small" style="margin-top:6px">Tài sản ${vnd(nw.assets)} · Nợ ${vnd(nw.liabilities)} · cập nhật ${esc(d.as_of)}</div>
          <div class="who">${who}</div>
        </div>
        <div id="srcmix"></div>
      </div>
      <div class="grid g3 mt">
        <div class="card"><h2>Phân bổ tài sản <span class="hint">lãi/lỗ: % so với giá vốn</span></h2><div id="alloc"></div></div>
        <div class="card"><h2>Lãi / lỗ danh mục <span class="hint">cổ phiếu, quỹ, trái phiếu</span></h2>
          <div class="stats">
            <div class="stat"><span class="k">Đã chốt (từ đầu năm)</span><span class="v">${vnd(pf.realized_ytd, true)}</span></div>
            <div class="stat"><span class="k">Chưa chốt</span><span class="v">${vnd(pf.unrealized, true)} <span class="muted">(${pct(pf.unrealized_pct, true)})</span></span></div>
            <div class="stat"><span class="k">Lợi nhuận từ đầu năm</span><span class="v">${pct(pf.ytd_return, true)}</span></div>
            <div class="stat"><span class="k">So với ${esc(pf.benchmark_name)} (${pct(pf.benchmark_ytd, true)})</span>
              <span class="v delta ${pf.vs_benchmark >= 0 ? "up" : "down"}">${pct(pf.vs_benchmark, true)}</span></div>
          </div>
          ${pf.by_class.length ? `<div class="tablewrap mt"><table><thead><tr><th>Loại</th><th class="num">Giá trị</th><th class="num">Lãi/lỗ</th></tr></thead><tbody>
            ${pf.by_class.map(c => `<tr><td>${esc(c.label)}</td><td class="num">${vnd(c.value)}</td><td class="num">${vnd(c.pnl, true)} <span class="muted">${pct(c.return, true)}</span></td></tr>`).join("")}
          </tbody></table></div>` : ""}
        </div>
        <div class="card"><h2>Rủi ro</h2>
          ${d.profile.risk_profile ? `<div class="stat"><span class="k">Hồ sơ rủi ro (bài test)</span><span class="v">${esc(d.profile.risk_profile)} · ${esc(d.profile.risk_persona)}</span></div>` : `<p class="muted small" style="margin:0 0 8px">Chưa làm bài test rủi ro: ngưỡng lấy theo hồ sơ.</p>`}
          <div class="stat"><span class="k">Ngưỡng sụt giảm chấp nhận</span><span class="v">${pct(rk.limit, false, 0)}</span></div>
          <div class="stat"><span class="k">Mức sụt giảm ước tính khi thị trường xấu</span><span class="v">${pct(rk.current)}</span></div>
          <div id="riskmeter"></div>
          <div>${status(rk.status)} <span class="muted small">· mất ${vnd(rk.stress_loss)} trong kịch bản xấu</span></div>
          ${d.concentration.warnings.length ? `<ul class="warn-list">${d.concentration.warnings.map(w => `<li><span class="ic" aria-hidden="true">⚠</span><span>Tập trung: ${esc(w)}</span></li>`).join("")}</ul>` : `<p class="muted small">Không có khoản nào tập trung quá ngưỡng.</p>`}
        </div>
      </div>
      <div class="card mt"><h2>Thanh khoản dự phòng</h2>
        <div class="stat"><span class="k">${vnd(lq.value)} tiền và tài sản rút được ngay</span>
          <span class="v">đủ chi ${monthsText(lq.months)} ${status(lq.status)}</span></div>
        <div id="liqmeter"></div>
        <div class="muted small">Chi tiêu ${vnd(lq.spending_monthly)}/tháng · mốc an toàn: 6 tháng</div>
      </div>
      <div class="card mt">
        <h2>Dòng tiền · ${PAST_MONTHS} tháng qua và ${cf.months.length} tháng tới
          <span class="hint">dự báo ${cf.months.length} tháng tới: vào ${vnd(cf.total_in)} · ra ${vnd(cf.total_out)}</span></h2>
        <div class="keys">${cashKeys()}
          <span><b style="color:var(--critical)">⚠</b> Khoản phải trả lớn</span>
          <span class="seg" role="group" aria-label="Số tháng" style="margin-left:auto">
            ${[12, 24, 36].map(n => `<button type="button" data-months="${n}" aria-pressed="${state.months === n}">${n} tháng</button>`).join("")}
          </span></div>
        <div id="cash" class="mt"></div>
        <div class="grid g2 mt">
          <div><h2>Khoản phải trả lớn</h2>${cf.large.length ? `<ul class="warn-list">${cf.large.map(l => `<li><span class="ic" aria-hidden="true">⚠</span><span><b>${monthName(l.month)}</b> · ${esc(l.label)} · ${vnd(l.amount)}</span></li>`).join("")}</ul>` : `<p class="muted small">Không có khoản lớn nào trong ${cf.months.length} tháng tới.</p>`}</div>
          <div><h2>Khoản định kỳ tìm thấy trong giao dịch</h2>
            <ul class="legend">${cf.recurring.map(r => `<li><span class="sw" style="background:${r.direction === "in" ? "var(--in)" : "var(--out)"}"></span><span>${esc(r.label)} <span class="muted small">· ${r.cadence === "monthly" ? "hằng tháng" : "theo kỳ"}</span></span><span class="v">${r.direction === "in" ? "+" : "−"}${vnd(r.amount)}</span><span></span></li>`).join("")}</ul></div>
        </div>
      </div>
      <div class="card mt" id="alerts-card"><h2>Headline news</h2><p class="muted small">Đang quét chính sách, vĩ mô và hạ tầng…</p></div>`;
    drawSourceMix();
    $("#alloc", box).append(C.shareBar(d.allocation.map(a => ({label: a.group, value: a.value, share: a.share, pnl: a.pnl, ret: a.return})),
      r => GROUP_COLOR[r.label] || "var(--other)",
      r => r.ret == null ? `<span class="muted" title="Chưa có giá vốn">—</span>`
        : `<span class="delta ${r.ret >= 0 ? "up" : "down"}" title="${vnd(r.pnl, true)} so với giá vốn">${pct(r.ret, true)}</span>`,
      ["Loại tài sản", "Giá trị", "Tỷ trọng", "Lãi/lỗ"]));
    const rmax = Math.max(rk.limit * 1.6, rk.current * 1.1);
    $("#riskmeter", box).append(C.meter(rk.current, rmax, rk.limit, (STATUS[rk.status] || STATUS.ok).color,
      `Sụt giảm ước tính ${pct(rk.current)} so với ngưỡng ${pct(rk.limit, false, 0)}`));
    const lmax = Math.max(12, Math.min(lq.months, 36));
    $("#liqmeter", box).append(C.meter(Math.min(lq.months, lmax), lmax, 6, (STATUS[lq.status] || STATUS.ok).color,
      `Đủ chi ${monthsText(lq.months)}, mốc an toàn 6 tháng`));
    drawCash();
    for (const b of box.querySelectorAll("[data-months]")) b.onclick = () => { state.months = Number(b.dataset.months); load(); };
  }

  // what happened (solid), this month and the forecast (lighter): one series for the chart
  const PAST_MONTHS = 6;
  function cashSeries(cf, past, ahead) {
    return [...(cf.history || []).slice(-past).map(m => ({...m, phase: "past"})),
      ...(cf.current ? [{...cf.current, phase: "now"}] : []),
      ...cf.months.slice(0, ahead).map(m => ({...m, phase: "next"}))];
  }

  function cashKeys() {
    return `<span><span class="sw" style="background:var(--in)"></span>Tiền vào</span>
      <span><span class="sw" style="background:var(--out)"></span>Tiền ra</span>
      <span><span class="sw" style="background:var(--in);opacity:${C.FORECAST_OPACITY}"></span><span class="sw" style="background:var(--out);opacity:${C.FORECAST_OPACITY};margin-left:-4px"></span>Dự báo (màu nhạt)</span>`;
  }

  function drawCash() {
    if (!state.board) return;
    const cf = state.board.cashflow;
    const host = $("#cash");
    if (host && host.clientWidth) host.replaceChildren(C.cashflow(cashSeries(cf, PAST_MONTHS, cf.months.length), cf.large, host.clientWidth));
    const plan = $("#plan-cash");   // hidden tabs measure no width: drawn when their tab shows
    if (plan && plan.clientWidth) plan.replaceChildren(C.cashflow(cashSeries(cf, 12, 12), cf.large, plan.clientWidth));
  }
  let resizeTimer = null;
  addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(drawCash, 120); });

  // ── where the assets sit: the three tiers of sources, each opening onto its sources ──
  const TIERS = [
    {n: 1, title: "Our Wealth at Techcombank", vi: "Tài sản tại hệ sinh thái Techcombank", color: "var(--s1)", sub: "tự động, không cần thao tác"},
    {n: 2, title: "Custody around the world", vi: "Tài sản lưu ký bên ngoài", color: "var(--s7)", sub: "Open API hoặc sao kê tải lên"},
    {n: 3, title: "Self-managed", vi: "Tài sản bạn tự quản lý", color: "var(--s4)", sub: "khai qua chat hoặc sao kê"},
  ];

  function drawSourceMix() {
    const box = $("#srcmix"), d = state.board;
    if (!box || !d) return;
    const total = d.net_worth.assets || 1;
    const tiers = TIERS.map(t => {
      const src = d.sources.filter(s => s.tier === t.n);
      return {...t, src, value: src.reduce((a, s) => a + s.assets, 0), on: src.filter(s => s.count).length};
    });
    const open = state.srcOpen;
    const bar = tiers.filter(t => t.value > 0).map(t => `<button type="button" class="seg-hit${open === t.n ? " on" : ""}" data-tier="${t.n}"
      style="flex:${t.value / total} 1 0;background:${t.color}" title="${esc(t.vi)}: ${vnd(t.value)} · ${pct(t.value / total)}" aria-label="${esc(t.vi)} ${pct(t.value / total)}"></button>`).join("");
    const card = (t) => `<div class="tiercard${open === t.n ? " on" : ""}">
        <button type="button" class="tierhead" data-tier="${t.n}" aria-expanded="${open === t.n}">
          <span class="sw" style="background:${t.color}"></span>
          <span class="tt"><b>${esc(t.title)}</b><span class="muted small">${esc(t.vi)} · ${t.on}/${t.src.length} nguồn đã kết nối</span></span>
          <span class="tv"><b>${pct(t.value / total, false, t.value / total < 0.1 ? 1 : 0)}</b><span class="muted small">${vnd(t.value)}</span></span>
          <span class="caret" aria-hidden="true">${open === t.n ? "▾" : "▸"}</span></button>
        ${open === t.n ? `<div class="tierlist">${t.src.map(s => `
          <div class="src"><span class="${s.status === "connected" ? "ok" : "no"}" aria-hidden="true">${s.status === "connected" ? "✓" : "○"}</span>
            <span><b>${esc(s.label)}</b></span>
            <span class="num">${s.count ? `${vnd(s.assets - s.liabilities)} <span class="muted small">· ${pct(s.assets / total, false, s.assets / total < 0.1 ? 1 : 0)}</span>` : "—"}</span>
            <span class="what">${esc(s.what)} · ${s.count ? `${s.count} khoản · ${s.trust.map(esc).join(", ")}` : "chưa có dữ liệu"}</span></div>`).join("")}
          <button type="button" class="linkbtn" data-goto="sources" style="margin:6px 0 0">Xem từng khoản →</button></div>` : ""}
      </div>`;
    box.innerHTML = `<div class="label">Tài sản theo nguồn dữ liệu <span class="hint">% tổng tài sản ${vnd(d.net_worth.assets)} · bấm để xem từng nguồn</span></div>
      <div class="stack hit mt">${bar}</div>
      <div class="tierstack mt">${tiers.map(card).join("")}</div>`;
    for (const b of box.querySelectorAll("[data-tier]")) {
      b.onclick = () => { const n = Number(b.dataset.tier); state.srcOpen = state.srcOpen === n ? null : n; drawSourceMix(); };
    }
    for (const b of box.querySelectorAll("[data-goto]")) b.onclick = () => showTab(b.dataset.goto);
  }

  // ── every holding, and adding more ──────────────────────────────────
  function renderSources(d) {
    const box = $("#tab-sources");
    box.innerHTML = `
      <div class="tabhead"><h1>Dữ liệu chi tiết tài sản</h1><p>Từng khoản tài sản và khoản nợ · thêm dữ liệu bằng sao kê hoặc chat</p></div>
      <div class="grid g2">${uploadCard()}${chatCard()}</div>
      ${holdingsTable(d)}`;
    wireSources();
  }

  // ── every holding, by asset class: when and at what it was bought, and its profit ──
  const BOOK = [
    {id: "real_estate", label: "Bất động sản", color: "var(--s1)", classes: ["real_estate"]},
    {id: "stock", label: "Cổ phiếu", color: "var(--s2)", classes: ["stock"]},
    {id: "fund", label: "Chứng chỉ quỹ", color: "var(--s5)", classes: ["fund"]},
    {id: "bond", label: "Trái phiếu", color: "var(--s7)", classes: ["bond"]},
    {id: "deposit", label: "Tiền gửi tiết kiệm", color: "var(--s3)", classes: ["deposit"]},
    {id: "cash", label: "Tiền mặt & tài khoản thanh toán", color: "var(--s3)", classes: ["cash"]},
    {id: "gold", label: "Vàng", color: "var(--s4)", classes: ["gold"]},
    {id: "business", label: "Cổ phần doanh nghiệp", color: "var(--s6)", classes: ["business"]},
    {id: "insurance", label: "Bảo hiểm", color: "var(--other)", classes: ["insurance"]},
    {id: "crypto", label: "Tài sản số", color: "var(--s8)", classes: ["crypto"]},
    {id: "debt", label: "Khoản nợ", color: "var(--critical)", classes: ["loan", "card"], debt: true},
  ];
  const UNIT_NAME = {stock: "cp", bond: "TP", fund: "CCQ", gold: "lượng"};
  const num = (x) => vnd(x).replace(/ đ$/, "");
  const day = (iso) => iso ? iso.slice(8, 10) + "/" + iso.slice(5, 7) + "/" + iso.slice(0, 4) : "";

  // what one holding row says: bought when, at what, cost, profit (null where the source does not know)
  function bookRow(h, asOf) {
    const d = h.detail || {};
    const r = {bought: "", price: "", cost: h.cost, pnl: null, ret: null, note: ""};
    if (h.class === "stock" || h.class === "bond") {
      r.bought = day(d.bought);
      if (d.avg_price) r.price = `${num(d.avg_price)} đ/${UNIT_NAME[h.class]}`;
      r.note = `${num(d.qty)} ${UNIT_NAME[h.class]} · giá nay ${num(d.price)} đ`;
      if (h.class === "bond") r.note += ` · coupon ${pct(d.coupon)}/năm · đáo hạn ${day(d.maturity)}`;
    } else if (h.class === "fund") {
      r.bought = day(d.bought);
      if (d.avg_nav) r.price = `${num(d.avg_nav)} đ/CCQ`;
      r.note = `${num(d.units)} CCQ · NAV nay ${num(d.nav)} đ`;
    } else if (h.class === "real_estate") {
      r.bought = d.purchase_year ? `Năm ${d.purchase_year}` : "";
      if (h.cost) r.price = vnd(h.cost);
      r.note = [d.sqm ? `${num(d.sqm)} m²` : "", d.area_name || "", d.rental_monthly ? `cho thuê ${vnd(d.rental_monthly)}/tháng` : ""].filter(Boolean).join(" · ");
    } else if (h.class === "deposit") {
      r.bought = day(d.opened);
      r.cost = h.value;
      if (d.rate && d.opened) {
        const days = Math.max(0, (new Date(asOf) - new Date(d.opened)) / 864e5);
        r.pnl = Math.round(h.value * d.rate * days / 365);
        r.ret = r.pnl / h.value;
        r.accrued = true;
      }
      r.note = [d.rate ? `lãi suất ${pct(d.rate)}/năm` : "", d.maturity ? `đáo hạn ${day(d.maturity)}` : ""].filter(Boolean).join(" · ");
    } else if (h.class === "gold") {
      r.note = `${num(d.qty)} lượng · giá nay ${vnd(d.price)}/lượng`;
    } else if (h.class === "insurance") {
      r.note = d.premium_annual ? `phí ${vnd(d.premium_annual)}/năm` : "";
    } else if (h.class === "loan") {
      r.note = [d.rate ? `lãi suất ${pct(d.rate)} ${d.rate_type === "floating" ? "thả nổi" : "cố định"}` : "",
        d.monthly_payment ? `trả ${vnd(d.monthly_payment)}/tháng` : "", d.end ? `đến ${day(d.end).slice(3)}` : ""].filter(Boolean).join(" · ");
    } else if (h.class === "card") {
      r.note = d.limit ? `hạn mức ${vnd(d.limit)}` : "";
    }
    if (r.pnl == null && r.cost != null && h.kind === "asset") {
      r.pnl = h.value - r.cost;
      r.ret = r.cost ? r.pnl / r.cost : null;
    }
    return r;
  }

  const pnlCell = (pnl, ret, accrued) => pnl == null ? `<span class="muted">—</span>`
    : `<span class="delta ${pnl >= 0 ? "up" : "down"}">${vnd(pnl, true)}</span><div class="small ${pnl >= 0 ? "delta up" : "delta down"}">${ret == null ? "" : pct(ret, true)}${accrued ? `<span class="muted"> lãi dồn tích</span>` : ""}</div>`;

  function holdingsTable(d) {
    const family = d.scope === "family";
    const srcLabel = (h) => esc((d.sources.find(s => s.source === h.source) || {}).label || h.source);
    const assets = d.net_worth.assets || 1;
    // the cells before the money columns, label in "Khoản": hidden columns (.wide) stay aligned on a phone
    const lead = (label) => `${family ? `<td class="wide"></td>` : ""}<td>${label}</td><td class="wide"></td><td></td><td class="wide"></td>`;
    const known = new Set(BOOK.flatMap(g => g.classes));
    const groups = BOOK.map(g => ({...g, rows: d.holdings.filter(h => g.classes.includes(h.class))}))
      .concat([{id: "other", label: "Khác", color: "var(--other)", rows: d.holdings.filter(h => !known.has(h.class))}])
      .filter(g => g.rows.length);
    const body = groups.map(g => {
      const rows = g.rows.map(h => ({h, r: bookRow(h, d.as_of)}));
      const total = rows.reduce((a, x) => a + x.h.value, 0);
      const priced = rows.filter(x => x.r.pnl != null);
      const pnl = priced.length ? priced.reduce((a, x) => a + x.r.pnl, 0) : null;
      const cost = priced.reduce((a, x) => a + (x.r.cost || 0), 0);
      const open = !state.closed[g.id];
      const head = `<tr class="grouprow" data-group="${g.id}" tabindex="0" aria-expanded="${open}">
        ${lead(`<span class="caret" aria-hidden="true">${open ? "▾" : "▸"}</span><span class="sw" style="background:${g.color}"></span>
          <b>${esc(g.label)}</b> <span class="muted small nowrap">${rows.length} khoản${g.debt ? "" : ` · ${pct(total / assets, false, total / assets < 0.1 ? 1 : 0)} tài sản`}</span>`)}
        <td class="num">${cost && !g.debt ? vnd(cost) : ""}</td>
        <td class="num"><b>${g.debt ? "−" : ""}${vnd(total)}</b></td>
        <td class="num">${g.debt ? "" : pnlCell(pnl, pnl != null && cost ? pnl / cost : null)}</td></tr>`;
      const lines = open ? rows.map(({h, r}) => `<tr class="line">
        ${family ? `<td class="wide">${esc(h.owner_name)}</td>` : ""}
        <td><div>${esc(h.name)}</div>${r.note ? `<div class="muted small">${esc(r.note)}</div>` : ""}<div class="sub">${family ? esc(h.owner_name) + " · " : ""}${srcLabel(h)}</div></td>
        <td class="wide"><div>${srcLabel(h)}</div><span class="badge ${h.trust}">${TRUST_LABEL[h.trust]}</span></td>
        <td class="nowrap">${r.bought || `<span class="muted">—</span>`}</td>
        <td class="num wide">${r.price || `<span class="muted">—</span>`}</td>
        <td class="num">${r.cost != null && h.kind === "asset" ? vnd(r.cost) : `<span class="muted">—</span>`}</td>
        <td class="num">${h.kind === "liability" ? "−" : ""}${vnd(h.value)}</td>
        <td class="num">${h.kind === "liability" ? `<span class="muted">—</span>` : pnlCell(r.pnl, r.ret, r.accrued)}</td></tr>`).join("") : "";
      return `<tbody>${head}${lines}</tbody>`;
    }).join("");
    const nw = d.net_worth;
    return `<div class="card mt"><h2>Tất cả tài sản và khoản nợ <span class="hint">${d.holdings.length} khoản · ${groups.length} nhóm · bấm tên nhóm để thu gọn</span></h2>
      <div class="tablewrap"><table class="book">
        <thead><tr>${family ? `<th class="wide">Chủ sở hữu</th>` : ""}<th>Khoản</th><th class="wide">Nguồn · độ tin cậy</th><th>Ngày mua</th>
          <th class="num wide">Giá mua</th><th class="num">Giá vốn</th><th class="num">Giá trị hiện tại</th><th class="num">Lãi / lỗ</th></tr></thead>
        ${body}
        <tfoot>
          <tr>${lead("Tổng tài sản")}<td></td><td class="num">${vnd(nw.assets)}</td><td></td></tr>
          <tr>${lead("Tổng nợ")}<td></td><td class="num">−${vnd(nw.liabilities)}</td><td></td></tr>
          <tr class="total">${lead("Tài sản ròng")}<td></td><td class="num">${vnd(nw.value)}</td><td></td></tr>
        </tfoot>
      </table></div>
      <p class="muted small" style="margin-bottom:0">Giá vốn: tổng số tiền đã bỏ ra · lãi/lỗ so với giá vốn, chưa trừ thuế phí · tiền gửi: lãi dồn tích đến ${esc(day(d.as_of))} · “—”: nguồn chưa cung cấp.</p></div>`;
  }

  // ── tier 2: a statement the client uploads ──────────────────────────
  const METHOD = {ai: "AI đọc", rules: "Đọc theo mẫu"};
  function uploadCard() {
    const me = state.clients.find(c => c.id === state.client) || {};
    const read = state.reads[state.client];
    const rows = read ? read.holdings.map(h => `<tr><td>${esc(h.name)}</td><td class="num">${vnd(h.value)}</td></tr>`).join("") : "";
    return `<div class="card"><h2>Tải sao kê <span class="hint">PDF · Excel · CSV</span></h2>
      <p class="muted small" style="margin-top:-6px">AI đọc sao kê của ngân hàng / công ty chứng khoán khác và tách từng khoản; bạn không phải nhập tay.</p>
      <div class="actions"><label class="btn"><input type="file" id="stmt-file" accept=".pdf,.xlsx,.xlsm,.csv,.txt" hidden>Chọn tệp…</label>
        ${(me.samples || []).map(n => `<button type="button" class="btn ghostbtn" data-sample="${esc(n)}">Dùng sao kê mẫu: ${esc(n)}</button>`).join("")}</div>
      <div id="stmt-out" class="mt" aria-live="polite">${read ? `<div><b>Đã đọc ${read.count} khoản từ ${esc(read.institution)}</b> · ${vnd(read.total)}
        <span class="badge statement">${METHOD[read.method] || read.method}</span></div>
        <div class="tablewrap"><table><tbody>${rows}</tbody></table></div>` : ""}</div></div>`;
  }

  function b64(buf) {
    const bytes = new Uint8Array(buf);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  }

  async function sendStatement(name, buf) {
    const out = $("#stmt-out");
    if (out) out.innerHTML = `<span class="muted">Đang đọc ${esc(name)}…</span>`;
    try {
      const read = (await api("/api/statement", {client_id: state.client, filename: name, content: b64(buf)})).read;
      state.reads[state.client] = read;
      await load();
    } catch (e) {
      if (out) out.innerHTML = `<span class="error">Không đọc được tệp: ${esc(e.message)}</span>`;
    }
  }

  // ── tier 3: the chat ────────────────────────────────────────────────
  function chatCard() {
    const log = state.chat[state.client] || [];
    const lines = log.map(m => m.who === "me"
      ? `<div class="msg me">${esc(m.text)}</div>`
      : `<div class="msg bot">${esc(m.text).replace(/\n/g, "<br>")}${m.method ? `<div class="muted small">${m.method === "ai" ? "Trợ lý AI" : "Đọc theo quy tắc"}${m.recorded ? ` · ghi ${m.recorded} mục` : ""}</div>` : ""}</div>`).join("");
    return `<div class="card"><h2>Bổ sung tài sản <span class="hint">khai báo qua chat</span></h2>
      <div class="chat" id="chat-log" aria-live="polite">${lines || `<div class="msg bot">Chào anh/chị, hãy kể những tài sản ngân hàng chưa thấy: nhà đất, vàng, cổ phần, khoản nợ, người phụ thuộc…</div>`}</div>
      <div class="chips">${EXAMPLES.map(t => `<button type="button" class="chipbtn" data-say="${esc(t)}">${esc(t)}</button>`).join("")}</div>
      <form id="chat-form" class="chatform"><input id="chat-in" autocomplete="off" placeholder="Ví dụ: Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ" aria-label="Tin nhắn">
        <button type="submit" class="btn">Gửi</button></form></div>`;
  }

  async function say(text) {
    text = (text || "").trim();
    if (!text || state.busy) return;
    const log = state.chat[state.client] = state.chat[state.client] || [];
    log.push({who: "me", text});
    state.busy = true;
    if (state.board) renderSources(state.board);
    try {
      const turn = (await api("/api/declare", {client_id: state.client, message: text, session_id: `${state.client}-web`})).turn;
      log.push({who: "bot", text: turn.reply, method: turn.method, recorded: turn.recorded.length});
    } catch (e) {
      log.push({who: "bot", text: "Xin lỗi, có lỗi khi ghi nhận: " + e.message});
    }
    state.busy = false;
    await load();
  }

  function wireSources() {
    for (const row of document.querySelectorAll("#tab-sources [data-group]")) {
      const flip = () => { state.closed[row.dataset.group] = !state.closed[row.dataset.group]; renderSources(state.board); };
      row.onclick = flip;
      row.onkeydown = (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); flip(); } };
    }
    const file = $("#stmt-file");
    if (file) file.onchange = async () => { const f = file.files[0]; if (f) sendStatement(f.name, await f.arrayBuffer()); };
    for (const b of document.querySelectorAll("[data-sample]")) {
      b.onclick = async () => {
        const r = await fetch(`/samples/${encodeURIComponent(b.dataset.sample)}`);
        sendStatement(b.dataset.sample, await r.arrayBuffer());
      };
    }
    for (const b of document.querySelectorAll("[data-say]")) b.onclick = () => say(b.dataset.say);
    const form = $("#chat-form");
    if (form) form.onsubmit = (ev) => { ev.preventDefault(); const i = $("#chat-in"); const t = i.value; i.value = ""; say(t); };
    const log = $("#chat-log");
    if (log) log.scrollTop = log.scrollHeight;
  }

  // ── alerts: what is moving the picture ──────────────────────────────
  const SEV = {
    high: {icon: "■", label: "Cao", color: "var(--critical)"},
    medium: {icon: "▲", label: "Trung bình", color: "var(--warning)"},
    low: {icon: "●", label: "Thấp", color: "var(--axis)"},
  };
  const KIND = {policy: "Chính sách", macro: "Vĩ mô", infrastructure: "Hạ tầng"};

  function sevTag(a) {
    if (a.opportunity) return `<span class="status"><span class="dot" style="background:var(--good)" aria-hidden="true"></span>Cơ hội · ${SEV[a.severity].label.toLowerCase()}</span>`;
    const v = SEV[a.severity];
    return `<span class="status"><span aria-hidden="true" style="color:${v.color}">${v.icon}</span>Rủi ro · ${v.label.toLowerCase()}</span>`;
  }

  function alertsCard(rep) {
    const box = $("#alerts-card");
    if (!box) return;
    const top = rep.alerts.slice(0, 3);
    box.innerHTML = `<h2>Headline news <span class="hint">${rep.risks} rủi ro · ${rep.opportunities} cơ hội</span></h2>
      <div class="alist">${top.map(a => `<div class="arow">${sevTag(a)}<b>${esc(a.title)}</b><span class="v ${a.impact >= 0 ? "delta up" : "delta down"}">${vnd(a.impact, true)}</span>
        <span class="muted small">${esc(a.message)}</span></div>`).join("")}</div>
      <button type="button" class="btn ghostbtn mt" id="to-alerts">Xem tất cả ${rep.alerts.length} tin →</button>`;
    $("#to-alerts").onclick = () => showTab("alerts");
  }

  // the short check on top of the news: the portfolio against its benchmark, the goals' gaps,
  // and what to do first (the full plan is in Wealth Planning Advisor)
  function wealthCheck() {
    const d = state.board;
    if (!d) return "";
    const pf = d.performance, rk = d.risk;
    const behind = pf.vs_benchmark < 0;
    const worst = d.holdings.filter(h => h.kind === "asset" && ["stock", "fund"].includes(h.class) && h.cost)
      .map(h => ({name: h.name, ret: (h.value - h.cost) / h.cost})).sort((a, b) => a.ret - b.ret)[0];
    const goals = followedGoals();
    const short = goals.filter(g => g.goal.gap > 0 && g.goal.status !== "on_track");
    const gap = short.reduce((a, g) => a + g.goal.gap, 0);
    const first = short.sort((a, b) => GOAL_RANK[b.goal.status] - GOAL_RANK[a.goal.status] || b.goal.gap - a.goal.gap)[0];
    const acts = [];
    if (behind && worst && worst.ret < pf.benchmark_ytd) acts.push(`Xem lại ${esc(worst.name)} (${pct(worst.ret, true)} so với giá vốn)`);
    if (rk.status !== "ok") acts.push(`Giảm điểm nóng: mức sụt giảm ước tính ${pct(rk.current)} so với ngưỡng ${pct(rk.limit, false, 0)}`);
    if (first && first.goal.actions[0]) acts.push(`${esc(first.title)}: ${esc(first.goal.actions[0].text)}`);
    return `<div class="card check">
      <h2>Wealth check <span class="hint">chênh lệch mục tiêu và hiệu quả so với benchmark</span></h2>
      <div class="grid g3">
        <div><div class="k">Lợi nhuận từ đầu năm</div><div class="big">${pct(pf.ytd_return, true)}</div>
          <div class="${behind ? "delta down" : "delta up"}">${behind ? "▼ kém" : "▲ hơn"} ${esc(pf.benchmark_name)} ${pct(Math.abs(pf.vs_benchmark))} <span class="muted">(${esc(pf.benchmark_name)} ${pct(pf.benchmark_ytd, true)})</span></div></div>
        <div><div class="k">Mục tiêu đang theo dõi</div><div class="big">${goals.length ? `${short.length}/${goals.length}` : "—"}</div>
          <div class="muted">${short.length ? `cần chú ý · thiếu tổng ${vnd(gap)}` : goals.length ? "đều đúng tiến độ" : "chưa đặt mục tiêu"}</div></div>
        <div><div class="k">Required action</div>
          ${acts.length ? `<ol class="acts">${acts.slice(0, 3).map(a => `<li>${a}</li>`).join("")}</ol>` : `<p class="muted">Không có việc gấp.</p>`}</div>
      </div>
      <button type="button" class="btn ghostbtn mt" id="to-plan">Mở Wealth Planning Advisor →</button></div>`;
  }

  const KIND_HEAD = {
    policy: ["Policy headlines", "Chính sách, pháp luật"],
    macro: ["Market & macro headlines", "Thị trường, lãi suất, tỷ giá"],
    infrastructure: ["Infrastructure headlines", "Hạ tầng, quy hoạch"],
  };

  // house views: what research houses expect, and which of the client's holdings each is about
  const STANCE = {
    positive: {text: "Tích cực", color: "var(--good)"},
    neutral: {text: "Trung tính", color: "var(--axis)"},
    cautious: {text: "Thận trọng", color: "var(--warning)"},
  };

  function viewTouches(v) {
    const t = v.touches || {};
    return ((state.board && state.board.holdings) || []).filter(h => {
      if (h.detail && h.detail.ticker && (t.tickers || []).includes(h.detail.ticker)) return true;
      if (h.class === "real_estate" && t.areas) return t.areas.includes(h.detail.area);
      return (t.classes || []).includes(h.class);
    });
  }

  function houseViews() {
    const vs = state.views;
    if (!vs) return "";
    if (vs.error) return `<div class="card mt error">Không tải được house views: ${esc(vs.error)}</div>`;
    const rows = vs.views.map(v => {
      const hit = viewTouches(v);
      return {v, hit, exposure: hit.reduce((a, h) => a + h.value, 0)};
    }).sort((a, b) => (b.hit.length > 0) - (a.hit.length > 0) || b.exposure - a.exposure);
    const mine = rows.filter(r => r.hit.length).length;
    const card = ({v, hit, exposure}) => {
      const st = STANCE[v.stance] || STANCE.neutral;
      return `<div class="card vcard${hit.length ? "" : " far"}">
        <div class="vhead"><b>${esc(v.house)}</b><span class="chip">${esc(v.kind)}</span><span class="muted small">${esc(v.date)}</span>
          <span class="stance" style="--c:${st.color};margin-left:auto">${st.text}</span></div>
        <h3>${esc(v.title)}</h3>
        <p>${esc(v.summary)}</p>
        <div class="stats small">
          <div class="stat"><span class="k">Dự báo / mục tiêu</span><span class="v">${esc(v.target)}</span></div>
          <div class="stat"><span class="k">Chủ đề · kỳ hạn</span><span class="v">${esc(v.topic)} · ${esc(v.horizon)}</span></div>
          <div class="stat"><span class="k">Liên quan danh mục của bạn</span><span class="v">${hit.length
            ? `${hit.slice(0, 4).map(h => esc(h.name)).join(", ")}${hit.length > 4 ? ` +${hit.length - 4}` : ""} · ${hit.some(h => h.kind === "asset") ? vnd(exposure) : "khoản nợ"}`
            : `<span class="muted">không trực tiếp</span>`}</span></div>
        </div></div>`;
    };
    return `<section class="mt"><div class="sechead"><h2>House views</h2><span class="muted">Dự báo từ quỹ, công ty chứng khoán, hãng tin và nghiên cứu nội bộ ·
        ${rows.length} góc nhìn · <b>${mine}</b> liên quan danh mục của bạn</span></div>
      <div class="grid g2">${(state.viewsAll ? rows : rows.slice(0, 2)).map(card).join("")}</div>
      ${rows.length > 2 ? `<button type="button" class="btn ghostbtn mt" id="views-more">${state.viewsAll ? "Thu gọn ↑" : `Xem thêm ${rows.length - 2} góc nhìn khác →`}</button>` : ""}
      <p class="note mt">ⓘ ${esc(vs.note)}</p></section>`;
  }

  async function loadViews() {
    try {
      const r = await fetch("/api/views");
      if (!r.ok) throw new Error(`/api/views: ${r.status}`);
      state.views = await r.json();
    } catch (e) {
      state.views = {error: e.message};
    }
    if (state.tab === "alerts") renderAlerts();
  }

  function renderAlerts() {
    const box = $("#tab-alerts");
    const rep = state.alerts;
    if (!rep) { box.innerHTML = `${wealthCheck()}<div class="card muted mt">Đang quét…</div>`; wireCheck(box); return; }
    const f = state.alertFilter;
    const list = rep.alerts.filter(a => f === "all" || (f === "opp" ? a.opportunity : !a.opportunity));
    const maxAbs = Math.max(1, ...rep.alerts.map(a => Math.abs(a.impact)));
    const card = (a) => `<div class="card acard">
          <div class="ahead2">${sevTag(a)}<span class="chip">${esc(a.status_label)}</span></div>
          <h3>${esc(a.title)}</h3>
          <p>${esc(a.message)}</p>
          <div class="stats small">
            <div class="stat"><span class="k">Tác động ước tính (đã tính xác suất)</span><span class="v ${a.impact >= 0 ? "delta up" : "delta down"}">${vnd(a.impact, true)} · ${pct(a.impact_pct, true, 2)} tài sản ròng</span></div>
            <div class="stat"><span class="k">Mức nắm giữ × Độ nhạy × Xác suất</span><span class="v">${vnd(a.exposure)} × ${pct(a.sensitivity, true, 2)} × ${pct(a.probability, false, 0)}</span></div>
            <div class="stat"><span class="k">Khoản bị ảnh hưởng</span><span class="v">${a.affected.map(esc).join(", ")}</span></div>
          </div>
          <div class="muted small mt">Nguồn: ${esc(a.source)}</div></div>`;
    const sections = Object.keys(KIND_HEAD).map(k => {
      const items = list.filter(a => a.kind === k);
      if (!items.length) return "";
      const net = items.reduce((t, a) => t + a.impact, 0);
      return `<section class="mt"><div class="sechead"><h2>${KIND_HEAD[k][0]}</h2><span class="muted">${KIND_HEAD[k][1]} · ${items.length} tin · tổng tác động
        <b class="${net >= 0 ? "delta up" : "delta down"}">${vnd(net, true)}</b></span></div>
        <div class="grid g2">${items.map(card).join("")}</div></section>`;
    }).join("");
    box.innerHTML = `${wealthCheck()}
      <div class="card mt"><h2>Tác động lên tài sản ròng <span class="hint">${rep.scope === "family" ? "gia đình" : "cá nhân"} · tài sản ròng ${vnd(rep.net_worth)}</span></h2>
        <p class="muted small" style="margin-top:-4px">Tác động (VND) = Mức nắm giữ × Độ nhạy × Xác suất xảy ra · xác suất theo trạng thái: dự thảo thấp, đang lấy ý kiến trung bình, đã thông qua cao.</p>
        <div class="keys"><span><span class="sw" style="background:var(--out)"></span>Rủi ro (giảm tài sản)</span><span><span class="sw" style="background:var(--in)"></span>Cơ hội (tăng tài sản)</span>
          <span class="seg" role="group" aria-label="Lọc" style="margin-left:auto">${[["all", "Tất cả"], ["risk", "Rủi ro"], ["opp", "Cơ hội"]].map(([k, t]) => `<button type="button" data-af="${k}" aria-pressed="${f === k}">${t}</button>`).join("")}</span></div>
        <div class="dbars mt">${list.slice(0, 10).map(a => `<div class="dbar" tabindex="0" data-tip="${esc(a.id)}"><span class="dl">${esc(a.title)}</span>
          <span class="dt"><span class="dneg">${a.impact < 0 ? `<span style="width:${Math.abs(a.impact) / maxAbs * 100}%"></span>` : ""}</span><span class="dpos">${a.impact > 0 ? `<span style="width:${a.impact / maxAbs * 100}%"></span>` : ""}</span></span>
          <span class="dv">${vnd(a.impact, true)}</span></div>`).join("")}</div>
      </div>
      ${houseViews()}
      <p class="note mt">⚠ ${esc(rep.note)}</p>
      ${sections}`;
    wireCheck(box);
    const more = $("#views-more", box);
    if (more) more.onclick = () => { state.viewsAll = !state.viewsAll; renderAlerts(); };
    for (const b of box.querySelectorAll("[data-af]")) b.onclick = () => { state.alertFilter = b.dataset.af; renderAlerts(); };
    for (const el of box.querySelectorAll("[data-tip]")) {
      const a = rep.alerts.find(x => x.id === el.dataset.tip);
      C.hover(el, `<b>${esc(a.title)}</b><div>${esc(a.message)}</div><div class="row"><span>Tác động</span><span>${vnd(a.impact, true)}</span></div>`);
    }
  }

  function wireCheck(box) {
    const b = $("#to-plan", box);
    if (b) b.onclick = () => showTab("scenarios");
  }

  async function loadAlerts(seq) {
    try {
      const rep = (await api("/api/alerts", {client_id: state.client, scope: state.scope})).report;
      if (seq !== state.seq) return;
      state.alerts = rep;
      alertsCard(rep);
      renderAlerts();
    } catch (e) {
      const box = $("#alerts-card");
      if (box) box.innerHTML = `<h2>Headline news</h2><p class="error">Không tải được: ${esc(e.message)}</p>`;
    }
  }

  // ── Wealth Planning Advisor: life goals, their gaps, what to do ──────
  const PARAMS = {
    per_year: ["Học phí mỗi năm", "tỷ"], years: ["Số năm", ""], start_year: ["Năm bắt đầu", ""], fx_rise: ["Tỷ giá tăng", "%"],
    retire_age: ["Tuổi nghỉ hưu", ""], spending_after: ["Chi tiêu mỗi tháng sau nghỉ hưu", "triệu"], price: ["Giá BĐS", "tỷ"],
    loan_ratio: ["Tỷ lệ vay", "%"], rate: ["Lãi suất vay", "%"], rent_monthly: ["Tiền thuê kỳ vọng mỗi tháng", "triệu"],
    share: ["Phần chuyển cho con", "%"], need: ["Số tiền cần", "tỷ"], cost: ["Chi phí điều trị", "tỷ"], cover: ["Bảo hiểm chi trả", "%"],
    usd: ["Số USD cần", "USD"], amount: ["Khoản rút ra", "tỷ"],
  };
  const UNIT = {"tỷ": 1e9, "triệu": 1e6, "%": 0.01, "": 1, "USD": 1};
  // green / amber / red belong to a goal's status only, never to a scenario's numbers
  const GOAL_STATUS = {
    on_track: {text: "On track", color: "var(--good)"},
    at_risk: {text: "At risk", color: "var(--warning)"},
    off_track: {text: "Off track", color: "var(--critical)"},
    none: {text: "Chưa theo dõi", color: "var(--other)"},
  };
  const GOAL_RANK = {on_track: 0, at_risk: 1, off_track: 2};
  const QUEUE_TAG = {pending: ["statement", "Chờ chuyên gia duyệt"], approved: ["verified", "Đã duyệt"], rejected: ["declared", "Từ chối"]};

  function planState() {
    const cid = state.client;
    if (!state.plan[cid]) {
      let set = null;
      try { set = JSON.parse(localStorage.getItem(`mf.goals.${cid}`) || "null"); } catch (_) { /* */ }
      state.plan[cid] = {pick: null, result: null, set, sent: {}};
    }
    return state.plan[cid];
  }

  function isFollowed(g) {
    const st = planState();
    return st.set ? st.set.includes(g.id) : g.followed;
  }

  function followedGoals() {
    if (!state.goals || state.goals.client !== state.client) return [];
    return state.goals.list.filter(isFollowed);
  }

  function follow(id, on) {
    const st = planState();
    const now = new Set(st.set || state.goals.list.filter(g => g.followed).map(g => g.id));
    if (on) now.add(id); else now.delete(id);
    st.set = [...now];
    try { localStorage.setItem(`mf.goals.${state.client}`, JSON.stringify(st.set)); } catch (_) { /* */ }
  }

  function chip(key) {
    const s = GOAL_STATUS[key] || GOAL_STATUS.none;
    return `<span class="gchip" style="--c:${s.color}"><span class="dot" aria-hidden="true"></span>${s.text}</span>`;
  }

  function gapLine(g) {
    return g.gap > 0 ? `Thiếu ${vnd(g.gap)}` : g.gap < 0 ? `Dư ${vnd(-g.gap)}` : "Vừa đủ";
  }

  async function loadGoals(seq) {
    try {
      const out = await api("/api/goals", {client_id: state.client, scope: state.scope});
      if (seq !== state.seq) return;
      state.goals = {client: state.client, scope: state.scope, list: out.goals, stages: out.stages};
      const st0 = planState(), r0 = st0.result;
      const kept = r0 && !r0.error && st0.scope === state.scope && out.goals.find(g => g.id === r0.scenario);
      if (kept && r0.goal) { kept.goal = r0.goal; kept.params = r0.params; }
    } catch (e) {
      state.goals = {client: state.client, list: [], stages: {}, error: e.message};
    }
    const st = planState();
    if (st.scope !== state.scope) { st.scope = state.scope; st.result = null; }   // numbers of another view
    if (!st.pick || !state.goals.list.concat(state.catalog).some(x => x.id === st.pick)) {
      const mine = followedGoals().sort((a, b) => GOAL_RANK[b.goal.status] - GOAL_RANK[a.goal.status]);
      st.pick = (mine[0] || state.goals.list[0] || {}).id || null;
      st.result = null;
    }
    renderScenarios();
    if (state.tab === "alerts") renderAlerts();
    // the picked one again on fresh data, with the assumptions it was last tried with
    const r1 = st.result && !st.result.error && st.result.scenario === st.pick ? st.result : null;
    if (st.pick) runScenario(st.pick, r1 && !r1.goal ? r1.params : null, true);
  }

  async function runScenario(id, params, quiet) {
    const st = planState();
    st.pick = id;
    const goalNow = state.goals && state.goals.list.find(g => g.id === id);
    state.simBusy = true;
    if (!quiet) renderScenarios();
    try {
      st.result = (await api("/api/scenario", {client_id: state.client, scenario: id, params: params || (goalNow ? goalNow.params : {}), scope: state.scope})).result;
      // a goal follows the assumptions just tried: its card and status update with them
      if (goalNow && st.result.goal) { goalNow.goal = st.result.goal; goalNow.params = st.result.params; }
    } catch (e) {
      st.result = {error: e.message};
    }
    state.simBusy = false;
    renderScenarios();
    if (!quiet) {
      const panel = $("#tab-scenarios .simgrid > div:last-child");
      if (panel && innerWidth <= 980) panel.scrollIntoView({block: "start", behavior: "smooth"});
    }
  }

  async function propose(scenario, option, title, summary) {
    const st = planState();
    try {
      const item = (await api("/api/review/propose", {client_id: state.client, scenario, title, option, summary})).item;
      st.sent[`${scenario}:${option.title}`] = item.id;
      await loadQueue();
    } catch (e) { alert("Không gửi được: " + e.message); }
    renderScenarios();
  }

  function sentTag(key) {
    const st = planState();
    const id = st.sent[key];
    const item = id && state.queue.find(q => q.id === id);
    if (!item) return "";
    const [cls, text] = QUEUE_TAG[item.status] || QUEUE_TAG.pending;
    return `<span class="badge ${cls}">${text}</span>`;
  }

  function simForm(r) {
    const form = Object.entries(r.params || {}).filter(([k]) => PARAMS[k]).map(([k, v]) => {
      const [label, unit] = PARAMS[k];
      const shown = typeof v === "number" ? +(v / UNIT[unit]).toFixed(unit === "%" ? 1 : 2) : v;
      return `<label class="field"><span>${label}${unit ? ` (${unit})` : ""}</span><input type="number" step="any" name="${k}" value="${shown}"></label>`;
    }).join("");
    return form ? `<form id="sim-form" class="simform">${form}<button type="submit" class="btn">Chạy lại</button></form>` : "";
  }

  function beforeAfter(r) {
    const cmp = (k, f) => `<td class="num">${f(r.before[k])}</td><td class="num">${f(r.after[k])}</td>`;
    return `<div class="tablewrap mt"><table><thead><tr><th></th><th class="num">Trước</th><th class="num">Sau</th></tr></thead><tbody>
      <tr><td>Tài sản ròng</td>${cmp("net_worth", vnd)}</tr>
      <tr><td>Thanh khoản</td>${cmp("liquid", vnd)}</tr>
      <tr><td>Đủ chi</td>${cmp("liquid_months", monthsText)}</tr></tbody></table></div>`;
  }

  // the numbers behind a scenario, all in one neutral tone
  function summaryLines(r) {
    return `<div class="stats mt">${r.summary.map(l => `<div class="stat"><span class="k">${esc(l.label)}</span><span class="v">${esc(l.value)}</span></div>`).join("")}</div>`;
  }

  // how the goal and the portfolio funding it moved: this month and this year, against the plan
  function trackingCard(g) {
    const t = g.tracking;
    if (!t) return "";
    const m = t.month, d = state.board && state.board.performance;
    const sign = (x) => `<span class="${x >= 0 ? "delta up" : "delta down"}">${vnd(x, true)}</span>`;
    const pc = (x) => `<span class="${x >= 0 ? "delta up" : "delta down"}">${pct(x, true)}</span>`;
    const rows = t.points.map((p, i) => {
      const prev = i ? t.points[i - 1] : null;
      const move = prev ? p.gap - prev.gap : null;
      return `<tr><td>${esc(p.label)}</td><td class="num">${vnd(p.pool)}</td>
        <td class="num">${p.gap > 0 ? "Thiếu " + vnd(p.gap) : "Dư " + vnd(-p.gap)}</td>
        <td class="num">${move == null || Math.abs(move) < 1e6 ? "—" : `<span class="${move > 0 ? "delta down" : "delta up"}">${move > 0 ? "xấu đi " : "cải thiện "}${vnd(Math.abs(move))}</span>`}</td></tr>`;
    }).join("");
    return `<div class="card mt"><h2>Performance tracking <span class="hint">Theo dõi so với danh mục · nguồn: ${esc(t.pool_label.toLowerCase())}</span></h2>
      <div class="callout ${t.behind ? "behind" : "ahead"}"><b>${t.behind ? "▼ Tháng này kém kỳ vọng" : "▲ Tháng này đạt kỳ vọng"}</b><div>${esc(t.note)}</div></div>
      <div class="grid g3 mt">
        <div><div class="k">Tháng này · thực tế</div><div class="big">${sign(m.actual)}</div><div class="small">${pc(m.actual_pct)} nguồn tài sản</div></div>
        <div><div class="k">Tháng này · kỳ vọng</div><div class="big">${vnd(m.expected, true)}</div><div class="small muted">lãi ${pct(t.rate, false, 0)}/năm${t.saving ? ` + để dành ${vnd(t.saving)}/tháng` : ""}</div></div>
        <div><div class="k">Hụt / vượt so với kỳ vọng</div><div class="big">${sign(m.short)}</div><div class="small muted">từ đầu năm: ${pc(t.ytd.actual_pct)} so với kỳ vọng ${pct(t.ytd.expected_pct, true)}</div></div>
      </div>
      <div class="tablewrap mt"><table><thead><tr><th>Mốc</th><th class="num">Nguồn cho mục tiêu</th><th class="num">Chênh lệch mục tiêu</th><th class="num">Thay đổi</th></tr></thead><tbody>${rows}</tbody></table></div>
      ${t.movers.length ? `<div class="mt"><div class="k">Biến động lớn tháng này trong nguồn</div>
        <ul class="legend">${t.movers.map(x => `<li><span class="sw" style="background:${x.change >= 0 ? "var(--in)" : "var(--out)"}"></span><span>${esc(x.name)}</span><span class="v">${vnd(x.change, true)}</span><span class="p">${pct(x.pct, true)}</span></li>`).join("")}</ul></div>` : ""}
      ${d ? `<p class="small muted mt" style="margin-bottom:0">Toàn danh mục đầu tư từ đầu năm ${pct(d.ytd_return, true)} so với ${esc(d.benchmark_name)} ${pct(d.benchmark_ytd, true)}:
        <span class="${d.vs_benchmark >= 0 ? "delta up" : "delta down"}">${d.vs_benchmark >= 0 ? "hơn" : "kém"} ${pct(Math.abs(d.vs_benchmark))}</span>.</p>` : ""}
    </div>`;
  }

  function optionCards(r, key) {
    return `<div class="grid g2 mt">${(r.options || []).map(o => {
      const tag = sentTag(`${key}:${o.title}`);
      return `<div class="card"><div class="ahead2"><span class="chip">${o.id === "light" ? "Hướng nhẹ" : "Hướng mạnh"}</span>${tag}</div>
        <h3 style="margin:8px 0">${esc(o.title)}</h3>
        <div class="small muted">Làm gì</div><ul>${o.actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul>
        <div class="small muted">Kết quả</div><ul>${o.effect.map(a => `<li>${esc(a)}</li>`).join("")}</ul>
        ${tag ? "" : `<button type="button" class="btn ghostbtn" data-propose="${o.id}">Gửi chuyên gia duyệt</button>`}</div>`;
    }).join("")}</div>`;
  }

  function goalPanel(entry, r) {
    const g = (r && r.goal) || entry.goal;
    const followed = isFollowed(entry);
    const key = followed ? g.status : "none";
    const color = (GOAL_STATUS[key] || GOAL_STATUS.none).color;
    const acts = g.actions.map((a, i) => {
      const tag = sentTag(`${entry.id}:${a.text}`);
      const worth = a.cut > 0 ? (g.gap > 0 ? `giảm chênh lệch ~${vnd(a.cut)}` : `giá trị ~${vnd(a.cut)}`) : esc(a.effect);
      return `<li class="act"><span class="n">${i + 1}</span><div><b>${esc(a.text)}</b><div class="muted small">${worth} · ${a.option === "light" ? "Hướng nhẹ" : "Hướng mạnh"}</div></div>
        <div class="actbtn">${tag || `<button type="button" class="btn ghostbtn" data-act="${i}">Gửi chuyên gia duyệt</button>`}</div></li>`;
    }).join("");
    return `<div class="card">
        <div class="ahead2">${chip(key)}<span class="muted small">Mốc: ${esc(g.by)} · ${esc(entry.stage_label)}</span>
          <span style="margin-left:auto">${followed ? `<button type="button" class="linkbtn" data-unfollow="${entry.id}">Bỏ theo dõi</button>` : `<button type="button" class="btn" data-follow="${entry.id}">Đặt mục tiêu</button>`}</span></div>
        <h3 class="qtext" style="margin:8px 0 2px">${esc(entry.title)}</h3>
        ${r ? `<p class="muted" style="margin:0">${esc(r.question)}</p>` : ""}
      </div>
      <div class="card mt"><h2>Goal status <span class="hint">Tình trạng mục tiêu</span></h2>
        <div class="trio">
          <div><div class="k">Cần có</div><div class="big">${vnd(g.need)}</div></div>
          <div><div class="k">${esc(g.have_label)}</div><div class="big">${vnd(g.have)}</div></div>
          <div><div class="k">Chênh lệch</div><div class="big">${g.gap > 0 ? "−" + vnd(g.gap) : "+" + vnd(-g.gap)}</div></div>
        </div>
        <div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(g.progress * 100)}" aria-label="Tiến độ ${pct(g.progress, false, 0)}">
          <span class="fill" style="width:${g.progress * 100}%;background:${color}"></span></div>
        <div class="muted small">Đã có ${pct(g.progress, false, 0)} nhu cầu</div>
        <p class="verdict">${esc(g.verdict)}</p>
      </div>
      ${r ? trackingCard(g) : `<div class="card mt muted">Đang tính diễn biến so với danh mục…</div>`}
      <div class="card mt"><h2>Required action <span class="hint">Hành động cần làm · xếp theo mức giảm chênh lệch</span></h2>
        ${acts ? `<ol class="actlist">${acts}</ol>` : `<p class="muted">Không cần hành động thêm.</p>`}
      </div>
      ${r ? `<div class="card mt"><h2>Calculation details <span class="hint">Chi tiết tính toán · đổi giả định rồi Chạy lại, mục tiêu cập nhật ngay · dữ liệu ngày ${esc(r.as_of)}</span></h2>
        ${simForm(r)}${summaryLines(r)}${beforeAfter(r)}</div>
        ${optionCards(r, entry.id)}
        <p class="note mt">${esc(r.note)}</p>` : ""}`;
  }

  function scenarioPanel(r) {
    return `<div class="card">
        <div class="muted small">${r.kind === "stress" ? "Stress test thị trường · AI tự chạy" : "Quyết định tài sản"} · dữ liệu ngày ${esc(r.as_of)}</div>
        <h3 class="qtext" style="margin:4px 0 2px">${esc(r.title)}</h3><p class="muted">${esc(r.question)}</p>
        ${simForm(r)}${summaryLines(r)}${beforeAfter(r)}
      </div>
      ${optionCards(r, r.scenario)}
      <p class="note mt">${esc(r.note)}</p>`;
  }

  // a small wealth view on top of the plan: what there is, how it earns, the goals' need against
  // what is there, and the money in and out — the past year as it happened, the next as forecast
  function wealthMini() {
    const d = state.board;
    if (!d) return "";
    const nw = d.net_worth, pf = d.performance, cf = d.cashflow;
    const goals = followedGoals();
    const need = goals.reduce((a, g) => a + g.goal.need, 0), have = goals.reduce((a, g) => a + Math.min(g.goal.have, g.goal.need), 0);
    const short = goals.filter(g => g.goal.gap > 0);
    const saving = short.reduce((a, g) => a + (g.goal.monthly || 0), 0);
    const unfunded = short.filter(g => g.goal.monthly == null);
    const past = (cf.history || []).filter(m => m.in || m.out);
    const pastNet = past.length ? past.reduce((a, m) => a + m.net, 0) / past.length : null;
    const ahead = cf.months.slice(0, 12);
    const aheadIn = ahead.reduce((a, m) => a + m.in, 0), aheadOut = ahead.reduce((a, m) => a + m.out, 0);
    // what is left each month (income less spending), as the goals measure it
    const surplus = goals.length ? Math.max(0, goals[0].goal.surplus) : 0;
    const left = surplus - saving;
    const up = nw.month_change >= 0;
    // a decision or a stress test picked below: the summary shows the picture after it
    const st = planState(), r = st.result;
    const sc = r && !r.error && r.scenario === st.pick && r.before && r.after
      && !(state.goals && state.goals.list.some(g => g.id === r.scenario)) ? r : null;
    const dNw = sc ? sc.after.net_worth - sc.before.net_worth : 0;
    const dLq = sc ? sc.after.liquid - sc.before.liquid : 0;
    const was = (x) => `<span class="muted">trước ${x}</span>`;
    const bars = goals.map(g => {
      const x = g.goal, col = (GOAL_STATUS[x.status] || GOAL_STATUS.none).color;
      return `<li><div class="ahead2"><b>${esc(g.title)}</b>${chip(x.status)}</div>
        <div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(x.progress * 100)}" aria-label="${esc(g.title)}: đang có ${pct(x.progress, false, 0)} nhu cầu">
          <span class="fill" style="width:${x.progress * 100}%;background:${col}"></span><span class="need" aria-hidden="true"></span></div>
        <div class="small"><span class="muted">Đang có</span> ${vnd(Math.min(x.have, x.need))} <span class="muted">/ cần</span> ${vnd(x.need)}
          <span class="muted">· ${esc(x.by)}</span> · ${x.gap > 0 ? `<span class="delta down">thiếu ${vnd(x.gap)}</span>` : `<span class="delta up">đủ</span>`}</div></li>`;
    }).join("");
    return `<div class="card mini mb">
      <h2>Wealth view <span class="hint">tóm tắt tài sản · so với mục tiêu đã đặt · ${d.scope === "family" ? "gia đình" : "cá nhân"}</span></h2>
      ${sc ? `<div class="scenbar"><span class="chip">${sc.kind === "stress" ? "Stress test" : "Kịch bản"}</span><span>Số liệu bên dưới là <b>sau</b> kịch bản <b>${esc(sc.title)}</b></span>
        <button type="button" class="linkbtn" id="scen-off">Về hiện trạng</button></div>` : ""}
      <div class="minitiles${sc ? " scen" : ""}">
        ${sc ? `<div><div class="k">Tổng tài sản ròng · sau kịch bản</div><div class="big">${vnd(sc.after.net_worth)}</div>
          <div class="small"><span class="delta ${dNw >= 0 ? "up" : "down"}">${vnd(dNw, true)} (${pct(sc.before.net_worth ? dNw / sc.before.net_worth : 0, true)})</span> ${was(vnd(sc.before.net_worth))}</div></div>`
        : `<div><div class="k">Tổng tài sản ròng</div><div class="big">${vnd(nw.value)}</div>
          <div class="small"><span class="delta ${up ? "up" : "down"}">${up ? "▲" : "▼"} ${pct(nw.month_change_pct, true)}</span> <span class="muted">tháng này · tài sản ${vnd(nw.assets)}, nợ ${vnd(nw.liabilities)}</span></div></div>`}
        ${sc ? `<div><div class="k">Thanh khoản · sau kịch bản</div><div class="big">${vnd(sc.after.liquid)}</div>
          <div class="small"><span class="delta ${dLq >= 0 ? "up" : "down"}">${vnd(dLq, true)}</span> · đủ chi ${monthsText(sc.after.liquid_months)} ${was(monthsText(sc.before.liquid_months))}</div></div>` : ""}
        <div${sc ? " hidden" : ""}><div class="k">Lãi / lỗ danh mục đầu tư</div><div class="big"><span class="delta ${pf.unrealized >= 0 ? "up" : "down"}">${pct(pf.unrealized_pct, true)}</span></div>
          <div class="small"><span class="muted">${vnd(pf.unrealized, true)} chưa chốt · từ đầu năm</span> ${pct(pf.ytd_return, true)}
            <span class="${pf.vs_benchmark >= 0 ? "delta up" : "delta down"}">(${pf.vs_benchmark >= 0 ? "hơn" : "kém"} ${esc(pf.benchmark_name)} ${pct(Math.abs(pf.vs_benchmark))})</span></div></div>
        <div><div class="k">Mục tiêu đã đặt · đang có / cần có</div><div class="big">${goals.length ? pct(need ? have / need : 1, false, 0) : "—"}</div>
          <div class="small muted">${goals.length ? `${vnd(have)} / ${vnd(need)} · ${short.length}/${goals.length} mục tiêu còn thiếu` : "chưa đặt mục tiêu nào"}</div></div>
        <div${sc ? " hidden" : ""}><div class="k">Dòng tiền ròng 12 tháng tới · dự báo</div><div class="big">${vnd(aheadIn - aheadOut, true)}</div>
          <div class="small muted">vào ${vnd(aheadIn)} · ra ${vnd(aheadOut)}${pastNet != null ? ` · 12 tháng qua thực tế ${vnd(pastNet, true)}/tháng` : ""}</div></div>
      </div>
      <div class="minigrid mt">
        <div><div class="k">Dòng tiền vào / ra · 12 tháng qua (thực tế) và 12 tháng tới (dự báo)</div>
          <div class="keys">${cashKeys()}</div>
          <div id="plan-cash"></div></div>
        <div><div class="k">Cần có so với đang có · từng mục tiêu</div>
          ${goals.length ? `<ul class="gbars">${bars}</ul>` : `<p class="muted small">Chọn một mục tiêu bên dưới và bấm <b>Đặt mục tiêu</b> để theo dõi ở đây.</p>`}
          ${goals.length ? `<div class="callout ${left >= 0 && !unfunded.length ? "ahead" : "behind"} mt">
            <b>${saving ? `Mục tiêu cần để dành ${vnd(saving)}/tháng` : short.length ? "Mục tiêu còn thiếu nguồn bù" : "Các mục tiêu đã đủ nguồn"}</b>
            <div class="small">Thu nhập trừ chi tiêu còn dư ${vnd(surplus)}/tháng${saving ? ` → ${left >= 0 ? `còn dư ${vnd(left)}/tháng sau khi để dành` : `thiếu ${vnd(-left)}/tháng`}` : ""}${unfunded.length ? ` · ${unfunded.length} mục tiêu chưa có nguồn bù: ${unfunded.map(g => esc(g.title)).join(", ")}` : ""}.</div></div>` : ""}
        </div>
      </div></div>`;
  }

  function renderScenarios() {
    const box = $("#tab-scenarios");
    const st = planState();
    const goals = state.goals && state.goals.client === state.client ? state.goals : null;
    const head = `<div class="tabhead"><h1>Wealth Planning Advisor</h1><p>Tư vấn kế hoạch tài chính theo mốc đời</p></div>`;
    if (!goals) { box.innerHTML = `${head}${wealthMini()}<div class="card muted">Đang tính các mục tiêu…</div>`; drawCash(); return; }
    const stages = Object.keys(goals.stages);
    const card = (e) => {
      const on = isFollowed(e), g = e.goal;
      return `<button type="button" class="gitem${st.pick === e.id ? " on" : ""}" data-sim="${e.id}">
        <span class="gtop"><b>${esc(e.title)}</b>${chip(on ? g.status : "none")}</span>
        ${on ? `<span class="small">${gapLine(g)}</span>` : `<span class="small muted">Chưa đặt mục tiêu</span>`}</button>`;
    };
    const left = stages.map(k => {
      const items = goals.list.filter(e => e.stage === k);
      if (!items.length) return "";
      return `<div class="stage"><div class="stagehead">${esc(goals.stages[k])}</div><div class="slist">${items.map(card).join("")}</div></div>`;
    }).join("");
    const others = state.catalog.filter(c => !goals.list.some(g => g.id === c.id));
    const otherList = `<div class="stage"><div class="stagehead">Quyết định & stress test</div><div class="slist">${others.map(c => `<button type="button" class="sitem${st.pick === c.id ? " on" : ""}" data-sim="${c.id}">
      <b>${esc(c.title)}</b><span class="muted small">${esc(c.question)}</span></button>`).join("")}</div></div>`;
    const entry = goals.list.find(g => g.id === st.pick);
    const r = st.result && st.result.scenario === st.pick ? st.result : null;
    let panel;
    if (st.result && st.result.error) panel = `<div class="card error">Không mô phỏng được: ${esc(st.result.error)}</div>`;
    else if (entry) panel = goalPanel(entry, r);
    else if (state.simBusy || !r) panel = `<div class="card muted">Đang mô phỏng…</div>`;
    else panel = scenarioPanel(r);
    box.innerHTML = `${head}${wealthMini()}<div class="simgrid"><div class="card"><h2>Life goals <span class="hint">Mục tiêu theo giai đoạn đời</span></h2>${left}${otherList}</div>
      <div class="${state.simBusy ? "loading" : ""}">${panel}</div></div>`;
    drawCash();
    for (const b of box.querySelectorAll("[data-sim]")) b.onclick = () => runScenario(b.dataset.sim, null);
    const off = $("#scen-off", box);
    if (off) off.onclick = () => {
      const mine = followedGoals().sort((a, b) => GOAL_RANK[b.goal.status] - GOAL_RANK[a.goal.status]);
      const g = mine[0] || goals.list[0];
      if (g) runScenario(g.id, null);
    };
    for (const b of box.querySelectorAll("[data-follow]")) b.onclick = () => { follow(b.dataset.follow, true); renderScenarios(); };
    for (const b of box.querySelectorAll("[data-unfollow]")) b.onclick = () => { follow(b.dataset.unfollow, false); renderScenarios(); };
    for (const b of box.querySelectorAll("[data-propose]")) b.onclick = () => propose(r.scenario, r.options.find(o => o.id === b.dataset.propose), r.title, r.summary);
    for (const b of box.querySelectorAll("[data-act]")) {
      b.onclick = () => {
        const g = (r && r.goal) || entry.goal, a = g.actions[Number(b.dataset.act)];
        const opt = (r && r.options || []).find(o => o.id === a.option) || {};
        propose(entry.id, {id: a.option, title: a.text, actions: [a.text], effect: a.effect ? [a.effect] : (opt.effect || [])},
          entry.title, [{label: "Chênh lệch", value: gapLine(g)}, {label: "Giảm chênh lệch ước tính", value: vnd(a.cut)}]);
      };
    }
    const form = $("#sim-form");
    if (form) form.onsubmit = (ev) => {
      ev.preventDefault();
      const prm = {...r.params};
      for (const i of form.querySelectorAll("input")) prm[i.name] = Number(i.value) * UNIT[PARAMS[i.name][1]];
      runScenario(r.scenario, prm, true);
    };
  }

  // ── Advisory performance: what the AI advised, and what came of it ──
  const OUTCOME = {
    right: ["verified", "Đúng"], wrong: ["declared", "Sai"], missed: ["statement", "Bỏ lỡ"],
    avoided: ["", "Không làm · đúng"], open: ["", "Đang theo dõi"],
  };
  const AGENT_NAME = {news: "AI News Reader", impact: "AI Impact Assessor", planner: "AI Planning Advisor", chat: "AI Client Chat"};

  async function loadAdvisory() {
    const cid = state.client;
    if (state.advisory && state.advisory.client === cid && !state.advisory.stale) return;
    try {
      const r = await fetch(`/api/advisory?client_id=${encodeURIComponent(cid)}`);
      if (!r.ok) throw new Error(`/api/advisory: ${r.status}`);
      state.advisory = {client: cid, ...(await r.json())};
    } catch (e) {
      state.advisory = {client: cid, error: e.message};
    }
    if (cid !== state.client) return;
    renderPerformance();
    renderRM();
  }

  function tile(label, value, sub, tone) {
    return `<div class="card tile"><div class="k">${label}</div><div class="big ${tone || ""}">${value}</div><div class="muted small">${sub}</div></div>`;
  }

  function renderPerformance() {
    const box = $("#tab-performance");
    const me = state.clients.find(c => c.id === state.client) || {};
    const head = `${STAFF_BAR}
      <div class="tabhead"><h1>Advisory performance</h1><p>Hiệu quả tư vấn và AI cho khách hàng ${esc(me.name || "")} · 12 tháng</p></div>`;
    const a = state.advisory;
    if (!a || a.client !== state.client) { box.innerHTML = `${head}<div class="card muted">Đang tải…</div>`; return; }
    if (a.error) { box.innerHTML = `${head}<div class="card error">Không tải được: ${esc(a.error)}</div>`; return; }
    const t = a.tracking, sm = t.summary;
    const decided = sm.right + sm.wrong;
    const eng = t.engagement;
    const avgMin = Math.round(eng.minutes.reduce((x, y) => x + y, 0) / eng.minutes.length);
    const avgDays = Math.round(eng.days.reduce((x, y) => x + y, 0) / eng.days.length);
    const tests = t.risk_tests;
    const first = tests[0], last = tests[tests.length - 1];
    const drift = last.tolerance - first.tolerance;
    const over = last.tolerance - last.capacity;
    box.innerHTML = `${head}
      <div class="tiles">
        ${tile("Khuyến nghị", sm.advice, `${sm.right} đúng · ${sm.wrong} sai · ${sm.open} đang theo dõi`)}
        ${tile("Tỷ lệ đúng", decided ? pct(sm.right / decided, false, 0) : "—", "trên các khuyến nghị đã thực hiện")}
        ${tile("Tiền mang lại", vnd(sm.gained, true), "từ các khuyến nghị đúng", "delta up")}
        ${tile("Sai, thiệt hại", vnd(sm.lost, true), `${sm.wrong} khuyến nghị sai`, "delta down")}
        ${tile("Hành động bỏ lỡ", sm.missed, `khách hàng không thực hiện · đã có thể thêm ${vnd(sm.missed_value)}`)}
        ${tile("Tin quan trọng bị miss", sm.missed_news, `đã có tín hiệu sớm · tác động ${vnd(sm.missed_news_value, true)}`)}
      </div>
      <div class="card mt"><h2>AI pipeline <span class="hint">hiệu quả từng AI · điểm 0–100 · xu hướng độ chính xác 12 tháng</span></h2>
        <div class="pipe">${t.agents.map((g, i) => `<div class="agent">
          <div class="ahead2"><span class="step">${i + 1}</span><div><b>${esc(g.name)}</b><div class="muted small">${esc(g.name_vi)}</div></div><span class="score">${g.score}</span></div>
          <div class="spark" data-spark="${i}"></div>
          <div class="stats small">${g.metrics.map(m => `<div class="stat"><span class="k">${esc(m.label)}</span><span class="v ${m.tone === "bad" ? "delta down" : ""}">${esc(m.value)}</span></div>`).join("")}</div>
        </div>`).join("")}</div></div>
      <div class="grid g2 mt">
        <div class="card"><h2>Nhật ký khuyến nghị <span class="hint">${t.advice.length} khuyến nghị</span></h2>
          <div class="tablewrap"><table><thead><tr><th>Ngày</th><th>Khuyến nghị</th><th>Kết quả</th><th class="num">Giá trị</th></tr></thead><tbody>
          ${t.advice.map(x => `<tr><td class="nowrap">${esc(x.date)}</td><td>${esc(x.text)}<div class="muted small">${esc(AGENT_NAME[x.agent] || x.agent)}</div></td>
            <td><span class="badge ${OUTCOME[x.outcome][0]}">${OUTCOME[x.outcome][1]}</span></td>
            <td class="num ${x.value > 0 && x.outcome === "right" ? "delta up" : x.value < 0 ? "delta down" : ""}">${x.value ? vnd(x.value, x.outcome !== "missed") : "—"}</td></tr>`).join("")}
          </tbody></table></div></div>
        <div class="card"><h2>Tin quan trọng bị bỏ lỡ <span class="hint">đã có thể dự đoán</span></h2>
          <ul class="missed">${t.missed_news.map(n => `<li><div class="ahead2"><b>${esc(n.title)}</b><span class="delta down" style="margin-left:auto">${vnd(n.impact, true)}</span></div>
            <div class="small"><span class="muted">Xảy ra:</span> ${esc(n.date)} · <span class="muted">Tín hiệu sớm:</span> ${esc(n.signal)}</div>
            <div class="small muted">Vì sao bỏ lỡ: ${esc(n.why)}</div></li>`).join("")}</ul></div>
      </div>
      <div class="grid g2 mt">
        <div class="card"><h2>Mức độ theo dõi tin của khách hàng</h2>
          <div class="trio">
            <div><div class="k">Thời gian đọc</div><div class="big">${avgMin} phút</div><div class="muted small">trung bình mỗi tuần</div></div>
            <div><div class="k">Số ngày đọc</div><div class="big">${avgDays} ngày</div><div class="muted small">trung bình mỗi tháng</div></div>
            <div><div class="k">Cảnh báo đã mở</div><div class="big">${esc(eng.alerts_opened)}</div><div class="muted small">chuỗi ${eng.streak} ngày liền</div></div>
          </div>
          <div class="keys mt"><span class="seg" role="group" aria-label="Chỉ số">${[["minutes", "Phút đọc / tuần"], ["days", "Ngày đọc / tháng"]].map(([k, l]) => `<button type="button" data-eng="${k}" aria-pressed="${(state.engView || "minutes") === k}">${l}</button>`).join("")}</span></div>
          <div id="eng-chart" class="mt"></div></div>
        <div class="card"><h2>Khẩu vị rủi ro theo thời gian <span class="hint">${tests.length} lần làm bài test</span></h2>
          <div class="keys"><span><span class="sw" style="background:var(--s2)"></span>Mức chấp nhận rủi ro (khách hàng muốn)</span><span><span class="sw" style="background:var(--s1)"></span>Khả năng chịu rủi ro (dữ liệu cho thấy)</span></div>
          <div id="risk-chart" class="mt"></div>
          <p class="small">Mức chấp nhận ${drift >= 0 ? "tăng" : "giảm"} <b>${Math.abs(drift)} điểm</b> từ ${esc(first.date)} · hồ sơ hiện tại <b>${esc(last.profile || "—")}</b>${last.live ? " (bài test vừa làm)" : ""}.
            ${over > 15 ? `<br><span class="delta down">Khách hàng muốn chịu rủi ro cao hơn khả năng ${over} điểm: chuyên gia nên trao đổi lại trước khi tăng tỷ trọng rủi ro.</span>` : ""}</p></div>
      </div>
      <p class="note mt">${esc(a.note)}</p>`;
    t.agents.forEach((g, i) => $(`[data-spark="${i}"]`, box).append(C.sparkline(g.trend.map(v => Math.round(v * 100)), `${g.name}: độ chính xác 12 tháng`)));
    drawPerf();
    for (const b of box.querySelectorAll("[data-eng]")) b.onclick = () => { state.engView = b.dataset.eng; renderPerformance(); };
  }

  function drawPerf() {
    const all = state.advisoryAll, ea = $("#eng-all");
    if (all && !all.error && ea && ea.clientWidth) {
      const view = state.engView || "minutes";
      ea.replaceChildren(C.columns(all.engagement.months, all.engagement[view], ea.clientWidth, view === "minutes" ? "phút / tuần" : "ngày / tháng"));
    }
    const a = state.advisory;
    const eng = $("#eng-chart"), rc = $("#risk-chart");
    if (!a || a.error || !eng || !eng.clientWidth) return;   // hidden: drawn when its tab shows
    const view = state.engView || "minutes";
    eng.replaceChildren(C.columns(a.tracking.engagement.months, a.tracking.engagement[view], eng.clientWidth,
      view === "minutes" ? "phút / tuần" : "ngày / tháng"));
    const tests = a.tracking.risk_tests;
    rc.replaceChildren(C.lines(tests.map(x => x.date), [
      {name: "Mức chấp nhận rủi ro", color: "var(--s2)", values: tests.map(x => x.tolerance)},
      {name: "Khả năng chịu rủi ro", color: "var(--s1)", values: tests.map(x => x.capacity)},
    ], rc.clientWidth));
  }

  // ── Advisory performance over every client ───────────────────────────
  async function loadAdvisoryAll() {
    if (!state.advisoryAll || state.advisoryAll.error) {
      try {
        const r = await fetch("/api/advisory/all");
        if (!r.ok) throw new Error(`/api/advisory/all: ${r.status}`);
        state.advisoryAll = await r.json();
      } catch (e) {
        state.advisoryAll = {error: e.message};
      }
    }
    renderPerfAll();
  }

  const STAFF_BAR = `<div class="staffbar"><span class="lock">Nội bộ</span><span>Chỉ nhân viên Techcombank (RM, chuyên gia, quản lý) xem được trang này · khách hàng không thấy.</span></div>`;

  function renderPerfAll() {
    const box = $("#tab-perfall");
    const a = state.advisoryAll;
    const head = `${STAFF_BAR}<div class="tabhead"><h1>Advisory performance</h1><p>Hiệu quả tư vấn và AI trên tất cả khách hàng${a && a.clients ? ` · ${a.clients.length} khách hàng` : ""} · 12 tháng</p></div>`;
    if (!a) { box.innerHTML = `${head}<div class="card muted">Đang tải…</div>`; return; }
    if (a.error) { box.innerHTML = `${head}<div class="card error">Không tải được: ${esc(a.error)}</div>`; return; }
    const sm = a.summary, decided = sm.right + sm.wrong;
    const rate = (c) => c.right + c.wrong ? pct(c.right / (c.right + c.wrong), false, 0) : "—";
    box.innerHTML = `${head}
      <div class="tiles">
        ${tile("Khuyến nghị", sm.advice, `${sm.right} đúng · ${sm.wrong} sai · ${sm.open} đang theo dõi`)}
        ${tile("Tỷ lệ đúng", decided ? pct(sm.right / decided, false, 0) : "—", "trên các khuyến nghị đã thực hiện")}
        ${tile("Tiền mang lại", vnd(sm.gained, true), "từ các khuyến nghị đúng", "delta up")}
        ${tile("Sai, thiệt hại", vnd(sm.lost, true), `${sm.wrong} khuyến nghị sai`, "delta down")}
        ${tile("Hành động bỏ lỡ", sm.missed, `khách hàng không thực hiện · đã có thể thêm ${vnd(sm.missed_value)}`)}
        ${tile("Tin quan trọng bị miss", sm.missed_news, `lượt khách hàng · tác động ${vnd(sm.missed_news_value, true)}`)}
      </div>
      <div class="card mt"><h2>AI pipeline <span class="hint">điểm trung bình trên mọi khách hàng · xu hướng độ chính xác 12 tháng</span></h2>
        <div class="pipe">${a.agents.map((g, i) => `<div class="agent">
          <div class="ahead2"><span class="step">${i + 1}</span><div><b>${esc(g.name)}</b><div class="muted small">${esc(g.name_vi)}</div></div><span class="score">${g.score}</span></div>
          <div class="spark" data-sparkall="${i}"></div>
          <div class="stats small">${g.by_client.map(c => `<div class="stat"><span class="k">${esc(c.client)}</span><span class="v">${c.score}</span></div>`).join("")}</div>
        </div>`).join("")}</div></div>
      <div class="card mt"><h2>Theo từng khách hàng <span class="hint">bấm một dòng để mở chi tiết khách hàng đó</span></h2>
        <div class="tablewrap"><table><thead><tr><th>Khách hàng</th><th class="num">Khuyến nghị</th><th class="num">Đúng / sai</th><th class="num">Tỷ lệ đúng</th>
          <th class="num">Tiền mang lại</th><th class="num wide">Thiệt hại</th><th class="num wide">Bỏ lỡ</th><th class="num wide">Tin bị miss</th><th class="num wide">Mở cảnh báo</th></tr></thead><tbody>
          ${a.clients.map(c => `<tr class="rowlink" data-client="${esc(c.id)}" tabindex="0"><td><b>${esc(c.name)}</b></td><td class="num">${c.advice}</td><td class="num">${c.right} / ${c.wrong}</td>
            <td class="num">${rate(c)}</td><td class="num delta up">${vnd(c.gained, true)}</td><td class="num wide delta down">${c.lost ? vnd(c.lost, true) : "—"}</td>
            <td class="num wide">${c.missed} · ${vnd(c.missed_value)}</td><td class="num wide">${c.missed_news}</td><td class="num wide">${esc(c.alerts_opened)}</td></tr>`).join("")}
        </tbody></table></div></div>
      <div class="grid g2 mt">
        <div class="card"><h2>Nhật ký khuyến nghị <span class="hint">mới nhất · ${a.advice.length} khuyến nghị</span></h2>
          <div class="tablewrap"><table><thead><tr><th>Ngày</th><th>Khuyến nghị</th><th>Kết quả</th><th class="num">Giá trị</th></tr></thead><tbody>
          ${a.advice.slice(0, 12).map(x => `<tr><td class="nowrap">${esc(x.date)}</td><td>${esc(x.text)}<div class="muted small">${esc(x.client)} · ${esc(AGENT_NAME[x.agent] || x.agent)}</div></td>
            <td><span class="badge ${OUTCOME[x.outcome][0]}">${OUTCOME[x.outcome][1]}</span></td>
            <td class="num ${x.value > 0 && x.outcome === "right" ? "delta up" : x.value < 0 ? "delta down" : ""}">${x.value ? vnd(x.value, x.outcome !== "missed") : "—"}</td></tr>`).join("")}
          </tbody></table></div></div>
        <div class="card"><h2>Tin quan trọng bị bỏ lỡ <span class="hint">gộp theo tin · tổng tác động</span></h2>
          <ul class="missed">${a.missed_news.map(n => `<li><div class="ahead2"><b>${esc(n.title)}</b><span class="delta down" style="margin-left:auto">${vnd(n.impact, true)}</span></div>
            <div class="small"><span class="muted">Xảy ra:</span> ${esc(n.date)} · <span class="muted">Tín hiệu sớm:</span> ${esc(n.signal)}</div>
            <div class="small"><span class="muted">Khách hàng bị ảnh hưởng:</span> ${n.clients.map(esc).join(", ")}</div>
            <div class="small muted">Vì sao bỏ lỡ: ${esc(n.why)}</div></li>`).join("")}</ul></div>
      </div>
      <div class="card mt"><h2>Mức độ theo dõi tin của khách hàng <span class="hint">trung bình mọi khách hàng</span></h2>
        <div class="keys"><span class="seg" role="group" aria-label="Chỉ số">${[["minutes", "Phút đọc / tuần"], ["days", "Ngày đọc / tháng"]].map(([k, l]) => `<button type="button" data-engall="${k}" aria-pressed="${(state.engView || "minutes") === k}">${l}</button>`).join("")}</span></div>
        <div id="eng-all" class="mt"></div></div>
      <p class="note mt">${esc(a.note)}</p>`;
    a.agents.forEach((g, i) => $(`[data-sparkall="${i}"]`, box).append(C.sparkline(g.trend.map(v => Math.round(v * 100)), `${g.name}: độ chính xác trung bình 12 tháng`)));
    drawPerf();
    for (const b of box.querySelectorAll("[data-engall]")) b.onclick = () => { state.engView = b.dataset.engall; renderPerfAll(); };
    for (const row of box.querySelectorAll("[data-client]")) {
      const go = () => {
        state.client = row.dataset.client;
        $("#client").value = state.client;
        try { localStorage.setItem("mf.client", state.client); } catch (_) { /* */ }
        showTab("performance");
        load();
      };
      row.onclick = go;
      row.onkeydown = (ev) => { if (ev.key === "Enter") go(); };
    }
  }

  // ── Relationship specialist: the RM, the specialists around them, the approval queue ──
  async function loadQueue() {
    try { state.queue = (await api("/api/review")).items; } catch (_) { state.queue = []; }
    renderRM();
  }

  async function decideItem(id, decision) {
    const note = ($(`#note-${id}`) || {}).value || "";
    try {
      await api("/api/review/decide", {item_id: id, decision, note});
    } catch (e) { alert("Không lưu được: " + e.message); }
    await loadQueue();
    renderScenarios();
  }

  function person(p, center) {
    return `<div class="person${center ? " center" : ""}${p.lead ? " lead" : ""}" id="sp-${esc(p.id || "rm")}">
      <div class="ahead2"><span class="avatar" aria-hidden="true">${esc(p.name.split(" ").pop()[0])}</span>
        <div><b>${esc(p.name)}</b><div class="small">${esc(p.role)}</div><div class="muted small">${esc(p.role_vi)}</div></div>
        ${p.lead ? `<span class="chip" style="margin-left:auto">Phụ trách chính cho bạn</span>` : ""}</div>
      ${p.covers ? `<ul class="small covers">${p.covers.map(c => `<li>${esc(c)}</li>`).join("")}</ul>` : ""}
      <div class="contact small">
        <a href="tel:${esc(p.phone.replace(/\s/g, ""))}">☎ ${esc(p.phone)}</a>
        <a href="mailto:${esc(p.email)}">✉ ${esc(p.email)}</a>
        <span class="muted">⌂ ${esc(p.office)}</span>
        ${p.hours ? `<span class="muted">◷ ${esc(p.hours)}</span>` : ""}
      </div></div>`;
  }

  function renderRM() {
    const box = $("#tab-rm");
    const head = `<div class="tabhead"><h1>Relationship specialist</h1><p>Chuyên viên quan hệ khách hàng phụ trách bạn</p></div>`;
    const a = state.advisory;
    const pending = state.queue.filter(q => q.status === "pending");
    const done = state.queue.filter(q => q.status !== "pending");
    const row = (q) => `<div class="card"><div class="ahead2"><b>${esc(q.client_name)}</b><span class="muted small">${new Date(q.created * 1000).toLocaleString("vi-VN")}</span>
        ${q.status !== "pending" ? `<span class="badge ${q.status === "approved" ? "verified" : "declared"}">${q.status === "approved" ? "Đã duyệt" : "Từ chối"}</span>` : ""}</div>
      <h3 style="margin:8px 0">${esc(q.title)}</h3>
      <ul>${((q.data.option || {}).actions || []).map(x => `<li>${esc(x)}</li>`).join("")}</ul>
      <div class="stats small">${(q.data.summary || []).slice(0, 4).map(l => `<div class="stat"><span class="k">${esc(l.label)}</span><span class="v">${esc(l.value)}</span></div>`).join("")}</div>
      ${q.status === "pending" ? `<div class="chatform mt"><input id="note-${q.id}" placeholder="Ghi chú cho khách hàng (không bắt buộc)" aria-label="Ghi chú">
        <button type="button" class="btn" data-ok="${q.id}">Duyệt</button><button type="button" class="btn ghostbtn" data-no="${q.id}">Từ chối</button></div>`
        : (q.note ? `<p class="small"><b>Ghi chú:</b> ${esc(q.note)}</p>` : "")}</div>`;
    let team = `<div class="card muted">Đang tải đội chuyên gia…</div>`;
    if (a && a.client === state.client && a.error) team = `<div class="card error">Không tải được: ${esc(a.error)}</div>`;
    else if (a && a.client === state.client) {
      const t = a.team;
      team = `<div class="grid g3 people">${person({...t.rm, id: "rm"}, true)}</div>
        <p class="note mt">${esc(a.note)}</p>`;
    }
    box.innerHTML = `${head}${team}
      <div class="card mt"><h2>Approval queue <span class="hint">Hàng chờ chuyên gia duyệt · ${pending.length} đang chờ</span></h2>
        <p class="muted small" style="margin-top:-6px">Mọi khuyến nghị từ Wealth Planning Advisor đều là mô phỏng cho đến khi chuyên gia duyệt.</p></div>
      <div class="grid g2 mt">${pending.map(row).join("") || `<div class="card muted">Không có đề xuất nào đang chờ.</div>`}</div>
      ${done.length ? `<h2 class="mt subhead">Đã xử lý</h2><div class="grid g2">${done.map(row).join("")}</div>` : ""}`;
    for (const b of box.querySelectorAll("[data-ok]")) b.onclick = () => decideItem(b.dataset.ok, "approved");
    for (const b of box.querySelectorAll("[data-no]")) b.onclick = () => decideItem(b.dataset.no, "rejected");
  }

  // ── the risk test ───────────────────────────────────────────────────
  const LEVEL_NAMES = ["Bảo toàn", "Thận trọng", "Cân bằng", "Tăng trưởng", "Mạo hiểm"];
  function riskState() {
    return state.risk[state.client] = state.risk[state.client] || {answers: {}, order: [], reply: null};
  }

  async function riskStep() {
    const r = riskState();
    const box = $("#tab-risk");
    box.classList.add("loading");
    try {
      r.reply = (await api("/api/risk", {client_id: state.client, answers: r.answers})).reply;
    } catch (e) {
      r.reply = {error: e.message};
    }
    box.classList.remove("loading");
    renderRisk();
    if (r.reply && r.reply.result) {
      load();   // the dashboard measures risk against it now
      if (state.advisory) state.advisory.stale = true;   // and it is the last point of the risk history
      loadAdvisory();
    }
  }

  function scoreBar(label, score, level) {
    return `<div class="stat"><span class="k">${label}</span><span class="v">${LEVEL_NAMES[level - 1]} · ${Math.round(score)}/100</span></div>
      <div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${score}" aria-label="${label}">
        <span class="fill" style="width:${score}%;background:var(--s1)"></span>
        ${[20, 40, 60, 80].map(x => `<span class="mark" style="left:calc(${x}% - 1px);height:10px;top:0;background:var(--surface)"></span>`).join("")}</div>`;
  }

  function renderRisk() {
    const box = $("#tab-risk");
    const r = riskState();
    const me = state.clients.find(c => c.id === state.client) || {};
    if (!r.reply) {
      box.innerHTML = `<div class="card"><h2>Bài test khẩu vị rủi ro</h2>
        <p>8–12 câu hỏi tình huống; câu sau phụ thuộc vào câu trả lời trước. Kết quả tách hai điều:
        <b>mức chấp nhận rủi ro</b> (anh/chị muốn chịu bao nhiêu) và <b>khả năng chịu rủi ro</b> (dữ liệu tài chính cho thấy anh/chị có thể chịu bao nhiêu).</p>
        <button type="button" class="btn" id="risk-start">Bắt đầu cho ${esc(me.name || "")}</button></div>`;
      $("#risk-start").onclick = riskStep;
      return;
    }
    if (r.reply.error) {
      box.innerHTML = `<div class="card error">Không tải được bài test: ${esc(r.reply.error)}</div>`;
      return;
    }
    if (r.reply.question) {
      const q = r.reply.question;
      box.innerHTML = `<div class="card qcard"><div class="muted small">Câu ${q.number} / ${q.of}</div>
        <h3 class="qtext">${esc(q.text)}</h3>
        <div class="opts">${q.options.map(o => `<button type="button" class="opt" data-opt="${esc(o.id)}">${esc(o.text)}</button>`).join("")}</div>
        <div class="actions mt">${r.order.length ? `<button type="button" class="btn ghostbtn" id="risk-back">← Câu trước</button>` : ""}</div></div>`;
      for (const b of box.querySelectorAll("[data-opt]")) {
        b.onclick = () => { r.answers[q.id] = b.dataset.opt; r.order.push(q.id); riskStep(); };
      }
      const back = $("#risk-back");
      if (back) back.onclick = () => { delete r.answers[r.order.pop()]; riskStep(); };
      return;
    }
    const res = r.reply.result;
    box.innerHTML = `
      <div class="card hero">
        <div><div class="label">Hồ sơ rủi ro</div>
          <div class="figure" style="font-size:40px">${esc(res.profile.name)}</div>
          <div>Ngưỡng sụt giảm tối đa <b>${pct(res.drawdown_limit, false, 0)}</b> · ${res.questions} câu · ngày ${esc(res.taken)}</div>
          <div class="who"><span class="chip">Chân dung: <b>${esc(res.persona)}</b></span></div>
          <p class="muted small">${esc(res.persona_text)}</p></div>
        <div>${scoreBar("Mức chấp nhận rủi ro (bạn muốn)", res.tolerance, res.tolerance_level)}
          ${scoreBar("Khả năng chịu rủi ro (dữ liệu cho thấy)", res.capacity, res.capacity_level)}
          <div class="muted small">Hồ sơ lấy mức thấp hơn của hai chỉ số.</div></div>
      </div>
      ${res.warnings.length ? `<div class="card mt"><h2>Cần lưu ý</h2><ul class="warn-list">${res.warnings.map(w => `<li><span class="ic" aria-hidden="true">⚠</span><span>${esc(w)}</span></li>`).join("")}</ul></div>` : ""}
      <div class="grid g2 mt">
        <div class="card"><h2>Vì sao khả năng chịu rủi ro ở mức này</h2><ul class="legend">${res.capacity_reasons.map(w => `<li><span class="sw" style="background:var(--axis)"></span><span>${esc(w)}</span><span></span><span></span></li>`).join("")}</ul></div>
        <div class="card"><h2>Phân bổ gợi ý cho hồ sơ ${esc(res.profile.name)}</h2>
          <table><tbody>${Object.entries(res.profile.mix).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${esc(v)}</td></tr>`).join("")}</tbody></table>
          <p class="muted small">Gợi ý mang tính mô phỏng; khuyến nghị cụ thể phải qua RM duyệt.</p></div>
      </div>
      <div class="card mt"><h2>Tự cập nhật</h2><p>Hệ thống sẽ hỏi lại vào <b>${esc(res.retest.date)}</b>, hoặc sớm hơn:</p>
        <ul>${res.retest.when.map(w => `<li>${esc(w)}</li>`).join("")}</ul>
        <button type="button" class="btn ghostbtn" id="risk-redo">Làm lại bài test</button></div>`;
    $("#risk-redo").onclick = () => { state.risk[state.client] = null; renderRisk(); };
  }

  // ── loading ─────────────────────────────────────────────────────────
  async function load() {
    const seq = ++state.seq;
    const main = $("#main");
    main.classList.add("loading");
    try {
      const d = (await api("/api/dashboard", {client_id: state.client, scope: state.scope, months: state.months})).dashboard;
      if (seq !== state.seq) return;
      state.board = d;
      renderOverview(d);
      renderSources(d);
      if (state.alerts && state.alerts.client_id === state.client && state.alerts.scope === state.scope) alertsCard(state.alerts);
      loadAlerts(seq);
      loadGoals(seq);
      loadAdvisory();
      if (state.tab === "alerts") renderAlerts();
      if (!$("#tab-risk").dataset.client || $("#tab-risk").dataset.client !== state.client) {
        $("#tab-risk").dataset.client = state.client;
        renderRisk();
      }
    } catch (e) {
      $("#tab-overview").innerHTML = `<div class="card error">Không tải được dữ liệu: ${esc(e.message)}</div>`;
    } finally {
      if (seq === state.seq) main.classList.remove("loading");
    }
  }

  function showTab(tab) {
    state.tab = tab;
    // the pillar holding the tab shows, with only its own tabs under it
    const pillar = (document.querySelector(`.tabs [data-tab="${tab}"]`) || {dataset: {}}).dataset.pillar;
    for (const b of document.querySelectorAll(".pillars button")) {
      if (b.dataset.pillar === pillar) b.setAttribute("aria-current", "true");
      else b.removeAttribute("aria-current");
    }
    for (const b of document.querySelectorAll(".tabs button")) {
      b.hidden = b.dataset.pillar !== pillar;
      if (b.dataset.tab === tab) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    }
    // a pillar with one page needs no row of tabs under it
    $(".tabs").hidden = document.querySelectorAll(`.tabs [data-pillar="${pillar}"]`).length < 2;
    state.lastTab[pillar] = tab;
    for (const s of document.querySelectorAll(".tab")) s.hidden = s.id !== `tab-${tab}`;
    // a chart drawn while its tab was hidden measured no width: draw it again now it shows
    if (tab === "overview" || tab === "scenarios") drawCash();
    if (tab === "performance") drawPerf();
    if (tab === "perfall") loadAdvisoryAll();
    if (tab === "alerts") renderAlerts();
    try { localStorage.setItem("mf.tab", tab); } catch (_) { /* private mode */ }
  }

  function setViewer(v) {
    state.viewer = v === "staff" ? "staff" : "client";
    for (const b of document.querySelectorAll("[data-viewer]")) b.setAttribute("aria-pressed", String(b.dataset.viewer === state.viewer));
    for (const el of document.querySelectorAll(".pillars [data-staff]")) el.hidden = state.viewer !== "staff";
    try { localStorage.setItem("mf.viewer", state.viewer); } catch (_) { /* private mode */ }
    // a client never stays on an internal page
    if (state.viewer !== "staff" && document.querySelector(`.tabs [data-tab="${state.tab}"][data-staff]`)) showTab("overview");
  }

  function theme() {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("mf.theme", root.dataset.theme); } catch (_) { /* private mode */ }
  }

  async function start() {
    try { const t = localStorage.getItem("mf.theme"); if (t) document.documentElement.dataset.theme = t; } catch (_) { /* */ }
    const {clients} = await api("/api/clients");
    try { state.catalog = (await api("/api/scenarios")).scenarios; } catch (_) { state.catalog = []; }
    loadQueue();
    state.clients = clients;
    const sel = $("#client");
    sel.innerHTML = clients.map(c => `<option value="${esc(c.id)}">${esc(c.name)} · ${esc(c.persona_hint)}</option>`).join("");
    let saved = null;
    try { saved = localStorage.getItem("mf.client"); } catch (_) { /* */ }
    state.client = clients.some(c => c.id === saved) ? saved : clients[0].id;
    sel.value = state.client;
    sel.onchange = () => { state.client = sel.value; try { localStorage.setItem("mf.client", sel.value); } catch (_) { /* */ } load(); };
    for (const b of document.querySelectorAll("[data-scope]")) {
      b.onclick = () => {
        state.scope = b.dataset.scope;
        for (const o of document.querySelectorAll("[data-scope]")) o.setAttribute("aria-pressed", String(o === b));
        load();
      };
    }
    for (const b of document.querySelectorAll(".tabs button")) b.onclick = () => showTab(b.dataset.tab);
    for (const b of document.querySelectorAll(".pillars button")) {
      b.onclick = () => showTab(state.lastTab[b.dataset.pillar] || document.querySelector(`.tabs [data-pillar="${b.dataset.pillar}"]`).dataset.tab);
    }
    $("#theme").onclick = theme;
    for (const b of document.querySelectorAll("[data-viewer]")) b.onclick = () => setViewer(b.dataset.viewer);
    loadViews();
    $("#reset").onclick = async () => {
      if (!confirm("Xóa mọi dữ liệu đã tải lên, đã khai, bài test, mục tiêu và hàng chờ duyệt để làm lại demo?")) return;
      await api("/api/reset", {});
      try { for (const c of state.clients) localStorage.removeItem(`mf.goals.${c.id}`); } catch (_) { /* */ }
      Object.assign(state, {reads: {}, chat: {}, risk: {}, plan: {}, goals: null, alerts: null, queue: [], advisory: null});
      $("#tab-risk").dataset.client = "";
      await loadQueue();
      load();
    };
    let tab = "overview";
    try { tab = localStorage.getItem("mf.tab") || tab; } catch (_) { /* */ }
    let viewer = "client";
    try { viewer = localStorage.getItem("mf.viewer") || viewer; } catch (_) { /* */ }
    showTab(document.querySelector(`.tabs [data-tab="${tab}"]`) ? tab : "overview");
    setViewer(viewer);
    load();
  }

  start();
})();
