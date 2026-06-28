// Talent Match — recruiter page logic
// No frameworks, no build step. Talks directly to the FastAPI backend.

const API_BASE = "";

const jdForm = document.getElementById("jd-form");
const jdStatus = document.getElementById("jd-status");
const jdSubmitBtn = document.getElementById("jd-submit-btn");

const resultsSection = document.getElementById("results-section");
const resultsTitle = document.getElementById("results-title");
const resultsSub = document.getElementById("results-sub");
const ledger = document.getElementById("ledger");
const emptySection = document.getElementById("empty-section");

let currentJobId = null;

function showBanner(el, message, kind) {
  el.textContent = message;
  el.className = `status-banner show ${kind}`;
}

function showLoadingBanner(el, message) {
  el.innerHTML = `${message} <span class="loader-dot"></span><span class="loader-dot"></span><span class="loader-dot"></span>`;
  el.className = "status-banner show loading";
}

jdForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const title = document.getElementById("job-title").value.trim();
  const recruiterName = document.getElementById("recruiter-name").value.trim();
  const description = document.getElementById("job-description").value.trim();

  if (!title || !description) return;

  jdSubmitBtn.disabled = true;
  resultsSection.style.display = "none";
  emptySection.style.display = "none";
  showLoadingBanner(jdStatus, "Reading the job description and scoring every candidate in the pool");

  try {
    const res = await fetch(`${API_BASE}/recruiter/job`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        description,
        recruiter_name: recruiterName || null,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Matching failed.");
    }

    const data = await res.json();
    currentJobId = data.job_id;

    jdStatus.className = "status-banner";

    if (data.top_candidates.length === 0) {
      emptySection.style.display = "block";
      emptySection.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      renderResults(data);
    }
  } catch (err) {
    showBanner(jdStatus, err.message, "error");
  } finally {
    jdSubmitBtn.disabled = false;
  }
});

function renderResults(data) {
  resultsTitle.textContent = `Top ${data.top_candidates.length} for "${data.job_title}"`;
  resultsSub.textContent = `Scored against ${data.total_candidates_considered} candidate${
    data.total_candidates_considered === 1 ? "" : "s"
  } in the pool. Click a row to see the full breakdown.`;

  ledger.innerHTML = "";

  data.top_candidates.forEach((c) => {
    const row = document.createElement("div");
    row.className = "ledger-row";
    row.tabIndex = 0;

    const matchedTags = (c.matched_skills || [])
      .map((s) => `<span class="tag sage">${escapeHtml(s)}</span>`)
      .join("");
    const missingTags = (c.missing_skills || [])
      .map((s) => `<span class="tag coral">${escapeHtml(s)}</span>`)
      .join("");

    row.innerHTML = `
      <div class="rank-mark ${c.rank === 1 ? "rank-1" : ""}">
        ${c.rank}<span class="ordinal">${ordinalSuffix(c.rank)}</span>
      </div>
      <div class="ledger-main">
        <h3>${escapeHtml(c.name || "Unknown candidate")}</h3>
        <p class="email">${escapeHtml(c.email || "")}</p>
        <p class="reasoning">${escapeHtml(c.reasoning || "")}</p>
        <div class="ledger-detail">
          ${
            matchedTags
              ? `<div class="detail-section"><div class="detail-heading">Matched skills</div><div class="tag-row">${matchedTags}</div></div>`
              : ""
          }
          ${
            missingTags
              ? `<div class="detail-section"><div class="detail-heading">Missing skills</div><div class="tag-row">${missingTags}</div></div>`
              : ""
          }
        </div>
      </div>
      <div class="score-block">
        <div class="score-num">${Math.round(c.match_score)}<small>/100</small></div>
        <div class="score-label">Match score</div>
      </div>
    `;

    row.addEventListener("click", () => row.classList.toggle("expanded"));
    row.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        row.classList.toggle("expanded");
      }
    });

    ledger.appendChild(row);
  });

  resultsSection.style.display = "block";
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function ordinalSuffix(n) {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = String(str ?? "");
  return div.innerHTML;
}
