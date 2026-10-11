// Leaderboard & Badges Controller

// Mock Global ranks
const mockGlobalList = [
  { name: "AStarMaster 🛰", xp: 1250, level: 4, badges: ["ai_novice", "level_3", "arena_first"] },
  { name: "DeepLearnHero 🧠", xp: 950, level: 3, badges: ["ml_novice", "level_3"] },
  { name: "BinaryBoss ⚔️", xp: 810, level: 3, badges: ["dsa_novice", "arena_first"] },
  { name: "GradientGuru 📉", xp: 620, level: 2, badges: ["ml_novice"] },
  { name: "ByteWizard 🧙‍♂️", xp: 400, level: 2, badges: ["dsa_novice"] },
  { name: "CyberCoder 💻", xp: 250, level: 1, badges: [] },
  { name: "StackStar 📚", xp: 120, level: 1, badges: [] }
];

// Mock Friends ranks
const mockFriendsList = [
  { name: "CodeChamp 🥇", xp: 750, level: 3, badges: ["dsa_novice", "arena_first"] },
  { name: "AlgoQueen 👑", xp: 510, level: 2, badges: ["dsa_novice"] },
  { name: "StackSlayer 🗡", xp: 180, level: 1, badges: [] },
  { name: "LogicLoop 🔄", xp: 90, level: 1, badges: [] }
];

let activeTab = 'global';

document.addEventListener("DOMContentLoaded", () => {
  initLeaderboard();
});

async function initLeaderboard() {
  // Wait a small bit to ensure progress.js loaded and synced
  setTimeout(() => {
    renderRanks();
    syncBadgesCabinet();
  }, 300);

  document.getElementById("tab-global").addEventListener("click", () => {
    switchTab('global');
  });

  document.getElementById("tab-friends").addEventListener("click", () => {
    switchTab('friends');
  });
}

function switchTab(tab) {
  activeTab = tab;
  
  const tabGlobal = document.getElementById("tab-global");
  const tabFriends = document.getElementById("tab-friends");

  if (tab === 'global') {
    tabGlobal.className = "btn btn-blue";
    tabFriends.className = "btn btn-secondary";
  } else {
    tabGlobal.className = "btn btn-secondary";
    tabFriends.className = "btn btn-blue";
  }

  renderRanks();
}

// Render rankings table
function renderRanks() {
  const tbody = document.getElementById("leaderboard-body");
  tbody.innerHTML = "";

  // Get active list template
  let rawList = activeTab === 'global' ? [...mockGlobalList] : [...mockFriendsList];

  // Insert current user in list
  const userRow = {
    name: "YOU (Cadet)",
    xp: window.userProgress.xp,
    level: window.userProgress.level,
    badges: window.userProgress.unlockedBadges,
    isUser: true
  };
  rawList.push(userRow);

  // Sort by XP descending
  rawList.sort((a, b) => b.xp - a.xp);

  rawList.forEach((player, index) => {
    const rank = index + 1;
    const tr = document.createElement("tr");
    if (player.isUser) {
      tr.className = "user-row";
    }

    // Rank badge styling
    let rankBadgeClass = "";
    if (rank === 1) rankBadgeClass = "rank-badge rank-1";
    else if (rank === 2) rankBadgeClass = "rank-badge rank-2";
    else if (rank === 3) rankBadgeClass = "rank-badge rank-3";
    else rankBadgeClass = "rank-badge";

    const badgeIcons = {
      ml_novice: "📉",
      ai_novice: "🛰",
      dsa_novice: "⛓",
      level_3: "🥉",
      level_5: "🥈",
      arena_first: "⚔️"
    };

    const playerBadgesRendered = player.badges.map(bId => badgeIcons[bId] || "🏆").join(" ");

    tr.innerHTML = `
      <td><span class="${rankBadgeClass}">${rank}</span></td>
      <td style="font-weight: ${player.isUser ? 'bold' : 'normal'}; color: ${player.isUser ? 'var(--neon-purple)' : '#fff'}">
        ${player.name}
      </td>
      <td style="font-family:var(--font-mono);">${player.xp} XP</td>
      <td>Lvl ${player.level}</td>
      <td style="font-size:1.1rem;">${playerBadgesRendered || '<span style="color:var(--text-muted); font-size:0.75rem;">None</span>'}</td>
    `;

    tbody.appendChild(tr);
  });
}

// Highlight unlocked badges in cabinet
function syncBadgesCabinet() {
  const userBadges = window.userProgress.unlockedBadges || [];

  userBadges.forEach(badgeId => {
    const el = document.getElementById(`badge-${badgeId}`);
    if (el) {
      el.classList.add("unlocked");
      el.style.opacity = "1";
      el.style.filter = "none";
    }
  });
}
