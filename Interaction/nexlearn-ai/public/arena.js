// Code Arena Frontend controller
let challenges = [];
let activeChallenge = null;
let currentMode = "practice"; // practice, speed, daily
let speedTimer = null;
let timeRemaining = 900; // 15 mins in seconds
let failedAttempts = {}; // challengeId -> count
let recognition = null;
let editor = null;
let typeInterval = null;

document.addEventListener("DOMContentLoaded", () => {
  initArena();
});

async function initArena() {
  // Initialize CodeMirror editor
  const codeTextarea = document.getElementById("editor-code");
  if (codeTextarea) {
    editor = CodeMirror.fromTextArea(codeTextarea, {
      lineNumbers: true,
      theme: "dracula",
      mode: "javascript",
      lineWrapping: true,
      tabSize: 2
    });
    
    // Auto save draft to localStorage
    editor.on("change", () => {
      if (activeChallenge) {
        const lang = document.getElementById("language-select").value;
        localStorage.setItem(`editor_code_${activeChallenge.id}_${lang}`, editor.getValue());
      }
    });
  }

  // Load challenges from server
  await loadChallenges();

  // Initialize Speech Recognition
  initSpeechRecognition();

  // Event Listeners
  document.getElementById("arena-reset-btn").addEventListener("click", resetStarterCode);
  document.getElementById("arena-run-btn").addEventListener("click", submitSolution);
  document.getElementById("arena-hint-btn").addEventListener("click", buyHint);
  document.getElementById("arena-solution-btn").addEventListener("click", revealSolution);
  
  // Language Select
  document.getElementById("language-select").addEventListener("change", (e) => {
    changeLanguage(e.target.value);
  });

  // Filter Event Listeners
  document.getElementById("search-input").addEventListener("input", filterAndRenderChallenges);
  document.getElementById("category-filter").addEventListener("change", filterAndRenderChallenges);
  document.getElementById("difficulty-filter").addEventListener("change", filterAndRenderChallenges);
  document.getElementById("status-filter").addEventListener("change", filterAndRenderChallenges);
  document.getElementById("sort-filter").addEventListener("change", filterAndRenderChallenges);

  // Mode buttons
  document.getElementById("mode-practice").addEventListener("click", () => selectMode("practice"));
  document.getElementById("mode-speed").addEventListener("click", () => selectMode("speed"));
  document.getElementById("mode-daily").addEventListener("click", () => selectMode("daily"));

  // Ask Nex Overlay
  document.getElementById("ask-nex-float-btn").addEventListener("click", openNexSidebar);
  document.getElementById("ask-nex-close-btn").addEventListener("click", closeNexSidebar);
  document.getElementById("reveal-approach-btn").addEventListener("click", speakApproach);
  document.getElementById("mic-btn").addEventListener("click", toggleMic);
  
  // Doubt Input enter
  document.getElementById("doubt-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      submitDoubt(e.target.value);
    }
  });

  // Speech rate slider
  const speedSlider = document.getElementById("speech-speed");
  if (speedSlider) {
    speedSlider.addEventListener("input", (e) => {
      const displayVal = document.getElementById("speed-val");
      if (displayVal) displayVal.textContent = e.target.value + "x";
    });
  }

  // Double check voice preferences are loaded
  setTimeout(() => {
    if (window.userProgress) {
      updateHeaderUI();
      updateProgressBar();
    }
  }, 500);
}

// 1. Fetch Challenges list
async function loadChallenges() {
  try {
    const res = await fetch("/api/arena/challenges");
    if (res.ok) {
      challenges = await res.json();
      filterAndRenderChallenges();
      
      // Auto select first challenge
      if (challenges.length > 0) {
        selectChallenge(challenges[0].id);
      }
    }
  } catch (err) {
    console.error("Error fetching challenges:", err);
  }
}

// 2. Select Challenge
function selectChallenge(id) {
  activeChallenge = challenges.find(c => c.id === id);
  if (!activeChallenge) return;

  // Highlight in sidebar
  const items = document.querySelectorAll(".challenge-item");
  items.forEach(item => {
    if (item.dataset.id === id) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Render Description
  document.getElementById("challenge-title").textContent = activeChallenge.title;
  document.getElementById("challenge-difficulty").textContent = activeChallenge.difficulty;
  document.getElementById("challenge-difficulty").className = `difficulty-badge ${activeChallenge.difficulty.toLowerCase()}`;
  
  const xpVal = currentMode === "daily" ? activeChallenge.xpReward * 2 : activeChallenge.xpReward;
  document.getElementById("challenge-xp").textContent = `+${xpVal} XP`;

  const isCompleted = window.userProgress && window.userProgress.completedChallenges.includes(id);
  const status = document.getElementById("challenge-status");
  status.textContent = isCompleted ? "Solved" : "Unsolved";
  status.className = isCompleted ? "neon-text-green" : "neon-text-blue";

  document.getElementById("challenge-body").innerHTML = `
    <p style="margin-bottom:1rem;">${activeChallenge.description}</p>
    <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom: 0.5rem;">
      <strong>Category:</strong> ${activeChallenge.category.replace('_', ' ').toUpperCase()} | 
      <strong>Tags:</strong> ${activeChallenge.tags.join(', ')}
    </div>
  `;

  // Hide hints and solution
  document.getElementById("challenge-hint-box").style.display = "none";
  document.getElementById("challenge-solution-box").style.display = "none";

  // Check failed attempts to lock/unlock solution button
  const solBtn = document.getElementById("arena-solution-btn");
  if (solBtn) {
    const fails = failedAttempts[id] || 0;
    if (fails >= 3) {
      solBtn.style.display = "inline-block";
      solBtn.disabled = false;
      solBtn.textContent = "🔑 View Solution";
    } else {
      solBtn.style.display = "none";
      solBtn.disabled = true;
    }
  }

  // Load language settings & editor value
  const lang = document.getElementById("language-select").value;
  changeLanguage(lang);

  // Render original test suite (all pending)
  renderTestSuitePending();

  // Clear log
  const term = document.getElementById("terminal-output");
  term.innerHTML = `
    <div class="terminal-line info">> Loaded challenge: ${activeChallenge.title}</div>
    <div class="terminal-line">> Editor initialized. Write code and click 'Submit Code'.</div>
  `;

  // If Speed run timer is running, reset time for new problem
  if (currentMode === "speed") {
    startSpeedTimer();
  }

  // Set Nex speech bubble initial text
  const nexSpeechText = document.getElementById("nex-speech-text");
  if (nexSpeechText) {
    nexSpeechText.textContent = `Analyzing "${activeChallenge.title}". Click "Explain Approach" or ask a doubt to get started!`;
  }
}

// 3. Change Language
function changeLanguage(lang) {
  if (!activeChallenge || !editor) return;

  let modeName = "javascript";
  if (lang === "python") modeName = "python";
  if (lang === "java") modeName = "text/x-java";

  editor.setOption("mode", modeName);

  // Load from local storage draft or default starterCode
  const saved = localStorage.getItem(`editor_code_${activeChallenge.id}_${lang}`);
  if (saved !== null) {
    editor.setValue(saved);
  } else {
    const codeVal = typeof activeChallenge.starterCode === "object"
      ? (activeChallenge.starterCode[lang] || "")
      : activeChallenge.starterCode;
    editor.setValue(codeVal);
  }
}

// 4. Reset Code
function resetStarterCode() {
  if (!activeChallenge || !editor) return;
  const lang = document.getElementById("language-select").value;
  
  const codeVal = typeof activeChallenge.starterCode === "object"
    ? (activeChallenge.starterCode[lang] || "")
    : activeChallenge.starterCode;
  
  editor.setValue(codeVal);
  localStorage.removeItem(`editor_code_${activeChallenge.id}_${lang}`);

  const term = document.getElementById("terminal-output");
  const line = document.createElement("div");
  line.className = "terminal-line info";
  line.textContent = `> Code reset to ${lang.toUpperCase()} boilerplate boilerplate.`;
  term.appendChild(line);
}

// 5. Submit solution to backend sandbox
async function submitSolution() {
  if (!activeChallenge || !editor) return;

  const code = editor.getValue();
  const lang = document.getElementById("language-select").value;
  
  const term = document.getElementById("terminal-output");
  term.innerHTML = `
    <div class="terminal-line info">> Ingesting ${lang.toUpperCase()} source files...</div>
    <div class="terminal-line info">> Compiling code and executing test suite...</div>
  `;

  try {
    const res = await fetch("/api/arena/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        challengeId: activeChallenge.id,
        code,
        language: lang,
        mode: currentMode
      })
    });

    if (res.ok) {
      const data = await res.json();

      if (data.compilationError) {
        // Show compiler crash logs
        const crashLine = document.createElement("div");
        crashLine.className = "terminal-line error";
        crashLine.style.whiteSpace = "pre-wrap";
        crashLine.textContent = `> COMPILER ERROR:\n${data.compilationMessage}`;
        term.appendChild(crashLine);
        
        playChime(false);
        speakWithNex("Oh, it looks like there's a compilation error. Check the terminal logs to see what failed!");
        return;
      }

      // Update test assertions UI
      renderTestSuiteResults(data.results);

      const finalLine = document.createElement("div");
      if (data.success) {
        finalLine.className = "terminal-line success";
        finalLine.style.fontWeight = "bold";
        finalLine.textContent = `> SUCCESS! All tests passed! Reward: +${data.xpEarned} XP awarded! 🎉`;
        term.appendChild(finalLine);

        playChime(true);
        speakWithNex(`Outstanding! All assertions passed. You earned ${data.xpEarned} XP!`);

        // If Speed mode, stop timer
        if (currentMode === "speed") {
          clearInterval(speedTimer);
          document.getElementById("timer-display").textContent = "🏆 CHALLENGE SOLVED IN TIME!";
        }

        // Sync and refresh progress
        await syncProgressWithServer();
        updateProgressBar();
        
        // Refresh statuses in lists
        filterAndRenderChallenges();
        selectChallenge(activeChallenge.id);
      } else {
        finalLine.className = "terminal-line error";
        finalLine.style.fontWeight = "bold";
        finalLine.textContent = `> FAILURE. Some assertions did not match expectation.`;
        term.appendChild(finalLine);

        playChime(false);
        speakWithNex("Some assertions failed. Check the actual outputs vs expected and try adjusting your logic.");

        // Increment failed attempts
        failedAttempts[activeChallenge.id] = (failedAttempts[activeChallenge.id] || 0) + 1;
        if (failedAttempts[activeChallenge.id] >= 3) {
          const solBtn = document.getElementById("arena-solution-btn");
          if (solBtn) {
            solBtn.style.display = "inline-block";
            solBtn.disabled = false;
            solBtn.textContent = "🔑 View Solution";
          }
        }
      }
    }
  } catch (err) {
    console.error("Submission error:", err);
    const line = document.createElement("div");
    line.className = "terminal-line error";
    line.textContent = "> Execution Failed: Connection interrupted.";
    term.appendChild(line);
  }
}

// 6. Test Suite Renderers
function renderTestSuitePending() {
  const container = document.getElementById("test-suite-container");
  if (!container || !activeChallenge) return;

  container.innerHTML = "";

  activeChallenge.testCases.forEach((tc, idx) => {
    const isHidden = idx >= 3;
    const item = document.createElement("div");
    item.className = "test-case-item";
    item.id = `tc-item-${idx}`;

    if (isHidden) {
      item.innerHTML = `
        <div class="test-case-header">
          <span>🔒 Hidden Test Case ${idx + 1}</span>
          <span class="tc-status" id="tc-status-${idx}" style="color:var(--text-muted);">Locked</span>
        </div>
        <div class="test-case-io">
          <strong>Input:</strong> [Hidden Input]<br>
          <strong>Expected:</strong> [Hidden Expected]
        </div>
      `;
    } else {
      item.innerHTML = `
        <div class="test-case-header">
          <span>Test Case ${idx + 1}</span>
          <span class="tc-status" id="tc-status-${idx}" style="color:var(--text-muted);">Pending</span>
        </div>
        <div class="test-case-io">
          <strong>Input:</strong> <code>${tc.input}</code><br>
          <strong>Expected:</strong> <code>${tc.expected}</code>
          <div id="tc-actual-box-${idx}" style="display:none; margin-top:0.3rem;">
            <strong>Actual:</strong> <code id="tc-actual-${idx}">-</code>
          </div>
        </div>
      `;
    }
    container.appendChild(item);
  });
}

function renderTestSuiteResults(results) {
  results.forEach((r, idx) => {
    const item = document.getElementById(`tc-item-${idx}`);
    const status = document.getElementById(`tc-status-${idx}`);
    
    if (item && status) {
      if (r.passed) {
        item.className = "test-case-item passed";
        status.textContent = "Passed ✅";
        status.style.color = "var(--neon-green)";
      } else {
        item.className = "test-case-item failed";
        status.textContent = "Failed ❌";
        status.style.color = "var(--neon-pink)";
      }

      // If visible, reveal actual outputs
      if (idx < 3) {
        const actualBox = document.getElementById(`tc-actual-box-${idx}`);
        const actualVal = document.getElementById(`tc-actual-${idx}`);
        if (actualBox && actualVal) {
          actualBox.style.display = "block";
          actualVal.textContent = r.actual;
        }
      }
    }
  });
}

// 7. Get Hint (-10 XP)
async function buyHint() {
  if (!activeChallenge) return;

  if (currentMode === "speed") {
    alert("Hints are disabled during Speed Run challenges!");
    return;
  }

  if (window.userProgress.xp < 10) {
    alert("Insufficient XP! Hints require 10 XP.");
    return;
  }

  // Confirm buy
  if (!confirm("Unlock hint for 10 XP?")) return;

  await addXP(-10);

  const hintBox = document.getElementById("challenge-hint-box");
  hintBox.style.display = "block";
  hintBox.innerHTML = `💡 <strong>Hint unlocked:</strong> ${activeChallenge.hint}`;

  const term = document.getElementById("terminal-output");
  const line = document.createElement("div");
  line.className = "terminal-line info";
  line.textContent = `> Hint unlocked. 10 XP deducted from your profile.`;
  term.appendChild(line);

  speakWithNex(`Hint unlocked: ${activeChallenge.hint}`);
}

// 8. View Solution keys
function revealSolution() {
  if (!activeChallenge) return;
  const lang = document.getElementById("language-select").value;

  const solBox = document.getElementById("challenge-solution-box");
  const solCode = document.getElementById("challenge-solution-code");

  if (solBox && solCode) {
    solBox.style.display = "block";
    
    // Check if challenge provides solution key for specific language
    // e.g. activeChallenge.solution can be a string or object.
    let codeText = "";
    if (typeof activeChallenge.solution === "object") {
      codeText = activeChallenge.solution[lang] || activeChallenge.solution.javascript || "";
    } else {
      codeText = activeChallenge.solution || "";
    }
    
    solCode.textContent = codeText;
    
    speakWithNex("Here is the reference solution approach. Take a look at the syntax structural breakdown!");
  }
}

// 9. Filters and Search Logic
function filterAndRenderChallenges() {
  const searchVal = document.getElementById("search-input").value.toLowerCase().trim();
  const categoryVal = document.getElementById("category-filter").value;
  const difficultyVal = document.getElementById("difficulty-filter").value;
  const statusVal = document.getElementById("status-filter").value;
  const sortVal = document.getElementById("sort-filter").value;

  let filtered = [...challenges];

  // Search by title or description
  if (searchVal) {
    filtered = filtered.filter(c => 
      c.title.toLowerCase().includes(searchVal) || 
      c.description.toLowerCase().includes(searchVal)
    );
  }

  // Category Filter
  if (categoryVal !== "all") {
    filtered = filtered.filter(c => c.category === categoryVal);
  }

  // Difficulty Filter
  if (difficultyVal !== "all") {
    filtered = filtered.filter(c => c.difficulty.toLowerCase() === difficultyVal.toLowerCase());
  }

  // Status Filter
  if (statusVal !== "all") {
    const completedList = window.userProgress ? window.userProgress.completedChallenges : [];
    filtered = filtered.filter(c => {
      const solved = completedList.includes(c.id);
      return statusVal === "solved" ? solved : !solved;
    });
  }

  // Sort
  if (sortVal === "difficulty") {
    const diffWeights = { 'easy': 1, 'medium': 2, 'hard': 3 };
    filtered.sort((a, b) => diffWeights[a.difficulty.toLowerCase()] - diffWeights[b.difficulty.toLowerCase()]);
  } else if (sortVal === "xp") {
    filtered.sort((a, b) => b.xpReward - a.xpReward);
  } else if (sortVal === "title") {
    filtered.sort((a, b) => a.title.localeCompare(b.title));
  }

  // Render sidebar
  const container = document.getElementById("arena-challenge-list");
  if (!container) return;
  container.innerHTML = "";

  if (filtered.length === 0) {
    container.innerHTML = `<div style="padding:1rem; text-align:center; color:var(--text-muted); font-size:0.8rem;">No challenges match filters.</div>`;
    return;
  }

  filtered.forEach(c => {
    const isCompleted = window.userProgress && window.userProgress.completedChallenges.includes(c.id);
    const item = document.createElement("div");
    item.className = "challenge-item";
    item.dataset.id = c.id;
    if (activeChallenge && activeChallenge.id === c.id) {
      item.classList.add("active");
    }

    item.innerHTML = `
      <span>${c.title}</span>
      <div style="display:flex; align-items:center; gap:0.4rem;">
        <span class="difficulty-badge ${c.difficulty.toLowerCase()}" style="font-size:0.6rem; padding:0.05rem 0.3rem;">${c.difficulty}</span>
        <span style="font-size:0.7rem; color:${isCompleted ? 'var(--neon-green)' : 'var(--text-muted)'}">
          ${isCompleted ? '✅' : '●'}
        </span>
      </div>
    `;

    item.onclick = () => selectChallenge(c.id);
    container.appendChild(item);
  });
}

// 10. Update progress bar
function updateProgressBar() {
  const bar = document.getElementById("progress-bar-fill");
  const text = document.getElementById("progress-text");
  
  if (bar && text && window.userProgress) {
    const count = window.userProgress.completedChallenges.length;
    const total = 30; // 30 problems generated
    const percent = Math.min(100, Math.floor((count / total) * 100));
    
    bar.style.width = percent + "%";
    text.textContent = `${count}/${total} Solved`;
  }
}

// 11. Selector Mode Tab switching
function selectMode(mode) {
  currentMode = mode;
  
  // Update tabs styles
  const buttons = document.querySelectorAll(".mode-tabs button");
  buttons.forEach(btn => {
    if (btn.id === `mode-${mode}`) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Enable compiler run button if blocked by speed timeout
  const runBtn = document.getElementById("arena-run-btn");
  if (runBtn) runBtn.disabled = false;

  clearInterval(speedTimer);
  document.getElementById("timer-display").classList.remove("warning");

  if (mode === "practice") {
    document.getElementById("timer-display").textContent = "⏳ PRACTICE MODE";
    // Enable list choice
    enableListLibrary(true);
    if (activeChallenge) selectChallenge(activeChallenge.id); // reload XP display
  } else if (mode === "speed") {
    // Start count down
    startSpeedTimer();
    enableListLibrary(true);
    if (activeChallenge) selectChallenge(activeChallenge.id);
    speakWithNex("Speed challenge initiated! Complete this algorithm before the timer runs out to secure a speed XP bonus!");
  } else if (mode === "daily") {
    // Select daily problem
    enableListLibrary(false);
    selectDailyChallenge();
    speakWithNex("Daily Challenge loaded! You'll receive double XP multipliers upon successful submission!");
  }
}

function enableListLibrary(enable) {
  const list = document.getElementById("arena-challenge-list");
  if (list) {
    list.style.pointerEvents = enable ? "auto" : "none";
    list.style.opacity = enable ? "1" : "0.5";
  }
}

function selectDailyChallenge() {
  if (challenges.length === 0) return;
  const dayOfYear = Math.floor((new Date() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
  const dailyIdx = dayOfYear % challenges.length;
  const dailyChallenge = challenges[dailyIdx];
  
  selectChallenge(dailyChallenge.id);
  document.getElementById("timer-display").textContent = "⭐ DAILY CHALLENGE (2X XP)";
}

// 12. Speed run Countdown Timer
function startSpeedTimer() {
  clearInterval(speedTimer);
  timeRemaining = 900; // 15 mins
  updateTimerDisplay();

  speedTimer = setInterval(() => {
    timeRemaining--;
    updateTimerDisplay();

    if (timeRemaining <= 0) {
      clearInterval(speedTimer);
      handleSpeedTimeout();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const display = document.getElementById("timer-display");
  if (!display) return;

  if (currentMode !== "speed") {
    return;
  }

  const mins = Math.floor(timeRemaining / 60);
  const secs = timeRemaining % 60;
  const timeStr = `${mins}:${secs < 10 ? '0' : ''}${secs}`;

  display.textContent = `⏱️ SPEED RUN: ${timeStr}`;

  if (timeRemaining < 120) {
    display.classList.add("warning");
  } else {
    display.classList.remove("warning");
  }
}

function handleSpeedTimeout() {
  const runBtn = document.getElementById("arena-run-btn");
  if (runBtn) runBtn.disabled = true;

  speakWithNex("Oh no! Time has run out for this challenge. Click 'Reset Code' or switch modes to try again.");

  const term = document.getElementById("terminal-output");
  const line = document.createElement("div");
  line.className = "terminal-line error";
  line.textContent = "⏱️ SPEED TIME EXPIRED. COMPILATION RUN DISABLED.";
  term.appendChild(line);
}

// 13. Ask Nex Overlay Handlers
function openNexSidebar() {
  document.getElementById("ask-nex-sidebar").classList.add("open");
  
  // Speak initial greeting if nex bubble is empty
  const txt = document.getElementById("nex-speech-text").textContent;
  speakWithNex(txt);
}

function closeNexSidebar() {
  document.getElementById("ask-nex-sidebar").classList.remove("open");
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  clearInterval(typeInterval);
}

function speakApproach() {
  if (!activeChallenge) return;
  
  // Set thinking face first
  const face = document.getElementById("mascot-face");
  if (face) face.className.baseVal = "expr-thinking";

  setTimeout(() => {
    speakWithNex(activeChallenge.approach);
  }, 600);
}

// 14. Voice Speech Synthesis & Typewriter Sync
function speakWithNex(text) {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  clearInterval(typeInterval);

  const speedSlider = document.getElementById("speech-speed");
  const speedVal = speedSlider ? parseFloat(speedSlider.value) : 1.0;

  const face = document.getElementById("mascot-face");
  if (face) {
    face.className.baseVal = "expr-explaining"; // speaking animation
  }

  // Run Typewriter
  typeWriteText("nex-speech-text", text, speedVal, () => {
    if (face) face.className.baseVal = "expr-happy";
  });

  // Run SpeechSynthesis
  if (window.userProgress && window.userProgress.speechEnabled && window.speechSynthesis) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = speedVal;

    utterance.onend = () => {
      if (face) face.className.baseVal = "expr-happy";
    };
    utterance.onerror = () => {
      if (face) face.className.baseVal = "expr-happy";
    };

    window.speechSynthesis.speak(utterance);
  }
}

function typeWriteText(elementId, text, speedMultiplier = 1.0, callback) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = "";

  let index = 0;
  const delay = Math.max(10, 32 / speedMultiplier);

  typeInterval = setInterval(() => {
    if (index < text.length) {
      el.textContent += text[index];
      index++;
      
      const bubble = document.getElementById("nex-speech-bubble");
      if (bubble) bubble.scrollTop = bubble.scrollHeight;
    } else {
      clearInterval(typeInterval);
      if (callback) callback();
    }
  }, delay);
}

// 15. Voice recognition doubt system
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("SpeechRecognition not supported in this browser.");
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    const micBtn = document.getElementById("mic-btn");
    if (micBtn) micBtn.classList.add("listening");
    const statusWrapper = document.getElementById("voice-status-wrapper");
    if (statusWrapper) statusWrapper.style.display = "block";
    document.getElementById("voice-heard-text").textContent = "Listening for doubts...";
  };

  recognition.onresult = async (event) => {
    const resultText = event.results[0][0].transcript;
    document.getElementById("voice-heard-text").textContent = `Heard: "${resultText}"`;

    const input = document.getElementById("doubt-input");
    if (input) input.value = resultText;

    setTimeout(() => {
      submitDoubt(resultText);
    }, 800);
  };

  recognition.onend = () => {
    const micBtn = document.getElementById("mic-btn");
    if (micBtn) micBtn.classList.remove("listening");
    setTimeout(() => {
      const statusWrapper = document.getElementById("voice-status-wrapper");
      if (statusWrapper) statusWrapper.style.display = "none";
    }, 2000);
  };

  recognition.onerror = (err) => {
    console.error("SpeechRecognition error:", err);
    const micBtn = document.getElementById("mic-btn");
    if (micBtn) micBtn.classList.remove("listening");
    document.getElementById("voice-heard-text").textContent = "Voice error. Try again.";
  };
}

function toggleMic() {
  if (!recognition) {
    alert("Speech recognition is only supported on Google Chrome/Microsoft Edge browsers.");
    return;
  }
  // Stop speaking
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  
  try {
    recognition.start();
  } catch (e) {
    recognition.stop();
  }
}

async function submitDoubt(question) {
  if (!question || !activeChallenge) return;
  document.getElementById("doubt-input").value = "";

  // Show thinking face
  const face = document.getElementById("mascot-face");
  if (face) face.className.baseVal = "expr-thinking";

  speakWithNex("Let me think about that...");

  try {
    const res = await fetch("/api/doubt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topicId: activeChallenge.id,
        question
      })
    });

    if (res.ok) {
      const data = await res.json();
      speakWithNex(data.answer);
    }
  } catch (err) {
    console.error("Doubt submittal error:", err);
    speakWithNex("Sorry, I had trouble connecting to my knowledge base. Try again!");
  }
}

// Play feedback sound waves
function playChime(success) {
  if (!window.AudioContext && !window.webkitAudioContext) return;
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    if (success) {
      osc.type = "triangle";
      osc.frequency.setValueAtTime(523.25, ctx.currentTime);
      osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.1);
      osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.2);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
      osc.start();
      osc.stop(ctx.currentTime + 0.35);
    } else {
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(220, ctx.currentTime);
      osc.frequency.setValueAtTime(165, ctx.currentTime + 0.15);
      gain.gain.setValueAtTime(0.05, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    }
  } catch (e) {}
}
