const api = {
  getSettings: () => fetch('/api/settings').then((r) => r.json()),
  saveSettings: (payload) =>
    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),
  uploadKb: (formData) =>
    fetch('/api/kb/upload', {
      method: 'POST',
      body: formData,
    }).then((r) => r.json()),
  reindex: (source_paths) =>
    fetch('/api/kb/reindex', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_paths }),
    }).then((r) => r.json()),
  chat: (payload) =>
    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then((r) => r.json()),
};

const existingSession = localStorage.getItem('arvinds_bot_session_id');
const sessionId = existingSession || `sess_${Math.random().toString(36).slice(2)}`;
if (!existingSession) {
  localStorage.setItem('arvinds_bot_session_id', sessionId);
}

const els = {
  messages: document.getElementById('messages'),
  userInput: document.getElementById('userInput'),
  sendBtn: document.getElementById('sendBtn'),
  kbFiles: document.getElementById('kbFiles'),
  uploadBtn: document.getElementById('uploadBtn'),
  sourcePaths: document.getElementById('sourcePaths'),
  reindexBtn: document.getElementById('reindexBtn'),
  apiKey: document.getElementById('apiKey'),
  apiKeyState: document.getElementById('apiKeyState'),
  modelName: document.getElementById('modelName'),
  contextWindow: document.getElementById('contextWindow'),
  topK: document.getElementById('topK'),
  threshold: document.getElementById('threshold'),
  enableImages: document.getElementById('enableImages'),
  systemPrompt: document.getElementById('systemPrompt'),
  saveSettingsBtn: document.getElementById('saveSettingsBtn'),
  status: document.getElementById('status'),
};

const defaultKbPaths = [
  '/Users/sanskar/Downloads/Compliance Handbook (1).docx',
  '/Users/sanskar/Downloads/SE_SAFETY DOC.docx',
  '/Users/sanskar/Downloads/Security Alert Configuration Guide (1).docx',
  '/Users/sanskar/Downloads/Security Dashboard (1) (1).docx',
];

function addMessage(kind, text) {
  const div = document.createElement('div');
  div.className = `message ${kind}`;
  div.textContent = text;
  els.messages.appendChild(div);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function setStatus(text) {
  els.status.textContent = text;
}

async function loadSettings() {
  const s = await api.getSettings();
  els.apiKey.value = '';
  els.apiKeyState.textContent = s.has_api_key ? 'API key is configured.' : 'API key is not configured.';
  els.modelName.value = s.model_name;
  els.contextWindow.value = s.context_window_turns;
  els.topK.value = s.top_k;
  els.threshold.value = s.similarity_threshold;
  els.systemPrompt.value = s.system_prompt;
  els.enableImages.checked = Boolean(s.enable_image_understanding);
}

async function sendMessage() {
  const msg = els.userInput.value.trim();
  if (!msg) return;
  els.userInput.value = '';
  addMessage('user', msg);
  setStatus('Thinking...');
  try {
    const res = await api.chat({ session_id: sessionId, message: msg });
    addMessage('bot', res.answer || 'No response');
    setStatus(res.escalated ? 'High priority case detected.' : 'Ready');
  } catch (e) {
    setStatus('Chat failed. Check server logs.');
  }
}

els.sendBtn.addEventListener('click', sendMessage);
els.userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

els.saveSettingsBtn.addEventListener('click', async () => {
  const payload = {
    system_prompt: els.systemPrompt.value,
    model_name: els.modelName.value,
    context_window_turns: Number(els.contextWindow.value),
    top_k: Number(els.topK.value),
    similarity_threshold: Number(els.threshold.value),
    enable_image_understanding: Boolean(els.enableImages.checked),
  };
  if (els.apiKey.value.trim()) {
    payload.anthropic_api_key = els.apiKey.value.trim();
  }
  setStatus('Saving settings...');
  const res = await api.saveSettings(payload);
  els.apiKey.value = '';
  els.apiKeyState.textContent = res.has_api_key ? 'API key is configured.' : 'API key is not configured.';
  setStatus('Settings saved.');
});

els.uploadBtn.addEventListener('click', async () => {
  const files = els.kbFiles.files;
  if (!files.length) {
    setStatus('Select at least one .docx file first.');
    return;
  }
  const fd = new FormData();
  Array.from(files).forEach((f) => fd.append('files', f));
  setStatus('Uploading files...');
  const res = await api.uploadKb(fd);
  setStatus(`Uploaded ${res.uploaded.length} file(s).`);
});

els.reindexBtn.addEventListener('click', async () => {
  const sources = els.sourcePaths.value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  setStatus('Rebuilding vector DB... this may take a while.');
  try {
    const res = await api.reindex(sources);
    setStatus(`Indexed ${res.indexed_files.length} file(s), ${res.chunks} chunks.`);
  } catch (e) {
    setStatus('Reindex failed. Confirm source paths and API key.');
  }
});

addMessage(
  'bot',
  "Hello, I'm Arvind's Bot. Ask me anything about onboarding and integration from your knowledge base."
);
loadSettings();
if (!els.sourcePaths.value.trim()) {
  els.sourcePaths.value = defaultKbPaths.join(', ');
}
