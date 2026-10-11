// Shared Progress and XP tracking helper

window.userProgress = {
  xp: 0,
  level: 1,
  streak: 0,
  completedTopics: [],
  completedChallenges: [],
  unlockedBadges: [],
  speechEnabled: true
};

// Initial sync on script load
document.addEventListener("DOMContentLoaded", () => {
  initGlobalProgress();
});

async function initGlobalProgress() {
  // Sync voice preference from localStorage (default to true)
  const speechPref = localStorage.getItem("nex_speech_enabled");
  window.userProgress.speechEnabled = speechPref !== "false";
  updateSpeechToggleButton();

  // Load stats from server
  await syncProgressWithServer();

  // Bind toggle click
  const speechBtn = document.getElementById("speech-toggle");
  if (speechBtn) {
    speechBtn.addEventListener("click", () => {
      window.userProgress.speechEnabled = !window.userProgress.speechEnabled;
      localStorage.setItem("nex_speech_enabled", window.userProgress.speechEnabled);
      updateSpeechToggleButton();
      
      // Stop speaking immediately if disabled
      if (!window.userProgress.speechEnabled && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    });
  }
}

async function syncProgressWithServer() {
  try {
    const res = await fetch("/api/progress");
    if (res.ok) {
      const data = await res.json();
      window.userProgress = { ...window.userProgress, ...data };
      updateHeaderUI();
    }
  } catch (err) {
    console.error("Error syncing progress data with server:", err);
  }
}

function updateHeaderUI() {
  const xpSpan = document.getElementById("header-xp");
  const levelSpan = document.getElementById("header-level");
  
  if (xpSpan) xpSpan.textContent = window.userProgress.xp;
  if (levelSpan) levelSpan.textContent = window.userProgress.level;
}

function updateSpeechToggleButton() {
  const btn = document.getElementById("speech-toggle");
  if (btn) {
    btn.textContent = window.userProgress.speechEnabled ? "🔊" : "🔇";
    btn.title = window.userProgress.speechEnabled ? "Mute Voice Speech" : "Enable Voice Speech";
    if (window.userProgress.speechEnabled) {
      btn.style.borderColor = "var(--neon-blue)";
      btn.style.boxShadow = "var(--glow-blue)";
    } else {
      btn.style.borderColor = "var(--border-glow)";
      btn.style.boxShadow = "none";
    }
  }
}

// Global XP award helper
async function addXP(amount) {
  try {
    const res = await fetch("/api/progress/add-xp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount })
    });
    if (res.ok) {
      const data = await res.json();
      window.userProgress = { ...window.userProgress, ...data.progress };
      updateHeaderUI();
      if (data.leveledUp) {
        showLevelUpNotification(window.userProgress.level);
      }
      return data;
    }
  } catch (err) {
    console.error("Error awarding XP:", err);
  }
}

// Global completion helper
async function completeTopic(topicId) {
  try {
    const res = await fetch("/api/progress/complete-topic", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topicId })
    });
    if (res.ok) {
      const data = await res.json();
      window.userProgress = { ...window.userProgress, ...data.progress };
      updateHeaderUI();
      if (data.leveledUp) {
        showLevelUpNotification(window.userProgress.level);
      }
      return data;
    }
  } catch (err) {
    console.error("Error completing topic:", err);
  }
}

// Visual Level up feedback
function showLevelUpNotification(lvl) {
  const notif = document.createElement("div");
  notif.style.position = "fixed";
  notif.style.bottom = "20px";
  notif.style.right = "20px";
  notif.style.background = "var(--bg-space-dark)";
  notif.style.border = "2px solid var(--neon-green)";
  notif.style.boxShadow = "var(--glow-green)";
  notif.style.color = "#fff";
  notif.style.padding = "1rem 2rem";
  notif.style.borderRadius = "10px";
  notif.style.zIndex = "1000";
  notif.style.fontFamily = "var(--font-tech)";
  notif.style.animation = "slideIn 0.5s ease-out";
  
  notif.innerHTML = `🚀 LEVEL UP! You reached Level <strong>${lvl}</strong> 🎉`;
  
  document.body.appendChild(notif);
  
  // Audio chime (synth)
  if (window.AudioContext || window.webkitAudioContext) {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = "sine";
      
      osc.frequency.setValueAtTime(440, ctx.currentTime); // A4
      osc.frequency.setValueAtTime(880, ctx.currentTime + 0.15); // A5
      
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      
      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch(e){}
  }

  setTimeout(() => {
    notif.style.animation = "fadeOut 0.5s ease-in";
    setTimeout(() => notif.remove(), 500);
  }, 4000);
}
