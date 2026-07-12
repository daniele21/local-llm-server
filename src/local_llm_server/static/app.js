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
        sidebarRuntimeCount: document.getElementById('sidebar-runtime-count'),
        sidebarRuntimeList: document.getElementById('sidebar-runtime-list'),

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
        enableThinkingCheckbox: document.getElementById('param-enable-thinking'),
        showThinkingCheckbox: document.getElementById('param-show-thinking'),
        chatImageInput: document.getElementById('chat-image-input'),
        attachImageBtn: document.getElementById('attach-image-btn'),
        chatImagePreviewContainer: document.getElementById('chat-image-preview-container'),
        chatImagePreview: document.getElementById('chat-image-preview'),
        removeImageBtn: document.getElementById('remove-image-btn'),

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
        configModelSelect: document.getElementById('config-model-select'),
        configTargetStatus: document.getElementById('config-target-status'),
        modelsContainer: document.getElementById('models-list-container'),
        residentModelCount: document.getElementById('resident-model-count'),
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
    let residentModels = [];
    let configModelKey = '';
    let activeConfigCapabilities = [];
    let currentServerInfo = null;
    let selectedImageBase64 = '';

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

        ModelCatalog.init(dom.modelsContainer, handleModelAction);
        if (dom.configModelSelect) {
            dom.configModelSelect.addEventListener('change', () => {
                configModelKey = dom.configModelSelect.value;
                const model = residentModels.find(item => item.key === configModelKey);
                if (model) applyRuntimeConfig(model);
            });
        }

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

        if (dom.enableThinkingCheckbox) {
            const savedEnableThinking = localStorage.getItem('enable_thinking');
            if (savedEnableThinking !== null) {
                dom.enableThinkingCheckbox.checked = savedEnableThinking === 'true';
            }
        }

        if (dom.showThinkingCheckbox) {
            const savedShowThinking = localStorage.getItem('show_thinking');
            if (savedShowThinking !== null) {
                dom.showThinkingCheckbox.checked = savedShowThinking === 'true';
                ChatWindow.setShowThinking(savedShowThinking === 'true');
            }
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

        // Model change handler to toggle vision and thinking support
        if (dom.modelSelect) {
            dom.modelSelect.addEventListener('change', () => {
                updateVisionSupport();
                updateThinkingSupport();
            });
        }

        // Image attach handlers
        if (dom.attachImageBtn && dom.chatImageInput) {
            dom.attachImageBtn.addEventListener('click', () => {
                dom.chatImageInput.click();
            });
            dom.chatImageInput.addEventListener('change', handleImageSelect);
        }

        if (dom.removeImageBtn) {
            dom.removeImageBtn.addEventListener('click', clearSelectedImage);
        }

        // Chat Settings check updates
        if (dom.forceJsonCheckbox) {
            dom.forceJsonCheckbox.addEventListener('change', (e) => {
                localStorage.setItem('force_json', e.target.checked);
            });
        }

        if (dom.enableThinkingCheckbox) {
            dom.enableThinkingCheckbox.addEventListener('change', (e) => {
                localStorage.setItem('enable_thinking', e.target.checked);
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
                    Toast.show("Seleziona un runtime residente da configurare.", "error");
                    return;
                }

                const formData = new FormData(dom.hardwareForm);
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

                const values = {
                    ctx_size, n_gpu_layers, n_threads, n_batch, n_ubatch, timeout,
                    offload_kqv, flash_attn, use_mmap, enable_thinking, show_thinking, verbose
                };
                const payload = { model: activeModelKey };
                activeConfigCapabilities.forEach(key => {
                    if (values[key] !== null && values[key] !== undefined) payload[key] = values[key];
                });

                const btnSubmit = dom.hardwareForm.querySelector('button[type="submit"]');
                const originalBtnText = btnSubmit.innerHTML;
                btnSubmit.disabled = true;
                btnSubmit.innerHTML = `
                    <svg class="animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" width="14" height="14" style="margin-right: 6px; display: inline-block; vertical-align: middle; animation: spin 1s linear infinite;"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" style="opacity: 0.25;"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" style="opacity: 0.75;"></path></svg>
                    <span>Caricamento modello...</span>
                `;

                Toast.show(`Applicazione parametri a ${activeModelKey}...`, "info");

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
                    Toast.show(`Configurazione applicata a ${activeModelKey}`, "success");
                    
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

        // Initialize modern input UI behaviors
        function setupSliderStepper(sliderId, inputId, minusId, plusId) {
            const slider = document.getElementById(sliderId);
            const input = document.getElementById(inputId);
            const minusBtn = document.getElementById(minusId);
            const plusBtn = document.getElementById(plusId);

            if (!slider || !input) return;

            // Sync slider -> input
            slider.addEventListener('input', () => {
                input.value = slider.value;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            });

            // Sync input -> slider
            input.addEventListener('change', () => {
                let val = parseInt(input.value);
                if (isNaN(val)) return;
                const min = parseInt(slider.min) || 0;
                const max = parseInt(slider.max) || 200;
                if (val < min) val = min;
                if (val > max) val = max;
                slider.value = val;
            });

            // Minus button
            if (minusBtn) {
                minusBtn.addEventListener('click', () => {
                    let val = parseInt(input.value);
                    if (isNaN(val)) val = parseInt(slider.value) || 0;
                    const step = parseInt(slider.step) || 1;
                    const min = parseInt(slider.min) || 0;
                    val = Math.max(min, val - step);
                    input.value = val;
                    slider.value = val;
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                });
            }

            // Plus button
            if (plusBtn) {
                plusBtn.addEventListener('click', () => {
                    let val = parseInt(input.value);
                    if (isNaN(val)) val = parseInt(slider.value) || 0;
                    const step = parseInt(slider.step) || 1;
                    const max = parseInt(slider.max) || 200;
                    val = Math.min(max, val + step);
                    input.value = val;
                    slider.value = val;
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                });
            }
        }

        function setupSegmentedControl(presetContainerId, hiddenInputId) {
            const container = document.getElementById(presetContainerId);
            const hiddenInput = document.getElementById(hiddenInputId);
            if (!container || !hiddenInput) return;

            const buttons = container.querySelectorAll('.segmented-control__btn');

            buttons.forEach(btn => {
                btn.addEventListener('click', () => {
                    buttons.forEach(b => b.classList.remove('segmented-control__btn--active'));
                    btn.classList.add('segmented-control__btn--active');

                    const val = btn.dataset.value;
                    if (val === 'custom') {
                        hiddenInput.style.display = 'block';
                        hiddenInput.focus();
                    } else {
                        hiddenInput.value = val;
                        if (hiddenInput.tagName === 'INPUT') {
                            hiddenInput.style.display = 'none';
                        }
                        hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
            });

            const syncFromSource = () => {
                const currentVal = hiddenInput.value;
                let found = false;
                buttons.forEach(btn => {
                    if (btn.dataset.value === String(currentVal)) {
                        buttons.forEach(b => b.classList.remove('segmented-control__btn--active'));
                        btn.classList.add('segmented-control__btn--active');
                        if (hiddenInput.tagName === 'INPUT') {
                            hiddenInput.style.display = 'none';
                        }
                        found = true;
                    }
                });
                if (!found && currentVal !== "") {
                    buttons.forEach(b => b.classList.remove('segmented-control__btn--active'));
                    const customBtn = Array.from(buttons).find(b => b.dataset.value === 'custom');
                    if (customBtn) {
                        customBtn.classList.add('segmented-control__btn--active');
                        if (hiddenInput.tagName === 'INPUT') {
                            hiddenInput.style.display = 'block';
                        }
                    }
                }
            };

            hiddenInput.addEventListener('change', syncFromSource);
            setTimeout(syncFromSource, 100);
        }

        // Setup the widgets
        setupSegmentedControl('ctx-preset-control', 'cfg-ctx-size');
        setupSegmentedControl('batch-preset-control', 'cfg-n-batch');
        setupSegmentedControl('ubatch-preset-control', 'cfg-n-ubatch');

        setupSliderStepper('slide-gpu-layers', 'cfg-gpu-layers', 'btn-gpu-minus', 'btn-gpu-plus');
        setupSliderStepper('slide-threads', 'cfg-threads', 'btn-threads-minus', 'btn-threads-plus');
        setupSliderStepper('slide-timeout', 'cfg-timeout', 'btn-timeout-minus', 'btn-timeout-plus');
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
                currentServerInfo = data;
                const modelShort = data.model ? data.model.split('/').pop() : 'Model';
                
                // Update Sidebar
                const loadedCount = (data.loaded_models || []).length;
                setServerStatus(true, `${APP_CONFIG.labels.online} · ${loadedCount} ${loadedCount === 1 ? 'modello' : 'modelli'}`);
                dom.sidebarActiveModel.textContent = modelShort;
                dom.sidebarActiveModel.title = data.model;
                dom.sidebarBackend.textContent = data.backend || 'llama_cpp';
                dom.sidebarAddress.textContent = `${data.host || '127.0.0.1'}:${data.port || '1235'}`;

                if (!residentModels.length) {
                    activeModelKey = data.model_key || '';
                    configModelKey = activeModelKey;
                    applyConfigValues(data);
                }

                if (!isHardwareConfigLoaded && !residentModels.length) {
                    if (dom.cfgCtxSize && data.ctx_size) {
                        dom.cfgCtxSize.value = data.ctx_size;
                        dom.cfgCtxSize.dispatchEvent(new Event('change'));
                    }
                    if (dom.cfgGpuLayers && data.n_gpu_layers !== undefined) {
                        dom.cfgGpuLayers.value = data.n_gpu_layers;
                        dom.cfgGpuLayers.dispatchEvent(new Event('change'));
                    }
                    if (dom.cfgThreads && data.n_threads) {
                        dom.cfgThreads.value = data.n_threads;
                        dom.cfgThreads.dispatchEvent(new Event('change'));
                    }
                    if (dom.cfgNBatch && data.n_batch) {
                        dom.cfgNBatch.value = data.n_batch;
                        dom.cfgNBatch.dispatchEvent(new Event('change'));
                    }
                    if (dom.cfgNUbatch && data.n_ubatch) {
                        dom.cfgNUbatch.value = data.n_ubatch;
                        dom.cfgNUbatch.dispatchEvent(new Event('change'));
                    }
                    if (dom.cfgTimeout && data.timeout) {
                        dom.cfgTimeout.value = data.timeout;
                        dom.cfgTimeout.dispatchEvent(new Event('change'));
                    }
                    if (dom.cfgOffloadKqv && data.offload_kqv !== undefined) dom.cfgOffloadKqv.checked = data.offload_kqv;
                    if (dom.cfgFlashAttn && data.flash_attn !== undefined) dom.cfgFlashAttn.checked = data.flash_attn;
                    if (dom.cfgUseMmap && data.use_mmap !== undefined) dom.cfgUseMmap.checked = data.use_mmap;
                    if (dom.cfgEnableThinking && data.enable_thinking !== undefined) dom.cfgEnableThinking.checked = data.enable_thinking;
                    if (dom.cfgShowThinking && data.show_thinking !== undefined) dom.cfgShowThinking.checked = data.show_thinking;
                    if (dom.enableThinkingCheckbox && data.enable_thinking !== undefined && localStorage.getItem('enable_thinking') === null) {
                        dom.enableThinkingCheckbox.checked = data.enable_thinking;
                    }
                    if (dom.showThinkingCheckbox && data.show_thinking !== undefined && localStorage.getItem('show_thinking') === null) {
                        dom.showThinkingCheckbox.checked = data.show_thinking;
                        ChatWindow.setShowThinking(data.show_thinking);
                    }
                    if (dom.cfgVerbose && data.verbose !== undefined) dom.cfgVerbose.checked = data.verbose;
                    isHardwareConfigLoaded = true;
                }
                
                if (dom.defaultModelOpt) {
                    dom.defaultModelOpt.textContent = `Predefinito (${modelShort})`;
                }
                updateVisionSupport();
                updateThinkingSupport();
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
        if (dom.sidebarRuntimeCount) dom.sidebarRuntimeCount.textContent = '0';
        if (dom.sidebarRuntimeList) {
            dom.sidebarRuntimeList.innerHTML = '<li class="resident-runtimes__empty">Nessun modello caricato</li>';
        }
    }

    function applyConfigValues(config) {
        if (dom.cfgHost) dom.cfgHost.textContent = config.host || '127.0.0.1';
        if (dom.cfgPort) dom.cfgPort.textContent = config.port || '1235';
        dom.cfgModelPath.textContent = config.model_path || '-';
        if (dom.cfgBackend) {
            dom.cfgBackend.textContent = config.backend || '-';
        }
        const numericFields = [
            [dom.cfgCtxSize, 'ctx_size'], [dom.cfgGpuLayers, 'n_gpu_layers'],
            [dom.cfgThreads, 'n_threads'], [dom.cfgNBatch, 'n_batch'],
            [dom.cfgNUbatch, 'n_ubatch'], [dom.cfgTimeout, 'timeout']
        ];
        numericFields.forEach(([element, key]) => {
            if (element && config[key] !== undefined && config[key] !== null) {
                element.value = config[key];
                element.dispatchEvent(new Event('change'));
            }
        });
        const booleanFields = [
            [dom.cfgOffloadKqv, 'offload_kqv'], [dom.cfgFlashAttn, 'flash_attn'],
            [dom.cfgUseMmap, 'use_mmap'], [dom.cfgEnableThinking, 'enable_thinking'],
            [dom.cfgShowThinking, 'show_thinking'], [dom.cfgVerbose, 'verbose']
        ];
        booleanFields.forEach(([element, key]) => {
            if (element && config[key] !== undefined) element.checked = Boolean(config[key]);
        });
    }

    function applyRuntimeConfig(model) {
        configModelKey = model.key;
        activeModelKey = model.key;
        if (dom.configModelSelect) dom.configModelSelect.value = model.key;
        activeConfigCapabilities = model.config_capabilities || [];
        applyConfigValues(model.runtime_config || {});
        document.querySelectorAll('[data-config-key]').forEach(group => {
            const supported = activeConfigCapabilities.includes(group.dataset.configKey);
            group.classList.toggle('config-field--hidden', !supported);
            group.querySelectorAll('input, select, button').forEach(control => {
                control.disabled = !supported;
            });
        });
        if (dom.configTargetStatus) {
            const backend = model.runtime_config?.backend || model.backend;
            dom.configTargetStatus.textContent = `${backend} · ${model.default ? 'modello predefinito' : 'runtime residente'}`;
        }
        const submit = dom.hardwareForm?.querySelector('button[type="submit"] span');
        if (submit) submit.textContent = `Applica e riavvia ${model.key}`;
        isHardwareConfigLoaded = true;
    }

    function renderResidentSidebar(models) {
        const residents = models.filter(model => model.resident);
        if (dom.sidebarRuntimeCount) dom.sidebarRuntimeCount.textContent = String(residents.length);
        if (!dom.sidebarRuntimeList) return;
        dom.sidebarRuntimeList.replaceChildren();
        if (!residents.length) {
            const empty = document.createElement('li');
            empty.className = 'resident-runtimes__empty';
            empty.textContent = 'Nessun modello caricato';
            dom.sidebarRuntimeList.appendChild(empty);
            return;
        }
        residents.forEach(model => {
            const item = document.createElement('li');
            item.className = 'resident-runtime-item';
            const dot = document.createElement('span');
            dot.className = 'resident-runtime-item__dot';
            const name = document.createElement('span');
            name.className = 'resident-runtime-item__name';
            name.textContent = model.key;
            name.title = model.model_id;
            item.append(dot, name);
            if (model.default) {
                const defaultBadge = document.createElement('span');
                defaultBadge.className = 'resident-runtime-item__default';
                defaultBadge.textContent = 'Default';
                item.appendChild(defaultBadge);
            }
            dom.sidebarRuntimeList.appendChild(item);
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Models Registry management
    // ═══════════════════════════════════════════════════════════════════════════
    async function loadRegistryModels() {
        try {
            const res = await fetch('/api/v1/models/registry');
            if (!res.ok) throw new Error('API registry error');
            const data = await res.json();
            
            // Chat can route only to models currently resident in memory.
            dom.modelSelect.innerHTML = `<option value="">Predefinito del server</option>`;
            
            const models = data.models || [];
            residentModels = models.filter(model => model.resident);
            
            // Populate select options
            models.filter(model => model.resident).forEach(model => {
                const opt = document.createElement('option');
                opt.value = model.key;
                opt.textContent = `${model.key}${model.default ? ' · predefinito' : ''}`;
                dom.modelSelect.appendChild(opt);
            });

            const residentCount = residentModels.length;
            if (dom.residentModelCount) dom.residentModelCount.textContent = String(residentCount);
            renderResidentSidebar(models);
            if (dom.configModelSelect) {
                const previous = configModelKey;
                dom.configModelSelect.replaceChildren();
                residentModels.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.key;
                    option.textContent = `${model.key}${model.default ? ' · predefinito' : ''}`;
                    dom.configModelSelect.appendChild(option);
                });
                const selected = residentModels.find(model => model.key === previous)
                    || residentModels.find(model => model.default)
                    || residentModels[0];
                dom.configModelSelect.disabled = !selected;
                if (selected) {
                    applyRuntimeConfig(selected);
                } else if (dom.configTargetStatus) {
                    dom.configTargetStatus.textContent = 'Carica un modello per configurarlo';
                }
            }
            ModelCatalog.render(models);
            updateVisionSupport();
            updateThinkingSupport();

        } catch (err) {
            console.error('Error loading model registry:', err);
            dom.modelsContainer.innerHTML = `<div class="models-grid__placeholder">Impossibile caricare il catalogo modelli.</div>`;
        }
    }

    async function handleModelAction(action, modelKey) {
        if (action === 'configure') {
            const model = residentModels.find(item => item.key === modelKey);
            if (model) {
                applyRuntimeConfig(model);
                const advanced = document.querySelector('.advanced-config-disclosure');
                if (advanced) advanced.open = true;
                document.getElementById('config-model-select')?.focus();
            }
            return;
        }
        const endpoints = {
            load: { url: '/api/v1/models/load', method: 'POST', body: { model: modelKey } },
            default: { url: '/api/v1/models/activate', method: 'POST', body: { model: modelKey } },
            unload: { url: `/api/v1/models/${encodeURIComponent(modelKey)}`, method: 'DELETE' }
        };
        const operation = endpoints[action];
        if (!operation) return;
        if (action === 'unload' && !window.confirm(`Scaricare ${modelKey} dalla memoria?`)) return;
        const labels = { load: 'Caricamento', default: 'Cambio predefinito', unload: 'Scaricamento' };
        Toast.show(`${labels[action]} di ${modelKey}...`, 'info');
        try {
            const res = await fetch(operation.url, {
                method: operation.method,
                headers: { 'Content-Type': 'application/json' },
                body: operation.body ? JSON.stringify(operation.body) : undefined
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();
            const success = {
                load: `${modelKey} è ora residente in memoria`,
                default: `${modelKey} è il modello predefinito`,
                unload: `${modelKey} è stato scaricato dalla memoria`
            };
            Toast.show(success[action], 'success');
            isHardwareConfigLoaded = false;
            await checkServerHealth();
            await loadRegistryModels();
            if (action !== 'unload' && dom.modelSelect) dom.modelSelect.value = modelKey;
        } catch (err) {
            console.error(`Model ${action} failed:`, err);
            Toast.show(`Operazione non riuscita: ${err.message}`, 'error');
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
        const imgUrlToSend = selectedImageBase64;
        if (imgUrlToSend) {
            ChatWindow.appendMessage('user', userText, '', {}, imgUrlToSend);
            chatHistory.push({
                role: 'user',
                content: [
                    { type: 'image_url', image_url: { url: imgUrlToSend } },
                    { type: 'text', text: userText }
                ]
            });
            clearSelectedImage();
        } else {
            ChatWindow.appendMessage('user', userText);
            chatHistory.push({ role: 'user', content: userText });
        }

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
            stream: true,
        };
        if (model) payload.model = model;
        if (max_tokens) payload.max_tokens = max_tokens;
        if (dom.enableThinkingCheckbox && localStorage.getItem('enable_thinking') !== null && isCurrentModelThinkingSupported()) {
            payload.enable_thinking = dom.enableThinkingCheckbox.checked;
        }
        if (dom.showThinkingCheckbox && localStorage.getItem('show_thinking') !== null && isCurrentModelThinkingSupported()) {
            payload.show_thinking = dom.showThinkingCheckbox.checked;
        }
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
                throw new Error(errData.detail || errData.error || `HTTP ${response.status}`);
            }

            if (!response.body) throw new Error('Il browser non supporta lo streaming della risposta');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            const assistantMessage = ChatWindow.appendMessage('assistant', 'In attesa del primo token…');
            let buffer = '';
            let reply = '';
            let done = false;

            while (!done) {
                const result = await reader.read();
                done = result.done;
                buffer += decoder.decode(result.value || new Uint8Array(), { stream: !done });
                const events = buffer.split(/\r?\n\r?\n/);
                buffer = events.pop() || '';
                for (const event of events) {
                    const dataLine = event.split(/\r?\n/).find(line => line.startsWith('data:'));
                    if (!dataLine) continue;
                    const raw = dataLine.slice(5).trim();
                    if (!raw || raw === '[DONE]') continue;
                    const chunk = JSON.parse(raw);
                    if (chunk.error) throw new Error(chunk.error);
                    reply += chunk.choices?.[0]?.delta?.content || '';
                    ChatWindow.updateAssistantMessage(assistantMessage, reply);
                }
            }

            if (!reply) throw new Error('Il modello non ha restituito contenuto');
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
                    const selectedModel = dom.modelSelect?.value;
                    const activeStatus = status.models?.[selectedModel] || status;
                    if (activeStatus.active) {
                        if (activeStatus.phase === 'prompt_eval') {
                            dom.typingText.textContent = APP_CONFIG.labels.typingEval;
                        } else if (activeStatus.phase === 'generating') {
                            const speed = activeStatus.tokens_per_second ? activeStatus.tokens_per_second.toFixed(1) : '0';
                            dom.typingText.textContent = APP_CONFIG.labels.typingGenerating(activeStatus.tokens_generated, speed);
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
        clearSelectedImage();
        ChatWindow.clearChat(APP_CONFIG.labels.emptyChatPlaceholder);
        Toast.show(APP_CONFIG.labels.toastChatCleared, 'success');
    }

    function isCurrentModelMultimodal() {
        const selectedKey = dom.modelSelect.value;
        if (!selectedKey) {
            if (currentServerInfo) {
                const modalities = currentServerInfo.modalities || [];
                return !!currentServerInfo.multimodal && modalities.includes('image');
            }
            return false;
        }
        const model = residentModels.find(m => m.key === selectedKey);
        if (model) {
            const modalities = model.modalities || [];
            return !!model.multimodal && modalities.includes('image');
        }
        return false;
    }

    function updateVisionSupport() {
        if (!dom.attachImageBtn) return;

        if (isCurrentModelMultimodal()) {
            dom.attachImageBtn.style.display = 'inline-flex';
        } else {
            dom.attachImageBtn.style.display = 'none';
            clearSelectedImage();
        }
    }

    function isCurrentModelThinkingSupported() {
        const selectedKey = dom.modelSelect.value;
        if (!selectedKey) {
            if (currentServerInfo) {
                const caps = currentServerInfo.config_capabilities || [];
                return caps.includes('enable_thinking');
            }
            return false;
        }
        const model = residentModels.find(m => m.key === selectedKey);
        if (model) {
            const caps = model.config_capabilities || [];
            return caps.includes('enable_thinking');
        }
        return false;
    }

    function updateThinkingSupport() {
        if (!dom.enableThinkingCheckbox) return;
        const supported = isCurrentModelThinkingSupported();
        const enableGroup = dom.enableThinkingCheckbox.closest('.checkbox-group');
        const showGroup = dom.showThinkingCheckbox.closest('.checkbox-group');
        if (enableGroup) {
            enableGroup.style.display = supported ? 'block' : 'none';
        }
        if (showGroup) {
            showGroup.style.display = supported ? 'block' : 'none';
        }
    }

    function handleImageSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Supported types validation (jpeg, png, webp)
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            Toast.show('Formato immagine non supportato. Usa JPEG, PNG o WebP.', 'error');
            dom.chatImageInput.value = '';
            return;
        }

        // Limit size validation (10 MB maximum, matches DEFAULT_MAX_IMAGE_BYTES in python)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            Toast.show('L\'immagine è troppo grande. Dimensione massima 10MB.', 'error');
            dom.chatImageInput.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            selectedImageBase64 = event.target.result;
            if (dom.chatImagePreview && dom.chatImagePreviewContainer) {
                dom.chatImagePreview.src = selectedImageBase64;
                dom.chatImagePreviewContainer.style.display = 'flex';
            }
        };
        reader.readAsDataURL(file);
    }

    function clearSelectedImage() {
        selectedImageBase64 = '';
        if (dom.chatImagePreview) {
            dom.chatImagePreview.src = '';
        }
        if (dom.chatImagePreviewContainer) {
            dom.chatImagePreviewContainer.style.display = 'none';
        }
        if (dom.chatImageInput) {
            dom.chatImageInput.value = '';
        }
    }

    // Listen to language changes to update dynamic layouts
    window.addEventListener('app-lang-changed', (e) => {
        // 1. Refresh health state immediately to update Online/Offline status texts
        checkServerHealth();

        // 2. If chat is empty, reload the welcome message with the new placeholder
        if (chatHistory.length === 0) {
            ChatWindow.clearChat(APP_CONFIG.labels.emptyChatPlaceholder);
        }

        // 3. Update the terminal welcome message if there is no custom command output
        const termWelcome = dom.terminalBody.querySelector('.terminal-welcome');
        if (termWelcome) {
            termWelcome.innerHTML = APP_CONFIG.terminal.welcomeMessage;
        }

        // 4. Update logs count display
        const logLines = dom.serverLogsBody.querySelectorAll('.log-line');
        if (dom.logLineCount) {
            const count = logLines.length;
            dom.logLineCount.textContent = e.detail.lang === 'it' 
                ? `${count} righe caricate` 
                : `${count} lines loaded`;
        }
    });

    // Boot the UI Orchestrator
    init();
});
