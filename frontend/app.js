/**
 * Tamil & Multilingual News Truth Checker - Client Controller
 * Handles latest breaking news feed, media OCR uploads, text verification, stepper animation, executive summaries, and history.
 */

document.addEventListener("DOMContentLoaded", () => {
    // API Base URL (Supports localhost:8000 when opened via file:/// or custom origin)
    const API_BASE = (window.location.protocol === "file:" || !window.location.port) && window.location.hostname === "" ? "http://127.0.0.1:8000" : "";

    // DOM Elements - Text Form
    const form = document.getElementById("verificationForm");
    const newsInput = document.getElementById("newsInput");
    const urlInput = document.getElementById("urlInput");
    const languageSelect = document.getElementById("languageSelect");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const clearBtn = document.getElementById("clearBtn");

    // DOM Elements - Tabs & Media Form
    const tabTextBtn = document.getElementById("tabTextBtn");
    const tabMediaBtn = document.getElementById("tabMediaBtn");
    const mediaForm = document.getElementById("mediaForm");
    const dropZone = document.getElementById("dropZone");
    const mediaFileInput = document.getElementById("mediaFileInput");
    const browseFileBtn = document.getElementById("browseFileBtn");
    const dropzonePrompt = document.getElementById("dropzonePrompt");
    const mediaPreviewContainer = document.getElementById("mediaPreviewContainer");
    const previewMediaWrapper = document.getElementById("previewMediaWrapper");
    const previewFileName = document.getElementById("previewFileName");
    const previewFileSize = document.getElementById("previewFileSize");
    const removeMediaBtn = document.getElementById("removeMediaBtn");
    const mediaLanguageSelect = document.getElementById("mediaLanguageSelect");
    const mediaSubmitBtn = document.getElementById("mediaSubmitBtn");
    const mediaBtnText = document.getElementById("mediaBtnText");

    // Sections
    const latestNewsGrid = document.getElementById("latestNewsGrid");
    const refreshNewsBtn = document.getElementById("refreshNewsBtn");
    const loadingSection = document.getElementById("loadingSection");
    const resultSection = document.getElementById("resultSection");
    const mediaOcrBanner = document.getElementById("mediaOcrBanner");
    const mediaOcrTypeBadge = document.getElementById("mediaOcrTypeBadge");
    const mediaOcrContent = document.getElementById("mediaOcrContent");

    // Verdict Elements
    const verdictBanner = document.getElementById("verdictBanner");
    const verdictBadgeIcon = document.getElementById("verdictBadgeIcon");
    const verdictBadgeLabel = document.getElementById("verdictBadgeLabel");
    const verdictTitle = document.getElementById("verdictTitle");
    const confidenceValue = document.getElementById("confidenceValue");
    const confidenceBar = document.getElementById("confidenceBar");
    const resultClaimText = document.getElementById("resultClaimText");
    const resultReasonText = document.getElementById("resultReasonText");
    const resultDetailedExplanation = document.getElementById("resultDetailedExplanation");

    // Executive Summary Elements
    const executiveSummaryCard = document.getElementById("executiveSummaryCard");
    const execHeadline = document.getElementById("execHeadline");
    const execClaimedEvent = document.getElementById("execClaimedEvent");
    const execFactualReality = document.getElementById("execFactualReality");
    const execKeyReasonsList = document.getElementById("execKeyReasonsList");
    const execAdvisory = document.getElementById("execAdvisory");

    // Stats Elements
    const statTotalArticles = document.getElementById("statTotalArticles");
    const statIndependent = document.getElementById("statIndependent");
    const statSyndicated = document.getElementById("statSyndicated");
    const statPrimary = document.getElementById("statPrimary");

    // Table & Articles
    const comparisonTableBody = document.getElementById("comparisonTableBody");
    const articlesGrid = document.getElementById("articlesGrid");
    const filterPills = document.querySelectorAll(".filter-pills .pill");
    const filterAllCount = document.getElementById("filterAllCount");
    const filterSupportsCount = document.getElementById("filterSupportsCount");
    const filterContradictsCount = document.getElementById("filterContradictsCount");

    // Modals & Action buttons
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const themeIcon = document.getElementById("themeIcon");
    const sourcesBtn = document.getElementById("sourcesBtn");
    const sourcesModal = document.getElementById("sourcesModal");
    const closeSourcesModal = document.getElementById("closeSourcesModal");
    const sourcesListContainer = document.getElementById("sourcesListContainer");
    const historyBtn = document.getElementById("historyBtn");
    const historyModal = document.getElementById("historyModal");
    const closeHistoryModal = document.getElementById("closeHistoryModal");
    const historyListContainer = document.getElementById("historyListContainer");
    const clearHistoryBtn = document.getElementById("clearHistoryBtn");
    const shareBtn = document.getElementById("shareBtn");
    const printBtn = document.getElementById("printBtn");

    // State
    let currentResult = null;
    let currentArticles = [];
    let activeFilter = "all";
    let selectedMediaFile = null;

    // Initialize Theme
    const savedTheme = localStorage.getItem("truth_checker_theme") || "light";
    if (savedTheme === "dark") {
        document.body.classList.replace("light-mode", "dark-mode");
        themeIcon.textContent = "☀️";
    }

    themeToggleBtn.addEventListener("click", () => {
        if (document.body.classList.contains("light-mode")) {
            document.body.classList.replace("light-mode", "dark-mode");
            localStorage.setItem("truth_checker_theme", "dark");
            themeIcon.textContent = "☀️";
        } else {
            document.body.classList.replace("dark-mode", "light-mode");
            localStorage.setItem("truth_checker_theme", "light");
            themeIcon.textContent = "🌙";
        }
    });

    // Quick prompt chips
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const claim = chip.getAttribute("data-claim");
            newsInput.value = claim;
            switchTab("text");
            newsInput.scrollIntoView({ behavior: "smooth", block: "center" });
        });
    });

    function showToast(message, type = "info") {
        const container = document.getElementById("toastContainer");
        if (!container) return;
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        
        let icon = "ℹ️";
        if (type === "error") icon = "❌";
        if (type === "success") icon = "✅";
        if (type === "warning") icon = "⚠️";

        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-msg">${escapeHtml(message)}</span>
            <button class="toast-close" type="button">&times;</button>
        `;

        toast.querySelector(".toast-close").addEventListener("click", () => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(8px)";
            setTimeout(() => toast.remove(), 200);
        });

        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = "0";
                toast.style.transform = "translateY(8px)";
                setTimeout(() => toast.remove(), 200);
            }
        }, 4500);
    }

    clearBtn.addEventListener("click", () => {
        newsInput.value = "";
        urlInput.value = "";
        languageSelect.value = "auto";
        mediaLanguageSelect.value = "auto";
        selectedMediaFile = null;
        mediaFileInput.value = "";
        previewMediaWrapper.innerHTML = "";
        mediaPreviewContainer.classList.add("hidden");
        dropzonePrompt.classList.remove("hidden");
        mediaOcrBanner.classList.add("hidden");
        resultSection.classList.add("hidden");
        stopLoading();
        showToast("Form cleared", "info");
    });

    // -------------------------------------------------------------
    // 1. LIVE LATEST BREAKING NEWS LOADER (Official & Top Outlets)
    // -------------------------------------------------------------
    const refreshBtnLabel = document.getElementById("refreshBtnLabel");
    let currentNewsCategory = "all";

    async function loadLatestBreakingNews(isManual = false) {
        if (!latestNewsGrid) return;
        
        if (refreshNewsBtn) {
            refreshNewsBtn.classList.add("loading");
            if (refreshBtnLabel) refreshBtnLabel.textContent = "Refreshing...";
        }

        if (!latestNewsGrid.children.length || isManual) {
            latestNewsGrid.innerHTML = `<div class="news-loading-placeholder">🔄 Fetching latest official & verified headlines...</div>`;
        }

        try {
            const timestamp = Date.now();
            const catParam = currentNewsCategory !== "all" ? `&category=${encodeURIComponent(currentNewsCategory)}` : "";
            const response = await fetch(`${API_BASE}/api/latest-news?limit=12${catParam}&t=${timestamp}`, { cache: "no-store" });
            if (!response.ok) throw new Error("Failed to load latest news");
            const items = await response.json();
            renderLatestNews(items);
        } catch (err) {
            console.error("Latest news error:", err);
            latestNewsGrid.innerHTML = `<div class="news-loading-placeholder" style="color:var(--text-muted);">Could not fetch live feeds. Ensure server is running at http://localhost:8000.</div>`;
        } finally {
            if (refreshNewsBtn) {
                refreshNewsBtn.classList.remove("loading");
                if (refreshBtnLabel) refreshBtnLabel.textContent = "Refresh";
            }
        }
    }

    function renderLatestNews(items) {
        latestNewsGrid.innerHTML = "";
        if (!items || items.length === 0) {
            latestNewsGrid.innerHTML = `<div class="news-loading-placeholder">No recent breaking news found for this category. Click Refresh to reload.</div>`;
            return;
        }

        items.forEach(item => {
            const isOfficial = item.is_official || item.category === "official";
            const div = document.createElement("div");
            div.className = "breaking-news-item";
            div.innerHTML = `
                <div class="breaking-news-meta">
                    <span class="breaking-news-source ${isOfficial ? "official" : ""}">
                        ${isOfficial ? "🏛️ " : "📰 "}${escapeHtml(item.source)}
                    </span>
                    <div style="display:flex;gap:0.35rem;align-items:center;">
                        ${isOfficial ? `<span class="official-badge-tag">Official Govt</span>` : ""}
                        <span>${item.language === "ta" ? "🇮🇳 தமிழ்" : "🇬🇧 English"}</span>
                    </div>
                </div>
                <h4 class="breaking-news-headline" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</h4>
                <div class="breaking-news-actions">
                    <button type="button" class="btn-verify-chip">⚡ Verify This News</button>
                </div>
            `;

            div.querySelector(".btn-verify-chip").addEventListener("click", () => {
                newsInput.value = item.title;
                urlInput.value = item.url || "";
                languageSelect.value = item.language === "ta" ? "ta" : "en";
                
                switchTab("text");
                form.dispatchEvent(new Event("submit"));
            });

            latestNewsGrid.appendChild(div);
        });
    }

    // Category pills click handler
    document.querySelectorAll(".news-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".news-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            currentNewsCategory = pill.getAttribute("data-cat") || "all";
            loadLatestBreakingNews(true);
        });
    });

    if (refreshNewsBtn) {
        refreshNewsBtn.addEventListener("click", (e) => {
            e.preventDefault();
            loadLatestBreakingNews(true);
        });
    }

    // Load initial breaking news
    loadLatestBreakingNews(false);

    // -------------------------------------------------------------
    // 2. TAB SWITCHING (Text vs Media Upload)
    // -------------------------------------------------------------
    function switchTab(mode) {
        if (mode === "text") {
            tabTextBtn.classList.add("active");
            tabMediaBtn.classList.remove("active");
            form.classList.remove("hidden");
            form.classList.add("active");
            mediaForm.classList.add("hidden");
            mediaForm.classList.remove("active");
        } else {
            tabMediaBtn.classList.add("active");
            tabTextBtn.classList.remove("active");
            mediaForm.classList.remove("hidden");
            mediaForm.classList.add("active");
            form.classList.add("hidden");
            form.classList.remove("active");
        }
    }

    tabTextBtn.addEventListener("click", () => switchTab("text"));
    tabMediaBtn.addEventListener("click", () => switchTab("media"));

    // -------------------------------------------------------------
    // 3. MEDIA UPLOAD HANDLING (Images & Videos)
    // -------------------------------------------------------------
    browseFileBtn.addEventListener("click", () => mediaFileInput.click());
    dropZone.addEventListener("click", (e) => {
        if (e.target === dropZone || e.target.closest("#dropzonePrompt")) {
            mediaFileInput.click();
        }
    });

    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        }, false);
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleSelectedMedia(files[0]);
        }
    });

    mediaFileInput.addEventListener("change", () => {
        if (mediaFileInput.files.length > 0) {
            handleSelectedMedia(mediaFileInput.files[0]);
        }
    });

    function handleSelectedMedia(file) {
        selectedMediaFile = file;
        previewFileName.textContent = file.name;
        previewFileSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;

        dropzonePrompt.classList.add("hidden");
        mediaPreviewContainer.classList.remove("hidden");
        previewMediaWrapper.innerHTML = "";

        if (file.type.startsWith("image/")) {
            const img = document.createElement("img");
            img.src = URL.createObjectURL(file);
            previewMediaWrapper.appendChild(img);
        } else if (file.type.startsWith("video/")) {
            const video = document.createElement("video");
            video.src = URL.createObjectURL(file);
            video.controls = true;
            previewMediaWrapper.appendChild(video);
        }
    }

    removeMediaBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        selectedMediaFile = null;
        mediaFileInput.value = "";
        previewMediaWrapper.innerHTML = "";
        mediaPreviewContainer.classList.add("hidden");
        dropzonePrompt.classList.remove("hidden");
    });

    // -------------------------------------------------------------
    // 4. FORM SUBMISSION - MEDIA OCR UPLOAD
    // -------------------------------------------------------------
    mediaForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!selectedMediaFile) {
            showToast("Please select or drop an image screenshot, poster, or video file.", "warning");
            return;
        }

        startVerification();
        mediaSubmitBtn.disabled = true;
        mediaBtnText.textContent = "Extracting OCR & Verifying...";

        try {
            const formData = new FormData();
            formData.append("file", selectedMediaFile);
            formData.append("language", mediaLanguageSelect.value);

            const response = await fetch(`${API_BASE}/api/check-media`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ detail: "Media analysis failed" }));
                throw new Error(errData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            finishVerification(data);

        } catch (error) {
            console.error("Media verification error:", error);
            const msg = error.message && error.message.includes("Failed to fetch")
                ? "Cannot connect to server. Please ensure backend is running at http://localhost:8000."
                : `Media analysis failed: ${error.message}`;
            showToast(msg, "error");
            stopLoading();
        } finally {
            mediaSubmitBtn.disabled = false;
            mediaBtnText.textContent = "ANALYZE & VERIFY MEDIA / சரிபார்க்கவும்";
        }
    });

    // -------------------------------------------------------------
    // 5. FORM SUBMISSION - TEXT & URL
    // -------------------------------------------------------------
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = newsInput.value.trim();
        const url = urlInput.value.trim();
        const language = languageSelect.value;

        if (!text && !url) {
            showToast("Please enter a news claim or provide a news article URL.", "warning");
            return;
        }

        startVerification();

        try {
            let response;
            if (url && !text) {
                response = await fetch(`${API_BASE}/api/check-url`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url, language })
                });
            } else {
                response = await fetch(`${API_BASE}/api/check`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text, url: url || null, language })
                });
            }

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ detail: "Verification request failed" }));
                throw new Error(errData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            finishVerification(data);

        } catch (error) {
            console.error("Verification error:", error);
            const msg = error.message && error.message.includes("Failed to fetch")
                ? "Cannot connect to backend server. Make sure the server is running at http://localhost:8000."
                : `Verification failed: ${error.message}`;
            showToast(msg, "error");
            stopLoading();
        }
    });

    // -------------------------------------------------------------
    // 6. ANIMATED STEPPER & DASHBOARD RENDERER
    // -------------------------------------------------------------
    let stepperInterval = null;
    function startVerification() {
        submitBtn.disabled = true;
        btnText.textContent = "Verifying News...";
        resultSection.classList.add("hidden");
        loadingSection.classList.remove("hidden");
        loadingSection.scrollIntoView({ behavior: "smooth", block: "nearest" });

        for (let i = 1; i <= 10; i++) {
            const step = document.getElementById(`step-${i}`);
            if (step) {
                step.className = "step-item";
                step.querySelector(".step-icon").textContent = "⏳";
            }
        }

        let currentStep = 1;
        const totalSteps = 10;
        
        stepperInterval = setInterval(() => {
            if (currentStep <= totalSteps) {
                const prevStep = document.getElementById(`step-${currentStep - 1}`);
                if (prevStep) {
                    prevStep.className = "step-item completed";
                    prevStep.querySelector(".step-icon").textContent = "✓";
                }
                const activeStep = document.getElementById(`step-${currentStep}`);
                if (activeStep) {
                    activeStep.className = "step-item active";
                    activeStep.querySelector(".step-icon").textContent = "🔄";
                }
                currentStep++;
            }
        }, 320);
    }

    function finishVerification(data) {
        clearInterval(stepperInterval);
        for (let i = 1; i <= 10; i++) {
            const step = document.getElementById(`step-${i}`);
            if (step) {
                step.className = "step-item completed";
                step.querySelector(".step-icon").textContent = "✓";
            }
        }

        setTimeout(() => {
            stopLoading();
            renderResults(data);
        }, 350);
    }

    function stopLoading() {
        clearInterval(stepperInterval);
        submitBtn.disabled = false;
        btnText.textContent = "CHECK NEWS / சரிபார்க்கவும்";
        loadingSection.classList.add("hidden");
    }

    function renderResults(data) {
        currentResult = data;
        currentArticles = data.articles || [];

        // Media OCR Banner
        if (data.extracted_text) {
            mediaOcrBanner.classList.remove("hidden");
            mediaOcrTypeBadge.textContent = data.media_type === "video" ? "Video Keyframe OCR" : "Image OCR";
            mediaOcrContent.textContent = data.extracted_text;
        } else {
            mediaOcrBanner.classList.add("hidden");
        }

        // 1. Verdict Banner
        verdictBanner.className = "card verdict-card";
        const v = data.verdict;

        if (v === "TRUE") {
            verdictBanner.classList.add("verdict-true");
            verdictBadgeIcon.textContent = "🟢";
            verdictBadgeLabel.textContent = "VERIFIED TRUE / உண்மை செய்தி";
            verdictTitle.textContent = "Verified as Authentic News";
        } else if (v === "FALSE") {
            verdictBanner.classList.add("verdict-false");
            verdictBadgeIcon.textContent = "🔴";
            verdictBadgeLabel.textContent = "🔴 FAKE / FALSE (போலிச் செய்தி / வதந்தி)";
            verdictTitle.textContent = "Classified as Fake News / Fabricated Rumor";
        } else if (v === "MISLEADING") {
            verdictBanner.classList.add("verdict-misleading");
            verdictBadgeIcon.textContent = "🟡";
            verdictBadgeLabel.textContent = "MISLEADING / தவறான தகவல்";
            verdictTitle.textContent = "Misleading / Outdated Context";
        } else {
            verdictBanner.classList.add("verdict-unverified");
            verdictBadgeIcon.textContent = "⚪";
            verdictBadgeLabel.textContent = "UNVERIFIED / சரிபார்க்கப்படவில்லை";
            verdictTitle.textContent = "Insufficient Evidence to Confirm";
        }

        // 2. Confidence
        confidenceValue.textContent = data.confidence_display;
        confidenceBar.style.width = data.confidence_display;

        // 3. Claim Quote
        resultClaimText.textContent = `"${data.claim}"`;

        // 4. Fact-Check Executive Summary
        if (data.executive_summary) {
            const isTa = data.executive_summary.language === "ta" || data.language === "ta";
            const execLabelClaim = document.getElementById("execLabelClaim");
            const execLabelReality = document.getElementById("execLabelReality");
            const execLabelReasons = document.getElementById("execLabelReasons");
            const execWhyTitle = document.getElementById("execWhyTitle");

            if (execLabelClaim) execLabelClaim.textContent = isTa ? "கூறப்பட்ட செய்தி:" : "Claimed Assertion:";
            if (execLabelReality) execLabelReality.textContent = isTa ? "உண்மை நிலை:" : "Factual Reality:";
            if (execLabelReasons) execLabelReasons.textContent = isTa ? "முக்கிய காரணங்கள் / உண்மை பின்னணி:" : "Why is this Fake / Verdict Justification:";
            if (execWhyTitle) execWhyTitle.textContent = isTa ? "💡 இந்த முடிவிற்கான காரணம் என்ன?" : "💡 Why did the system reach this conclusion?";

            executiveSummaryCard.classList.remove("hidden");
            execHeadline.textContent = data.executive_summary.headline || (isTa ? "உண்மை சரிபார்ப்பு சுருக்கம்" : "Fact-Check Executive Summary");
            execClaimedEvent.textContent = `"${data.executive_summary.claimed_event || data.claim}"`;
            execFactualReality.textContent = data.executive_summary.factual_reality || data.reason;
            
            execKeyReasonsList.innerHTML = "";
            const reasons = data.executive_summary.key_reasons || [];
            reasons.forEach(r => {
                const li = document.createElement("li");
                li.textContent = r;
                execKeyReasonsList.appendChild(li);
            });
            
            if (data.executive_summary.advisory) {
                execAdvisory.textContent = data.executive_summary.advisory;
                execAdvisory.classList.remove("hidden");
            } else {
                execAdvisory.classList.add("hidden");
            }
        } else {
            executiveSummaryCard.classList.add("hidden");
        }

        // 5. Reason & Detailed Explanation
        resultReasonText.textContent = data.reason;
        resultDetailedExplanation.innerHTML = formatMarkdown(data.detailed_explanation);

        // 6. Stats Grid
        const stats = data.stats || {};
        statTotalArticles.textContent = stats.total_articles || currentArticles.length;
        statIndependent.textContent = stats.independent_reports || 0;
        statSyndicated.textContent = stats.syndicated_reports || 0;
        statPrimary.textContent = stats.primary_sources || 0;

        // 7. Source Comparison Table
        renderComparisonTable(data.comparison_table || []);

        // 8. Articles Grid
        updateArticleFilterCounts();
        renderArticles(currentArticles);

        // Show Dashboard & Scroll smoothly directly to Verdict Banner
        resultSection.classList.remove("hidden");
        verdictBanner.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function renderComparisonTable(rows) {
        comparisonTableBody.innerHTML = "";
        if (!rows || rows.length === 0) {
            comparisonTableBody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);">No comparison records available</td></tr>`;
            return;
        }

        rows.forEach(r => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHtml(r.source_name)}</strong></td>
                <td>${r.found ? '<span class="status-badge status-found">✓ Found</span>' : '<span class="status-badge status-not-found">—</span>'}</td>
                <td>${r.supports ? '<span class="status-badge status-found">✓ Supports</span>' : '<span class="status-badge status-not-found">—</span>'}</td>
                <td>${r.contradicts ? '<span class="status-badge status-found" style="background:var(--color-false-bg);color:var(--color-false);">✗ Denies</span>' : '<span class="status-badge status-not-found">—</span>'}</td>
                <td>${escapeHtml(r.date || "Recent")}</td>
                <td><small>${escapeHtml(r.source_type || "—")}</small></td>
                <td><small>${escapeHtml(r.reliability || "—")}</small></td>
                <td>${r.article_url ? `<a href="${escapeHtml(r.article_url)}" target="_blank" rel="noopener noreferrer" style="color:var(--primary);font-weight:700;">View ↗</a>` : '<span style="color:var(--text-light);">—</span>'}</td>
            `;
            comparisonTableBody.appendChild(tr);
        });
    }

    function updateArticleFilterCounts() {
        const supportsCount = currentArticles.filter(a => a.polarity === "SUPPORTS").length;
        const contradictsCount = currentArticles.filter(a => a.polarity === "CONTRADICTS").length;

        filterAllCount.textContent = currentArticles.length;
        filterSupportsCount.textContent = supportsCount;
        filterContradictsCount.textContent = contradictsCount;
    }

    function renderArticles(articles) {
        articlesGrid.innerHTML = "";

        let filtered = articles;
        if (activeFilter === "supports") {
            filtered = articles.filter(a => a.polarity === "SUPPORTS");
        } else if (activeFilter === "contradicts") {
            filtered = articles.filter(a => a.polarity === "CONTRADICTS");
        }

        if (filtered.length === 0) {
            articlesGrid.innerHTML = `
                <div class="card" style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;">
                    No relevant articles matching filter "${activeFilter}".
                </div>
            `;
            return;
        }

        filtered.forEach(art => {
            const card = document.createElement("div");
            card.className = "article-card";

            let polarityClass = "tag-neutral";
            let polarityText = "Neutral / Context";
            if (art.polarity === "SUPPORTS") {
                polarityClass = "tag-supports";
                polarityText = "✓ Supports";
            } else if (art.polarity === "CONTRADICTS") {
                polarityClass = "tag-contradicts";
                polarityText = "✖ Contradicts / Debunks";
            } else if (art.polarity === "MISLEADING_CONTEXT") {
                polarityClass = "tag-misleading";
                polarityText = "⚠️ Outdated Context";
            }

            const pubDate = art.publication_date ? new Date(art.publication_date).toLocaleDateString() : "Recent";

            card.innerHTML = `
                <div>
                    <div class="article-meta">
                        <span class="article-source">${escapeHtml(art.source)}</span>
                        <span>${escapeHtml(pubDate)}</span>
                    </div>
                    <h4 class="article-title">
                        <a href="${escapeHtml(art.url)}" target="_blank" rel="noopener noreferrer">
                            ${escapeHtml(art.title)}
                        </a>
                    </h4>
                    <p class="article-snippet">${escapeHtml(art.snippet || art.summary || "")}</p>
                </div>
                <div class="article-footer">
                    <span class="polarity-tag ${polarityClass}">${polarityText}</span>
                    <span style="color:var(--text-muted);font-weight:600;">Relevance: ${Math.round(art.relevance_score * 100)}%</span>
                </div>
            `;
            articlesGrid.appendChild(card);
        });
    }

    // Filter pills
    filterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            filterPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            activeFilter = pill.getAttribute("data-filter");
            renderArticles(currentArticles);
        });
    });

    // -------------------------------------------------------------
    // 7. MODALS - SOURCES & HISTORY
    // -------------------------------------------------------------
    sourcesBtn.addEventListener("click", async () => {
        sourcesModal.classList.remove("hidden");
        sourcesListContainer.innerHTML = `<div style="text-align:center;padding:1rem;">Loading sources...</div>`;

        try {
            const resp = await fetch(`${API_BASE}/api/sources`);
            const sources = await resp.json();
            renderSourcesList(sources);
        } catch (err) {
            sourcesListContainer.innerHTML = `<div style="color:red;padding:1rem;">Failed to connect to backend server. Make sure http://localhost:8000 is active.</div>`;
        }
    });

    closeSourcesModal.addEventListener("click", () => sourcesModal.classList.add("hidden"));

    function renderSourcesList(sources) {
        sourcesListContainer.innerHTML = "";
        sources.forEach(s => {
            const item = document.createElement("div");
            item.className = "source-item";
            item.innerHTML = `
                <div class="source-info">
                    <span class="source-name">${escapeHtml(s.name)}</span>
                    <span class="source-domain">${escapeHtml(s.domain)} • ${s.languages.join(", ")} • Priority: ${s.priority}</span>
                </div>
                <label style="display:flex;align-items:center;gap:0.4rem;cursor:pointer;">
                    <input type="checkbox" ${s.enabled ? "checked" : ""} data-id="${s.id}" class="source-toggle-cb">
                    <span style="font-size:0.8rem;font-weight:600;">${s.enabled ? "Enabled" : "Disabled"}</span>
                </label>
            `;

            item.querySelector(".source-toggle-cb").addEventListener("change", async (e) => {
                const checked = e.target.checked;
                await fetch(`${API_BASE}/api/sources/${s.id}/toggle`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ enabled: checked })
                });
            });

            sourcesListContainer.appendChild(item);
        });
    }

    historyBtn.addEventListener("click", async () => {
        historyModal.classList.remove("hidden");
        historyListContainer.innerHTML = `<div style="text-align:center;padding:1rem;">Loading history...</div>`;

        try {
            const resp = await fetch(`${API_BASE}/api/history`);
            const history = await resp.json();
            renderHistoryList(history);
        } catch (err) {
            historyListContainer.innerHTML = `<div style="color:red;padding:1rem;">Failed to load history from backend server.</div>`;
        }
    });

    closeHistoryModal.addEventListener("click", () => historyModal.classList.add("hidden"));

    function renderHistoryList(items) {
        historyListContainer.innerHTML = "";
        if (!items || items.length === 0) {
            historyListContainer.innerHTML = `<div style="text-align:center;color:var(--text-muted);padding:2rem;">No verifications in history yet.</div>`;
            return;
        }

        items.forEach(h => {
            const item = document.createElement("div");
            item.className = "history-item";
            const dateStr = new Date(h.created_at).toLocaleString();

            let verdictColor = "var(--color-unverified)";
            if (h.verdict === "TRUE") verdictColor = "var(--color-true)";
            if (h.verdict === "FALSE") verdictColor = "var(--color-false)";
            if (h.verdict === "MISLEADING") verdictColor = "var(--color-misleading)";

            item.innerHTML = `
                <div>
                    <div class="history-claim">"${escapeHtml(h.claim)}"</div>
                    <div class="history-meta">${dateStr} • ${h.language.toUpperCase()} • Confidence: ${h.confidence_display || Math.round(h.confidence * 100) + '%'}</div>
                </div>
                <div style="display:flex;align-items:center;gap:0.75rem;">
                    <span style="font-weight:800;color:${verdictColor};font-size:0.85rem;">${h.verdict_display || h.verdict}</span>
                    <button class="btn-ghost btn-sm btn-delete-history" title="Delete">🗑️</button>
                </div>
            `;

            item.querySelector(".history-claim").addEventListener("click", () => {
                historyModal.classList.add("hidden");
                renderResults(h);
            });

            item.querySelector(".btn-delete-history").addEventListener("click", async (e) => {
                e.stopPropagation();
                await fetch(`${API_BASE}/api/history/${h.id}`, { method: "DELETE" });
                item.remove();
            });

            historyListContainer.appendChild(item);
        });
    }

    clearHistoryBtn.addEventListener("click", async () => {
        if (confirm("Are you sure you want to clear all verification history?")) {
            await fetch(`${API_BASE}/api/history`, { method: "DELETE" });
            historyListContainer.innerHTML = `<div style="text-align:center;color:var(--text-muted);padding:2rem;">History cleared.</div>`;
        }
    });

    // Share & Print
    shareBtn.addEventListener("click", () => {
        if (navigator.share && currentResult) {
            navigator.share({
                title: "News Verification Report",
                text: `[${currentResult.verdict_display}] "${currentResult.claim}" - Fact-checked by News Truth Checker`,
                url: window.location.href
            }).catch(() => {});
        } else {
            navigator.clipboard.writeText(window.location.href);
            showToast("Verification link copied to clipboard!", "success");
        }
    });

    printBtn.addEventListener("click", () => {
        window.print();
    });

    // Helper functions
    function escapeHtml(text) {
        if (!text) return "";
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function formatMarkdown(md) {
        if (!md) return "";
        let html = escapeHtml(md);
        // Headings
        html = html.replace(/### (.*?)\n/g, '<h3>$1</h3>');
        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Bullet points
        html = html.replace(/^- (.*?)(?=\n|$)/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        // Newlines
        html = html.replace(/\n\n/g, '<br><br>');
        return html;
    }
});
