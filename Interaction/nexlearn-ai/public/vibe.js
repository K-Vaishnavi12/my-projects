// Vibe Coding Studio controller

let sortingArray = [];
let sortAnimationRunning = false;
let listAnimationRunning = false;
let audioCtx = null;

document.addEventListener("DOMContentLoaded", () => {
  initVibeStudio();
});

function initVibeStudio() {
  // Save/Restore local workspace code
  const savedVibe = localStorage.getItem("vibe_workspace_code");
  if (savedVibe) {
    document.getElementById("vibe-editor").value = savedVibe;
  }

  document.getElementById("vibe-editor").addEventListener("input", (e) => {
    localStorage.setItem("vibe_workspace_code", e.target.value);
  });

  // Prompt Buttons
  document.getElementById("prompt-refactor").addEventListener("click", handleRefactor);
  document.getElementById("prompt-complexity").addEventListener("click", handleComplexity);
  document.getElementById("prompt-sort-vis").addEventListener("click", triggerSortVisualization);
  document.getElementById("prompt-list-vis").addEventListener("click", triggerListVisualization);

  // Custom chat send
  document.getElementById("vibe-send-btn").addEventListener("click", sendCustomMessage);
  document.getElementById("vibe-chat-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendCustomMessage();
  });
}

// 1. Helper to append chat messages
function appendChatMessage(sender, text) {
  const box = document.getElementById("vibe-chat-box");
  const msg = document.createElement("div");
  msg.className = `ai-message ${sender}`;
  msg.innerHTML = text;
  box.appendChild(msg);
  box.scrollTop = box.scrollHeight;
}

// 2. Refactor Prompt
function handleRefactor() {
  const code = document.getElementById("vibe-editor").value;
  appendChatMessage("user", "Refactor this code using modern ES6 clean practices.");
  
  setTimeout(() => {
    const refactoredCode = `// Refactored and Optimized Version
const bubbleSort = (arr) => {
  const n = arr.length;
  let swapped;
  
  for (let i = 0; i < n - 1; i++) {
    swapped = false;
    for (let j = 0; j < n - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
        swapped = true;
      }
    }
    // If no elements were swapped in inner loop, then break
    if (!swapped) break;
  }
  return arr;
};`;

    appendChatMessage("assistant", "I've refactored your Bubble Sort using ES6 destructuring for swaps, and implemented an early termination flag `swapped`. This improves the best-case time complexity to $O(N)$! Check the editor workspace.");
    document.getElementById("vibe-editor").value = refactoredCode;
    localStorage.setItem("vibe_workspace_code", refactoredCode);
  }, 1200);
}

// 3. Complexity Prompt
function handleComplexity() {
  appendChatMessage("user", "Analyze the time and space complexity of the code in my editor.");
  
  setTimeout(() => {
    const analysis = `
      <strong>Complexity Analysis (Bubble Sort):</strong><br><br>
      • <strong>Time Complexity:</strong><br>
      &nbsp;&nbsp;- <em>Worst Case:</em> $O(N^2)$ (when the array is reverse sorted).<br>
      &nbsp;&nbsp;- <em>Average Case:</em> $O(N^2)$ (double loop comparisons).<br>
      &nbsp;&nbsp;- <em>Best Case:</em> $O(N)$ (if early break optimization is used on sorted inputs).<br><br>
      • <strong>Space Complexity:</strong> $O(1)$ auxiliary space because we swap elements in-place without copying.
    `;
    appendChatMessage("assistant", analysis);
  }, 1000);
}

// 4. Custom Message Sender
function sendCustomMessage() {
  const input = document.getElementById("vibe-chat-input");
  const query = input.value.trim();
  if (!query) return;

  appendChatMessage("user", query);
  input.value = "";

  const cleanQuery = query.toLowerCase();

  setTimeout(() => {
    if (cleanQuery.includes("quicksort") || cleanQuery.includes("quick sort")) {
      const quickCode = `function quickSort(arr) {
  if (arr.length <= 1) return arr;
  const pivot = arr[arr.length - 1];
  const left = [];
  const right = [];
  
  for (let i = 0; i < arr.length - 1; i++) {
    if (arr[i] < pivot) left.push(arr[i]);
    else right.push(arr[i]);
  }
  
  return [...quickSort(left), pivot, ...quickSort(right)];
}`;
      appendChatMessage("assistant", "Here is a clean implementation of Quick Sort (Divide-and-Conquer). I've injected it into your editor.");
      document.getElementById("vibe-editor").value = quickCode;
      localStorage.setItem("vibe_workspace_code", quickCode);
    } else if (cleanQuery.includes("binary search")) {
      const binCode = `function binarySearch(arr, target) {
  let left = 0;
  let right = arr.length - 1;
  while (left <= right) {
    let mid = Math.floor((left + right) / 2);
    if (arr[mid] === target) return mid;
    if (arr[mid] < target) left = mid + 1;
    else right = mid - 1;
  }
  return -1;
}`;
      appendChatMessage("assistant", "I've written a standard binary search function for you. Added to editor.");
      document.getElementById("vibe-editor").value = binCode;
      localStorage.setItem("vibe_workspace_code", binCode);
    } else {
      appendChatMessage("assistant", "Interesting query! I can help you write, refactor, or explain algorithms. Try requesting specific scripts like 'write quicksort' or 'write binary search'.");
    }
  }, 800);
}

// --- ALGORITHM VISUALIZER SYSTEM --- //

// A. Trigger Sorting Visualization
async function triggerSortVisualization() {
  if (sortAnimationRunning || listAnimationRunning) return;
  sortAnimationRunning = true;
  
  appendChatMessage("assistant", "Initializing sorting visualizer... Generating random dataset of 15 elements.");
  
  const container = document.getElementById("visualizer-content");
  container.innerHTML = "";
  
  // Create 15 random heights
  sortingArray = [];
  for (let i = 0; i < 15; i++) {
    sortingArray.push(Math.floor(Math.random() * 150) + 30);
  }

  // Draw initial bars
  sortingArray.forEach((h, idx) => {
    const bar = document.createElement("div");
    bar.className = "visual-bar";
    bar.style.height = `${h}px`;
    bar.style.width = "22px";
    bar.id = `bar-${idx}`;
    container.appendChild(bar);
  });

  // Run bubble sort loop
  const n = sortingArray.length;
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      // Highlight comparisons
      const barJ = document.getElementById(`bar-${j}`);
      const barNext = document.getElementById(`bar-${j+1}`);
      
      if (barJ && barNext) {
        barJ.style.background = "var(--neon-blue)";
        barNext.style.background = "var(--neon-blue)";
      }
      
      playVisualTone(sortingArray[j]);
      await sleep(150);

      if (sortingArray[j] > sortingArray[j+1]) {
        // Swap heights
        let temp = sortingArray[j];
        sortingArray[j] = sortingArray[j+1];
        sortingArray[j+1] = temp;

        if (barJ && barNext) {
          barJ.style.height = `${sortingArray[j]}px`;
          barNext.style.height = `${sortingArray[j+1]}px`;
          barJ.style.background = "var(--neon-pink)";
          barNext.style.background = "var(--neon-pink)";
        }
        await sleep(100);
      }

      if (barJ && barNext) {
        barJ.style.background = "linear-gradient(to top, var(--neon-purple), var(--neon-blue))";
        barNext.style.background = "linear-gradient(to top, var(--neon-purple), var(--neon-blue))";
      }
    }
    
    // Last element of pass is sorted
    const sortedBar = document.getElementById(`bar-${n - 1 - i}`);
    if (sortedBar) {
      sortedBar.style.background = "var(--neon-green)";
    }
  }

  // Final highlight green
  for (let i = 0; i < n; i++) {
    const bar = document.getElementById(`bar-${i}`);
    if (bar) bar.style.background = "var(--neon-green)";
  }
  
  appendChatMessage("assistant", "Sorting Completed! The dataset is now arranged in ascending order ✅");
  sortAnimationRunning = false;
}

// B. Trigger Linked List Visualization
async function triggerListVisualization() {
  if (sortAnimationRunning || listAnimationRunning) return;
  listAnimationRunning = true;
  
  appendChatMessage("assistant", "Initializing linked list visualizer. Let's animate a node insertion at index 1!");

  const container = document.getElementById("visualizer-content");
  container.innerHTML = "";
  container.style.alignItems = "center";
  container.style.flexDirection = "row";
  container.style.gap = "0.4rem";

  // Create Initial list: Head -> Node A -> Node C -> Null
  const nodes = [
    { id: "node-head", name: "Head", data: "10" },
    { id: "node-a", name: "Node A", data: "20" },
    { id: "node-c", name: "Node C", data: "40" }
  ];

  nodes.forEach((n, idx) => {
    // Render Node box
    const nodeDiv = document.createElement("div");
    nodeDiv.style.border = "1px solid var(--border-glow)";
    nodeDiv.style.background = "rgba(13, 13, 33, 0.8)";
    nodeDiv.style.padding = "0.6rem 0.8rem";
    nodeDiv.style.borderRadius = "6px";
    nodeDiv.style.fontFamily = "var(--font-mono)";
    nodeDiv.style.fontSize = "0.85rem";
    nodeDiv.style.textAlign = "center";
    nodeDiv.id = n.id;
    nodeDiv.innerHTML = `<span style="font-size:0.6rem; color:var(--text-secondary);">${n.name}</span><br><strong>${n.data}</strong>`;
    
    container.appendChild(nodeDiv);

    // Arrow pointing to next
    const arrow = document.createElement("span");
    arrow.id = `arrow-${idx}`;
    arrow.style.color = "var(--neon-blue)";
    arrow.style.fontFamily = "var(--font-mono)";
    arrow.style.fontSize = "1rem";
    arrow.style.padding = "0 0.2rem";
    arrow.textContent = "➔";
    container.appendChild(arrow);
  });

  // Null terminator
  const nullDiv = document.createElement("div");
  nullDiv.style.color = varNameToString({ "--text-muted": "" }) ? "var(--text-muted)" : "#666";
  nullDiv.style.fontFamily = "var(--font-mono)";
  nullDiv.style.fontSize = "0.85rem";
  nullDiv.innerHTML = "Null";
  container.appendChild(nullDiv);

  await sleep(1500);

  // Spawn New Node B descending from top
  const nodeB = document.createElement("div");
  nodeB.id = "node-b";
  nodeB.style.border = "1px solid var(--neon-pink)";
  nodeB.style.boxShadow = "var(--glow-pink)";
  nodeB.style.background = "rgba(13, 13, 33, 0.8)";
  nodeB.style.padding = "0.6rem 0.8rem";
  nodeB.style.borderRadius = "6px";
  nodeB.style.fontFamily = "var(--font-mono)";
  nodeB.style.fontSize = "0.85rem";
  nodeB.style.textAlign = "center";
  nodeB.style.position = "absolute";
  nodeB.style.top = "20px";
  nodeB.style.left = "45%";
  nodeB.style.transform = "translateY(-50px)";
  nodeB.style.opacity = "0";
  nodeB.style.transition = "all 0.8s ease-out";
  nodeB.innerHTML = `<span style="font-size:0.6rem; color:var(--neon-pink);">New Node B</span><br><strong>30</strong>`;
  
  document.querySelector(".visualizer-canvas-box").appendChild(nodeB);
  
  // Animate descent
  await sleep(100);
  nodeB.style.transform = "translateY(50px)";
  nodeB.style.opacity = "1";
  playVisualTone(350);

  await sleep(1500);

  // Step 1: Sever Arrow between Node A and Node C
  appendChatMessage("assistant", "Severing link between Node A and Node C...");
  const arrowA_C = document.getElementById("arrow-1");
  arrowA_C.style.color = "var(--neon-pink)";
  arrowA_C.textContent = "✖";
  playVisualTone(150);

  await sleep(1800);

  // Step 2: Link Node B to Node C
  appendChatMessage("assistant", "Linking New Node B.next to Node C...");
  nodeB.style.borderColor = "var(--neon-purple)";
  nodeB.style.boxShadow = "var(--glow-purple)";
  playVisualTone(400);

  await sleep(1500);

  // Step 3: Link Node A to Node B and clean up Layout
  appendChatMessage("assistant", "Linking Node A.next to Node B. Insertion complete!");
  playChimeSound();

  // Reset visual layouts inside content
  container.innerHTML = "";
  nodeB.remove();

  // Draw final chain
  const finalNodes = [
    { name: "Head", data: "10" },
    { name: "Node A", data: "20" },
    { name: "Node B", data: "30" },
    { name: "Node C", data: "40" }
  ];

  finalNodes.forEach((n, idx) => {
    const nodeDiv = document.createElement("div");
    nodeDiv.style.border = "1px solid var(--neon-green)";
    nodeDiv.style.boxShadow = "var(--glow-green)";
    nodeDiv.style.background = "rgba(13, 13, 33, 0.8)";
    nodeDiv.style.padding = "0.6rem 0.8rem";
    nodeDiv.style.borderRadius = "6px";
    nodeDiv.style.fontFamily = "var(--font-mono)";
    nodeDiv.style.fontSize = "0.85rem";
    nodeDiv.style.textAlign = "center";
    nodeDiv.innerHTML = `<span style="font-size:0.6rem; color:var(--text-secondary);">${n.name}</span><br><strong>${n.data}</strong>`;
    
    container.appendChild(nodeDiv);

    const arrow = document.createElement("span");
    arrow.style.color = "var(--neon-green)";
    arrow.style.fontFamily = "var(--font-mono)";
    arrow.style.fontSize = "1rem";
    arrow.style.padding = "0 0.2rem";
    arrow.textContent = "➔";
    container.appendChild(arrow);
  });

  const finalNull = document.createElement("div");
  finalNull.style.color = "#666";
  finalNull.style.fontFamily = "var(--font-mono)";
  finalNull.style.fontSize = "0.85rem";
  finalNull.innerHTML = "Null";
  container.appendChild(finalNull);

  listAnimationRunning = false;
}

// Visualizer helper routines
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function playVisualTone(freq) {
  if (!window.AudioContext && !window.webkitAudioContext) return;
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    
    osc.type = "sine";
    // Scale height frequency
    osc.frequency.setValueAtTime(freq + 150, audioCtx.currentTime);
    
    gain.gain.setValueAtTime(0.02, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.1);
    
    osc.start();
    osc.stop(audioCtx.currentTime + 0.1);
  } catch (e) {}
}

function playChimeSound() {
  if (!window.AudioContext && !window.webkitAudioContext) return;
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.type = "triangle";
    osc.frequency.setValueAtTime(440, audioCtx.currentTime);
    osc.frequency.setValueAtTime(554, audioCtx.currentTime + 0.1);
    osc.frequency.setValueAtTime(659, audioCtx.currentTime + 0.2);
    gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.3);
  } catch (e) {}
}

function varNameToString(obj) {
  return Object.keys(obj)[0];
}
