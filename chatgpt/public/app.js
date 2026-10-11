let currentSessionId = '';
let isGenerating = false;

// DOM Elements
const sidebar = document.getElementById('app-sidebar');
const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const toggleSettingsBtn = document.getElementById('toggle-settings-btn');
const closeSettingsBtn = document.getElementById('close-settings-btn');
const settingsPanel = document.getElementById('settings-panel');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const historyList = document.getElementById('history-list');
const activeChatTitle = document.getElementById('active-chat-title');
const activeModelName = document.getElementById('active-model-name');
const statusText = document.getElementById('status-text');
const statusSpinner = document.getElementById('status-spinner');

// Config Form Inputs
const modelSelect = document.getElementById('model-select');
const promptSelect = document.getElementById('prompt-select');
const promptPreview = document.getElementById('prompt-preview');
const temperatureSlider = document.getElementById('temperature-slider');
const temperatureValue = document.getElementById('temperature-value');
const tokensSlider = document.getElementById('tokens-slider');
const tokensValue = document.getElementById('tokens-value');

// Diagnostics
const diagGemini = document.getElementById('diag-gemini');
const diagOpenai = document.getElementById('diag-openai');
const diagAnthropic = document.getElementById('diag-anthropic');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  loadHarnessConfig();
  loadPromptsList();
  loadSessionHistory();
  setupEventListeners();
  startNewChat();
});

function setupEventListeners() {
  // Sidebar toggle
  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
    });
  }

  // Input Auto-Grow and Send on Enter
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = (chatInput.scrollHeight - 4) + 'px';
    sendBtn.disabled = !chatInput.value.trim() || isGenerating;
  });

  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);
  newChatBtn.addEventListener('click', startNewChat);

  // Settings Drawer Toggle
  toggleSettingsBtn.addEventListener('click', () => {
    settingsPanel.classList.toggle('hidden');
    if (!settingsPanel.classList.contains('hidden')) {
      loadDiagnostics();
    }
  });
  closeSettingsBtn.addEventListener('click', () => settingsPanel.classList.add('hidden'));

  // Slider Updates
  temperatureSlider.addEventListener('input', (e) => {
    temperatureValue.textContent = e.target.value;
  });
  tokensSlider.addEventListener('input', (e) => {
    tokensValue.textContent = e.target.value;
  });

  // Prompt select auto-preview
  promptSelect.addEventListener('change', () => {
    const selected = promptSelect.value;
    const prompts = promptSelect.dataset.prompts ? JSON.parse(promptSelect.dataset.prompts) : [];
    const found = prompts.find(p => p.name === selected);
    promptPreview.value = found ? found.content : '';
  });

  // Save Settings
  saveSettingsBtn.addEventListener('click', saveHarnessSettings);

  // Suggestions Card Clicks
  document.addEventListener('click', (e) => {
    const card = e.target.closest('.suggestion-card');
    if (card) {
      chatInput.value = card.dataset.prompt;
      chatInput.focus();
      chatInput.dispatchEvent(new Event('input'));
    }
  });
}

// Start a Fresh Session
function startNewChat() {
  currentSessionId = `session_${Date.now()}`;
  chatMessages.innerHTML = `
    <div class="welcome-screen">
      <div class="welcome-badge">SYSTEM ONLINE</div>
      <h1 class="gemini-greeting">Hello, Sandbox</h1>
      <h2 class="gemini-subheading">How can I help you today?</h2>
      <p class="gemini-intro">Ask questions, execute code locally, search the web in real-time, or generate visually rich vector assets.</p>
      
      <div class="suggestions-grid">
        <div class="suggestion-card" data-prompt="Write a Python script to compute the first 10 prime numbers and run it.">
          <h4>🐍 Python Sandbox</h4>
          <p>Write & execute code locally to get answers.</p>
        </div>
        <div class="suggestion-card" data-prompt="Search the web for the latest SpaceX launch status and summarize.">
          <h4>🌐 Web Search</h4>
          <p>Fetch real-time documentation or news.</p>
        </div>
        <div class="suggestion-card" data-prompt="Generate an image of a cybernetic space banana floating in a neon galaxy.">
          <h4>🎨 Image Generator</h4>
          <p>Generate high-quality cached art.</p>
        </div>
      </div>
    </div>
  `;
  activeChatTitle.textContent = 'New Conversation';
  updateActiveSidebarItem();
  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;
}

// Set status messaging
function setStatus(text, showSpinner = false) {
  statusText.textContent = text;
  if (showSpinner) {
    statusSpinner.classList.remove('hidden');
  } else {
    statusSpinner.classList.add('hidden');
  }
}

// Load configurations
async function loadHarnessConfig() {
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    
    activeModelName.textContent = data.defaultModel;
    
    // Select correct option or build options
    modelSelect.innerHTML = data.models.map(m => `
      <option value="${m}" ${m === data.defaultModel ? 'selected' : ''}>${m}</option>
    `).join('');

    temperatureSlider.value = data.temperature;
    temperatureValue.textContent = data.temperature;
    
    tokensSlider.value = data.maxTokens;
    tokensValue.textContent = data.maxTokens;
  } catch (err) {
    console.error('Failed to load configuration', err);
    setStatus('Config load failed');
  }
}

// Load prompts list
async function loadPromptsList() {
  try {
    const res = await fetch('/api/prompts');
    const prompts = await res.json();
    
    promptSelect.dataset.prompts = JSON.stringify(prompts);
    
    // Find active config prompt
    const configRes = await fetch('/api/config');
    const config = await configRes.json();

    promptSelect.innerHTML = prompts.map(p => `
      <option value="${p.name}" ${p.name === config.activePrompt ? 'selected' : ''}>${p.name}</option>
    `).join('');

    const activePromptObj = prompts.find(p => p.name === config.activePrompt);
    promptPreview.value = activePromptObj ? activePromptObj.content : '';
  } catch (err) {
    console.error('Failed to load prompts', err);
  }
}

// Save active harness settings
async function saveHarnessSettings() {
  const settings = {
    defaultModel: modelSelect.value,
    activePrompt: promptSelect.value,
    temperature: parseFloat(temperatureSlider.value),
    maxTokens: parseInt(tokensSlider.value)
  };

  try {
    setStatus('Updating config...', true);
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    
    const result = await res.json();
    if (result.success) {
      activeModelName.textContent = result.config.defaultModel;
      setStatus('Config updated');
      settingsPanel.classList.add('hidden');
    }
  } catch (err) {
    console.error('Failed to save configs', err);
    setStatus('Update config failed');
  }
}

// Diagnostics helper
function loadDiagnostics() {
  fetch('/api/config')
    .then(r => r.json())
    .then(() => {
      diagGemini.textContent = 'Configured';
      diagGemini.className = 'status-dot configured';
      diagOpenai.textContent = 'Configured';
      diagOpenai.className = 'status-dot configured';
      diagAnthropic.textContent = 'Configured';
      diagAnthropic.className = 'status-dot configured';
    });
}

// Load sidebar sessions
async function loadSessionHistory() {
  try {
    const res = await fetch('/api/history');
    const list = await res.json();
    
    if (list.length === 0) {
      historyList.innerHTML = '<div class="history-item"><div class="history-title">No previous chats</div></div>';
      return;
    }

    historyList.innerHTML = list.map(session => `
      <div class="history-item ${session.sessionId === currentSessionId ? 'active' : ''}" data-id="${session.sessionId}">
        <div class="history-item-content">
          <svg class="history-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          <span class="history-title">${escapeHTML(session.title)}</span>
        </div>
        <button class="btn-delete-session" title="Delete conversation">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        </button>
      </div>
    `).join('');

    // Setup history clicks
    document.querySelectorAll('.history-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if (e.target.closest('.btn-delete-session')) {
          e.stopPropagation();
          deleteSession(item.dataset.id);
          return;
        }
        loadSession(item.dataset.id);
      });
    });
  } catch (err) {
    console.error('Failed to load session history', err);
  }
}

// Switch active sidebar highlight
function updateActiveSidebarItem() {
  document.querySelectorAll('.history-item').forEach(item => {
    if (item.dataset.id === currentSessionId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
}

// Load a specific conversation session
async function loadSession(sessionId) {
  try {
    setStatus('Loading session...', true);
    const res = await fetch(`/api/history/${sessionId}`);
    const session = await res.json();
    
    currentSessionId = sessionId;
    updateActiveSidebarItem();
    chatMessages.innerHTML = '';
    
    if (session.messages.length === 0) {
      startNewChat();
      setStatus('Harness Ready');
      return;
    }

    activeChatTitle.textContent = session.messages.find(m => m.role === 'user')?.content.substring(0, 30) || 'Active Chat';

    // Populate message bubbles
    session.messages.forEach(msg => {
      if (msg.role === 'system' && msg.content.includes('System Notification')) {
        return;
      }
      if (msg.role === 'system') return; // Skip standard instructions
      if (msg.role === 'tool') return; // Renders inline with assistant tool call

      if (msg.role === 'user') {
        appendUserMessage(msg.content);
      } else if (msg.role === 'assistant') {
        appendAssistantMessage(msg.content, msg.toolCalls, msg.id, false);
      }
    });

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    setStatus('Harness Ready');
  } catch (err) {
    console.error('Failed to load session', err);
    setStatus('Load session failed');
  }
}

// Delete session
async function deleteSession(sessionId) {
  try {
    const res = await fetch(`/api/history/${sessionId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      if (sessionId === currentSessionId) {
        startNewChat();
      }
      loadSessionHistory();
    }
  } catch (err) {
    console.error('Failed to delete session', err);
  }
}

// Send user message
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || isGenerating) return;

  isGenerating = true;
  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;

  // Clear welcome screen if present
  if (chatMessages.querySelector('.welcome-screen')) {
    chatMessages.innerHTML = '';
    activeChatTitle.textContent = text.substring(0, 30) + (text.length > 30 ? '...' : '');
  }

  appendUserMessage(text);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Prepare Assistant stream container
  const assistantMsgId = `msg_${Date.now()}`;
  const assistantBubble = appendAssistantMessage('', null, assistantMsgId, true);
  const assistantBody = assistantBubble.querySelector('.message-body');

  setStatus('Thinking...', true);

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: currentSessionId,
        message: text
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split('\n\n');
      
      buffer = blocks.pop() || '';

      for (const block of blocks) {
        const lines = block.split('\n');
        let event = '';
        let dataStr = '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            event = line.replace('event:', '').trim();
          } else if (line.startsWith('data:')) {
            dataStr = line.replace('data:', '').trim();
          }
        }

        if (event && dataStr) {
          try {
            const data = JSON.parse(dataStr);
            handleSSEEvent(event, data, assistantBody, assistantMsgId);
          } catch (e) {
            console.error('Error parsing SSE event data', e);
          }
        }
      }
    }

  } catch (err) {
    console.error('Chat execution error', err);
    setStatus('Execution error');
    assistantBody.innerHTML = `<div class="error-text">Harness Error: ${err.message}</div>`;
    assistantBody.classList.remove('streaming');
  } finally {
    isGenerating = false;
    sendBtn.disabled = !chatInput.value.trim();
    loadSessionHistory();
  }
}

// Handle incoming SSE stream events
function handleSSEEvent(event, data, bodyContainer, messageId) {
  switch (event) {
    case 'status':
      setStatus(data.message, true);
      break;

    case 'tool_start':
      setStatus(`Running ${data.name} tool...`, true);
      appendToolExecutionLog(bodyContainer, data.name, data.args, data.id);
      break;

    case 'tool_end':
      setStatus(`Tool completed`, true);
      updateToolExecutionLog(bodyContainer, data.name, data.result, data.id);
      break;

    case 'token':
      bodyContainer.classList.add('streaming');
      const textSpan = bodyContainer.querySelector('.text-content') || createTextSpan(bodyContainer);
      textSpan.innerHTML = formatMarkdown(textSpan.dataset.raw + data);
      textSpan.dataset.raw += data;
      chatMessages.scrollTop = chatMessages.scrollHeight;
      break;

    case 'complete':
      setStatus('Harness Ready', false);
      bodyContainer.classList.remove('streaming');
      chatMessages.scrollTop = chatMessages.scrollHeight;
      break;

    case 'error':
      setStatus('Error occurred');
      bodyContainer.classList.remove('streaming');
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-text';
      errorDiv.textContent = `Error: ${data.message}`;
      bodyContainer.appendChild(errorDiv);
      break;
  }
}

function createTextSpan(container) {
  const span = document.createElement('span');
  span.className = 'text-content';
  span.dataset.raw = '';
  container.appendChild(span);
  return span;
}

// UI Append user message element
function appendUserMessage(text) {
  const msg = document.createElement('div');
  msg.className = 'message user';
  msg.innerHTML = `
    <div class="message-body">${escapeHTML(text)}</div>
  `;
  chatMessages.appendChild(msg);
  return msg;
}

// UI Append flat assistant message element
function appendAssistantMessage(content, toolCalls, msgId, isStreaming = false) {
  const msg = document.createElement('div');
  msg.className = 'message assistant';
  msg.id = msgId;

  const header = `
    <div class="message-header">
      <span class="message-header-title">
        Neural Assistant
      </span>
      <span>${new Date().toLocaleTimeString()}</span>
    </div>
  `;

  const body = document.createElement('div');
  body.className = 'message-body';
  if (isStreaming) {
    body.classList.add('streaming');
  }

  msg.innerHTML = header;
  msg.appendChild(body);
  chatMessages.appendChild(msg);

  if (content || toolCalls) {
    const textSpan = createTextSpan(body);
    textSpan.innerHTML = formatMarkdown(content || '');
    textSpan.dataset.raw = content || '';

    if (toolCalls && toolCalls.length) {
      toolCalls.forEach(tc => {
        appendToolExecutionLog(body, tc.name, tc.args, tc.id);
        updateToolExecutionLog(body, tc.name, JSON.stringify({ status: 'completed' }), tc.id);
      });
    }
  }

  return msg;
}

// Append collapsible tool log
function appendToolExecutionLog(container, name, args, id) {
  const block = document.createElement('div');
  block.className = 'tool-block';
  block.id = `tool_${id}`;

  const icon = name === 'codeExec' ? '🐍' : name === 'search' ? '🌐' : '🎨';
  const displayTitle = name === 'codeExec' ? 'Python/JS Execution' : name === 'search' ? 'Web Search Scraper' : 'Imagen Image Generator';

  block.innerHTML = `
    <div class="tool-header" onclick="this.parentElement.classList.toggle('open')">
      <div class="tool-header-title">
        <span>${icon}</span>
        <strong>${displayTitle}</strong>
      </div>
      <div class="tool-header-status">executing...</div>
    </div>
    <div class="tool-body">
      <p style="font-size: 0.75rem; margin-bottom: 6px; color: var(--text-muted);">Arguments:</p>
      <pre><code>${escapeHTML(JSON.stringify(args, null, 2))}</code></pre>
      <div class="tool-output-container"></div>
    </div>
  `;

  const textSpan = container.querySelector('.text-content');
  if (textSpan) {
    container.insertBefore(block, textSpan);
  } else {
    container.appendChild(block);
  }
  
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update tool logs with outputs
function updateToolExecutionLog(container, name, result, id) {
  const block = container.querySelector(`#tool_${id}`);
  if (!block) return;

  const headerStatus = block.querySelector('.tool-header-status');
  headerStatus.textContent = 'completed';
  headerStatus.style.color = 'var(--success)';

  const outputContainer = block.querySelector('.tool-output-container');
  let parsedResult;
  try {
    parsedResult = JSON.parse(result);
  } catch (e) {
    parsedResult = { raw: result };
  }

  if (name === 'search') {
    if (parsedResult.results && parsedResult.results.length) {
      outputContainer.innerHTML = `
        <p style="font-size: 0.75rem; margin: 8px 0 4px; color: var(--text-muted);">Results:</p>
        <div class="search-results">
          ${parsedResult.results.map(r => `
            <div class="search-item">
              <a href="${r.url}" target="_blank">${escapeHTML(r.title)}</a>
              <p>${escapeHTML(r.snippet)}</p>
            </div>
          `).join('')}
        </div>
      `;
    } else {
      outputContainer.innerHTML = `<p style="font-size: 0.75rem; color: var(--error); margin-top: 8px;">No search results found or rate limited.</p>`;
    }
  } else if (name === 'codeExec') {
    const successColor = parsedResult.success ? 'var(--success)' : 'var(--error)';
    outputContainer.innerHTML = `
      <p style="font-size: 0.75rem; margin: 8px 0 4px; color: var(--text-muted);">Console Output:</p>
      <pre><code style="color: ${successColor}">${escapeHTML(parsedResult.stdout || '(no output)')}</code></pre>
      ${parsedResult.stderr ? `
        <p style="font-size: 0.75rem; margin: 4px 0; color: var(--error);">Console Stderr:</p>
        <pre><code style="color: var(--error)">${escapeHTML(parsedResult.stderr)}</code></pre>
      ` : ''}
      ${parsedResult.error ? `<p style="font-size: 0.75rem; color: var(--error); margin-top: 4px;">Error: ${escapeHTML(parsedResult.error)}</p>` : ''}
    `;
  } else if (name === 'imageGen') {
    if (parsedResult.success && parsedResult.url) {
      outputContainer.innerHTML = `
        <p style="font-size: 0.75rem; margin: 8px 0 4px; color: var(--text-muted);">Generated Canvas Asset:</p>
        <div class="image-block">
          <img src="${parsedResult.url}" alt="${escapeHTML(parsedResult.prompt)}" />
          <div class="image-meta">
            <span>Model: ${parsedResult.provider || 'AI'}</span>
            <span class="image-badge">Stored Locally</span>
          </div>
        </div>
      `;
    } else {
      outputContainer.innerHTML = `<p style="font-size: 0.75rem; color: var(--error); margin-top: 8px;">Image generation failed: ${escapeHTML(parsedResult.error)}</p>`;
    }
  }

  block.classList.add('open');
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Markdown formatting containing Google-style copy button code blocks
function formatMarkdown(text) {
  if (!text) return '';

  let html = escapeHTML(text);

  // Match and parse code blocks ```lang code ```
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const displayLang = lang || 'code';
    const cleanCode = code.trim();
    return `<div class="code-container">
      <div class="code-header">
        <span>${displayLang}</span>
        <button class="btn-copy" onclick="copyCode(this)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          Copy code
        </button>
      </div>
      <pre><code class="language-${lang}">${cleanCode}</code></pre>
    </div>`;
  });

  // Match and parse inline code `code`
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');

  // Match and parse bold text **bold**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Match and parse bullet lists
  html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>');
  html = html.replace(/<\/ul>\s*<ul>/g, '');

  html = html.split('\n').map(line => {
    if (line.trim().startsWith('<pre') || line.trim().startsWith('<li') || line.trim().startsWith('<ul') || line.trim().startsWith('</ul') || line.trim().startsWith('<div') || line.trim().startsWith('</div')) {
      return line;
    }
    return line + '<br>';
  }).join('\n');

  return html;
}

// Clipboard copying utility
window.copyCode = (button) => {
  const codeContainer = button.closest('.code-container');
  const codeElement = codeContainer.querySelector('pre code');
  const textToCopy = codeElement.innerText;
  
  navigator.clipboard.writeText(textToCopy).then(() => {
    const originalText = button.innerHTML;
    button.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
      Copied!
    `;
    setTimeout(() => {
      button.innerHTML = originalText;
    }, 2000);
  });
};

function escapeHTML(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
