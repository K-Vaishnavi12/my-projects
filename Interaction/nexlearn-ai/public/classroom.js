// Classroom Interactive Logic

let topics = [];
let currentTopic = null;
let currentLesson = null;

// State Tracking
let currentState = 'intro'; // 'intro', 'explaining', 'understanding_check', 'interrupted', 'quiz', 'completed', 'onboarding_name', 'quiz_confirm', 'doubt_confirm'
let currentChunkIndex = 0;
let currentExplanationVersion = 'primary'; // 'primary', 'simplified', 'visual', 'bullet_points'
let alternateAttempts = 0; // counts how many times they clicked 'No'

// Typewriter & Speech settings
let typewriterInterval = null;
let typewriterActive = false;
let typewriterCallback = null;

const speedConfigs = {
  "0.5": { label: "Slow", speechRate: 0.7, typewriterSpeed: 180 },
  "1.0": { label: "Normal", speechRate: 0.95, typewriterSpeed: 100 },
  "1.5": { label: "Fast", speechRate: 1.3, typewriterSpeed: 60 }
};
let currentSpeedSetting = localStorage.getItem("nex_speed_setting") || "1.0";

// Voice recognition settings
let recognition = null;
let isListening = false;
let studentName = localStorage.getItem("student_name") || "";

// Doubt & Interrupt state recovery
let preInterruptState = {}; // saves index, version, text, etc.
let doubtCandidateQuestion = "";

// Quiz state
let quizIndex = 0;
let quizScore = 0;
let quizQuestionAttempt = 1; // 1 = first try, 2 = after hint
let quizTotalXPEarned = 0;
let quizCandidateAnswer = null;

document.addEventListener("DOMContentLoaded", () => {
  initClassroom();
});

async function initClassroom() {
  await loadTopicDropdown();
  initSpeechRecognition();
  initSpeedSlider();

  // Bind event listeners
  document.getElementById("topic-select").addEventListener("change", (e) => {
    selectTopic(e.target.value);
  });

  // Doubt button bindings
  document.getElementById("doubt-trigger-btn").addEventListener("click", triggerDoubt);
  document.getElementById("doubt-submit-btn").addEventListener("click", submitDoubt);
  document.getElementById("doubt-cancel-btn").addEventListener("click", cancelDoubt);
  document.getElementById("doubt-question-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") submitDoubt();
  });

  // Mic button binding
  const micBtn = document.getElementById("mic-btn");
  if (micBtn) {
    micBtn.addEventListener("click", toggleMicrophone);
  }

  // Quiz bindings
  document.getElementById("quiz-hint-btn").addEventListener("click", showQuizHint);
  document.getElementById("quiz-next-btn").addEventListener("click", advanceQuiz);
  
  // Completion bindings
  document.getElementById("complete-next-topic").addEventListener("click", loadNextTopic);
}

// 0. Speech Speed slider control
function initSpeedSlider() {
  const speedSlider = document.getElementById("speed-slider");
  const speedText = document.getElementById("speed-value-text");
  
  if (speedSlider) {
    speedSlider.value = currentSpeedSetting;
    if (speedText) {
      speedText.textContent = speedConfigs[currentSpeedSetting].label;
    }
    
    speedSlider.addEventListener("input", (e) => {
      currentSpeedSetting = e.target.value;
      localStorage.setItem("nex_speed_setting", currentSpeedSetting);
      if (speedText) {
        speedText.textContent = speedConfigs[currentSpeedSetting].label;
      }
      
      // If voice is speaking, adjust rate dynamically on-the-fly
      if (window.speechSynthesis && window.speechSynthesis.speaking) {
        // We pause and restart to apply new rate
        const textContainer = document.getElementById("tutor-text");
        const remainingText = textContainer.textContent;
        // Skip restart if empty
        if (remainingText) {
          stopTypewriter();
          speakText(remainingText);
        }
      }
    });
  }
}

// 1. Fetch Topics & Populate Select Dropdown
async function loadTopicDropdown() {
  try {
    const res = await fetch("/api/topics");
    if (res.ok) {
      topics = await res.json();
      
      const select = document.getElementById("topic-select");
      // Clear options
      const optGroups = select.querySelectorAll("optgroup");
      optGroups[0].innerHTML = ""; // ML
      optGroups[1].innerHTML = ""; // AI
      optGroups[2].innerHTML = ""; // DSA
      
      topics.forEach(topic => {
        const option = document.createElement("option");
        option.value = topic.id;
        option.textContent = topic.name;
        
        if (topic.category === 'ml') {
          optGroups[0].appendChild(option);
        } else if (topic.category === 'ai') {
          optGroups[1].appendChild(option);
        } else if (topic.category === 'dsa') {
          optGroups[2].appendChild(option);
        }
      });

      // Load first topic from localStorage or default to ml_1
      const lastTopicId = localStorage.getItem("nex_last_topic_id") || "ml_1";
      select.value = lastTopicId;

      studentName = localStorage.getItem("student_name") || "";
      if (!studentName) {
        startOnboarding();
      } else {
        showTopicChoiceScreen();
      }
    }
  } catch (err) {
    console.error("Error loading topic dropdown:", err);
  }
}

// 1b. First launch Voice Onboarding
function startOnboarding() {
  currentState = 'onboarding_name';
  updateMascotExpression('neutral');

  stopTypewriter();
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  document.getElementById("board-main-content").style.display = "grid";
  document.getElementById("quiz-wrapper").style.display = "none";
  document.getElementById("topic-complete-box").style.display = "none";
  document.getElementById("doubt-input-panel").style.display = "none";
  document.getElementById("lesson-topic-title").textContent = "Onboarding Welcome";

  const welcomeText = "Hi! I am Nex, your AI tutor. I will teach you step by step and will not move on until YOU tell me you understand. You can talk to me or use the buttons. What is your name?";
  
  typewriter(welcomeText, () => {
    const actionsPanel = document.getElementById("tutor-actions");
    actionsPanel.innerHTML = `
      <div style="display:flex; gap:0.5rem; width:100%; max-width: 400px;">
        <input type="text" id="onboard-name-input" class="doubt-input" placeholder="Type your name...">
        <button id="onboard-submit-btn" class="btn btn-blue">Submit Name</button>
      </div>
    `;
    
    // Bind click
    document.getElementById("onboard-submit-btn").addEventListener("click", () => {
      const inputVal = document.getElementById("onboard-name-input").value;
      submitOnboardName(inputVal);
    });

    // Auto-focus name input
    const input = document.getElementById("onboard-name-input");
    if (input) input.focus();

    // Turn on microphone automatically to hear name response
    if (recognition && !isListening) {
      toggleMicrophone();
    }
  });
}

function extractName(text) {
  let clean = text.replace(/my name is/i, "")
                  .replace(/i am/i, "")
                  .replace(/call me/i, "")
                  .replace(/this is/i, "")
                  .replace(/[.\-_]/g, "")
                  .trim();
  if (clean.length > 0) {
    clean = clean.charAt(0).toUpperCase() + clean.slice(1);
  }
  return clean || "Cadet";
}

function submitOnboardName(rawName) {
  if (!rawName || rawName.trim().length === 0) return;
  
  studentName = extractName(rawName);
  localStorage.setItem("student_name", studentName);

  // Turn off mic temporarily if it was enabled
  const micBtn = document.getElementById("mic-btn");
  if (micBtn && micBtn.classList.contains("listening")) {
    toggleMicrophone();
  }

  updateMascotExpression('happy');
  const greetText = `Great to meet you, ${studentName}! Let us pick your first topic.`;
  typewriter(greetText, () => {
    updateMascotExpression('neutral');
    setTimeout(() => {
      showTopicChoiceScreen();
    }, 500);
  });
}

// 1c. Topic Selection Choice Board Screen
function showTopicChoiceScreen() {
  currentState = 'topic_select_screen';
  updateMascotExpression('neutral');

  stopTypewriter();
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  // Hide lesson board and quiz, show choice board
  document.getElementById("board-main-content").style.display = "none";
  document.getElementById("quiz-wrapper").style.display = "none";
  document.getElementById("topic-complete-box").style.display = "none";
  document.getElementById("doubt-input-panel").style.display = "none";
  document.getElementById("topic-choice-board").style.display = "flex";
  document.getElementById("track-topics-list").style.display = "none";

  document.getElementById("lesson-topic-title").textContent = "Select Lesson Track";

  const welcomeChoiceText = `Welcome back, ${studentName || "Cadet"}! Please select which track you want to join, or choose a topic from the list.`;
  speakText(welcomeChoiceText);
}

function chooseTrack(category) {
  const listContainer = document.getElementById("track-topics-list");
  const trackNameHeader = document.getElementById("selected-track-name");
  const buttonsContainer = document.getElementById("topics-buttons-container");

  listContainer.style.display = "block";
  
  let trackName = "";
  if (category === 'ml') trackName = "Machine Learning";
  else if (category === 'ai') trackName = "Artificial Intelligence";
  else if (category === 'dsa') trackName = "Data Structures & Algorithms";
  
  trackNameHeader.textContent = trackName + " Topics";
  trackNameHeader.style.color = category === 'ml' ? 'var(--neon-blue)' : (category === 'ai' ? 'var(--neon-purple)' : 'var(--neon-green)');
  
  buttonsContainer.innerHTML = "";

  const filteredTopics = topics.filter(t => t.category === category);
  filteredTopics.forEach(topic => {
    const btn = document.createElement("button");
    btn.className = "btn btn-secondary";
    btn.style.width = "100%";
    btn.style.textAlign = "left";
    btn.style.justifyContent = "flex-start";
    btn.style.padding = "0.75rem 1rem";
    btn.style.fontSize = "0.85rem";
    btn.style.marginTop = "0.3rem";
    
    const isCompleted = window.userProgress && window.userProgress.completedTopics.includes(topic.id);
    btn.innerHTML = `${isCompleted ? '✅' : '○'} ${topic.name} <span style="font-size:0.7rem; color:var(--text-muted); margin-left:auto;">${topic.level}</span>`;
    
    btn.onclick = () => {
      document.getElementById("topic-choice-board").style.display = "none";
      document.getElementById("board-main-content").style.display = "grid";
      document.getElementById("topic-select").value = topic.id;
      selectTopic(topic.id);
    };
    buttonsContainer.appendChild(btn);
  });

  speakText(`Showing topics for ${trackName}. Choose a lesson to join.`);
}

function backToTracks() {
  document.getElementById("track-topics-list").style.display = "none";
  speakText("Select a learning track below.");
}

// Expose globally
window.showTopicChoiceScreen = showTopicChoiceScreen;
window.chooseTrack = chooseTrack;
window.backToTracks = backToTracks;

// 2. Select Topic and Load Lesson
async function selectTopic(topicId) {
  // Cancel active speech/typewriter
  stopTypewriter();
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  
  localStorage.setItem("nex_last_topic_id", topicId);
  currentTopic = topics.find(t => t.id === topicId);
  
  // Hide completing, quiz layouts, reset board display
  document.getElementById("board-main-content").style.display = "grid";
  document.getElementById("quiz-wrapper").style.display = "none";
  document.getElementById("topic-complete-box").style.display = "none";
  document.getElementById("doubt-input-panel").style.display = "none";

  document.getElementById("lesson-topic-title").textContent = currentTopic.name;

  try {
    const res = await fetch(`/api/lessons/${topicId}`);
    if (res.ok) {
      currentLesson = await res.json();
      startLessonIntro();
    }
  } catch (err) {
    console.error("Error loading lesson:", err);
  }
}

// 3. Step 1: Lesson Intro (Session Awareness integration)
function startLessonIntro() {
  currentState = 'intro';
  currentChunkIndex = 0;
  currentExplanationVersion = 'primary';
  alternateAttempts = 0;
  
  updateDotsUI();
  updateMascotExpression('neutral');

  // Session Awareness text
  let introText = "";
  const completedTopics = window.userProgress ? window.userProgress.completedTopics || [] : [];
  if (completedTopics.length > 0) {
    const lastTopicId = completedTopics[completedTopics.length - 1];
    const lastTopic = topics.find(t => t.id === lastTopicId) || { name: "the last topic" };
    introText = `Welcome back! Last time we covered ${lastTopic.name}. Ready to continue? Today we are learning ${currentTopic.name}. Let me walk you through it step by step. Ready?`;
  } else {
    introText = `Welcome back, ${studentName || "Cadet"}! Ready to start? Today we are learning ${currentTopic.name}. Let me walk you through it step by step. Ready?`;
  }
  
  typewriter(introText, () => {
    // Render Yes/No/Choose buttons
    const actionsPanel = document.getElementById("tutor-actions");
    actionsPanel.innerHTML = `
      <button onclick="startExplaining()" class="btn btn-blue">Yes, let's go! 🚀</button>
      <button onclick="showTopicChoiceScreen()" class="btn btn-secondary">Choose another topic</button>
    `;

    // Ensure mic is restarted for student input
    triggerListeningCheck();
  });

  // Render visual welcome card
  const visualContent = document.getElementById("board-visual-content");
  visualContent.innerHTML = `
    <div style="text-align:center; padding:1.5rem; border:1px dashed var(--neon-purple); border-radius:8px;">
      <p style="color:#fff; font-size:1.1rem; font-weight:bold; margin-bottom:0.5rem;">Interactive Learning Lab</p>
      <p style="color:var(--text-secondary); font-size:0.8rem; line-height:1.5;">We will explain ${currentTopic.name} in 5 structured chunks, followed by a mini quiz. You can talk to NEX or ask questions anytime!</p>
    </div>
  `;
}

function focusTopicSelect() {
  document.getElementById("topic-select").focus();
}

// 4. Step 2: Concept Explanation Chunks
function startExplaining() {
  currentState = 'explaining';
  currentExplanationVersion = 'primary';
  alternateAttempts = 0;
  updateDotsUI();
  loadChunk();
}

function loadChunk() {
  const chunk = currentLesson.chunks[currentChunkIndex];
  updateMascotExpression('explaining');
  
  renderVisualPanel(chunk);
  
  const textToSpeak = getChunkText(chunk, currentExplanationVersion);
  
  typewriter(textToSpeak, () => {
    updateMascotExpression('neutral');
    const actionsPanel = document.getElementById("tutor-actions");
    actionsPanel.innerHTML = `
      <button onclick="promptUnderstandingCheck()" class="btn btn-blue">Continue ▶</button>
    `;

    triggerListeningCheck();
  });
}

function getChunkText(chunk, version) {
  if (version === 'primary') return chunk.primary;
  if (version === 'simplified') return chunk.simplified;
  if (version === 'visual') return `Let's analyze the visual diagram on the right board. ${chunk.primary}`;
  if (version === 'bullet_points') return `Let's break this down into key takeaways: ${chunk.bullet_points.join(" ")}`;
  return chunk.primary;
}

function renderVisualPanel(chunk) {
  const visualContent = document.getElementById("board-visual-content");
  
  if (currentExplanationVersion === 'bullet_points') {
    let listHTML = `<ul style="list-style: none; display:flex; flex-direction:column; gap:0.5rem;">`;
    chunk.bullet_points.forEach(bp => {
      listHTML += `<li style="border-left: 2px solid var(--neon-purple); padding-left: 0.5rem; color: var(--text-primary); font-size: 0.8rem; line-height:1.4;">✦ ${bp}</li>`;
    });
    listHTML += `</ul>`;
    visualContent.innerHTML = listHTML;
  } else if (currentExplanationVersion === 'visual') {
    visualContent.innerHTML = `<pre style="color:var(--neon-green); font-size:0.75rem; text-shadow:var(--glow-green);">${chunk.visual}</pre>`;
  } else {
    visualContent.innerHTML = `<pre style="color:var(--neon-blue); font-size:0.75rem;">${chunk.visual}</pre>`;
  }
}

// 5. Step 3: Understanding Check
function promptUnderstandingCheck() {
  currentState = 'understanding_check';
  updateMascotExpression('neutral');
  
  const promptText = `So ${studentName || "Cadet"}, does that make sense? Did you understand this part? 😊`;
  typewriter(promptText, () => {
    const actionsPanel = document.getElementById("tutor-actions");
    actionsPanel.innerHTML = `
      <button onclick="handleUnderstanding(true)" class="btn btn-green">✅ Yes, I got it! Move on</button>
      <button onclick="handleUnderstanding(false)" class="btn btn-pink">❓ No, explain again</button>
    `;

    triggerListeningCheck();
  });
}

async function handleUnderstanding(understood) {
  if (understood) {
    // Correct/Understood speech confirmation
    updateMascotExpression('happy');
    
    // Choose encouraging phrases
    const understoodTexts = [
      "Perfect! You're getting this really well! Let's advance.",
      "Excellent job! You are grasping these ideas quickly. Let's move to the next part.",
      "Awesome! Let's keep this momentum going."
    ];
    const speech = understoodTexts[Math.floor(Math.random() * understoodTexts.length)];
    
    typewriter(speech, () => {
      updateMascotExpression('neutral');
      if (currentChunkIndex < 4) {
        // Complete current dot
        const dots = document.querySelectorAll("#progress-dots .chunk-dot");
        dots[currentChunkIndex].classList.remove("active");
        dots[currentChunkIndex].classList.add("completed");

        currentChunkIndex++;
        startExplaining();
      } else {
        const dots = document.querySelectorAll("#progress-dots .chunk-dot");
        dots[currentChunkIndex].classList.remove("active");
        dots[currentChunkIndex].classList.add("completed");
        
        startMiniQuiz();
      }
    });
  } else {
    alternateAttempts++;
    updateMascotExpression('encouraging');
    
    // Speech response on doubt/confusion
    const failSpeech = "No problem! Let me try explaining this differently...";
    
    typewriter(failSpeech, () => {
      // Cycle versions: primary -> simplified -> visual -> bullet_points
      if (alternateAttempts === 1) {
        currentExplanationVersion = 'simplified';
        loadChunkAlternative();
      } else if (alternateAttempts === 2) {
        currentExplanationVersion = 'visual';
        loadChunkAlternative();
      } else {
        currentExplanationVersion = 'bullet_points';
        loadChunkAlternative();
        alternateAttempts = 0; // reset loop cycle
      }
    });
  }
}

function loadChunkAlternative() {
  const chunk = currentLesson.chunks[currentChunkIndex];
  renderVisualPanel(chunk);
  const text = getChunkText(chunk, currentExplanationVersion);
  
  typewriter(text, () => {
    updateMascotExpression('neutral');
    const actionsPanel = document.getElementById("tutor-actions");
    actionsPanel.innerHTML = `
      <button onclick="promptUnderstandingCheck()" class="btn btn-blue">Continue ▶</button>
    `;

    triggerListeningCheck();
  });
}

// 6. Step 4: Student Interrupt & Doubt Solving
function triggerDoubt() {
  stopTypewriter();
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  
  preInterruptState = {
    state: currentState,
    chunkIndex: currentChunkIndex,
    version: currentExplanationVersion,
    bubbleHTML: document.getElementById("tutor-speech-bubble").innerHTML,
    actionsHTML: document.getElementById("tutor-actions").innerHTML
  };
  
  currentState = 'interrupted';
  updateMascotExpression('thinking');
  
  const bubble = document.getElementById("tutor-text");
  bubble.textContent = "";
  
  typewriter("Sure! What's your question? You can speak or type it in the panel below.", () => {
    document.getElementById("doubt-input-panel").style.display = "flex";
    document.getElementById("tutor-actions").innerHTML = "";
    
    // Focus doubt input
    const input = document.getElementById("doubt-question-input");
    if (input) input.focus();

    // Trigger mic to start listening for their doubt
    if (recognition && !isListening) {
      toggleMicrophone();
    }
  });
}

async function submitDoubt() {
  const input = document.getElementById("doubt-question-input");
  const query = input.value.trim();
  if (!query) return;
  
  input.value = "";
  document.getElementById("doubt-input-panel").style.display = "none";
  updateMascotExpression('thinking');
  
  // Natural fillers
  const pauseFillers = [
    "Hmm, let me think about the best way to explain this...",
    "Good question! So here's the thing...",
    "Alright, let me break this down for you..."
  ];
  const fillerText = pauseFillers[Math.floor(Math.random() * pauseFillers.length)];

  typewriter(fillerText, async () => {
    try {
      const res = await fetch("/api/doubt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topicId: currentTopic.id, question: query })
      });
      
      if (res.ok) {
        const data = await res.json();
        updateMascotExpression('explaining');
        
        // Live feeling greeting prefix
        const replyText = `Great question, ${studentName || "Cadet"}! Here is how we break it down: ${data.answer} Does that answer your question? Say yes or no.`;
        
        typewriter(replyText, () => {
          updateMascotExpression('neutral');
          const actionsPanel = document.getElementById("tutor-actions");
          actionsPanel.innerHTML = `
            <button onclick="resolveDoubt(true)" class="btn btn-green">Yes, that clears it up! Resume</button>
            <button onclick="resolveDoubt(false)" class="btn btn-pink">No, explain differently</button>
          `;

          triggerListeningCheck();
        });
      }
    } catch (err) {
      console.error("Error asking doubt:", err);
      resolveDoubt(true);
    }
  });
}

function cancelDoubt() {
  document.getElementById("doubt-input-panel").style.display = "none";
  resolveDoubt(true);
}

function resolveDoubt(cleared) {
  if (cleared) {
    currentState = preInterruptState.state;
    currentChunkIndex = preInterruptState.chunkIndex;
    currentExplanationVersion = preInterruptState.version;
    
    document.getElementById("tutor-speech-bubble").innerHTML = preInterruptState.bubbleHTML;
    document.getElementById("tutor-actions").innerHTML = preInterruptState.actionsHTML;
    
    if (currentState === 'explaining') {
      loadChunk();
    } else if (currentState === 'intro') {
      startLessonIntro();
    } else if (currentState === 'understanding_check') {
      promptUnderstandingCheck();
    } else if (currentState === 'quiz') {
      loadQuizQuestion();
    }
  } else {
    // Re-explain query differently
    const altDoubtExplain = `This is a tricky concept — even experienced developers find it confusing at first. Think of it as standard coefficients adjusting to close an error gap. Let's return to the lesson and see if it makes sense.`;
    typewriter(altDoubtExplain, () => {
      const actionsPanel = document.getElementById("tutor-actions");
      actionsPanel.innerHTML = `
        <button onclick="resolveDoubt(true)" class="btn btn-green">Got it, resume lesson</button>
      `;
      triggerListeningCheck();
    });
  }
}

// 7. Step 5: Mini Quiz
function startMiniQuiz() {
  currentState = 'quiz';
  quizIndex = 0;
  quizScore = 0;
  quizTotalXPEarned = 0;
  
  document.getElementById("board-main-content").style.display = "none";
  document.getElementById("quiz-wrapper").style.display = "flex";
  
  typewriter("Great job finishing the topic! Let us test what you learned with a quick quiz!", () => {
    loadQuizQuestion();
  });
}

function loadQuizQuestion() {
  currentState = 'quiz';
  const question = currentLesson.quiz[quizIndex];
  quizQuestionAttempt = 1;
  quizCandidateAnswer = null;
  
  document.getElementById("quiz-feedback-box").style.display = "none";
  document.getElementById("quiz-next-btn").style.display = "none";
  document.getElementById("quiz-hint-btn").style.display = "inline-flex";
  document.getElementById("quiz-hint-btn").disabled = false;

  const questionBox = document.getElementById("quiz-question-box");
  questionBox.textContent = `${quizIndex + 1}. ${question.question}`;
  
  const choicesBox = document.getElementById("quiz-choices-box");
  choicesBox.innerHTML = "";

  if (question.type === 'mcq' || question.type === 'tf') {
    question.choices.forEach((choice, idx) => {
      const btn = document.createElement("button");
      btn.className = "quiz-choice-btn";
      btn.textContent = choice;
      btn.onclick = () => confirmQuizAnswer(idx);
      choicesBox.appendChild(btn);
    });
  } else if (question.type === 'fitb') {
    choicesBox.innerHTML = `
      <div style="display:flex; gap:1rem; width:100%;">
        <input type="text" id="quiz-fitb-input" class="doubt-input" style="flex-grow:1;" placeholder="Type your answer here...">
        <button id="fitb-submit-btn" class="btn btn-blue">Submit</button>
      </div>
    `;
    document.getElementById("fitb-submit-btn").addEventListener("click", () => {
      const val = document.getElementById("quiz-fitb-input").value;
      confirmQuizAnswer(val);
    });
    setTimeout(() => document.getElementById("quiz-fitb-input").focus(), 100);
  }

  // Speak the question aloud, then speak choices
  let voiceText = `Question ${quizIndex + 1}. ${question.question}`;
  if (question.type === 'mcq') {
    voiceText += ". The choices are: " + question.choices.map((c, i) => `Option ${String.fromCharCode(65+i)}: ${c}`).join(", ");
  } else if (question.type === 'tf') {
    voiceText += ". True or False?";
  }

  speakText(voiceText, () => {
    // Automatically start listening for answer once voice finishes
    triggerListeningCheck();
  });
}

function showQuizHint() {
  const question = currentLesson.quiz[quizIndex];
  const feedback = document.getElementById("quiz-feedback-box");
  feedback.style.display = "block";
  feedback.className = "quiz-feedback";
  feedback.innerHTML = `💡 <strong>Hint:</strong> ${question.hint}`;
  
  quizQuestionAttempt = 2; // reduces points to +15 XP
  document.getElementById("quiz-hint-btn").disabled = true;
}

// Voice Quiz confirmation flow
function confirmQuizAnswer(answer) {
  const question = currentLesson.quiz[quizIndex];
  quizCandidateAnswer = answer;
  currentState = 'quiz_confirm';

  let displayStr = "";
  if (question.type === 'mcq' || question.type === 'tf') {
    displayStr = question.choices[answer];
  } else {
    displayStr = answer;
  }

  // Show yes/no choice boxes
  const choicesBox = document.getElementById("quiz-choices-box");
  choicesBox.innerHTML = `
    <div style="text-align:center; padding:1.2rem; border:1px dashed var(--neon-purple); border-radius:8px; width:100%;">
      <p style="font-size:0.95rem; color:#fff;">I heard your answer as: <strong class="neon-text-blue">${displayStr}</strong></p>
      <p style="margin-top:0.4rem; font-size:0.8rem; color:var(--text-secondary);">Is this correct?</p>
      <div style="display:flex; justify-content:center; gap:1rem; margin-top:1rem;">
        <button onclick="submitConfirmedQuizAnswer()" class="btn btn-green">Yes, submit</button>
        <button onclick="rejectConfirmedQuizAnswer()" class="btn btn-pink">No, let me change</button>
      </div>
    </div>
  `;

  // Voice asks confirmation
  speakText(`I heard your answer as ${displayStr}. Is that correct?`, () => {
    triggerListeningCheck();
  });
}

function submitConfirmedQuizAnswer() {
  const question = currentLesson.quiz[quizIndex];
  const choiceVal = quizCandidateAnswer;
  
  if (question.type === 'mcq' || question.type === 'tf') {
    selectQuizAnswer(choiceVal);
  } else if (question.type === 'fitb') {
    // Render and submit FITB
    const choicesBox = document.getElementById("quiz-choices-box");
    choicesBox.innerHTML = `
      <div style="display:flex; gap:1rem; width:100%;">
        <input type="text" id="quiz-fitb-input" class="doubt-input" style="flex-grow:1;" value="${choiceVal}" disabled>
        <button class="btn btn-blue" disabled>Submit</button>
      </div>
    `;
    submitFitbAnswer(choiceVal);
  }
}

function rejectConfirmedQuizAnswer() {
  speakText("No problem! Please tell me your answer again.", () => {
    loadQuizQuestion();
  });
}

function selectQuizAnswer(selectedIndex) {
  currentState = 'quiz';
  const question = currentLesson.quiz[quizIndex];
  
  // Re-render full choices disabled with correct/incorrect highlights
  const choicesBox = document.getElementById("quiz-choices-box");
  choicesBox.innerHTML = "";
  question.choices.forEach((choice, idx) => {
    const btn = document.createElement("button");
    btn.className = "quiz-choice-btn";
    btn.textContent = choice;
    btn.disabled = true;
    
    if (idx === selectedIndex) {
      if (idx === question.answer) {
        btn.classList.add("correct");
      } else {
        btn.classList.add("incorrect");
      }
    } else if (idx === question.answer) {
      btn.classList.add("correct");
    }
    choicesBox.appendChild(btn);
  });
  
  const feedback = document.getElementById("quiz-feedback-box");
  feedback.style.display = "block";
  
  const isCorrect = selectedIndex === question.answer;
  if (isCorrect) {
    feedback.className = "quiz-feedback neon-text-green";
    feedback.innerHTML = `✅ <strong>Correct!</strong> ${question.explanation}`;
    
    const xpReward = quizQuestionAttempt === 1 ? 30 : 15;
    quizTotalXPEarned += xpReward;
    quizScore++;
    
    updateMascotExpression('happy');
    addXP(xpReward);
    speakText("That's correct! Great job!");
  } else {
    feedback.className = "quiz-feedback neon-text-pink";
    feedback.innerHTML = `❌ <strong>Incorrect.</strong> The correct answer is: <em>${question.choices[question.answer]}</em>.<br>${question.explanation}`;
    
    updateMascotExpression('neutral');
    speakText(`Good try! Let me clarify that... The correct answer is: ${question.choices[question.answer]}.`);
  }
  
  document.getElementById("quiz-hint-btn").style.display = "none";
  document.getElementById("quiz-next-btn").style.display = "inline-flex";
}

function submitFitbAnswer(typedValue) {
  currentState = 'quiz';
  const question = currentLesson.quiz[quizIndex];
  const value = typedValue.trim().toLowerCase();

  const feedback = document.getElementById("quiz-feedback-box");
  feedback.style.display = "block";

  const isCorrect = value === question.answer.toLowerCase();
  if (isCorrect) {
    feedback.className = "quiz-feedback neon-text-green";
    feedback.innerHTML = `✅ <strong>Correct!</strong> ${question.explanation}`;
    
    const xpReward = quizQuestionAttempt === 1 ? 30 : 15;
    quizTotalXPEarned += xpReward;
    quizScore++;

    updateMascotExpression('happy');
    addXP(xpReward);
    speakText("That's correct! Great job!");
  } else {
    feedback.className = "quiz-feedback neon-text-pink";
    feedback.innerHTML = `❌ <strong>Incorrect.</strong> The correct answer is: <strong>${question.answer}</strong>.<br>${question.explanation}`;
    
    updateMascotExpression('neutral');
    speakText(`Good try! Let me clarify that... The correct answer is: ${question.answer}.`);
  }

  document.getElementById("quiz-hint-btn").style.display = "none";
  document.getElementById("quiz-next-btn").style.display = "inline-flex";
}

function advanceQuiz() {
  quizIndex++;
  if (quizIndex < currentLesson.quiz.length) {
    loadQuizQuestion();
  } else {
    completeLesson();
  }
}

// 8. Step 6: Topic Completion & Badge Unlock
async function completeLesson() {
  currentState = 'completed';
  document.getElementById("quiz-wrapper").style.display = "none";
  document.getElementById("topic-complete-box").style.display = "block";
  
  updateMascotExpression('happy');
  
  // Request server completion & award +50 XP topic completion
  const res = await completeTopic(currentTopic.id);
  
  let rewardText = `+${quizTotalXPEarned} Quiz XP +50 Completion XP`;
  if (res && res.unlockedBadge) {
    rewardText += ` & Unlocked Badge: 🏆 ${res.unlockedBadge.name}`;
  }
  document.getElementById("complete-xp-earn").innerHTML = `🎉 You scored ${quizScore}/3! Earned: ${rewardText}`;
  
  // Confetti explosion
  if (window.confetti) {
    confetti({
      particleCount: 150,
      spread: 80,
      origin: { y: 0.6 }
    });
  }

  // Session Awareness End text
  const endSessionText = `Amazing session today, ${studentName || "Cadet"}! You completed ${currentTopic.name} and earned ${50 + quizTotalXPEarned} XP. Ready to practice or tackle the next lesson?`;
  speakText(endSessionText);
}

function loadNextTopic() {
  const currentIndex = topics.findIndex(t => t.id === currentTopic.id);
  if (currentIndex !== -1 && currentIndex + 1 < topics.length) {
    const nextTopic = topics[currentIndex + 1];
    document.getElementById("topic-select").value = nextTopic.id;
    selectTopic(nextTopic.id);
  } else {
    selectTopic(topics[0].id);
  }
}

// --- VOICE INTERACTION SYSTEM (Web Speech APIs) --- //

// A. Speech recognition initialization
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("SpeechRecognition is not supported in this browser. Falling back to text inputs.");
    const notice = document.getElementById("browser-notice");
    if (notice) {
      notice.textContent = "⚠️ Voice inputs not supported in this browser. For best voice experience, use Google Chrome or Edge.";
      notice.style.color = "var(--neon-pink)";
      notice.style.borderColor = "var(--neon-pink)";
      notice.style.background = "rgba(255, 0, 127, 0.08)";
    }
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false; // Process utterance by utterance
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    isListening = true;
    updateMicUI(true);
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    handleSpeechInput(transcript);
  };

  recognition.onerror = (event) => {
    console.error("Speech Recognition error:", event.error);
    if (event.error === 'not-allowed') {
      isListening = false;
      updateMicUI(false);
      alert("Microphone access blocked. Please enable permissions in browser address bar.");
    }
  };

  recognition.onend = () => {
    isListening = false;
    updateMicUI(false);
    
    // Auto-restart if microphone is toggled ON (always listening)
    const micBtn = document.getElementById("mic-btn");
    if (micBtn && micBtn.classList.contains("listening")) {
      setTimeout(() => {
        if (micBtn.classList.contains("listening") && !isListening) {
          try {
            recognition.start();
          } catch (e) {}
        }
      }, 400);
    }
  };
}

// B. Mic control toggle
function toggleMicrophone() {
  if (!recognition) {
    alert("Speech recognition is not supported in this browser.");
    return;
  }

  const micBtn = document.getElementById("mic-btn");
  if (micBtn.classList.contains("listening")) {
    micBtn.classList.remove("listening");
    document.getElementById("mic-status-text").textContent = "Speak or type";
    isListening = false;
    recognition.stop();
  } else {
    micBtn.classList.add("listening");
    document.getElementById("mic-status-text").textContent = "Listening...";
    try {
      recognition.start();
    } catch (e) {}
  }
}

function updateMicUI(listening) {
  const micBtn = document.getElementById("mic-btn");
  const micStatus = document.getElementById("mic-status-text");
  if (micBtn && micStatus) {
    if (listening) {
      micBtn.classList.add("listening");
      micStatus.textContent = "Listening...";
    } else if (!micBtn.classList.contains("listening")) {
      micBtn.classList.remove("listening");
      micStatus.textContent = "Speak or type";
    }
  }
}

// Helper to auto-listen if mic is enabled
function triggerListeningCheck() {
  const micBtn = document.getElementById("mic-btn");
  if (micBtn && micBtn.classList.contains("listening") && !isListening) {
    try {
      recognition.start();
    } catch(e){}
  }
}

// Display visual feedback bubble
function showVoiceFeedback(text) {
  const bubble = document.getElementById("voice-feedback-bubble");
  const textSpan = document.getElementById("voice-heard-text");
  
  if (bubble && textSpan) {
    textSpan.innerHTML = `I heard: "<em>${text}</em>"`;
    bubble.style.display = "flex";
    
    setTimeout(() => {
      bubble.style.display = "none";
    }, 3000);
  }
}

// C. Match keyword inputs against rules
const keywords = {
  understood: ["yes", "got it", "i understand", "understood", "makes sense", "clear", "next", "continue"],
  confused: ["no", "confused", "don't understand", "not clear", "explain again", "what", "huh"],
  interrupt: ["wait", "question", "doubt", "i have a question", "hold on", "pause"],
  repeat: ["repeat", "say again", "can you repeat"]
};

function checkKeywords(text) {
  const clean = text.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"").trim();
  
  if (keywords.interrupt.some(kw => clean.includes(kw))) return 'interrupt';
  if (keywords.repeat.some(kw => clean === kw || clean.startsWith(kw + " ") || clean.includes(" " + kw))) return 'repeat';
  if (keywords.understood.some(kw => clean === kw || clean.startsWith(kw + " ") || clean.includes(" " + kw))) return 'understood';
  if (keywords.confused.some(kw => clean === kw || clean.startsWith(kw + " ") || clean.includes(" " + kw))) return 'confused';
  
  return null;
}

// D. Speech Input State Routing
function handleSpeechInput(text) {
  const clean = text.toLowerCase().trim();
  if (clean.length === 0) return;

  showVoiceFeedback(text);

  // 1. Onboarding Name
  if (currentState === 'onboarding_name') {
    submitOnboardName(text);
    return;
  }

  // 2. Quiz Answer Confirmation
  if (currentState === 'quiz_confirm') {
    if (clean === 'yes' || clean.includes("correct") || clean.includes("yeah") || clean === 'true') {
      submitConfirmedQuizAnswer();
    } else if (clean === 'no' || clean.includes("wrong") || clean.includes("change") || clean === 'false') {
      rejectConfirmedQuizAnswer();
    } else {
      speakText("I didn't catch that. Is your answer correct? Say yes or no.", () => {
        triggerListeningCheck();
      });
    }
    return;
  }

  // 3. Quiz active answering
  if (currentState === 'quiz') {
    handleQuizVoiceAnswer(text);
    return;
  }

  // 4. Doubt feedback verification
  if (currentState === 'interrupted' && document.getElementById("tutor-actions").innerHTML.includes("resolveDoubt")) {
    if (clean.includes("yes") || clean.includes("clears") || clean.includes("resume") || clean.includes("got it")) {
      resolveDoubt(true);
    } else if (clean.includes("no") || clean.includes("differently")) {
      resolveDoubt(false);
    }
    return;
  }

  // 5. Doubt confirmation
  if (currentState === 'doubt_confirm') {
    if (clean === 'yes' || clean.includes("correct") || clean.includes("yeah") || clean === 'true') {
      submitConfirmedDoubt();
    } else {
      cancelDoubt();
    }
    return;
  }

  // 6. Doubt active transcription
  if (currentState === 'interrupted') {
    const input = document.getElementById("doubt-question-input");
    if (input) {
      input.value = text;
      speakText(`I heard your question as: "${text}". Is that correct? Say yes or no.`, () => {
        currentState = 'doubt_confirm';
        doubtCandidateQuestion = text;
        const actionsPanel = document.getElementById("tutor-actions");
        actionsPanel.innerHTML = `
          <button onclick="submitConfirmedDoubt()" class="btn btn-green">Yes, ask NEX</button>
          <button onclick="cancelDoubt()" class="btn btn-secondary">No, change question</button>
        `;
        triggerListeningCheck();
      });
    }
    return;
  }

  // 7. Standard keywords check (understood, confused, interrupt, repeat)
  const action = checkKeywords(text);
  if (action === 'understood') {
    handleUnderstanding(true);
  } else if (action === 'confused') {
    handleUnderstanding(false);
  } else if (action === 'interrupt') {
    triggerDoubt();
  } else if (action === 'repeat') {
    repeatCurrentText();
  } else {
    // Fallback if voice command not matched
    speakText("I didn't catch that — you can also click the buttons below", () => {
      triggerListeningCheck();
    });
  }
}

function repeatCurrentText() {
  if (currentState === 'intro') {
    startLessonIntro();
  } else if (currentState === 'explaining') {
    loadChunk();
  } else if (currentState === 'understanding_check') {
    promptUnderstandingCheck();
  }
}

function submitConfirmedDoubt() {
  const input = document.getElementById("doubt-question-input");
  if (input) input.value = doubtCandidateQuestion;
  submitDoubt();
}

// E. Match Spoken Quiz answers
function handleQuizVoiceAnswer(text) {
  const question = currentLesson.quiz[quizIndex];
  const clean = text.toLowerCase().trim();
  let matchedIdx = -1;

  if (question.type === 'mcq' || question.type === 'tf') {
    question.choices.forEach((choice, idx) => {
      const choiceVal = choice.toLowerCase();
      const letter = String.fromCharCode(65 + idx).toLowerCase(); // a, b, c, d
      
      if (clean === letter || 
          clean === `option ${letter}` || 
          clean.startsWith(`option ${letter}`) || 
          clean.startsWith(letter + " ") || 
          clean.endsWith(" " + letter) ||
          clean === choiceVal || 
          clean.includes(choiceVal)) {
        matchedIdx = idx;
      }
    });

    // Fallbacks for ordinals
    if (matchedIdx === -1) {
      if (clean.includes("first") || clean.includes("number one") || clean === "1") matchedIdx = 0;
      else if (clean.includes("second") || clean.includes("number two") || clean === "2") matchedIdx = 1;
      else if (clean.includes("third") || clean.includes("number three") || clean === "3") matchedIdx = 2;
      else if (clean.includes("fourth") || clean.includes("number four") || clean === "4") matchedIdx = 3;
    }
  } else if (question.type === 'fitb') {
    // String matching
    matchedIdx = text;
  }

  if (matchedIdx !== -1) {
    confirmQuizAnswer(matchedIdx);
  } else {
    speakText("I didn't catch that. Could you repeat your answer or click one of the options?", () => {
      triggerListeningCheck();
    });
  }
}

// --- UTILITY EFFECTS: Typewriter & Voice Speech --- //
function typewriter(text, callback) {
  stopTypewriter();
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  
  const textContainer = document.getElementById("tutor-text");
  textContainer.textContent = "";

  const speechEnabled = window.userProgress && window.userProgress.speechEnabled;
  
  // 1. Voice Speech Synthesis sync typewriter (onboundary based)
  if (speechEnabled && window.speechSynthesis) {
    const speechText = text.replace(/[\[\]]/g, "");
    const utterance = new SpeechSynthesisUtterance(speechText);
    
    // Choose voice
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => 
      v.name.includes("Google UK English Female") || 
      v.name.includes("Microsoft Zira") ||
      v.lang.includes("en-GB") ||
      v.lang.includes("en-US") || 
      v.lang.startsWith("en")
    );
    if (preferredVoice) utterance.voice = preferredVoice;

    utterance.pitch = 1.1;
    utterance.rate = speedConfigs[currentSpeedSetting].speechRate;
    utterance.volume = 1.0;

    utterance.onboundary = (event) => {
      if (event.name === 'word') {
        const charIndex = event.charIndex;
        // Output text up to character index
        const subText = speechText.slice(0, charIndex + event.charLength).trim();
        textContainer.textContent = subText;
      }
    };

    utterance.onend = () => {
      textContainer.textContent = text;
      stopTypewriter();
      if (callback) callback();
    };

    utterance.onerror = (err) => {
      console.error("SpeechSynthesis boundary error, falling back to timer:", err);
      // Fallback
      textContainer.textContent = text;
      stopTypewriter();
      if (callback) callback();
    };

    typewriterActive = true;
    window.speechSynthesis.speak(utterance);
  } else {
    // 2. Muted/No Speech Synthesis timer-based typewriter
    const words = text.split(" ");
    let index = 0;
    typewriterActive = true;
    typewriterCallback = callback;
    const speed = speedConfigs[currentSpeedSetting].typewriterSpeed;
    
    typewriterInterval = setInterval(() => {
      if (index < words.length) {
        textContainer.textContent = words.slice(0, index + 1).join(" ");
        index++;
      } else {
        stopTypewriter();
        if (callback) callback();
      }
    }, speed);
  }
}

function stopTypewriter() {
  if (typewriterInterval) {
    clearInterval(typewriterInterval);
    typewriterInterval = null;
  }
  typewriterActive = false;
}

function speakText(text, callback) {
  if (!window.userProgress || !window.userProgress.speechEnabled || !window.speechSynthesis) {
    if (callback) callback();
    return;
  }
  
  window.speechSynthesis.cancel();
  
  const speechText = text.replace(/[\[\]]/g, "");
  const utterance = new SpeechSynthesisUtterance(speechText);
  
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(v => 
    v.name.includes("Google UK English Female") || 
    v.name.includes("Microsoft Zira") ||
    v.lang.includes("en-US") || 
    v.lang.startsWith("en")
  );
  if (preferredVoice) utterance.voice = preferredVoice;
  
  utterance.pitch = 1.1;
  utterance.rate = speedConfigs[currentSpeedSetting].speechRate;
  utterance.volume = 1.0;

  if (callback) {
    utterance.onend = () => callback();
    utterance.onerror = () => callback();
  }
  
  window.speechSynthesis.speak(utterance);
}

// Trigger voices changed listener
if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => {
    console.log("SpeechSynthesis voices loaded.");
  };
}

// Helper to update dot nodes
function updateDotsUI() {
  const dots = document.querySelectorAll("#progress-dots .chunk-dot");
  dots.forEach((dot, idx) => {
    dot.className = "chunk-dot";
    if (idx < currentChunkIndex) {
      dot.classList.add("completed");
    } else if (idx === currentChunkIndex) {
      dot.classList.add("active");
    }
  });
}

// Helper to adjust mascot classes
function updateMascotExpression(expr) {
  const avatar = document.getElementById("tutor-avatar");
  if (avatar) {
    avatar.className = `mascot-container expr-${expr}`;
  }
}
