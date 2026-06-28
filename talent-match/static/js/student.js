// Talent Match — student page logic
// No frameworks, no build step. Talks directly to the FastAPI backend.

const API_BASE = ""; // same origin — FastAPI serves both the API and this page

let currentStudentId = null;
let selectedFile = null;

const registerForm = document.getElementById("register-form");
const registerStatus = document.getElementById("register-status");
const registerBtn = document.getElementById("register-btn");

const uploadCard = document.getElementById("upload-card");
const uploadStatus = document.getElementById("upload-status");
const uploadBtn = document.getElementById("upload-btn");

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("resume-file");
const dzFilename = document.getElementById("dz-filename");

const profileCard = document.getElementById("profile-card");
const profileContent = document.getElementById("profile-content");

function showBanner(el, message, kind) {
  el.textContent = message;
  el.className = `status-banner show ${kind}`;
}

function hideBanner(el) {
  el.className = "status-banner";
}

function showLoadingBanner(el, message) {
  el.innerHTML = `${message} <span class="loader-dot"></span><span class="loader-dot"></span><span class="loader-dot"></span>`;
  el.className = "status-banner show loading";
}

// ---------- Registration ----------

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();

  if (!name || !email) return;

  registerBtn.disabled = true;
  showLoadingBanner(registerStatus, "Registering");

  try {
    const res = await fetch(`${API_BASE}/student/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed.");
    }

    const student = await res.json();
    currentStudentId = student.id;

    showBanner(registerStatus, `Welcome, ${student.name}. Your profile is ready for a resume.`, "info");
    uploadCard.style.display = "block";
    uploadCard.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    showBanner(registerStatus, err.message, "error");
  } finally {
    registerBtn.disabled = false;
  }
});

// ---------- File selection (click + drag/drop) ----------

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    setSelectedFile(fileInput.files[0]);
  }
});

["dragover", "dragenter"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);

["dragleave", "dragend", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);

dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file && file.type === "application/pdf") {
    setSelectedFile(file);
  } else {
    showBanner(uploadStatus, "Only PDF files are accepted.", "error");
  }
});

function setSelectedFile(file) {
  selectedFile = file;
  dzFilename.textContent = file.name;
  uploadBtn.disabled = false;
  hideBanner(uploadStatus);
}

// ---------- Upload + parse ----------

uploadBtn.addEventListener("click", async () => {
  if (!selectedFile || !currentStudentId) return;

  uploadBtn.disabled = true;
  showLoadingBanner(uploadStatus, "Reading your resume and structuring your profile");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch(`${API_BASE}/student/${currentStudentId}/resume`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Upload failed.");
    }

    const resume = await res.json();

    if (resume.parse_status === "parsed") {
      showBanner(uploadStatus, "Resume uploaded and parsed successfully.", "info");
      renderProfile(JSON.parse(resume.parsed_json));
    } else {
      showBanner(
        uploadStatus,
        `Resume uploaded, but parsing failed: ${resume.parse_error || "unknown error"}`,
        "error"
      );
    }
  } catch (err) {
    showBanner(uploadStatus, err.message, "error");
  } finally {
    uploadBtn.disabled = false;
  }
});

// ---------- Profile rendering ----------

function renderProfile(profile) {
  const skillTags = (profile.skills || [])
    .map((s) => `<span class="tag">${escapeHtml(s)}</span>`)
    .join("");

  const education = (profile.education || [])
    .map(
      (ed) =>
        `${escapeHtml(ed.degree || "")} — ${escapeHtml(ed.institution || "")}${
          ed.year ? ` (${escapeHtml(ed.year)})` : ""
        }`
    )
    .join("<br/>");

  const experience = (profile.work_experience || [])
    .map(
      (w) =>
        `<strong>${escapeHtml(w.role || "")}</strong>, ${escapeHtml(w.company || "")} — ${escapeHtml(
          w.duration || ""
        )}<br/><span style="color:var(--text-muted); font-size:0.85rem;">${escapeHtml(
          w.description || ""
        )}</span>`
    )
    .join("<br/><br/>");

  const projects = (profile.projects || [])
    .map(
      (p) =>
        `<strong>${escapeHtml(p.name || "")}</strong><br/><span style="color:var(--text-muted); font-size:0.85rem;">${escapeHtml(
          p.description || ""
        )}</span>`
    )
    .join("<br/><br/>");

  profileContent.innerHTML = `
    <div class="profile-preview">
      <div class="profile-row">
        <div class="label">Summary</div>
        <div class="value">${escapeHtml(profile.summary || "—")}</div>
      </div>
      <div class="profile-row">
        <div class="label">Experience</div>
        <div class="value">${profile.total_experience_years ?? 0} years (estimated)</div>
      </div>
      <div class="profile-row">
        <div class="label">Skills</div>
        <div class="value"><div class="tag-row">${skillTags || "—"}</div></div>
      </div>
      <div class="profile-row">
        <div class="label">Education</div>
        <div class="value">${education || "—"}</div>
      </div>
      ${
        experience
          ? `<div class="profile-row"><div class="label">Work history</div><div class="value">${experience}</div></div>`
          : ""
      }
      ${
        projects
          ? `<div class="profile-row"><div class="label">Projects</div><div class="value">${projects}</div></div>`
          : ""
      }
    </div>
  `;

  profileCard.style.display = "block";
  profileCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = String(str ?? "");
  return div.innerHTML;
}
