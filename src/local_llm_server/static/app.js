/**
 * app.js — Main Orchestrator for Local LLM Studio
 */

document.addEventListener('DOMContentLoaded', () => {

    // ═══════════════════════════════════════════════════════════════════════════
    // DOM Elements
    // ═══════════════════════════════════════════════════════════════════════════
    const dom = {
        // Tabs
        tabLinks: document.querySelectorAll('.tab-link'),
        tabPanels: document.querySelectorAll('.tab-panel'),

        // Theme & Status
        themeToggle: document.getElementById('theme-toggle'),
        serverStatus: document.getElementById('server-status'),
        serverStatusDot: document.querySelector('#server-status .status-badge__dot'),
        serverStatusText: document.querySelector('#server-status .status-badge__text'),

        // Chat
        chatForm: document.getElementById('chat-params-form'),
        chatMessages: document.getElementById('chat-messages-container'),
        chatTextarea: document.getElementById('chat-textarea'),
        sendChatBtn: document.getElementById('send-chat-btn'),
        clearChatBtn: document.getElementById('clear-chat-btn'),
        modelSelect: document.getElementById('model-select'),
        defaultModelOpt: document.getElementById('default-model-opt'),
        typingStatus: document.getElementById('typing-status'),
        typingText: document.getElementById('typing-text'),
        forceJsonCheckbox: document.getElementById('param-force-json'),
        showThinkingCheckbox: document.getElementById('param-show-thinking'),

        // Logs
        logSearch: document.getElementById('log-search-input'),
        logAutoscroll: document.getElementById('log-autoscroll-check'),
        clearLogsBtn: document.getElementById('clear-logs-btn'),
        downloadLogsBtn: document.getElementById('download-logs-btn'),
        serverLogsBody: document.getElementById('server-logs-body'),
        logLineCount: document.getElementById('log-line-count'),
        sseIndicator: document.getElementById('sse-indicator'),

        // Registry & Config
        cfgHost: document.getElementById('cfg-host'),
        cfgPort: document.getElementById('cfg-port'),
        cfgBackend: document.getElementById('cfg-backend'),
        cfgModelPath: document.getElementById('cfg-model-path'),
        modelsContainer: document.getElementById('models-list-container'),
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // State
    // ═══════════════════════════════════════════════════════════════════════════
    let isServerOnline = false;
    let sseSource = null;
    let rawLogLines = []; // Store raw text lines for search/download
    let chatHistory = []; // {role, content}
    let isGenerating = false;
    let statusInterval = null;

    // Toast Duration (ms)
    const TOAST_DURATION_MS = 4000;

    // ═══════════════════════════════════════════════════════════════════════════
    // Toast Notification System
    // ═══════════════════════════════════════════════════════════════════════════
    const Toast = {
        show(message, type = 'success') {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = `toast toast--${type}`;
            toast.textContent = message;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(12px)';
                setTimeout(() => toast.remove(), 300);
            }, TOAST_DURATION_MS);
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // Init & Health polling
    // ═══════════════════════════════════════════════════════════════════════════
    function init() {
        // Theme init
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);

        bindEvents();
        checkServerHealth();
        setInterval(checkServerHealth, 10000); // Poll health every 10 seconds

        // Connect to Logs Stream
        connectLogsStream();
        loadRegistryModels();

        // Load Force JSON state
        if (dom.forceJsonCheckbox) {
            const savedForceJson = localStorage.getItem('force_json') === 'true';
            dom.forceJsonCheckbox.checked = savedForceJson;
        }

        // Load Show Thinking state
        if (dom.showThinkingCheckbox) {
            const savedShowThinking = localStorage.getItem('show_thinking') !== 'false';
            dom.showThinkingCheckbox.checked = savedShowThinking;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Bindings
    // ═══════════════════════════════════════════════════════════════════════════
    function bindEvents() {
        // Tab switching
        dom.tabLinks.forEach(link => {
            link.addEventListener('click', () => {
                const targetTab = link.dataset.tab;
                switchTab(targetTab);
            });
        });

        // Theme switcher
        dom.themeToggle.addEventListener('click', toggleTheme);

        // Chat controls
        dom.sendChatBtn.addEventListener('click', handleUserSendMessage);
        dom.chatTextarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleUserSendMessage();
            }
        });
        dom.clearChatBtn.addEventListener('click', clearChat);

        // Logs toolbar
        dom.clearLogsBtn.addEventListener('click', () => {
            dom.serverLogsBody.innerHTML = '';
            rawLogLines = [];
            updateLogCount();
        });

        dom.logSearch.addEventListener('input', () => {
            filterLogs(dom.logSearch.value);
        });

        dom.downloadLogsBtn.addEventListener('click', downloadLogs);

        if (dom.forceJsonCheckbox) {
            dom.forceJsonCheckbox.addEventListener('change', (e) => {
                localStorage.setItem('force_json', e.target.checked);
            });
        }

        if (dom.showThinkingCheckbox) {
            dom.showThinkingCheckbox.addEventListener('change', (e) => {
                localStorage.setItem('show_thinking', e.target.checked);
            });
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Tab & Theme Control
    // ═══════════════════════════════════════════════════════════════════════════
    function switchTab(tabId) {
        dom.tabLinks.forEach(btn => {
            if (btn.dataset.tab === tabId) {
                btn.classList.add('tab-link--active');
            } else {
                btn.classList.remove('tab-link--active');
            }
        });

        dom.tabPanels.forEach(panel => {
            if (panel.id === tabId) {
                panel.classList.add('tab-panel--active');
            } else {
                panel.classList.remove('tab-panel--active');
            }
        });
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Server status & Registry
    // ═══════════════════════════════════════════════════════════════════════════
    async function checkServerHealth() {
        try {
            const res = await fetch('/health');
            if (res.ok) {
                const data = await res.json();
                isServerOnline = true;
                const modelShort = data.model ? data.model.split('/').pop() : 'Model';
                setServerStatus(true, `Online (${modelShort})`);
                
                // Update System Info
                dom.cfgHost.textContent = data.host || '127.0.0.1';
                dom.cfgPort.textContent = data.port || '1235';
                dom.cfgBackend.textContent = data.backend || 'llama_cpp';
                dom.cfgModelPath.textContent = data.model_path || '-';
                
                if (dom.defaultModelOpt) {
                    dom.defaultModelOpt.textContent = `Predefinito (${modelShort})`;
                }
            } else {
                setServerStatus(false, 'Errore Server');
            }
        } catch (err) {
            setServerStatus(false, 'Disconnesso');
        }
    }

    function setServerStatus(online, text) {
        dom.serverStatusDot.className = `status-badge__dot status-badge__dot--${online ? 'online' : 'offline'}`;
        dom.serverStatusText.textContent = text;
    }

    async function loadRegistryModels() {
        try {
            const res = await fetch('/api/v1/models/registry');
            if (!res.ok) throw new Error('API registry error');
            const data = await res.json();
            
            // Popolate select dropdown
            dom.modelSelect.innerHTML = `<option value="">Predefinito del server</option>`;
            
            // Populate grid list
            dom.modelsContainer.innerHTML = '';
            
            if (data.models && data.models.length > 0) {
                data.models.forEach(model => {
                    // Populate select options
                    const opt = document.createElement('option');
                    opt.value = model.key;
                    opt.textContent = `${model.key} (${model.size_gb ? model.size_gb + ' GB' : 'Dimensione sconosciuta'})`;
                    dom.modelSelect.appendChild(opt);

                    // Populate catalog cards
                    const card = document.createElement('div');
                    card.className = 'model-card';

                    const tagsHtml = model.tags.map(t => `<span class="tag-badge">${t}</span>`).join('');
                    const statusBadge = model.downloaded 
                        ? `<span class="tag-badge tag-badge--downloaded">Scaricato</span>`
                        : `<span class="tag-badge">Non scaricato</span>`;

                    card.innerHTML = `
                        <div class="model-card__header">
                            <span class="model-card__title">${model.key}</span>
                            <div class="model-card__tags">
                                ${statusBadge}
                                ${tagsHtml}
                            </div>
                        </div>
                        <div class="model-card__body">
                            <span>ID Modello: <strong>${model.model_id}</strong></span>
                            <span>Dimensione stimata: <strong>${model.size_gb ? model.size_gb + ' GB' : 'N/A'}</strong></span>
                            <span>Percorso locale: <strong>${model.path}</strong></span>
                        </div>
                    `;
                    dom.modelsContainer.appendChild(card);
                });
            } else {
                dom.modelsContainer.innerHTML = `<div class="models-grid__placeholder">Nessun modello registrato.</div>`;
            }
        } catch (err) {
            console.error('Error loading model registry:', err);
            dom.modelsContainer.innerHTML = `<div class="models-grid__placeholder">Impossibile connettersi al catalogo modelli.</div>`;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Logs Terminal Stream (SSE)
    // ═══════════════════════════════════════════════════════════════════════════
    function connectLogsStream() {
        if (sseSource) {
            sseSource.close();
        }

        dom.sseIndicator.style.color = 'var(--text-muted)';
        dom.sseIndicator.querySelector('.active-sse-badge__dot').style.backgroundColor = 'var(--text-muted)';

        sseSource = new EventSource('/api/v1/logs/stream');

        sseSource.onopen = () => {
            dom.sseIndicator.style.color = 'var(--color-accent)';
            dom.sseIndicator.querySelector('.active-sse-badge__dot').style.backgroundColor = 'var(--color-accent)';
            
            // Remove placeholders if present
            const placeholder = dom.serverLogsBody.querySelector('.console-placeholder');
            if (placeholder) {
                placeholder.remove();
            }
        };

        sseSource.onmessage = (event) => {
            if (event.data === 'ping') return;
            appendLogLine(event.data);
        };

        sseSource.onerror = (err) => {
            console.error('Logs SSE error, retrying in 5s...', err);
            dom.sseIndicator.style.color = 'var(--color-danger)';
            dom.sseIndicator.querySelector('.active-sse-badge__dot').style.backgroundColor = 'var(--color-danger)';
            sseSource.close();
            setTimeout(connectLogsStream, 5000);
        };
    }

    function appendLogLine(lineText) {
        rawLogLines.push(lineText);
        updateLogCount();

        // Create log line div
        const div = document.createElement('div');
        div.className = 'log-line';
        
        // Parse line format to apply pretty colors
        // Example standard formats:
        // [17:34:25] INFO [local-llm.server]: ...
        // [17:34:25] ERROR ...
        // [17:34:25] WARNING ...
        // 127.0.0.1 - - [09/Jun/2026 09:22:15] "GET /health HTTP/1.1" 200 -
        
        let formatted = lineText;
        
        // Highlight dates/timestamps
        formatted = formatted.replace(/^(\[\d{2}:\d{2}:\d{2}\])/, '<span class="log-line--timestamp">$1</span>');
        formatted = formatted.replace(/^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} - - \[[^\]]+\])/, '<span class="log-line--timestamp">$1</span>');
        
        // Color logs level
        if (lineText.includes('INFO')) {
            div.classList.add('log-line--info');
        } else if (lineText.includes('ERROR') || lineText.includes('failed')) {
            div.classList.add('log-line--error');
        } else if (lineText.includes('WARNING') || lineText.includes('warn')) {
            div.classList.add('log-line--warning');
        } else if (lineText.includes('DEBUG')) {
            div.classList.add('log-line--debug');
        } else if (lineText.includes('inference') || lineText.includes('generating') || lineText.includes('evaluated')) {
            div.classList.add('log-line--inference');
        }

        div.innerHTML = formatted;

        // Apply filters
        const searchVal = dom.logSearch.value.toLowerCase();
        if (searchVal && !lineText.toLowerCase().includes(searchVal)) {
            div.style.display = 'none';
        }

        dom.serverLogsBody.appendChild(div);

        // Auto-scroll
        if (dom.logAutoscroll.checked) {
            dom.serverLogsBody.scrollTop = dom.serverLogsBody.scrollHeight;
        }
    }

    function updateLogCount() {
        const count = rawLogLines.length;
        dom.logLineCount.textContent = `${count} righe caricate`;
    }

    function filterLogs(query) {
        const queryLower = query.toLowerCase();
        const lines = dom.serverLogsBody.querySelectorAll('.log-line');
        lines.forEach((line, index) => {
            const rawText = rawLogLines[index] || line.innerText;
            if (rawText.toLowerCase().includes(queryLower)) {
                line.style.display = 'block';
            } else {
                line.style.display = 'none';
            }
        });
    }

    function downloadLogs() {
        const textContent = rawLogLines.join('\n');
        const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `local-llm-server-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        Toast.show('Log scaricati con successo!', 'success');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Chat Studio Generation Logic
    // ═══════════════════════════════════════════════════════════════════════════
    async function handleUserSendMessage() {
        const userText = dom.chatTextarea.value.trim();
        if (!userText || isGenerating) return;

        // Reset inputs
        dom.chatTextarea.value = '';
        dom.chatTextarea.style.height = 'auto';

        // Add user message to UI
        appendChatMessage('user', userText);
        chatHistory.push({ role: 'user', content: userText });

        isGenerating = true;
        dom.sendChatBtn.disabled = true;
        
        // Show typing indicator
        dom.typingText.textContent = "L'LLM sta valutando il prompt...";
        dom.typingStatus.style.display = 'flex';
        
        // Setup status polling
        startStatusPolling();

        // Prepare request
        const formData = new FormData(dom.chatForm);
        const model = formData.get('model');
        const temperature = parseFloat(formData.get('temperature') || '0.7');
        const max_tokens = formData.get('max_tokens') ? parseInt(formData.get('max_tokens')) : null;
        const top_p = parseFloat(formData.get('top_p') || '0.95');
        const top_k = parseInt(formData.get('top_k') || '40');
        const repeat_penalty = parseFloat(formData.get('repeat_penalty') || '1.0');
        const system_prompt = formData.get('system_prompt') || '';

        // Build messages payload
        const messages = [];
        if (system_prompt.trim()) {
            messages.push({ role: 'system', content: system_prompt.trim() });
        }
        
        // Include context history (limit to last 10 messages for context safety)
        const recentHistory = chatHistory.slice(-10);
        messages.push(...recentHistory);

        const payload = {
            messages,
            temperature,
            top_p,
            top_k,
            repeat_penalty,
            stream: false,
        };
        if (model) payload.model = model;
        if (max_tokens) payload.max_tokens = max_tokens;
        if (dom.forceJsonCheckbox && dom.forceJsonCheckbox.checked) {
            payload.response_format = { type: "json_object" };
        }

        try {
            const response = await fetch('/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Extract assistant reply and thinking block
            const reply = data.final_answer || data.choices[0].message.content;
            const thinking = data.thinking || '';
            const stats = data.stats || {};

            // Add response to conversation
            appendChatMessage('assistant', reply, thinking, stats);
            chatHistory.push({ role: 'assistant', content: reply });

        } catch (err) {
            console.error('Chat completions error:', err);
            appendChatMessage('assistant', `Errore durante l'elaborazione dell'inferenza: ${err.message}`, '', {});
            Toast.show(`Inference failed: ${err.message}`, 'error');
        } finally {
            isGenerating = false;
            dom.sendChatBtn.disabled = false;
            dom.typingStatus.style.display = 'none';
            stopStatusPolling();
        }
    }

    function startStatusPolling() {
        if (statusInterval) clearInterval(statusInterval);
        statusInterval = setInterval(async () => {
            try {
                const res = await fetch('/status');
                if (res.ok) {
                    const status = await res.json();
                    if (status.active) {
                        if (status.phase === 'prompt_eval') {
                            dom.typingText.textContent = "Valutazione prompt...";
                        } else if (status.phase === 'generating') {
                            const speed = status.tokens_per_second ? status.tokens_per_second.toFixed(1) : '0';
                            dom.typingText.textContent = `Generazione in corso: ${status.tokens_generated} tokens (${speed} t/s)`;
                        }
                    }
                }
            } catch (_) {}
        }, 300);
    }

    function stopStatusPolling() {
        if (statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
        }
    }

    function appendChatMessage(role, text, thinking = '', stats = {}) {
        const container = dom.chatMessages;
        const msgDiv = document.createElement('div');
        msgDiv.className = `message message--${role}`;

        const avatar = role === 'user' ? 'ME' : 'AI';
        
        let contentHtml = '';
        if (role === 'assistant') {
            if (dom.showThinkingCheckbox && dom.showThinkingCheckbox.checked && thinking && thinking.trim()) {
                contentHtml += `
                    <details class="think-details">
                        <summary class="think-summary">Mostra ragionamento</summary>
                        <div class="think-content">${formatTextMarkdown(thinking)}</div>
                    </details>
                `;
            }
            const cleanText = cleanJsonResponse(text);
            contentHtml += `<div class="assistant-response">${formatTextMarkdown(cleanText)}</div>`;
            
            // Add Stats metadata
            if (stats.tokens_per_second || stats.time_total_seconds) {
                const speed = stats.tokens_per_second ? stats.tokens_per_second.toFixed(1) : '-';
                const time = stats.time_total_seconds ? stats.time_total_seconds.toFixed(2) : '-';
                const tokens = stats.output_tokens || stats.total_tokens || '-';
                contentHtml += `
                    <div class="message-meta">
                        <span>${tokens} tokens</span>
                        <span>${time}s impiegati</span>
                        <span>${speed} tokens/s</span>
                    </div>
                `;
            }
        } else {
            contentHtml = `<p>${escapeHTML(text)}</p>`;
        }

        msgDiv.innerHTML = `
            <div class="message__avatar">${avatar}</div>
            <div class="message__content">${contentHtml}</div>
        `;

        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
    }

    function clearChat() {
        chatHistory = [];
        dom.chatMessages.innerHTML = `
            <div class="message message--assistant">
                <div class="message__avatar">AI</div>
                <div class="message__content">
                    <p>Ciao! Come posso aiutarti oggi? Puoi chiedermi spiegazioni di codice, compiti creativi o semplici traduzioni. L'inferenza verrà eseguita localmente e potrai monitorare i log del server nell'altro pannello.</p>
                </div>
            </div>
        `;
        Toast.show('Conversazione svuotata!', 'success');
    }

    // Simple markdown formatting helper
    function formatTextMarkdown(text) {
        let esc = escapeHTML(text);
        
        // Code blocks: ```code```
        esc = esc.replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code: `code`
        esc = esc.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Bold formatting: **text**
        esc = esc.replace(/\*\*([\s\S]+?)\*\*/g, '<strong>$1</strong>');
        
        // Convert double newlines to paragraphs
        esc = esc.split('\n\n').map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
        
        return esc;
    }

    // Automatically parse and clean JSON responses if the model outputs JSON
    function cleanJsonResponse(rawText) {
        const trimmed = rawText.trim();
        if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
            try {
                const parsed = JSON.parse(trimmed);
                if (parsed && typeof parsed === 'object') {
                    const keys = Object.keys(parsed);
                    if (keys.length === 1) {
                        return String(parsed[keys[0]]);
                    } else if (keys.length > 1) {
                        return Object.entries(parsed)
                            .map(([k, v]) => `**${k}**: ${v}`)
                            .join('\n');
                    }
                }
            } catch (e) {
                // Ignore parsing errors
            }
        }
        return rawText;
    }

    function escapeHTML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Auto-grow textarea height
    dom.chatTextarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Boot the UI
    init();
});
