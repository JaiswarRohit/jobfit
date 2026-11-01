document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const dropZone = document.getElementById("dropZone");
  const resumeFileInput = document.getElementById("resumeFileInput");
  const fileUploadLabel = document.getElementById("fileUploadLabel");
  const candidateName = document.getElementById("candidateName");
  const resumeText = document.getElementById("resumeText");
  const skillsPreviewContainer = document.getElementById("skillsPreviewContainer");
  const skillsBadges = document.getElementById("skillsBadges");

  const jobKeywords = document.getElementById("jobKeywords");
  const jobLocation1 = document.getElementById("jobLocation1");
  const jobLocation2 = document.getElementById("jobLocation2");
  const jobLocation3 = document.getElementById("jobLocation3");
  const suggestedTitlesBadges = document.getElementById("suggestedTitlesBadges");

  const experienceLevel = document.getElementById("experienceLevel");
  const detectedExpBadge = document.getElementById("detectedExpBadge");
  const sortSequence = document.getElementById("sortSequence");

  const maxJobs = document.getElementById("maxJobs");
  const minMatchSlider = document.getElementById("minMatchSlider");
  const matchSliderVal = document.getElementById("matchSliderVal");

  const telegramToken = document.getElementById("telegramToken");
  const telegramChatId = document.getElementById("telegramChatId");
  const testTelegramBtn = document.getElementById("testTelegramBtn");
  const saveTelegramBtn = document.getElementById("saveTelegramBtn");
  const sendToTelegramCheck = document.getElementById("sendToTelegramCheck");
  const telegramStatusPill = document.getElementById("telegramStatusPill");
  const tgTokenSavedBadge = document.getElementById("tgTokenSavedBadge");
  const tgChatSavedBadge = document.getElementById("tgChatSavedBadge");

  // 24/7 Watcher Elements
  const startWatcherBtn = document.getElementById("startWatcherBtn");
  const stopWatcherBtn = document.getElementById("stopWatcherBtn");
  const watcherInterval = document.getElementById("watcherInterval");
  const watcherActiveCard = document.getElementById("watcherActiveCard");
  const watcherStatusDesc = document.getElementById("watcherStatusDesc");
  const watcherTotalChecks = document.getElementById("watcherTotalChecks");
  const watcherTotalSent = document.getElementById("watcherTotalSent");
  const watcherLastCheck = document.getElementById("watcherLastCheck");

  const runPipelineBtn = document.getElementById("runPipelineBtn");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const emptyState = document.getElementById("emptyState");
  const jobResultsContainer = document.getElementById("jobResultsContainer");
  const resultsFilterBar = document.getElementById("resultsFilterBar");
  const resultsCountLabel = document.getElementById("resultsCountLabel");
  const filterJobInput = document.getElementById("filterJobInput");

  const statScanned = document.getElementById("statScanned");
  const statQualified = document.getElementById("statQualified");
  const statTopMatch = document.getElementById("statTopMatch");
  const statTelegram = document.getElementById("statTelegram");

  // Database Persistence Elements
  const dbLoadedBanner = document.getElementById("dbLoadedBanner");
  const dbResumeStatus = document.getElementById("dbResumeStatus");
  const manualSaveBtn = document.getElementById("manualSaveBtn");
  const saveBtnText = document.getElementById("saveBtnText");

  let selectedFile = null;
  let currentResults = [];

  // Sort Sequence change listener (Newest First vs Highest Match)
  if (sortSequence) {
    sortSequence.addEventListener("change", () => {
      sortAndRenderResults();
    });
  }

  function sortAndRenderResults() {
    const seq = sortSequence ? sortSequence.value : "recent";
    if (seq === "recent") {
      // Newest / lowest age hours first as top priority
      currentResults.sort((a, b) => {
        const ageA = (a.job && a.job.posted_age_hours !== undefined) ? a.job.posted_age_hours : 999;
        const ageB = (b.job && b.job.posted_age_hours !== undefined) ? b.job.posted_age_hours : 999;
        if (ageA !== ageB) return ageA - ageB;
        return b.match_percentage - a.match_percentage;
      });
    } else {
      // Highest match percentage first
      currentResults.sort((a, b) => {
        if (b.match_percentage !== a.match_percentage) return b.match_percentage - a.match_percentage;
        const ageA = (a.job && a.job.posted_age_hours !== undefined) ? a.job.posted_age_hours : 999;
        const ageB = (b.job && b.job.posted_age_hours !== undefined) ? b.job.posted_age_hours : 999;
        return ageA - ageB;
      });
    }

    const q = filterJobInput ? filterJobInput.value.toLowerCase().trim() : "";
    if (!q) {
      renderJobCards(currentResults);
      if (resultsCountLabel) resultsCountLabel.textContent = `All ${currentResults.length} Jobs Listed (Unlimited)`;
    } else {
      const filtered = currentResults.filter(item => {
        const title = (item.job && item.job.title ? item.job.title : "").toLowerCase();
        const company = (item.job && item.job.company ? item.job.company : "").toLowerCase();
        const loc = (item.job && item.job.location ? item.job.location : "").toLowerCase();
        const skills = (item.matching_skills || []).join(" ").toLowerCase();
        return title.includes(q) || company.includes(q) || loc.includes(q) || skills.includes(q);
      });
      renderJobCards(filtered);
      if (resultsCountLabel) resultsCountLabel.textContent = `Showing ${filtered.length} of ${currentResults.length} Jobs`;
    }
  }

  function autoSelectExperience(expYears) {
    if (!experienceLevel || expYears === undefined || expYears === null) return;
    let target = "all";
    if (expYears < 1.5) target = "entry";
    else if (expYears <= 3.5) target = "associate";
    else if (expYears <= 6.5) target = "mid_senior";
    else if (expYears <= 9.0) target = "senior";
    else target = "director";

    experienceLevel.value = target;
    if (detectedExpBadge) {
      detectedExpBadge.textContent = `${expYears} yrs detected`;
      detectedExpBadge.classList.remove("hidden");
    }
  }

  // Filter input event listener for managing listed jobs
  if (filterJobInput) {
    filterJobInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q) {
        renderJobCards(currentResults);
        if (resultsCountLabel) resultsCountLabel.textContent = `All ${currentResults.length} Jobs Listed (Unlimited)`;
        return;
      }
      const filtered = currentResults.filter(item => {
        const title = (item.job && item.job.title ? item.job.title : "").toLowerCase();
        const company = (item.job && item.job.company ? item.job.company : "").toLowerCase();
        const loc = (item.job && item.job.location ? item.job.location : "").toLowerCase();
        const skills = (item.matching_skills || []).join(" ").toLowerCase();
        return title.includes(q) || company.includes(q) || loc.includes(q) || skills.includes(q);
      });
      renderJobCards(filtered);
      if (resultsCountLabel) resultsCountLabel.textContent = `Showing ${filtered.length} of ${currentResults.length} Jobs`;
    });
  }

  // Initial setup
  loadSavedProfileFromDB();
  attachTitlePillListeners();
  checkWatcherStatus();
  setInterval(checkWatcherStatus, 10000);

  // ----------------------------------------------------------------------
  // 💾 SQLite Database Persistence (Auto-load on Dashboard Launch)
  // ----------------------------------------------------------------------
  async function loadSavedProfileFromDB() {
    try {
      const res = await fetch("/api/profile/saved");
      const data = await res.json();
      if (res.ok && data.has_saved_profile && data.profile) {
        const p = data.profile;
        if (p.candidate_name) candidateName.value = p.candidate_name;
        if (p.resume_text) resumeText.value = p.resume_text;
        if (p.keywords) jobKeywords.value = p.keywords;
        if (p.location_1 !== undefined && p.location_1 !== null) jobLocation1.value = p.location_1;
        if (p.location_2 !== undefined && p.location_2 !== null) jobLocation2.value = p.location_2;
        if (p.location_3 !== undefined && p.location_3 !== null) jobLocation3.value = p.location_3;
        if (p.experience_level) experienceLevel.value = p.experience_level;
        if (p.min_match_percentage !== undefined && p.min_match_percentage !== null) {
          minMatchSlider.value = p.min_match_percentage;
          matchSliderVal.textContent = `${p.min_match_percentage}%`;
        }
        if (p.telegram_bot_token) telegramToken.value = p.telegram_bot_token;
        if (p.telegram_chat_id) telegramChatId.value = p.telegram_chat_id;

        if (p.skills && p.skills.length > 0) {
          displayDetectedSkills(p.skills);
        }
        if (p.suggested_titles && p.suggested_titles.length > 0) {
          displaySuggestedTitles(p.suggested_titles);
        }
        if (p.experience_years !== undefined && p.experience_years !== null) {
          autoSelectExperience(p.experience_years);
        }

        if (dbLoadedBanner) {
          dbLoadedBanner.classList.remove("hidden");
          if (p.resume_filename) {
            fileUploadLabel.textContent = `Saved Resume: ${p.resume_filename}`;
            dropZone.classList.add("border-emerald-500/60", "bg-emerald-500/5");
            if (dbResumeStatus) dbResumeStatus.textContent = `Using saved resume "${p.resume_filename}" & Telegram credentials. Ready to scan!`;
          } else {
            if (dbResumeStatus) dbResumeStatus.textContent = "Profile, search preferences, and credentials ready in SQLite.";
          }
        }

        if (p.telegram_bot_token) {
          if (tgTokenSavedBadge) tgTokenSavedBadge.classList.remove("hidden");
        }
        if (p.telegram_chat_id) {
          if (tgChatSavedBadge) tgChatSavedBadge.classList.remove("hidden");
        }

        if (p.telegram_bot_token && p.telegram_chat_id) {
          showTelegramStatus(true, "✅ Saved Telegram Bot credentials loaded from SQLite database & .env.");
        }
      }
    } catch (err) {
      console.warn("Could not load saved profile from database:", err);
    }
  }

  if (manualSaveBtn) {
    manualSaveBtn.addEventListener("click", async () => {
      manualSaveBtn.disabled = true;
      if (saveBtnText) saveBtnText.textContent = "Saving...";

      try {
        const payload = {
          candidate_name: candidateName.value.trim() || "Candidate",
          keywords: jobKeywords.value.trim(),
          location_1: jobLocation1 ? jobLocation1.value.trim() : "",
          location_2: jobLocation2 ? jobLocation2.value.trim() : "",
          location_3: jobLocation3 ? jobLocation3.value.trim() : "",
          experience_level: experienceLevel ? experienceLevel.value : "mid_senior",
          min_match_percentage: parseFloat(minMatchSlider.value),
          telegram_bot_token: telegramToken.value.trim(),
          telegram_chat_id: telegramChatId.value.trim()
        };

        const res = await fetch("/api/profile/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          if (saveBtnText) saveBtnText.textContent = "Saved!";
          if (dbLoadedBanner) dbLoadedBanner.classList.remove("hidden");
          setTimeout(() => {
            if (saveBtnText) saveBtnText.textContent = "Save Settings";
            manualSaveBtn.disabled = false;
          }, 2000);
        } else {
          alert(`Error saving: ${data.detail || "Failed to save"}`);
          if (saveBtnText) saveBtnText.textContent = "Save Settings";
          manualSaveBtn.disabled = false;
        }
      } catch (e) {
        alert(`Network error saving profile: ${e.message}`);
        if (saveBtnText) saveBtnText.textContent = "Save Settings";
        manualSaveBtn.disabled = false;
      }
    });
  }

  function attachTitlePillListeners() {
    document.querySelectorAll(".title-pill").forEach(btn => {
      btn.addEventListener("click", () => {
        const title = btn.textContent.trim();
        jobKeywords.value = title;
        document.querySelectorAll(".title-pill").forEach(b => {
          b.className = "title-pill text-xs px-2.5 py-1 rounded-lg bg-indigo-500/15 text-indigo-200 border border-indigo-500/30 hover:bg-indigo-500/30 hover:border-indigo-400 transition cursor-pointer";
        });
        btn.className = "title-pill text-xs px-2.5 py-1 rounded-lg bg-indigo-600 text-white font-semibold shadow-sm transition cursor-pointer";
      });
    });
  }

  function displaySuggestedTitles(titles) {
    if (!titles || titles.length === 0 || !suggestedTitlesBadges) return;
    suggestedTitlesBadges.innerHTML = "";
    titles.forEach((title, index) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `title-pill text-xs px-2.5 py-1 rounded-lg transition cursor-pointer ${
        index === 0
          ? "bg-indigo-600 text-white font-semibold shadow-sm"
          : "bg-indigo-500/15 text-indigo-200 border border-indigo-500/30 hover:bg-indigo-500/30 hover:border-indigo-400"
      }`;
      btn.textContent = title;

      btn.addEventListener("click", () => {
        jobKeywords.value = title;
        document.querySelectorAll(".title-pill").forEach(b => {
          b.className = "title-pill text-xs px-2.5 py-1 rounded-lg bg-indigo-500/15 text-indigo-200 border border-indigo-500/30 hover:bg-indigo-500/30 hover:border-indigo-400 transition cursor-pointer";
        });
        btn.className = "title-pill text-xs px-2.5 py-1 rounded-lg bg-indigo-600 text-white font-semibold shadow-sm transition cursor-pointer";
      });

      suggestedTitlesBadges.appendChild(btn);
    });
  }

  // Slider update
  minMatchSlider.addEventListener("input", (e) => {
    matchSliderVal.textContent = `${e.target.value}%`;
  });

  // Drop zone interactions
  dropZone.addEventListener("click", () => resumeFileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-blue-500", "bg-blue-500/10");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("border-blue-500", "bg-blue-500/10");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-blue-500", "bg-blue-500/10");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  resumeFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  async function handleFileSelected(file) {
    selectedFile = file;
    fileUploadLabel.textContent = `Selected: ${file.name}`;
    dropZone.classList.add("border-emerald-500", "bg-emerald-500/10");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("candidate_name", candidateName.value || "Candidate");

    try {
      const res = await fetch("/api/resume/upload", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (res.ok && data.profile) {
        displayDetectedSkills(data.profile.skills);
        if (data.profile.suggested_titles && data.profile.suggested_titles.length > 0) {
          displaySuggestedTitles(data.profile.suggested_titles);
          jobKeywords.value = data.profile.suggested_titles[0];
        } else if (data.profile.title && data.profile.title !== "Software Engineer") {
          jobKeywords.value = data.profile.title;
        }
        if (data.profile.experience_years !== undefined) {
          autoSelectExperience(data.profile.experience_years);
        }
      }
    } catch (err) {
      console.warn("Resume preview parse failed:", err);
    }
  }

  function displayDetectedSkills(skills) {
    if (!skills || skills.length === 0) return;
    skillsBadges.innerHTML = "";
    skills.forEach(skill => {
      const span = document.createElement("span");
      span.className = "text-[11px] px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30 font-medium";
      span.textContent = skill;
      skillsBadges.appendChild(span);
    });
    skillsPreviewContainer.classList.remove("hidden");
  }

  // Save Telegram Credentials directly to SQLite & .env
  async function saveTelegramCredentialsOnly(notify = true) {
    const token = telegramToken.value.trim();
    const chat = telegramChatId.value.trim();

    if (!token && !chat) return;

    try {
      const res = await fetch("/api/telegram/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bot_token: token, chat_id: chat })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        if (token && tgTokenSavedBadge) tgTokenSavedBadge.classList.remove("hidden");
        if (chat && tgChatSavedBadge) tgChatSavedBadge.classList.remove("hidden");
        if (notify) {
          showTelegramStatus(true, "✅ Telegram Bot Token & Chat ID saved to SQLite database & .env successfully!");
        }
      } else if (notify) {
        showTelegramStatus(false, `❌ ${data.detail || "Failed to save Telegram credentials"}`);
      }
    } catch (e) {
      if (notify) showTelegramStatus(false, `❌ Error saving credentials: ${e.message}`);
    }
  }

  if (saveTelegramBtn) {
    saveTelegramBtn.addEventListener("click", () => saveTelegramCredentialsOnly(true));
  }

  // Auto-save Telegram credentials when user finishes typing/pasting
  telegramToken.addEventListener("blur", () => {
    if (telegramToken.value.trim() && telegramChatId.value.trim()) {
      saveTelegramCredentialsOnly(false);
    }
  });
  telegramChatId.addEventListener("blur", () => {
    if (telegramToken.value.trim() && telegramChatId.value.trim()) {
      saveTelegramCredentialsOnly(false);
    }
  });

  // Test Telegram Bot Ping
  testTelegramBtn.addEventListener("click", async () => {
    const token = telegramToken.value.trim();
    const chat = telegramChatId.value.trim();

    if (!token || !chat) {
      showTelegramStatus(false, "Please enter both Bot Token and Chat ID to test.");
      return;
    }

    testTelegramBtn.disabled = true;
    testTelegramBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Testing & Saving...`;

    try {
      const res = await fetch("/api/telegram/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bot_token: token, chat_id: chat })
      });
      const data = await res.json();
      if (res.ok) {
        showTelegramStatus(true, "✅ Bot connected & saved to database! Check Telegram for the ping message.");
        if (tgTokenSavedBadge) tgTokenSavedBadge.classList.remove("hidden");
        if (tgChatSavedBadge) tgChatSavedBadge.classList.remove("hidden");
      } else {
        showTelegramStatus(false, `❌ ${data.detail || "Connection failed. Check your token and chat ID."}`);
      }
    } catch (err) {
      showTelegramStatus(false, `❌ Network error: ${err.message}`);
    } finally {
      testTelegramBtn.disabled = false;
      testTelegramBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Test Bot Ping`;
    }
  });

  function showTelegramStatus(isSuccess, msg) {
    telegramStatusPill.className = `text-xs p-2.5 rounded-lg block ${
      isSuccess ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
    }`;
    telegramStatusPill.textContent = msg;
    telegramStatusPill.classList.remove("hidden");
  }

  // ----------------------------------------------------------------------
  // 🤖 24/7 Background Watcher Service Integration
  // ----------------------------------------------------------------------
  async function checkWatcherStatus() {
    try {
      const res = await fetch("/api/watcher/status");
      const data = await res.json();
      if (data.is_running) {
        watcherActiveCard.classList.remove("hidden");
        watcherTotalChecks.textContent = data.stats.total_checks;
        watcherTotalSent.textContent = data.stats.total_jobs_sent;
        watcherLastCheck.textContent = data.stats.last_check_time ? data.stats.last_check_time.split(" ")[1] : "Active";
        if (data.config) {
          const locs = data.config.locations && data.config.locations.length > 0 ? data.config.locations.join(", ") : "Worldwide / Remote";
          watcherStatusDesc.innerHTML = `Monitoring LinkedIn 24/7 for <b>${data.config.keywords}</b> in <b>${locs}</b> (Checking every ${data.config.interval_minutes} mins). You can safely close this browser — new jobs will automatically ping your Telegram bot!`;
        }
        startWatcherBtn.classList.add("opacity-60", "pointer-events-none");
        startWatcherBtn.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> <span>24/7 Background Watcher is Already Running</span>`;
      } else {
        watcherActiveCard.classList.add("hidden");
        startWatcherBtn.classList.remove("opacity-60", "pointer-events-none");
        startWatcherBtn.innerHTML = `<i class="fa-solid fa-play text-lg"></i> <span>Start 24/7 Background Auto-Watcher</span>`;
      }
    } catch (e) {
      console.warn("Watcher status check error:", e);
    }
  }

  startWatcherBtn.addEventListener("click", async () => {
    const token = telegramToken.value.trim();
    const chat = telegramChatId.value.trim();

    if (!token || !chat) {
      alert("Please enter your Telegram Bot Token and Chat ID first so the background watcher can deliver new jobs.");
      return;
    }

    startWatcherBtn.disabled = true;
    startWatcherBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Activating 24/7 Background Watcher...`;

    const formData = new FormData();
    if (selectedFile) {
      formData.append("file", selectedFile);
    } else {
      formData.append("resume_text", resumeText.value.trim());
    }

    formData.append("candidate_name", candidateName.value.trim() || "Candidate");
    formData.append("keywords", jobKeywords.value.trim());
    formData.append("location_1", jobLocation1 ? jobLocation1.value.trim() : "");
    formData.append("location_2", jobLocation2 ? jobLocation2.value.trim() : "");
    formData.append("location_3", jobLocation3 ? jobLocation3.value.trim() : "");
    formData.append("min_match_percentage", minMatchSlider.value);
    formData.append("interval_minutes", watcherInterval.value);
    formData.append("experience_level", experienceLevel ? experienceLevel.value : "all");
    formData.append("telegram_bot_token", token);
    formData.append("telegram_chat_id", chat);

    try {
      const res = await fetch("/api/watcher/start", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showTelegramStatus(true, "🟢 24/7 Background Watcher activated! Check Telegram for the confirmation message.");
        await checkWatcherStatus();
      } else {
        alert(`Error starting watcher: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      alert(`Network error starting watcher: ${err.message}`);
    } finally {
      startWatcherBtn.disabled = false;
    }
  });

  stopWatcherBtn.addEventListener("click", async () => {
    stopWatcherBtn.disabled = true;
    stopWatcherBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Stopping...`;

    try {
      const res = await fetch("/api/watcher/stop", { method: "POST" });
      const data = await res.json();
      if (res.ok && data.success) {
        showTelegramStatus(false, "🛑 Background Watcher stopped.");
        await checkWatcherStatus();
      }
    } catch (err) {
      alert(`Error stopping watcher: ${err.message}`);
    } finally {
      stopWatcherBtn.disabled = false;
      stopWatcherBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Watcher`;
    }
  });

  // ----------------------------------------------------------------------
  // Instant Scan Once Execution
  // ----------------------------------------------------------------------
  runPipelineBtn.addEventListener("click", async () => {
    emptyState.classList.add("hidden");
    jobResultsContainer.classList.add("hidden");
    loadingIndicator.classList.remove("hidden");
    runPipelineBtn.disabled = true;
    runPipelineBtn.classList.add("opacity-60");

    const formData = new FormData();
    if (selectedFile) {
      formData.append("file", selectedFile);
    } else {
      formData.append("resume_text", resumeText.value.trim());
    }

    formData.append("candidate_name", candidateName.value.trim() || "Candidate");
    formData.append("keywords", jobKeywords.value.trim());
    formData.append("location_1", jobLocation1 ? jobLocation1.value.trim() : "");
    formData.append("location_2", jobLocation2 ? jobLocation2.value.trim() : "");
    formData.append("location_3", jobLocation3 ? jobLocation3.value.trim() : "");

    formData.append("min_match_percentage", minMatchSlider.value);
    const maxJobsVal = maxJobs.value || "0";
    formData.append("max_jobs_to_scan", maxJobsVal);
    formData.append("experience_level", experienceLevel ? experienceLevel.value : "all");
    formData.append("sort_by", sortSequence ? sortSequence.value : "recent");
    formData.append("top_n_to_telegram", "0");
    formData.append("telegram_bot_token", telegramToken.value.trim());
    formData.append("telegram_chat_id", telegramChatId.value.trim());
    formData.append("send_telegram", sendToTelegramCheck.checked ? "true" : "false");

    try {
      const res = await fetch("/api/pipeline/run", {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Pipeline run failed");
      }

      if (data.candidate) {
        if (data.candidate.skills) {
          displayDetectedSkills(data.candidate.skills);
        }
        if (data.candidate.suggested_titles && data.candidate.suggested_titles.length > 0) {
          displaySuggestedTitles(data.candidate.suggested_titles);
        }
        if (data.candidate.experience_years !== undefined) {
          autoSelectExperience(data.candidate.experience_years);
        }
      }

      // Update Stats
      statScanned.textContent = data.search_parameters.total_scanned;
      statQualified.textContent = data.search_parameters.qualified_count;
      
      const topJob = data.all_ranked_results && data.all_ranked_results[0];
      statTopMatch.textContent = topJob ? `${topJob.match_percentage}%` : "0%";
      statTelegram.textContent = data.telegram_status && data.telegram_status.jobs_sent_count ? data.telegram_status.jobs_sent_count : (data.telegram_status && data.telegram_status.sent_to_telegram ? "Yes" : "0");

      if (data.telegram_status && data.telegram_status.errors && data.telegram_status.errors.length > 0) {
        showTelegramStatus(false, `❌ Telegram: ${data.telegram_status.errors[0]}`);
      } else if (data.telegram_status && data.telegram_status.sent_to_telegram) {
        showTelegramStatus(true, `✅ Delivered ${data.telegram_status.jobs_sent_count} jobs directly to Telegram!`);
      }

      // Render Job Cards
      renderJobResults(data.all_ranked_results || []);

    } catch (err) {
      alert(`Error running job scanner: ${err.message}`);
    } finally {
      loadingIndicator.classList.add("hidden");
      runPipelineBtn.disabled = false;
      runPipelineBtn.classList.remove("opacity-60");
    }
  });

  function renderJobResults(results) {
    currentResults = results || [];

    if (resultsFilterBar) {
      if (currentResults.length > 0) {
        resultsFilterBar.classList.remove("hidden");
        if (resultsCountLabel) resultsCountLabel.textContent = `All ${currentResults.length} Jobs Listed (Unlimited)`;
        if (filterJobInput) filterJobInput.value = "";
      } else {
        resultsFilterBar.classList.add("hidden");
      }
    }

    sortAndRenderResults();
  }

  function renderJobCards(results) {
    jobResultsContainer.innerHTML = "";

    if (!results || results.length === 0) {
      jobResultsContainer.innerHTML = `
        <div class="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-8 text-center">
          <i class="fa-solid fa-triangle-exclamation text-amber-400 text-3xl mb-2"></i>
          <h4 class="text-base font-semibold text-white">No jobs matched search</h4>
          <p class="text-xs text-slate-400 mt-1">Try adjusting the filter keyword or lowering the minimum match percentage.</p>
        </div>
      `;
      jobResultsContainer.classList.remove("hidden");
      return;
    }

    results.forEach((match, index) => {
      const job = match.job;
      const rank = index + 1;

      let scoreColor = "text-emerald-400 border-emerald-500/40 bg-emerald-500/10";
      let probColor = "text-emerald-300 bg-emerald-500/20";
      if (match.match_percentage < 65) {
        scoreColor = "text-amber-400 border-amber-500/40 bg-amber-500/10";
        probColor = "text-amber-300 bg-amber-500/20";
      } else if (match.match_percentage < 78) {
        scoreColor = "text-blue-400 border-blue-500/40 bg-blue-500/10";
        probColor = "text-blue-300 bg-blue-500/20";
      }

      // Check if job was posted within 24 hours
      const isFresh = (job.posted_age_hours !== undefined && job.posted_age_hours <= 24.0) ||
                      (job.posted_date && /hour|min|now|today/i.test(job.posted_date));

      const card = document.createElement("div");
      card.className = "bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-lg hover:border-slate-600 transition";

      const matchingBadges = match.matching_skills.map(s => 
        `<span class="text-[11px] px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">${s}</span>`
      ).join(" ");

      const missingBadges = match.missing_skills.length > 0 
        ? match.missing_skills.map(s => `<span class="text-[11px] px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/25">${s}</span>`).join(" ")
        : `<span class="text-[11px] text-slate-500 italic">None</span>`;

      card.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div class="space-y-1.5">
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-xs font-bold px-2 py-0.5 rounded bg-slate-700 text-slate-300">#${rank}</span>
              ${isFresh ? '<span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1 animate-pulse"><i class="fa-solid fa-sparkles text-cyan-400"></i> New</span>' : ''}
              <h3 class="text-base font-bold text-white hover:text-blue-400 transition">
                <a href="${job.url}" target="_blank">${job.title}</a>
              </h3>
            </div>
            <p class="text-xs text-slate-400 flex flex-wrap items-center gap-2">
              <span class="font-medium text-slate-300">${job.company}</span> • 
              <span><i class="fa-solid fa-location-dot text-slate-500"></i> ${job.location}</span>
            </p>
            <div class="flex flex-wrap items-center gap-2 pt-0.5">
              <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                <i class="fa-solid fa-clock text-cyan-400"></i> ${job.posted_date || "Recently"}
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
                <i class="fa-solid fa-briefcase text-indigo-400"></i> ${job.experience_level || "Mid-Senior"}
              </span>
            </div>
          </div>

          <div class="flex items-center sm:flex-col items-end gap-1">
            <div class="px-3 py-1 rounded-xl border ${scoreColor} font-black text-lg">
              ${match.match_percentage}%
            </div>
            <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full ${probColor}">
              ${match.selection_probability} Selection
            </span>
          </div>
        </div>

        <div class="mt-3 text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <div class="font-semibold text-slate-400 mb-1 flex items-center gap-1.5">
            <i class="fa-solid fa-bullseye text-cyan-400"></i> Recruiter Match Insight:
          </div>
          <p>${match.match_summary}</p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3 text-xs">
          <div>
            <span class="text-slate-400 font-medium block mb-1">✅ Matching Skills (${match.matching_skills.length}):</span>
            <div class="flex flex-wrap gap-1">${matchingBadges || '<span class="text-slate-500">None detected</span>'}</div>
          </div>
          <div>
            <span class="text-slate-400 font-medium block mb-1">⚠️ Missing / Desired (${match.missing_skills.length}):</span>
            <div class="flex flex-wrap gap-1">${missingBadges}</div>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
          <a href="${job.url}" target="_blank" class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition flex items-center gap-1.5">
            <i class="fa-brands fa-linkedin"></i> View & Apply on LinkedIn
          </a>
          <button class="sendSingleTgBtn text-xs px-3 py-1.5 rounded-lg border border-slate-700 hover:border-cyan-500/50 text-slate-300 hover:text-cyan-400 transition flex items-center gap-1.5">
            <i class="fa-brands fa-telegram"></i> Send to Telegram
          </button>
        </div>
      `;

      const singleTgBtn = card.querySelector(".sendSingleTgBtn");
      singleTgBtn.addEventListener("click", async () => {
        const token = telegramToken.value.trim();
        const chat = telegramChatId.value.trim();
        if (!token || !chat) {
          alert("Please enter Telegram Bot Token and Chat ID above.");
          return;
        }

        singleTgBtn.disabled = true;
        singleTgBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Sending...`;

        try {
          const res = await fetch("/api/telegram/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              bot_token: token,
              chat_id: chat,
              jobs: [match],
              top_n: 1
            })
          });
          const d = await res.json();
          if (res.ok && d.success) {
            singleTgBtn.innerHTML = `<i class="fa-solid fa-check text-emerald-400"></i> Sent!`;
          } else {
            alert(`Telegram error: ${d.detail || "Failed to send"}`);
            singleTgBtn.innerHTML = `<i class="fa-brands fa-telegram"></i> Send to Telegram`;
            singleTgBtn.disabled = false;
          }
        } catch (err) {
          alert(`Network error: ${err.message}`);
          singleTgBtn.disabled = false;
          singleTgBtn.innerHTML = `<i class="fa-brands fa-telegram"></i> Send to Telegram`;
        }
      });

      jobResultsContainer.appendChild(card);
    });

    jobResultsContainer.classList.remove("hidden");
  }
});
