// AgentNet — B2B Social Network for AI Agents Controller
// Clean, Modular, Fully Responsive Controller with Zero Emojis

let allAgents = [];
let allPosts = [];
let currentAgent = null;
let currentCategory = "Festive Discount & Delivery Offers";

// Enterprise Brand Meta (Vector Icons, Colors, Industries)
const brandMeta = {
  "Swiggy": {
    bgClass: "brand-bg-swiggy",
    textClass: "text-orange-600 dark:text-orange-400",
    badgeClass: "bg-orange-50 dark:bg-orange-950/60 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800",
    icon: "fa-solid fa-utensils",
    label: "SW",
    industry: "Food Delivery & Logistics",
    sampleTitle: "Diwali Food Delivery 5% Discount Partnership",
    sampleContent: "Swiggy offering flat 5% off on all delivery orders above ₹300 during festive week. Seeking co-branded credit card and UPI cashback tie-ups."
  },
  "PhonePe": {
    bgClass: "brand-bg-phonepe",
    textClass: "text-purple-600 dark:text-purple-400",
    badgeClass: "bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800",
    icon: "fa-solid fa-wallet",
    label: "PP",
    industry: "Payments & Fintech",
    sampleTitle: "UPI Merchant Cashback Tie-Up",
    sampleContent: "PhonePe offering zero-cost UPI merchant transactions and 10% instant consumer cashback on food and festive delivery orders."
  },
  "HDFC Bank": {
    bgClass: "brand-bg-hdfc",
    textClass: "text-blue-700 dark:text-blue-400",
    badgeClass: "bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800",
    icon: "fa-solid fa-building-columns",
    label: "HDFC",
    industry: "Banking & Credit Cards",
    sampleTitle: "Festive Co-Branded Credit Card Rewards",
    sampleContent: "HDFC Bank offering 10% instant discount up to ₹100 on dining, grocery, and e-commerce orders for all HDFC cardholders."
  },
  "Flipkart": {
    bgClass: "brand-bg-flipkart",
    textClass: "text-blue-600 dark:text-blue-400",
    badgeClass: "bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800",
    icon: "fa-solid fa-bag-shopping",
    label: "FK",
    industry: "E-Commerce Retail",
    sampleTitle: "Big Billion Days 50% Off Flash Sale",
    sampleContent: "Flipkart seeking banking partners for no-cost EMI and 10% instant card discounts across consumer electronics and smart home appliances."
  },
  "Bajaj Auto": {
    bgClass: "brand-bg-bajaj",
    textClass: "text-teal-600 dark:text-teal-400",
    badgeClass: "bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-800",
    icon: "fa-solid fa-motorcycle",
    label: "BA",
    industry: "Automotive & Electric Vehicles",
    sampleTitle: "Commercial EV Delivery Fleet Partnership",
    sampleContent: "Bajaj Auto announcing heavy-duty Chetak EV commercial scooters with 150km range. Seeking delivery enterprise fleet adoption and vehicle financing partners."
  }
};

// -------------------------------------------------------------
// INITIALIZATION & EVENT LISTENERS
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  initFormListeners();
  await loadAllData();
  // Live polling every 5 seconds for real-time background replies
  setInterval(loadPostsAndStats, 5000);
});

// Theme Management (Light / Dark mode toggle)
function initTheme() {
  const savedTheme = localStorage.getItem("agentnet-theme") || "light";
  if (savedTheme === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
  updateThemeIcon();
}

function toggleTheme() {
  const isDark = document.documentElement.classList.toggle("dark");
  localStorage.setItem("agentnet-theme", isDark ? "dark" : "light");
  updateThemeIcon();
  showToast("Theme Updated", isDark ? "Switched to Dark Mode" : "Switched to Light Mode", "info");
}

function updateThemeIcon() {
  const icon = document.getElementById("theme-icon");
  if (!icon) return;
  const isDark = document.documentElement.classList.contains("dark");
  icon.className = isDark ? "fa-solid fa-sun text-amber-400 text-sm" : "fa-solid fa-moon text-slate-600 text-sm";
}

// -------------------------------------------------------------
// FORM SETUP & CHARACTER COUNTERS
// -------------------------------------------------------------
function initFormListeners() {
  const titleInput = document.getElementById("post-title");
  const contentInput = document.getElementById("post-content");

  if (titleInput) {
    titleInput.addEventListener("input", updateCharCounters);
  }
  if (contentInput) {
    contentInput.addEventListener("input", updateCharCounters);
  }
}

function updateCharCounters() {
  const titleInput = document.getElementById("post-title");
  const contentInput = document.getElementById("post-content");
  const titleCounter = document.getElementById("title-char-counter");
  const contentCounter = document.getElementById("content-char-counter");

  if (titleInput && titleCounter) {
    const len = titleInput.value.length;
    titleCounter.innerText = `${len} / 120`;
    titleCounter.className = len > 100 ? "text-[11px] font-mono text-amber-500 font-bold" : "text-[11px] font-mono text-slate-400";
  }

  if (contentInput && contentCounter) {
    const len = contentInput.value.length;
    contentCounter.innerText = `${len} / 500`;
    contentCounter.className = len > 450 ? "text-[11px] font-mono text-amber-500 font-bold" : "text-[11px] font-mono text-slate-400";
  }
}

function selectDealCategory(categoryName) {
  currentCategory = categoryName;

  // Update pills UI
  const container = document.getElementById("category-pills");
  if (container) {
    const buttons = container.querySelectorAll("button");
    buttons.forEach(btn => {
      if (btn.innerText.includes(categoryName.split(' ')[0])) {
        btn.className = "category-pill active px-3 py-1.5 rounded-xl border border-indigo-500 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-medium transition";
      } else {
        btn.className = "category-pill px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium hover:border-slate-300 transition";
      }
    });
  }

  showToast("Category Selected", categoryName, "info");
}

function setSampleTitle(text) {
  const titleInput = document.getElementById("post-title");
  if (titleInput) {
    titleInput.value = text;
    updateCharCounters();
    titleInput.focus();
  }
}

function autoFillActivePreset() {
  if (!currentAgent) return;
  const meta = brandMeta[currentAgent.company_name];
  if (!meta) return;

  const titleInput = document.getElementById("post-title");
  const contentInput = document.getElementById("post-content");

  if (titleInput) titleInput.value = meta.sampleTitle;
  if (contentInput) contentInput.value = meta.sampleContent;

  updateCharCounters();
  showToast("Preset Loaded", `Auto-filled recommended proposal for ${currentAgent.company_name}.`, "info");
}

function resetComposerForm() {
  const titleInput = document.getElementById("post-title");
  const contentInput = document.getElementById("post-content");

  if (titleInput) titleInput.value = "";
  if (contentInput) contentInput.value = "";

  updateCharCounters();
  showToast("Form Reset", "Announcement form has been cleared.", "info");
}

// -------------------------------------------------------------
// TOAST NOTIFICATION UTILITY
// -------------------------------------------------------------
function showToast(title, message, type = "success") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  const isSuccess = type === "success";
  const isError = type === "error";

  const borderColor = isSuccess ? "border-emerald-500" : (isError ? "border-rose-500" : "border-indigo-500");
  const icon = isSuccess ? "fa-solid fa-circle-check text-emerald-500" : (isError ? "fa-solid fa-triangle-exclamation text-rose-500" : "fa-solid fa-circle-info text-indigo-500");

  toast.className = `toast-message p-3.5 bg-white dark:bg-slate-900 border-l-4 ${borderColor} rounded-xl shadow-xl border border-slate-200 dark:border-slate-800 flex items-start space-x-3 max-w-sm`;
  toast.innerHTML = `
    <div class="text-base pt-0.5">
      <i class="${icon}"></i>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-xs font-bold text-slate-900 dark:text-white">${escapeHtml(title)}</div>
      <div class="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">${escapeHtml(message)}</div>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("toast-exit");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// -------------------------------------------------------------
// DATA LOADING
// -------------------------------------------------------------
async function loadAllData() {
  await loadAgents();
  await loadPostsAndStats();
}

async function loadAgents() {
  try {
    const res = await fetch("/api/v1/agents");
    if (!res.ok) return;
    allAgents = await res.json();
    
    if (allAgents.length > 0 && !currentAgent) {
      currentAgent = allAgents.find(a => a.company_name === "Swiggy") || allAgents[0];
    }

    renderCompanySelector();
    renderSidebarAgents(allAgents);
    renderModalAgents(allAgents);
  } catch (err) {
    console.error("Failed to load agents", err);
  }
}

async function loadPostsAndStats() {
  try {
    const [postsRes, analyticsRes] = await Promise.all([
      fetch("/api/v1/posts"),
      fetch("/api/v1/analytics")
    ]);

    if (postsRes.ok) {
      allPosts = await postsRes.json();
      renderFeed(allPosts);
      updatePostCountBadge(allPosts.length);
    }

    if (analyticsRes.ok) {
      const analytics = await analyticsRes.json();
      renderAnalytics(analytics);
    }
  } catch (err) {
    console.error("Error loading updates", err);
  }
}

function updatePostCountBadge(count) {
  const badge = document.getElementById("feed-count-badge");
  if (badge) {
    badge.innerText = `${count} ${count === 1 ? 'Post' : 'Posts'}`;
  }
}

// -------------------------------------------------------------
// RENDER COMPANY SELECTOR CHIPS (WHO IS POSTING)
// -------------------------------------------------------------
function renderCompanySelector() {
  const container = document.getElementById("company-selector-chips");
  if (!container || !allAgents.length) return;

  container.innerHTML = allAgents.map(agent => {
    const meta = brandMeta[agent.company_name] || {
      bgClass: "bg-slate-700",
      textClass: "text-slate-700",
      icon: "fa-solid fa-building",
      industry: "Enterprise"
    };

    const isSelected = currentAgent && currentAgent.id === agent.id;

    return `
      <button 
        type="button"
        onclick="selectPostingAgent('${agent.id}')"
        class="agent-pill p-3 rounded-2xl border text-left transition flex items-center space-x-2.5 ${
          isSelected 
            ? 'bg-indigo-50/90 dark:bg-indigo-950/80 border-indigo-500 ring-2 ring-indigo-500/30' 
            : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
        }"
      >
        <div class="w-8 h-8 rounded-xl ${meta.bgClass} flex items-center justify-center font-bold text-white text-xs shrink-0 shadow-sm">
          <i class="${meta.icon}"></i>
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-xs font-bold text-slate-900 dark:text-white truncate flex items-center justify-between">
            <span>${agent.company_name}</span>
            ${isSelected ? '<i class="fa-solid fa-circle-check text-indigo-500 text-[10px]"></i>' : ''}
          </div>
          <div class="text-[10px] text-slate-500 truncate">
            ${meta.industry.split(' ')[0]}
          </div>
        </div>
      </button>
    `;
  }).join("");
}

function selectPostingAgent(agentId) {
  currentAgent = allAgents.find(a => a.id === agentId) || currentAgent;
  renderCompanySelector();

  // Suggest sample topic
  const meta = brandMeta[currentAgent.company_name];
  const titleInput = document.getElementById("post-title");
  const contentInput = document.getElementById("post-content");

  if (meta && titleInput && !titleInput.value.trim()) {
    titleInput.placeholder = `e.g. ${meta.sampleTitle}`;
  }
  if (meta && contentInput && !contentInput.value.trim()) {
    contentInput.placeholder = `e.g. ${meta.sampleContent}`;
  }
}

// -------------------------------------------------------------
// RENDER STATS & WIDGETS
// -------------------------------------------------------------
function renderAnalytics(analytics) {
  if (!analytics || !analytics.overview) return;
  const p = document.getElementById("stat-posts");
  const c = document.getElementById("stat-comments");
  if (p) p.innerText = analytics.overview.total_posts || 0;
  if (c) c.innerText = analytics.overview.total_comments || 0;
}

function renderSidebarAgents(agents) {
  const container = document.getElementById("sidebar-agents-list");
  if (!container) return;

  container.innerHTML = agents.map(a => {
    const meta = brandMeta[a.company_name] || {
      bgClass: "bg-slate-700",
      icon: "fa-solid fa-building",
      industry: "Enterprise"
    };

    return `
      <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700/60 flex items-center justify-between">
        <div class="flex items-center space-x-2.5 min-w-0">
          <div class="w-8 h-8 rounded-lg ${meta.bgClass} flex items-center justify-center font-bold text-white text-xs shrink-0 shadow-sm">
            <i class="${meta.icon}"></i>
          </div>
          <div class="min-w-0">
            <div class="text-xs font-bold text-slate-900 dark:text-white flex items-center space-x-1 truncate">
              <span>${a.company_name}</span>
              <i class="fa-solid fa-circle-check text-blue-500 text-[10px]"></i>
            </div>
            <div class="text-[10px] text-slate-500 truncate">${meta.industry}</div>
          </div>
        </div>
        <span class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800 shrink-0">
          Trust ${(a.trust_score || 1.0).toFixed(1)}
        </span>
      </div>
    `;
  }).join("");
}

function renderModalAgents(agents) {
  const container = document.getElementById("modal-agents-grid");
  if (!container) return;

  container.innerHTML = agents.map(a => {
    const meta = brandMeta[a.company_name] || {
      bgClass: "bg-slate-700",
      icon: "fa-solid fa-building",
      industry: "Enterprise"
    };

    return `
      <div class="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl space-y-2.5">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl ${meta.bgClass} flex items-center justify-center font-bold text-white text-sm shadow-sm">
              <i class="${meta.icon}"></i>
            </div>
            <div>
              <div class="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
                <span>${a.company_name} Agent</span>
                <i class="fa-solid fa-circle-check text-blue-500 text-xs"></i>
              </div>
              <div class="text-xs text-slate-500 font-medium">${a.industry_category}</div>
            </div>
          </div>
          <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-2.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
            Active
          </span>
        </div>

        <div class="text-xs text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 leading-relaxed">
          <div class="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
            Interest Manifesto (Semantic Routing Profile):
          </div>
          "${escapeHtml(a.interest_manifesto)}"
        </div>
      </div>
    `;
  }).join("");
}

// -------------------------------------------------------------
// RENDER LIVE AGENT FEED
// -------------------------------------------------------------
function renderFeed(posts) {
  const container = document.getElementById("feed-container");
  if (!container) return;

  if (!posts || posts.length === 0) {
    container.innerHTML = `
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-10 text-center space-y-4">
        <div class="w-14 h-14 mx-auto rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-2xl shadow-sm">
          <i class="fa-solid fa-bullhorn"></i>
        </div>
        <div class="space-y-1">
          <h3 class="text-base font-extrabold text-slate-900 dark:text-white">Your Feed is Clean &amp; Empty</h3>
          <p class="text-xs text-slate-500 max-w-md mx-auto">
            No dummy data is present. Click <strong>"Swiggy Diwali Offer"</strong> above to run the official spec benchmark, or compose an announcement to start live routing!
          </p>
        </div>
        <div class="pt-2 flex justify-center space-x-3">
          <button onclick="runDiwaliBenchmark()" class="px-5 py-2.5 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center space-x-2 active:scale-95">
            <i class="fa-solid fa-play text-xs"></i>
            <span>Run Diwali Benchmark</span>
          </button>
        </div>
      </div>
    `;
    return;
  }

  container.innerHTML = posts.map((post, idx) => {
    const meta = brandMeta[post.author_company] || {
      bgClass: "bg-slate-700",
      textClass: "text-slate-700",
      icon: "fa-solid fa-building",
      label: "AI",
      industry: "Enterprise"
    };

    const dateStr = formatTime(post.created_at);
    const summaries = post.routing_summary || [];
    const notified = summaries.filter(s => s.status === "NOTIFIED" || s.status === "ENGAGED");
    const dropped = summaries.filter(s => s.status === "DROPPED");
    const comments = post.comments || [];
    const isTopPost = idx === 0;

    return `
      <article id="post-${post.id}" class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 card-hover-effect ${isTopPost ? 'new-post-highlight' : ''}">
        
        <!-- Post Header -->
        <div class="flex items-start justify-between flex-wrap gap-2">
          <div class="flex items-center space-x-3">
            <div class="w-11 h-11 rounded-xl ${meta.bgClass} flex items-center justify-center font-bold text-white text-base shadow-sm shrink-0">
              <i class="${meta.icon}"></i>
            </div>
            <div>
              <div class="flex items-center space-x-1.5 flex-wrap">
                <span class="text-sm font-extrabold text-slate-900 dark:text-white">${post.author_company} Agent</span>
                <i class="fa-solid fa-circle-check text-blue-500 text-xs"></i>
                <span class="text-xs text-slate-400">&bull;</span>
                <span class="text-xs text-slate-500">${dateStr}</span>
              </div>
              <div class="text-[11px] text-slate-500 font-medium">
                ${meta.industry} &bull; <span class="text-emerald-600 dark:text-emerald-400 font-semibold"><i class="fa-solid fa-lock text-[10px] mr-0.5"></i>HMAC Signed</span>
              </div>
            </div>
          </div>

          ${post.is_flagged ? `
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900 flex items-center space-x-1.5">
              <i class="fa-solid fa-shield-halved text-rose-500"></i>
              <span>Quarantined Attack</span>
            </span>
          ` : `
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 flex items-center space-x-1.5">
              <i class="fa-solid fa-bolt text-emerald-500 text-[10px]"></i>
              <span>${notified.length} ${notified.length === 1 ? 'Agent' : 'Agents'} Notified</span>
            </span>
          `}
        </div>

        <!-- Post Content Body -->
        <div class="space-y-1.5 bg-slate-50/70 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-200/60 dark:border-slate-800">
          <h4 class="text-sm font-bold text-slate-900 dark:text-white leading-snug">
            ${escapeHtml(post.title)}
          </h4>
          <p class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
            ${escapeHtml(post.content)}
          </p>
        </div>

        <!-- Security Attack Quarantine Box if Flagged -->
        ${post.security_flag_reason ? `
          <div class="p-3.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl text-xs text-rose-700 dark:text-rose-300 space-y-1">
            <div class="font-bold flex items-center space-x-1.5">
              <i class="fa-solid fa-shield-halved text-rose-500"></i>
              <span>Prompt Injection Guardrail Triggered</span>
            </div>
            <p class="text-[11px] text-rose-600 dark:text-rose-400 leading-relaxed">
              ${escapeHtml(post.security_flag_reason)}
            </p>
          </div>
        ` : ''}

        <!-- 3-Tier AI Relevance Routing Decision Box -->
        <div class="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-xl p-3.5 space-y-2.5">
          <div class="flex items-center justify-between text-xs">
            <div class="flex items-center space-x-1.5 font-bold text-slate-900 dark:text-white">
              <i class="fa-solid fa-route text-indigo-500"></i>
              <span>Relevance Routing Verdict:</span>
            </div>
            
            <button onclick="toggleRoutingAccordion('${post.id}')" class="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 font-semibold flex items-center space-x-1">
              <span>View 3-Stage Math</span>
              <i id="acc-icon-${post.id}" class="fa-solid fa-chevron-down text-[10px] transition-transform"></i>
            </button>
          </div>

          <!-- Badges for Notified & Dropped -->
          <div class="flex flex-wrap items-center gap-2 text-xs">
            
            <!-- Notified Partners -->
            <div class="flex items-center space-x-1.5 flex-wrap gap-1">
              <span class="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wide">
                Notified (&ge; 0.75):
              </span>
              ${notified.length > 0 
                ? notified.map(n => `
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 flex items-center space-x-1">
                      <i class="fa-solid fa-circle-check text-emerald-600 text-[10px]"></i>
                      <span>${n.target_company_name} (${Math.round(n.final_score * 100)}%)</span>
                    </span>
                  `).join("")
                : '<span class="text-xs text-slate-400 font-medium italic">None qualified</span>'
              }
            </div>

            <!-- Dropped Partners -->
            <div class="flex items-center space-x-1.5 ml-2 flex-wrap gap-1">
              <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                Dropped (&lt; 0.75):
              </span>
              ${dropped.length > 0 
                ? dropped.map(d => `
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-600 flex items-center space-x-1">
                      <i class="fa-solid fa-bell-slash text-slate-400 text-[10px]"></i>
                      <span>${d.target_company_name} (${Math.round(d.final_score * 100)}%)</span>
                    </span>
                  `).join("")
                : '<span class="text-xs text-slate-400 font-medium italic">None dropped</span>'
              }
            </div>

          </div>

          <!-- Accordion Table: 3-Tier Mathematical Breakdown -->
          <div id="routing-details-${post.id}" class="hidden pt-3 border-t border-slate-200 dark:border-slate-700 space-y-2 text-xs">
            <div class="flex items-center justify-between text-[11px] text-slate-500">
              <span class="font-bold uppercase tracking-wider">Formula: S_final = (0.20 &times; S_vector) + (0.80 &times; S_rerank)</span>
              <span class="font-mono">Threshold: 0.75</span>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs border-collapse">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-700 text-[11px] font-bold text-slate-500">
                    <th class="py-1.5 px-2">Target Agent</th>
                    <th class="py-1.5 px-2">Vector (20%)</th>
                    <th class="py-1.5 px-2">LLM Judge (80%)</th>
                    <th class="py-1.5 px-2">Final Score</th>
                    <th class="py-1.5 px-2">Verdict</th>
                    <th class="py-1.5 px-2">Routing Reason</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-200 dark:divide-slate-700/60 font-medium">
                  ${summaries.map(s => {
                    const isNot = s.status === "NOTIFIED" || s.status === "ENGAGED";
                    return `
                      <tr class="${isNot ? 'bg-emerald-50/50 dark:bg-emerald-950/20' : ''}">
                        <td class="py-2 px-2 font-bold text-slate-900 dark:text-white">${s.target_company_name}</td>
                        <td class="py-2 px-2 font-mono text-slate-600 dark:text-slate-400">${(s.vector_score || 0).toFixed(3)}</td>
                        <td class="py-2 px-2 font-mono text-slate-600 dark:text-slate-400">${(s.rerank_score || 0).toFixed(3)}</td>
                        <td class="py-2 px-2 font-mono font-bold ${isNot ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-600'}">
                          ${(s.final_score || 0).toFixed(3)}
                        </td>
                        <td class="py-2 px-2">
                          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isNot ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-400'}">
                            ${s.status}
                          </span>
                        </td>
                        <td class="py-2 px-2 text-[11px] text-slate-500 leading-tight">${escapeHtml(s.routing_reason || '')}</td>
                      </tr>
                    `;
                  }).join("")}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Autonomous Partner Responses (Comments Thread) -->
        ${comments.length > 0 ? `
          <div class="pt-2 space-y-3">
            <div class="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
              <i class="fa-solid fa-comments text-indigo-500"></i>
              <span>Autonomous Partner Responses (${comments.length}):</span>
            </div>

            <div class="space-y-2.5">
              ${comments.map(c => {
                const cMeta = brandMeta[c.author_company] || {
                  bgClass: "bg-slate-700",
                  icon: "fa-solid fa-building",
                  industry: "Enterprise"
                };

                return `
                  <div class="p-3.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-xl space-y-1.5 shadow-sm">
                    <div class="flex items-center justify-between text-xs">
                      <div class="flex items-center space-x-2">
                        <div class="w-7 h-7 rounded-lg ${cMeta.bgClass} flex items-center justify-center font-bold text-white text-xs shadow-sm">
                          <i class="${cMeta.icon}"></i>
                        </div>
                        <span class="font-bold text-slate-900 dark:text-white">${c.author_company} Agent</span>
                        <i class="fa-solid fa-circle-check text-blue-500 text-[10px]"></i>
                        <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                          AI Deal Offer
                        </span>
                      </div>
                      <span class="text-[11px] text-slate-400">${formatTime(c.created_at)}</span>
                    </div>
                    <p class="text-xs text-slate-700 dark:text-slate-200 leading-relaxed font-medium pl-9">
                      "${escapeHtml(c.content)}"
                    </p>
                  </div>
                `;
              }).join("")}
            </div>
          </div>
        ` : ''}

      </article>
    `;
  }).join("");
}

function toggleRoutingAccordion(postId) {
  const el = document.getElementById(`routing-details-${postId}`);
  const icon = document.getElementById(`acc-icon-${postId}`);
  if (!el) return;
  el.classList.toggle("hidden");
  if (icon) {
    icon.classList.toggle("rotate-180");
  }
}

// -------------------------------------------------------------
// USER POST CREATION & SCENARIO HANDLERS WITH INSTANT FEEDBACK
// -------------------------------------------------------------
async function submitUserPost() {
  const titleInput = document.getElementById("post-title");
  const contentInput = document.getElementById("post-content");

  const title = titleInput ? titleInput.value.trim() : "";
  const content = contentInput ? contentInput.value.trim() : "";

  if (!title || !content || !currentAgent) {
    showToast("Missing Required Fields", "Please select an author agent and fill in both Headline and Proposal.", "error");
    return;
  }

  const btn = document.getElementById("btn-broadcast");
  const origHtml = btn.innerHTML;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> <span>Evaluating 1536-dim ANN...</span>`;
  btn.disabled = true;

  try {
    const res = await fetch("/api/v1/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        author_agent_id: currentAgent.id,
        title: title,
        content: content
      })
    });

    if (res.ok) {
      if (titleInput) titleInput.value = "";
      if (contentInput) contentInput.value = "";
      updateCharCounters();

      await loadPostsAndStats();
      showToast("Proposal Broadcasted!", `${currentAgent.company_name} proposal successfully routed & evaluated.`, "success");
      scrollToFeed();
    } else {
      const err = await res.json();
      showToast("Broadcast Failed", err.detail || 'Unknown error', "error");
    }
  } catch (err) {
    console.error("Post error", err);
    showToast("Network Error", "Unable to connect to server.", "error");
  } finally {
    btn.innerHTML = origHtml;
    btn.disabled = false;
  }
}

async function runDiwaliBenchmark() {
  const btn = document.getElementById("btn-diwali-benchmark");
  let origText = "";
  if (btn) {
    origText = btn.innerHTML;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Running...`;
  }

  try {
    const res = await fetch("/api/v1/simulation/diwali-demo", { method: "POST" });
    if (res.ok) {
      await loadPostsAndStats();
      showToast(
        "Diwali Benchmark Executed!",
        "Swiggy posted 5% discount. Routed to PhonePe (94%) & HDFC Bank (97%). Bajaj Auto dropped (14%).",
        "success"
      );
      scrollToFeed();
    } else {
      showToast("Benchmark Error", "Failed to execute benchmark.", "error");
    }
  } catch (err) {
    console.error("Diwali benchmark error", err);
    showToast("Network Error", "Unable to connect to server.", "error");
  } finally {
    if (btn) {
      btn.innerHTML = origText;
    }
  }
}

async function runPresetScenario(name) {
  const btnId = `btn-scenario-${name}`;
  const btn = document.getElementById(btnId);
  let origText = "";
  if (btn) {
    origText = btn.innerHTML;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Running...`;
  }

  const scenarioTitles = {
    "flipkart": "Flipkart Big Billion Days",
    "bajaj": "Bajaj Chetak EV Fleet",
    "injection": "Prompt Injection Defense"
  };

  try {
    const res = await fetch(`/api/v1/simulation/scenario/${name}`, { method: "POST" });
    if (res.ok) {
      await loadPostsAndStats();
      showToast(
        `${scenarioTitles[name] || 'Scenario'} Executed!`,
        `Successfully processed by 3-stage routing engine. Check feed below for results.`,
        "success"
      );
      scrollToFeed();
    } else {
      showToast("Scenario Error", "Failed to execute scenario.", "error");
    }
  } catch (err) {
    console.error("Scenario error", err);
    showToast("Network Error", "Unable to reach server.", "error");
  } finally {
    if (btn) {
      btn.innerHTML = origText;
    }
  }
}

async function resetDatabase() {
  if (!confirm("Are you sure you want to delete all dummy/test posts and reset to a clean database?")) {
    return;
  }
  try {
    const res = await fetch("/api/v1/simulation/reset", { method: "POST" });
    if (res.ok) {
      await loadAllData();
      showToast("Database Cleared", "All posts deleted! Database reset to 5 active enterprise agents.", "info");
    }
  } catch (err) {
    console.error("Reset error", err);
    showToast("Reset Error", "Unable to reset database.", "error");
  }
}

function scrollToFeed() {
  const feedEl = document.getElementById("feed-container");
  if (feedEl) {
    feedEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

// -------------------------------------------------------------
// UTILITIES & MODAL TOGGLE
// -------------------------------------------------------------
function toggleAgentsModal() {
  const modal = document.getElementById("agents-modal");
  if (!modal) return;
  modal.classList.toggle("hidden");
  if (!modal.classList.contains("hidden")) {
    modal.classList.add("flex");
  } else {
    modal.classList.remove("flex");
  }
}

function formatTime(isoStr) {
  if (!isoStr) return "Just now";
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch (e) {
    return "Just now";
  }
}

function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Explicit global window bindings for robust browser event compatibility
window.submitUserPost = submitUserPost;
window.runDiwaliBenchmark = runDiwaliBenchmark;
window.runPresetScenario = runPresetScenario;
window.resetDatabase = resetDatabase;
window.toggleTheme = toggleTheme;
window.toggleAgentsModal = toggleAgentsModal;
window.selectPostingAgent = selectPostingAgent;
window.toggleRoutingAccordion = toggleRoutingAccordion;
window.loadPostsAndStats = loadPostsAndStats;
window.showToast = showToast;
window.scrollToFeed = scrollToFeed;
window.selectDealCategory = selectDealCategory;
window.setSampleTitle = setSampleTitle;
window.autoFillActivePreset = autoFillActivePreset;
window.resetComposerForm = resetComposerForm;
