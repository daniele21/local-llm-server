/**
 * app.js — Main Orchestrator for Local LLM Studio
 */

document.addEventListener('DOMContentLoaded', () => {

    // ═══════════════════════════════════════════════════════════════════════════
    // DOM Elements Mapping
    // ═══════════════════════════════════════════════════════════════════════════
    const dom = {
        // Navigation Layout Tab Links
        navItems: document.querySelectorAll('.nav-item'),
        tabPanels: document.querySelectorAll('.tab-panel'),

        // Theme Toggle & Status Summary Sidebar
        themeToggle: document.getElementById('theme-toggle'),
        serverStatusDot: document.querySelector('#server-status .status-badge__dot'),
        serverStatusText: document.querySelector('#server-status .status-badge__text'),
        sidebarActiveModel: document.getElementById('sidebar-active-model'),
        sidebarBackend: document.getElementById('sidebar-backend'),
        sidebarAddress: document.getElementById('sidebar-address'),

        // Chat View components
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

        // Server Logs body
        logSearch: document.getElementById('log-search-input'),
        logTimestampCheck: document.getElementById('log-timestamp-check'),
        logLevelCheck: document.getElementById('log-level-check'),
        logCompactCheck: document.getElementById('log-compact-check'),
        logAutoscroll: document.getElementById('log-autoscroll-check'),
        clearLogsBtn: document.getElementById('clear-logs-btn'),
        downloadLogsBtn: document.getElementById('download-logs-btn'),
        serverLogsBody: document.getElementById('server-logs-body'),
        logLineCount: document.getElementById('log-line-count'),
        sseIndicator: document.getElementById('sse-indicator'),
        sseIndicatorDot: document.querySelector('#sse-indicator .active-sse-badge__dot'),

        // Hardware Config Metrics
        cfgHost: document.getElementById('cfg-host'),
        cfgPort: document.getElementById('cfg-port'),
        cfgBackend: document.getElementById('cfg-backend'),
        cfgModelPath: document.getElementById('cfg-model-path'),
        modelsContainer: document.getElementById('models-list-container'),
        hardwareForm: document.getElementById('hardware-config-form'),
        cfgCtxSize: document.getElementById('cfg-ctx-size'),
        cfgGpuLayers: document.getElementById('cfg-gpu-layers'),
        cfgThreads: document.getElementById('cfg-threads'),
        cfgNBatch: document.getElementById('cfg-n-batch'),
        cfgNUbatch: document.getElementById('cfg-n-ubatch'),
        cfgTimeout: document.getElementById('cfg-timeout'),
        cfgOffloadKqv: document.getElementById('cfg-offload-kqv'),
        cfgFlashAttn: document.getElementById('cfg-flash-attn'),
        cfgUseMmap: document.getElementById('cfg-use-mmap'),
        cfgEnableThinking: document.getElementById('cfg-enable-thinking'),
        cfgShowThinking: document.getElementById('cfg-show-thinking'),
        cfgVerbose: document.getElementById('cfg-verbose'),

        // Terminal elements
        terminalBody: document.getElementById('terminal-screen-body'),
        terminalInput: document.getElementById('terminal-command-input'),
        terminalRunBtn: document.getElementById('run-terminal-btn'),
        terminalClearBtn: document.getElementById('clear-terminal-btn'),
        terminalCwdPath: document.getElementById('terminal-cwd-path'),
        terminalSuggestions: document.getElementById('terminal-suggestions-container'),
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // Global Application State
    // ═══════════════════════════════════════════════════════════════════════════
    let isServerOnline = false;
    let sseSource = null;
    let chatHistory = [];
    let isGenerating = false;
    let statusInterval = null;
    let isHardwareConfigLoaded = false;
    let activeModelKey = '';

    // ═══════════════════════════════════════════════════════════════════════════
    // Core Initialisation
    // ═══════════════════════════════════════════════════════════════════════════
    function init() {
        // Theme recovery
        const savedTheme = localStorage.getItem(APP_CONFIG.theme.storageKey) || APP_CONFIG.theme.default;
        document.documentElement.setAttribute('data-theme', savedTheme);

        // Bind modular components
        LogConsole.bind({
            body: dom.serverLogsBody,
            count: dom.logLineCount,
            autoscroll: dom.logAutoscroll,
            search: dom.logSearch,
            sseIndicator: dom.sseIndicator,
            sseIndicatorDot: dom.sseIndicatorDot
        });

        TerminalComponent.bind({
            body: dom.terminalBody,
            input: dom.terminalInput,
            runBtn: dom.terminalRunBtn,
            clearBtn: dom.terminalClearBtn,
            cwdPath: dom.terminalCwdPath,
            suggestionsContainer: dom.terminalSuggestions
        });

        ChatWindow.bind(
            dom.chatMessages,
            dom.showThinkingCheckbox ? dom.showThinkingCheckbox.checked : true
        );

        ModelCatalog.init(dom.modelsContainer, handleModelActivation);

        // Clear and prepare chat welcome text
        ChatWindow.clearChat(APP_CONFIG.labels.emptyChatPlaceholder);

        // Initialize animations and collateral accordions
        CollapsiblePanel.init();

        // Attach global events
        bindEvents();

        // Run primary requests
        checkServerHealth();
        setInterval(checkServerHealth, APP_CONFIG.polling.serverHealth);

        connectLogsStream();
        loadRegistryModels();

        // Recover checkboxes settings from localstorage
        if (dom.forceJsonCheckbox) {
            const savedForceJson = localStorage.getItem('force_json') === 'true';
            dom.forceJsonCheckbox.checked = savedForceJson;
        }

        if (dom.showThinkingCheckbox) {
            const savedShowThinking = localStorage.getItem('show_thinking') !== 'false';
            dom.showThinkingCheckbox.checked = savedShowThinking;
            ChatWindow.setShowThinking(savedShowThinking);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Listeners Mapping
    // ═══════════════════════════════════════════════════════════════════════════
    function bindEvents() {
        // Tab switching
        dom.navItems.forEach(item => {
            item.addEventListener('click', () => {
                const targetTab = item.dataset.tab;
                switchTab(targetTab);
            });
        });

        // Theme switch
        dom.themeToggle.addEventListener('click', toggleTheme);

        // Chat inference triggering
        dom.sendChatBtn.addEventListener('click', handleUserSendMessage);
        dom.chatTextarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleUserSendMessage();
            }
        });
        dom.clearChatBtn.addEventListener('click', clearChat);

        // Chat Settings check updates
        if (dom.forceJsonCheckbox) {
            dom.forceJsonCheckbox.addEventListener('change', (e) => {
                localStorage.setItem('force_json', e.target.checked);
            });
        }

        if (dom.showThinkingCheckbox) {
            dom.showThinkingCheckbox.addEventListener('change', (e) => {
                localStorage.setItem('show_thinking', e.target.checked);
                ChatWindow.setShowThinking(e.target.checked);
            });
        }

        // Log Console controls
        dom.clearLogsBtn.addEventListener('click', () => LogConsole.clear());
        dom.downloadLogsBtn.addEventListener('click', downloadLogs);

        // Log Console view filters (Timestamps, Levels, Compact)
        if (dom.logTimestampCheck) {
            dom.logTimestampCheck.addEventListener('change', (e) => {
                LogConsole.toggleTimestamps(e.target.checked);
            });
        }
        if (dom.logLevelCheck) {
            dom.logLevelCheck.addEventListener('change', (e) => {
                LogConsole.toggleLevels(e.target.checked);
            });
        }
        if (dom.logCompactCheck) {
            dom.logCompactCheck.addEventListener('change', (e) => {
                LogConsole.toggleCompact(e.target.checked);
            });
        }

        // Auto-growing textbox
        dom.chatTextarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Hardware Config Form Submit Handler
        if (dom.hardwareForm) {
            dom.hardwareForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (!activeModelKey) {
                    Toast.show("Nessun modello attivo identificato per il riavvio.", "error");
                    return;
                }

                const formData = new FormData(dom.hardwareForm);
                const backend = formData.get('backend');
                const ctx_size = formData.get('ctx_size') ? parseInt(formData.get('ctx_size')) : null;
                const n_gpu_layers = formData.get('n_gpu_layers') !== "" ? parseInt(formData.get('n_gpu_layers')) : null;
                const n_threads = formData.get('n_threads') ? parseInt(formData.get('n_threads')) : null;
                const n_batch = formData.get('n_batch') ? parseInt(formData.get('n_batch')) : null;
                const n_ubatch = formData.get('n_ubatch') ? parseInt(formData.get('n_ubatch')) : null;
                const timeout = formData.get('timeout') ? parseInt(formData.get('timeout')) : null;
                
                const offload_kqv = formData.get('offload_kqv') === 'on';
                const flash_attn = formData.get('flash_attn') === 'on';
                const use_mmap = formData.get('use_mmap') === 'on';
                const enable_thinking = formData.get('enable_thinking') === 'on';
                const show_thinking = formData.get('show_thinking') === 'on';
                const verbose = formData.get('verbose') === 'on';

                const payload = {
                    model: activeModelKey,
                    backend,
                    ctx_size,
                    n_gpu_layers,
                    n_threads,
                    n_batch,
                    n_ubatch,
                    timeout,
                    offload_kqv,
                    flash_attn,
                    use_mmap,
                    enable_thinking,
                    show_thinking,
                    verbose
                };

                const btnSubmit = dom.hardwareForm.querySelector('button[type="submit"]');
                const originalBtnText = btnSubmit.innerHTML;
                btnSubmit.disabled = true;
                btnSubmit.innerHTML = `
                    <svg class="animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" width="14" height="14" style="margin-right: 6px; display: inline-block; vertical-align: middle; animation: spin 1s linear infinite;"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" style="opacity: 0.25;"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" style="opacity: 0.75;"></path></svg>
                    <span>Caricamento modello...</span>
                `;

                Toast.show("Riavvio del modello con i nuovi parametri in corso...", "info");

                try {
                    const res = await fetch('/api/v1/models/activate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    if (!res.ok) {
                        const err = await res.json().catch(() => ({}));
                        throw new Error(err.detail || `HTTP ${res.status}`);
                    }

                    const data = await res.json();
                    Toast.show(`Modello ricaricato con successo: ${data.model}`, "success");
                    
                    // Force refresh registry and server health
                    isHardwareConfigLoaded = false;
                    await checkServerHealth();
                    await loadRegistryModels();
                } catch (err) {
                    console.error("Failed to reload model:", err);
                    Toast.show(`Errore di ricarica: ${err.message}`, "error");
                } finally {
                    btnSubmit.disabled = false;
                    btnSubmit.innerHTML = originalBtnText;
                }
            });
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Application state controls
    // ═══════════════════════════════════════════════════════════════════════════
    function switchTab(tabId) {
        dom.navItems.forEach(btn => {
            btn.classList.toggle('nav-item--active', btn.dataset.tab === tabId);
        });

        dom.tabPanels.forEach(panel => {
            panel.classList.toggle('tab-panel--active', panel.id === tabId);
        });

        // Trigger LogConsole re-rendering if switching to Logs Tab
        if (tabId === 'logs-tab') {
            LogConsole.renderAll();
            TerminalComponent.refreshCwd();
            if (dom.terminalInput) {
                setTimeout(() => dom.terminalInput.focus(), 100);
            }
        }
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem(APP_CONFIG.theme.storageKey, next);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Server state polling
    // ═══════════════════════════════════════════════════════════════════════════
    async function checkServerHealth() {
        try {
            const res = await fetch('/health');
            if (res.ok) {
                const data = await res.json();
                isServerOnline = true;
                const modelShort = data.model ? data.model.split('/').pop() : 'Model';
                
                // Update Sidebar
                setServerStatus(true, `${APP_CONFIG.labels.online} (${modelShort})`);
                dom.sidebarActiveModel.textContent = modelShort;
                dom.sidebarActiveModel.title = data.model;
                dom.sidebarBackend.textContent = data.backend || 'llama_cpp';
                dom.sidebarAddress.textContent = `${data.host || '127.0.0.1'}:${data.port || '1235'}`;

                // Update tab 3 configuration metrics
                dom.cfgHost.textContent = data.host || '127.0.0.1';
                dom.cfgPort.textContent = data.port || '1235';
                dom.cfgModelPath.textContent = data.model_path || '-';
                activeModelKey = data.model_key || '';
                
                if (dom.cfgBackend) {
                    dom.cfgBackend.value = data.backend || 'llama_cpp';
                }

                if (!isHardwareConfigLoaded) {
                    if (dom.cfgCtxSize && data.ctx_size) dom.cfgCtxSize.value = data.ctx_size;
                    if (dom.cfgGpuLayers && data.n_gpu_layers !== undefined) dom.cfgGpuLayers.value = data.n_gpu_layers;
                    if (dom.cfgThreads && data.n_threads) dom.cfgThreads.value = data.n_threads;
                    if (dom.cfgNBatch && data.n_batch) dom.cfgNBatch.value = data.n_batch;
                    if (dom.cfgNUbatch && data.n_ubatch) dom.cfgNUbatch.value = data.n_ubatch;
                    if (dom.cfgTimeout && data.timeout) dom.cfgTimeout.value = data.timeout;
                    if (dom.cfgOffloadKqv && data.offload_kqv !== undefined) dom.cfgOffloadKqv.checked = data.offload_kqv;
                    if (dom.cfgFlashAttn && data.flash_attn !== undefined) dom.cfgFlashAttn.checked = data.flash_attn;
                    if (dom.cfgUseMmap && data.use_mmap !== undefined) dom.cfgUseMmap.checked = data.use_mmap;
                    if (dom.cfgEnableThinking && data.enable_thinking !== undefined) dom.cfgEnableThinking.checked = data.enable_thinking;
                    if (dom.cfgShowThinking && data.show_thinking !== undefined) dom.cfgShowThinking.checked = data.show_thinking;
                    if (dom.cfgVerbose && data.verbose !== undefined) dom.cfgVerbose.checked = data.verbose;
                    isHardwareConfigLoaded = true;
                }
                
                if (dom.defaultModelOpt) {
                    dom.defaultModelOpt.textContent = `Predefinito (${modelShort})`;
                }
            } else {
                setServerStatus(false, APP_CONFIG.labels.serverError);
                resetSidebarInfo();
            }
        } catch (err) {
            setServerStatus(false, APP_CONFIG.labels.offline);
            resetSidebarInfo();
        }
    }

    function setServerStatus(online, text) {
        dom.serverStatusDot.className = `status-badge__dot status-badge__dot--${online ? 'online' : 'offline'}`;
        dom.serverStatusText.textContent = text;
    }

    function resetSidebarInfo() {
        dom.sidebarActiveModel.textContent = '-';
        dom.sidebarBackend.textContent = '-';
        dom.sidebarAddress.textContent = '-';
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Models Registry management
    // ═══════════════════════════════════════════════════════════════════════════
    async function loadRegistryModels() {
        try {
            const res = await fetch('/api/v1/models/registry');
            if (!res.ok) throw new Error('API registry error');
            const data = await res.json();
            
            // Popolate select dropdown
            dom.modelSelect.innerHTML = `<option value="">Predefinito del server</option>`;
            
            const models = data.models || [];
            
            // Populate select options
            models.forEach(model => {
                const opt = document.createElement('option');
                opt.value = model.key;
                opt.textContent = `${model.key} (${model.size_gb ? model.size_gb + ' GB' : 'Dimensione N/A'})`;
                dom.modelSelect.appendChild(opt);
            });

            // Get active model to highlight in Catalog
            const activeModel = dom.sidebarActiveModel.textContent !== '-' ? dom.sidebarActiveModel.textContent : '';
            ModelCatalog.render(models, activeModel);

        } catch (err) {
            console.error('Error loading model registry:', err);
            dom.modelsContainer.innerHTML = `<div class="models-grid__placeholder">Impossibile caricare il catalogo modelli.</div>`;
        }
    }

    // Connect selected Catalog model to Chat select & switch tab & activate on server
    async function handleModelActivation(modelKey) {
        Toast.show(`Avvio attivazione modello ${modelKey}...`, 'info');
        
        try {
            const res = await fetch('/api/v1/models/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelKey })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();
            Toast.show(`Modello attivato con successo: ${data.model}`, 'success');
            
            if (dom.modelSelect) {
                dom.modelSelect.value = modelKey;
            }
            
            // Force refresh registry and server health
            isHardwareConfigLoaded = false;
            await checkServerHealth();
            await loadRegistryModels();
            
            switchTab('chat-tab');
        } catch (err) {
            console.error("Failed to activate model:", err);
            Toast.show(`Errore di attivazione: ${err.message}`, 'error');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Logs stream connector (SSE)
    // ═══════════════════════════════════════════════════════════════════════════
    function connectLogsStream() {
        if (sseSource) {
            sseSource.close();
        }

        LogConsole.setStreamStatus('connecting');

        sseSource = new EventSource('/api/v1/logs/stream');

        sseSource.onopen = () => {
            LogConsole.setStreamStatus('connected');
            
            // Remove console placeholder
            const placeholder = dom.serverLogsBody.querySelector('.console-placeholder');
            if (placeholder) placeholder.remove();
        };

        sseSource.onmessage = (event) => {
            if (event.data === 'ping') return;
            LogConsole.addLine(event.data);
        };

        sseSource.onerror = (err) => {
            console.error('Logs SSE error, retrying in 5s...', err);
            LogConsole.setStreamStatus('error');
            sseSource.close();
            setTimeout(connectLogsStream, APP_CONFIG.logs.sseRetryMs);
        };
    }

    function downloadLogs() {
        const rawLines = LogConsole.getRawLogs();
        if (rawLines.length === 0) return;

        const textContent = rawLines.join('\n');
        const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `local-llm-server-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        Toast.show(APP_CONFIG.labels.toastLogsDownloaded, 'success');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Chat Completions Handler
    // ═══════════════════════════════════════════════════════════════════════════
    async function handleUserSendMessage() {
        const userText = dom.chatTextarea.value.trim();
        if (!userText || isGenerating) return;

        // Reset text inputs
        dom.chatTextarea.value = '';
        dom.chatTextarea.style.height = 'auto';

        // Add user message to UI state & memory
        ChatWindow.appendMessage('user', userText);
        chatHistory.push({ role: 'user', content: userText });

        isGenerating = true;
        dom.sendChatBtn.disabled = true;
        
        // Setup typing status loaders
        dom.typingText.textContent = APP_CONFIG.labels.typingStart;
        dom.typingStatus.style.display = 'flex';
        
        // Start polling status
        startStatusPolling();

        // Get params fields
        const formData = new FormData(dom.chatForm);
        const model = formData.get('model');
        const temperature = parseFloat(formData.get('temperature') || '0.7');
        const max_tokens = formData.get('max_tokens') ? parseInt(formData.get('max_tokens')) : null;
        const top_p = parseFloat(formData.get('top_p') || '0.95');
        const top_k = parseInt(formData.get('top_k') || '40');
        const repeat_penalty = parseFloat(formData.get('repeat_penalty') || '1.0');
        const system_prompt = formData.get('system_prompt') || '';

        // Build prompt payload
        const messages = [];
        if (system_prompt.trim()) {
            messages.push({ role: 'system', content: system_prompt.trim() });
        }
        
        // Limit context size
        const recentHistory = chatHistory.slice(-APP_CONFIG.chat.maxContextHistory);
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
            
            // Extract content and stats
            const reply = data.final_answer || data.choices[0].message.content;
            const thinking = data.thinking || '';
            const stats = data.stats || {};

            // Render assistant response
            ChatWindow.appendMessage('assistant', reply, thinking, stats);
            chatHistory.push({ role: 'assistant', content: reply });

        } catch (err) {
            console.error('Chat completion error:', err);
            ChatWindow.appendMessage('assistant', `${APP_CONFIG.labels.inferenceError} ${err.message}`, '', {});
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
                            dom.typingText.textContent = APP_CONFIG.labels.typingEval;
                        } else if (status.phase === 'generating') {
                            const speed = status.tokens_per_second ? status.tokens_per_second.toFixed(1) : '0';
                            dom.typingText.textContent = APP_CONFIG.labels.typingGenerating(status.tokens_generated, speed);
                        }
                    }
                }
            } catch (_) {}
        }, APP_CONFIG.polling.statusUpdate);
    }

    function stopStatusPolling() {
        if (statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
        }
    }

    function clearChat() {
        chatHistory = [];
        ChatWindow.clearChat(APP_CONFIG.labels.emptyChatPlaceholder);
        Toast.show(APP_CONFIG.labels.toastChatCleared, 'success');
    }

    // Boot the UI Orchestrator
    init();
});
