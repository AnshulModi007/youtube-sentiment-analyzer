const BACKEND_URL = "http://127.0.0.1:8000";

// ── DOM refs ───────────────────────────────────────────────────
const analyzeBtn = document.getElementById("analyze-btn");
const videoBadge = document.getElementById("video-badge");
const videoIdDisp = document.getElementById("video-id-display");
const videoStatusTx = document.getElementById("video-status-text");
const commentCount = document.getElementById("comment-count");
const countRow = document.getElementById("comment-count-row");
const resultsSection = document.getElementById("results-section");
const overallCard = document.getElementById("overall-card");
const overallSent = document.getElementById("overall-sentiment");
const totalCount = document.getElementById("total-count");
const barPos = document.getElementById("bar-positive");
const barNeu = document.getElementById("bar-neutral");
const barNeg = document.getElementById("bar-negative");
const pctPos = document.getElementById("pct-positive");
const pctNeu = document.getElementById("pct-neutral");
const pctNeg = document.getElementById("pct-negative");
const commentList = document.getElementById("comment-list");
const errorToast = document.getElementById("error-toast");
const errorMsg = document.getElementById("error-msg");
const toastClose = document.getElementById("toast-close");
const donutCanvas = document.getElementById("donut-chart");

let currentVideoId = null;

// ── Init ───────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Detect current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url) {
    const match = tab.url.match(/(?:v=|\/shorts\/|youtu\.be\/)([A-Za-z0-9_-]{11})/);
    if (match) {
      currentVideoId = match[1];
      videoStatusTx.textContent = "Video detected";
      videoBadge.querySelector(".badge-dot").classList.add("active");
      videoIdDisp.textContent = `Video ID: ${currentVideoId}`;
      analyzeBtn.disabled = false;
      countRow.style.display = "flex";
    } else {
      videoStatusTx.textContent = "Not a YouTube video page";
    }
  } else {
    videoStatusTx.textContent = "Cannot read tab URL";
  }
});

// ── Analyze ────────────────────────────────────────────────────
analyzeBtn.addEventListener("click", async () => {
  if (!currentVideoId) { showError("No YouTube video detected."); return; }

  setLoading(true);

  try {
    const maxComments = parseInt(commentCount.value);

    // Call backend — it fetches comments & analyzes them
    const res = await fetch(`${BACKEND_URL}/analyze_video`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_id: currentVideoId, max_comments: maxComments }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errData.detail || `Server error (${res.status})`);
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    showError(err.message || "Something went wrong.");
  } finally {
    setLoading(false);
  }
});

// ── Render results ─────────────────────────────────────────────
function renderResults(data) {
  resultsSection.style.display = "block";

  // Overall card
  const sent = data.overall_sentiment;
  overallSent.textContent = sent;
  overallCard.className = "overall-card";
  overallSent.className = "overall-value";
  if (sent === "Positive") { overallCard.classList.add("positive-card"); overallSent.classList.add("positive-text"); }
  else if (sent === "Negative") { overallCard.classList.add("negative-card"); overallSent.classList.add("negative-text"); }
  else { overallCard.classList.add("neutral-card"); overallSent.classList.add("neutral-text"); }
  totalCount.textContent = `${data.total} comments analyzed`;

  // Bars
  barPos.style.width = `${data.positive_pct}%`;
  barNeu.style.width = `${data.neutral_pct}%`;
  barNeg.style.width = `${data.negative_pct}%`;
  pctPos.textContent = `${data.positive_pct}%`;
  pctNeu.textContent = `${data.neutral_pct}%`;
  pctNeg.textContent = `${data.negative_pct}%`;

  // Donut chart
  drawDonut(data.positive_pct, data.neutral_pct, data.negative_pct);

  // Comment cards
  commentList.innerHTML = "";
  data.results.forEach((r, i) => {
    const card = document.createElement("div");
    card.className = "comment-card";
    card.style.animationDelay = `${i * 0.04}s`;

    const badgeClass = r.sentiment === "Positive" ? "badge-positive"
      : r.sentiment === "Negative" ? "badge-negative" : "badge-neutral";

    card.innerHTML = `
      <div class="comment-top">
        <span class="comment-index">#${i + 1}</span>
        <span class="sentiment-badge ${badgeClass}">${r.sentiment}</span>
      </div>
      <p class="comment-text">${escapeHtml(r.text)}</p>
    `;
    commentList.appendChild(card);
  });

  // Smooth scroll to results
  resultsSection.scrollIntoView({ behavior: "smooth" });
}

// ── Donut Chart ────────────────────────────────────────────────
function drawDonut(posPct, neuPct, negPct) {
  const ctx = donutCanvas.getContext("2d");
  const W = donutCanvas.width;
  const H = donutCanvas.height;
  const cx = W / 2, cy = H / 2;
  const R = 80, r = 50;

  ctx.clearRect(0, 0, W, H);

  const total = posPct + neuPct + negPct;
  if (total === 0) return;

  const slices = [
    { pct: posPct, color: "#00e676" },
    { pct: neuPct, color: "#ffc107" },
    { pct: negPct, color: "#ff5252" },
  ];

  let startAngle = -Math.PI / 2;
  slices.forEach((s) => {
    if (s.pct <= 0) return;
    const sweep = (s.pct / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.arc(cx, cy, R, startAngle, startAngle + sweep);
    ctx.arc(cx, cy, r, startAngle + sweep, startAngle, true);
    ctx.closePath();
    ctx.fillStyle = s.color;
    ctx.fill();
    startAngle += sweep;
  });

  // Center emoji
  ctx.fillStyle = "#e8e8f0";
  ctx.font = "bold 22px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const dominant = posPct >= neuPct && posPct >= negPct ? "😊"
    : negPct >= posPct && negPct >= neuPct ? "😠" : "😐";
  ctx.fillText(dominant, cx, cy);
}

// ── Helpers ────────────────────────────────────────────────────
function setLoading(on) {
  analyzeBtn.disabled = on;
  if (on) analyzeBtn.classList.add("loading");
  else analyzeBtn.classList.remove("loading");
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorToast.style.display = "flex";
  setTimeout(() => { errorToast.style.display = "none"; }, 6000);
}
toastClose.addEventListener("click", () => { errorToast.style.display = "none"; });

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}
