const state = {
  userId: localStorage.getItem("shopping_user_id") || `user_${crypto.randomUUID().slice(0, 8)}`,
  sessionId: crypto.randomUUID(),
  busy: false,
};
localStorage.setItem("shopping_user_id", state.userId);

const $ = (selector) => document.querySelector(selector);
const esc = (value = "") => String(value).replace(/[&<>'"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
const money = (value) => `¥${Number(value).toLocaleString("zh-CN", {maximumFractionDigits: 0})}`;
const dateLabel = (value) => new Date(value).toLocaleDateString("zh-CN", {month:"short", day:"numeric"});

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  setTimeout(() => node.classList.remove("show"), 2200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {headers: {"Content-Type": "application/json"}, ...options});
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "服务暂时不可用");
  return body;
}

async function checkHealth() {
  try {
    const data = await api("/api/health");
    $("#runtimeBadge").classList.add("ready");
    $("#runtimeBadge span:last-child").textContent = data.llm_enabled ? `大模型 · ${data.model}` : "演示算法 · 可离线";
  } catch {
    $("#runtimeBadge span:last-child").textContent = "后端未连接";
  }
}

function addMessage(role, text, loading = false) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.innerHTML = `<div class="avatar">${role === "user" ? "你" : "AI"}</div><div class="bubble ${loading ? "thinking" : ""}">${loading ? "正在解析需求、检查评论并计算推荐 <b>•••</b>" : esc(text)}</div>`;
  $("#chatStream").append(node);
  node.scrollIntoView({behavior: "smooth", block: "center"});
  return node;
}

function scoreMini(label, value) {
  return `<div class="mini-score">${label}<b>${Number(value).toFixed(0)}</b><div class="mini-line"><i style="width:${Math.min(100, value)}%"></i></div></div>`;
}

function productCard(item) {
  const review = item.review_analysis;
  const riskClass = review.risk_level === "低风险" ? "risk-low" : review.risk_level === "中风险" ? "risk-medium" : "risk-high";
  return `<article class="product-card ${item.rank === 1 ? "primary" : ""}">
    <div class="rank">#${item.rank}</div><span class="role">${esc(item.role)}</span>
    <h4>${esc(item.title)}</h4><div class="price">${money(item.price)}</div>
    <div class="meta">★ ${item.rating} · ${Number(item.review_count).toLocaleString()} 条平台评论</div>
    <div class="overall-row"><span>综合决策分</span><strong>${item.overall_score}</strong></div>
    <div class="score-bar"><i style="width:${item.overall_score}%"></i></div>
    <div class="mini-scores">${scoreMini("评论可信", item.score_detail.credibility)}${scoreMini("需求匹配", item.score_detail.match)}${scoreMini("价格竞争", item.score_detail.price)}${scoreMini("平台评分", item.score_detail.rating)}</div>
    <div class="tags">${item.features.slice(0, 4).map(x => `<span>${esc(x)}</span>`).join("")}</div>
    <div class="review-row"><div>可信度<b>${review.credibility_score}%</b></div><div>风险等级<b class="${riskClass}">${review.risk_level}</b></div><div>验证购买<b>${review.verified_ratio}%</b></div><div>重复评论<b>${review.duplicate_ratio}%</b></div></div>
    <ul class="reason-list">${item.reasons.map(reason => `<li>${esc(reason)}</li>`).join("")}</ul>
    <button class="cart-btn" data-product="${esc(item.id)}" data-title="${esc(item.title)}">${item.rank === 1 ? "授权加入演示购物车" : "选择此备选"}</button>
  </article>`;
}

function renderResult(data) {
  if (data.status === "needs_clarification") {
    const panel = document.createElement("section");
    panel.className = "result-panel";
    panel.innerHTML = `<div class="result-head"><div><span class="kicker">需要补充信息</span><h2>先确认商品品类</h2></div><span class="mode-badge">${data.mode === "llm" ? "LLM" : "RULES"}</span></div>
      <div class="quick-prompts">${data.questions.map(q => `<button data-query="${esc(q)}">${esc(q)}</button>`).join("")}</div>`;
    $("#chatStream").append(panel);
    bindQuickPrompts(panel);
    return;
  }
  const d = data.demand;
  const panel = document.createElement("section");
  panel.className = "result-panel";
  panel.innerHTML = `
    <div class="result-head"><div><span class="kicker">可解释决策报告</span><h2>${esc(d.category_label)}选购方案</h2></div><span class="mode-badge">${data.mode === "llm" ? "LLM 已参与解析" : "离线演示模式"}</span></div>
    <div class="trace">${data.trace.map(step => `<div class="trace-step"><strong>${esc(step.step)}</strong><span>${esc(step.detail)}</span></div>`).join("")}</div>
    <div class="demand-strip"><div><small>品类</small><strong>${esc(d.category_label)}</strong></div><div><small>预算</small><strong>${d.budget_max ? `${money(d.budget_min)}–${money(d.budget_max)}` : "未设上限"}</strong></div><div><small>核心需求</small><strong>${esc(d.features.join(" / ") || "综合均衡")}</strong></div><div><small>解析置信度</small><strong>${Math.round(d.confidence * 100)}%</strong></div></div>
    <div class="zone-title"><h3>推荐方案</h3><span>算法必须输出 1 个主推 + 2 个备选</span></div>
    <div class="product-grid">${data.recommendations.map(productCard).join("")}</div>
    <div class="zone-title"><h3>横向对比</h3><span>完整评分明细可审计</span></div>
    <div class="table-wrap"><table><thead><tr><th>商品</th><th>价格</th><th>平台评分</th><th>评论可信度</th><th>需求匹配</th><th>综合分</th></tr></thead><tbody>
      ${data.comparison.map(item => `<tr><td>${esc(item.title)}</td><td>${money(item.price)}</td><td>${item.rating}</td><td>${item.credibility}</td><td>${item.match}</td><td><strong>${item.overall}</strong></td></tr>`).join("")}
    </tbody></table></div>
    <div class="advice"><div class="advice-mark">✓</div><div><h3>${esc(data.final_advice.title)}</h3><p>${esc(data.final_advice.summary)}</p></div><small>${esc(data.final_advice.disclaimer)}</small></div>`;
  $("#chatStream").append(panel);
  panel.querySelectorAll(".cart-btn").forEach(button => button.addEventListener("click", () => confirmCart(button.dataset.product, button.dataset.title)));
  panel.scrollIntoView({behavior: "smooth", block: "start"});
}

async function send(text) {
  text = text.trim();
  if (!text || state.busy) return;
  state.busy = true;
  $("#hero").classList.add("hidden");
  $("#composer").classList.remove("hidden");
  addMessage("user", text);
  const thinking = addMessage("assistant", "", true);
  try {
    const data = await api("/api/chat", {method: "POST", body: JSON.stringify({user_input: text, user_id: state.userId, session_id: state.sessionId})});
    thinking.remove();
    addMessage("assistant", data.message);
    renderResult(data);
    await loadSessions();
  } catch (error) {
    thinking.remove();
    addMessage("assistant", `出现问题：${error.message}`);
  } finally {
    state.busy = false;
    $("#heroInput").value = "";
    $("#chatInput").value = "";
  }
}

async function confirmCart(productId, title) {
  if (!window.confirm(`确认将“${title}”加入演示购物车吗？此操作不会产生真实订单。`)) return;
  try {
    const result = await api("/api/cart/confirm", {method: "POST", body: JSON.stringify({user_id: state.userId, session_id: state.sessionId, product_id: productId, authorized: true})});
    toast(result.message);
  } catch (error) { toast(error.message); }
}

function resetChat() {
  state.sessionId = crypto.randomUUID();
  $("#chatStream").innerHTML = "";
  $("#hero").classList.remove("hidden");
  $("#composer").classList.add("hidden");
  $("#sidebar").classList.remove("open");
  window.scrollTo({top: 0, behavior: "smooth"});
}

async function loadSessions() {
  try {
    const sessions = await api(`/api/sessions/${state.userId}`);
    $("#sessionList").innerHTML = sessions.length ? sessions.map(session => `<button class="session-item ${session.session_id === state.sessionId ? "active" : ""}" data-session="${esc(session.session_id)}"><span>${esc(session.title)}</span><small>${dateLabel(session.updated_at)}</small><span class="delete-session" data-delete="${esc(session.session_id)}">×</span></button>`).join("") : '<p class="muted">还没有历史会话</p>';
    $("#sessionList").querySelectorAll(".session-item").forEach(item => item.addEventListener("click", event => {
      if (event.target.dataset.delete) return;
      openSession(item.dataset.session);
    }));
    $("#sessionList").querySelectorAll("[data-delete]").forEach(button => button.addEventListener("click", event => deleteSession(event, button.dataset.delete)));
  } catch { /* health indicator already communicates backend state */ }
}

async function openSession(sessionId) {
  const data = await api(`/api/sessions/${state.userId}/${sessionId}`);
  state.sessionId = sessionId;
  $("#hero").classList.add("hidden");
  $("#composer").classList.remove("hidden");
  $("#chatStream").innerHTML = "";
  data.messages.forEach(message => {
    addMessage(message.role, message.content);
    if (message.role === "assistant" && message.payload?.status === "success") renderResult(message.payload);
  });
  $("#sidebar").classList.remove("open");
  loadSessions();
}

async function deleteSession(event, sessionId) {
  event.stopPropagation();
  if (!window.confirm("删除这段会话记录？")) return;
  await api(`/api/sessions/${state.userId}/${sessionId}`, {method: "DELETE"});
  if (sessionId === state.sessionId) resetChat();
  await loadSessions();
  toast("会话已删除");
}

function openSettings(open) {
  $("#settingsDrawer").classList.toggle("open", open);
  $("#settingsDrawer").setAttribute("aria-hidden", String(!open));
  $("#drawerBackdrop").classList.toggle("hidden", !open);
}

async function loadPreferences() {
  const data = await api(`/api/preferences/${state.userId}`);
  $("#brandPrefs").value = data.brands.join(", ");
  $("#avoidPrefs").value = data.avoid_terms.join(", ");
  $("#priceSensitivity").value = data.price_sensitivity;
  $("#priceOutput").textContent = `${data.price_sensitivity}%`;
  const radio = document.querySelector(`input[name="style"][value="${data.decision_style}"]`);
  if (radio) radio.checked = true;
}

async function savePreferences(event) {
  event.preventDefault();
  const split = value => value.split(/[,，、]/).map(x => x.trim()).filter(Boolean);
  await api(`/api/preferences/${state.userId}`, {method: "PUT", body: JSON.stringify({
    brands: split($("#brandPrefs").value), avoid_terms: split($("#avoidPrefs").value),
    price_sensitivity: Number($("#priceSensitivity").value), decision_style: document.querySelector('input[name="style"]:checked').value,
  })});
  openSettings(false);
  toast("偏好已保存，后续推荐会自动继承");
}

function bindQuickPrompts(root = document) {
  root.querySelectorAll("[data-query]").forEach(button => button.addEventListener("click", () => send(button.dataset.query)));
}

$("#heroSend").addEventListener("click", () => send($("#heroInput").value));
$("#chatSend").addEventListener("click", () => send($("#chatInput").value));
[$("#heroInput"), $("#chatInput")].forEach(input => input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(input.value); }
}));
$("#newChatBtn").addEventListener("click", resetChat);
$("#settingsBtn").addEventListener("click", async () => { openSettings(true); await loadPreferences(); });
$("#closeSettings").addEventListener("click", () => openSettings(false));
$("#drawerBackdrop").addEventListener("click", () => openSettings(false));
$("#preferenceForm").addEventListener("submit", savePreferences);
$("#priceSensitivity").addEventListener("input", event => $("#priceOutput").textContent = `${event.target.value}%`);
$("#mobileMenu").addEventListener("click", () => $("#sidebar").classList.toggle("open"));

bindQuickPrompts();
checkHealth();
loadSessions();
