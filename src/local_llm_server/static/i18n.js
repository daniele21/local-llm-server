/**
 * i18n.js — Internationalization System for Local LLM Studio
 */

const I18N_RESOURCES = {
    it: {
        flag: "🇮🇹",
        welcomeMessage: "Digita un comando e premi Invio. Esempi: <code>uname -a</code>, <code>ls -la</code> o <code>python --version</code>. Digita <code>help</code> per i comandi speciali.",
        labels: {
            online: "Online",
            offline: "Disconnesso",
            connecting: "Connessione...",
            serverError: "Errore Server",
            emptyChatPlaceholder: "Ciao! Come posso aiutarti oggi? Puoi chiedermi spiegazioni di codice, compiti creativi o semplici traduzioni. L'inferenza verrà eseguita localmente e potrai monitorare i log del server nell'altro pannello.",
            toastChatCleared: "Conversazione svuotata!",
            toastLogsDownloaded: "Log scaricati con successo!",
            toastLogsCleared: "Console log svuotata!",
            toastTerminalCleared: "Terminale pulito!",
            toastCopySuccess: "Copiato negli appunti!",
            toastCopyError: "Impossibile copiare il testo.",
            typingStart: "L'LLM sta pensando...",
            typingEval: "Valutazione prompt...",
            typingGenerating: (tokens, speed) => `Generazione in corso: ${tokens} tokens (${speed} t/s)`,
            inferenceError: "Errore durante l'elaborazione dell'inferenza:",
            terminalRunning: "In esecuzione..."
        },
        dom: {
            "title": "Local LLM Studio",
            ".sidebar-brand-text h1": "Local LLM Studio",
            ".sidebar-brand-text .subtext": "Console Inferenza",
            ".status-info-item:nth-child(1) .label": "Modello Attivo",
            ".status-info-item:nth-child(2) .label": "Inference Backend",
            ".status-info-item:nth-child(3) .label": "Indirizzo Server",
            ".nav-item[data-tab='chat-tab']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> Chat Studio',
            ".nav-item[data-tab='logs-tab']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><polyline points="4 17 10 11 12 13 18 7"/><polyline points="14 7 18 7 18 11"/></svg> Log del Server',
            ".nav-item[data-tab='registry-tab']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg> Modelli e Config',
            "#start-tour-btn": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polygon points="6 3 20 12 6 21 6 3"/></svg> Avvia tour guidato',
            ".sidebar-footer-link[href='/example']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><polygon points="6 3 20 12 6 21 6 3"/></svg> Esempi API',
            ".sidebar-footer-link[href='/docs']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/></svg> Swagger API',
            ".params-header h3": "Parametri Chat",
            "label[for='model-select']": "Modello Attivo",
            "#default-model-opt": "Predefinito del server",
            "label[for='system-prompt']": "Prompt di Sistema",
            "#system-prompt": { placeholder: "Sei un assistente utile e sintetico..." },
            "#advanced-params-trigger span": "Parametri Avanzati",
            "label[for='param-temp']": "Temperatura",
            "label[for='param-tokens']": "Max Output Tokens",
            "label[for='param-topp']": "Top P",
            "label[for='param-topk']": "Top K",
            "label[for='param-penalty']": "Repeat Penalty",
            "label[for='param-force-json'] span:last-child": "Forza output JSON",
            "label[for='param-enable-thinking'] span:last-child": "Abilita ragionamento (Thinking)",
            "label[for='param-show-thinking'] span:last-child": "Mostra blocco &lt;think&gt; nell'output",
            "#clear-chat-btn": "Svuota Conversazione",
            "#chat-textarea": { placeholder: "Scrivi un messaggio... (Invio invia, Shift+Invio per riga nuova)" },
            "#log-search-input": { placeholder: "Filtra per parola chiave..." },
            "label[for='log-timestamp-check'] span:last-child": "Timestamp",
            "label[for='log-level-check'] span:last-child": "Livello",
            "label[for='log-compact-check'] span:last-child": "Compatto",
            "label[for='log-autoscroll-check'] span:last-child": "Auto-scroll",
            "#clear-logs-btn": "Cancella",
            "#download-logs-btn": "Scarica (.txt)",
            ".console-placeholder": "In attesa dei log del server...",
            ".terminal-header-title span": "Terminale Esecuzione Comandi",
            "#clear-terminal-btn": "Pulisci",
            ".terminal-suggestions-label": "Esegui:",
            "#terminal-command-input": { placeholder: "Scrivi un comando (es: ls -la, uname -a, cd ..) e premi Invio..." },
            "#run-terminal-btn": "Invia",
            "#log-line-count": "0 righe caricate",
            "#sse-indicator span:last-child": "Streaming Attivo",
            ".config-card .card-header h2": "Stato Configurazione Hardware",
            ".config-card .card-header p": "Modifica i parametri del motore inference ed esegui un hot-reload del modello in-memory.",
            ".host-port-item:nth-child(1) .config-metric__label": "Host Binding",
            ".host-port-item:nth-child(3) .config-metric__label": "Porta server",
            "label[for='cfg-backend']": "Motore Backend",
            "label[for='cfg-ctx-size']": "Dimensione Contesto (ctx_size)",
            "label[for='cfg-gpu-layers']": "GPU Layers (n_gpu_layers)",
            "label[for='cfg-threads']": "CPU Threads (n_threads)",
            "label[for='cfg-n-batch']": "Batch Size (n_batch)",
            "label[for='cfg-n-ubatch']": "Micro-batch (n_ubatch)",
            "label[for='cfg-timeout']": "Timeout (secondi)",
            ".toggle-control-card:nth-of-type(1) .toggle-control-label": "Offload KQV",
            ".toggle-control-card:nth-of-type(1) .toggle-control-description": "Offload dei tensori K/V su memoria GPU",
            ".toggle-control-card:nth-of-type(2) .toggle-control-label": "Flash Attention",
            ".toggle-control-card:nth-of-type(2) .toggle-control-description": "Velocizza inferenza con Flash Attention",
            ".toggle-control-card:nth-of-type(3) .toggle-control-label": "Usa mmap",
            ".toggle-control-card:nth-of-type(3) .toggle-control-description": "Memoria mappata per caricamento rapido",
            ".toggle-control-card:nth-of-type(4) .toggle-control-label": "Abilita Thinking",
            ".toggle-control-card:nth-of-type(4) .toggle-control-description": "Ragionamento per modelli compatibili",
            ".toggle-control-card:nth-of-type(5) .toggle-control-label": "Mostra Thinking",
            ".toggle-control-card:nth-of-type(5) .toggle-control-description": "Mostra i passaggi intermedi del ragionamento",
            ".toggle-control-card:nth-of-type(6) .toggle-control-label": "Log Verbosi",
            ".toggle-control-card:nth-of-type(6) .toggle-control-description": "Abilita log dettagliati del server",
            ".path-metric .config-metric__label": "Percorso File Modello",
            "#btn-reload-model span": "Salva e Riavvia Modello",
            ".registry-card .card-header h2": "Catalogo Modelli Disponibili",
            ".registry-card .card-header p": "Visualizza i modelli locali configurati nel file <code>models.yaml</code> o pronti al download.",
            ".models-grid__placeholder": "Caricamento modelli in corso...",
            ".app-footer p": "Powered by <strong>llama-cpp-python</strong> &amp; <strong>ThreadingHTTPServer</strong>. Accelerazione hardware Apple Silicon/NVIDIA se disponibile."
        }
    },
    en: {
        flag: "🇬🇧",
        welcomeMessage: "Type a command and press Enter. Examples: <code>uname -a</code>, <code>ls -la</code>, or <code>python --version</code>. Type <code>help</code> for special commands.",
        labels: {
            online: "Online",
            offline: "Disconnected",
            connecting: "Connecting...",
            serverError: "Server Error",
            emptyChatPlaceholder: "Hello! How can I help you today? You can ask me for code explanations, creative tasks, or simple translations. Inference runs locally, and you can monitor server logs in the other panel.",
            toastChatCleared: "Chat cleared!",
            toastLogsDownloaded: "Logs downloaded successfully!",
            toastLogsCleared: "Logs console cleared!",
            toastTerminalCleared: "Terminal cleared!",
            toastCopySuccess: "Copied to clipboard!",
            toastCopyError: "Unable to copy text.",
            typingStart: "LLM is thinking...",
            typingEval: "Evaluating prompt...",
            typingGenerating: (tokens, speed) => `Generating: ${tokens} tokens (${speed} t/s)`,
            inferenceError: "Error during inference processing:",
            terminalRunning: "Running..."
        },
        dom: {
            "title": "Local LLM Studio",
            ".sidebar-brand-text h1": "Local LLM Studio",
            ".sidebar-brand-text .subtext": "Inference Console",
            ".status-info-item:nth-child(1) .label": "Active Model",
            ".status-info-item:nth-child(2) .label": "Inference Backend",
            ".status-info-item:nth-child(3) .label": "Server Address",
            ".nav-item[data-tab='chat-tab']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> Chat Studio',
            ".nav-item[data-tab='logs-tab']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><polyline points="4 17 10 11 12 13 18 7"/><polyline points="14 7 18 7 18 11"/></svg> Server Logs',
            ".nav-item[data-tab='registry-tab']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg> Models & Config',
            "#start-tour-btn": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polygon points="6 3 20 12 6 21 6 3"/></svg> Start Guided Tour',
            ".sidebar-footer-link[href='/example']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><polygon points="6 3 20 12 6 21 6 3"/></svg> API Examples',
            ".sidebar-footer-link[href='/docs']": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/></svg> Swagger API',
            ".params-header h3": "Chat Parameters",
            "label[for='model-select']": "Active Model",
            "#default-model-opt": "Server Default",
            "label[for='system-prompt']": "System Prompt",
            "#system-prompt": { placeholder: "You are a helpful and concise assistant..." },
            "#advanced-params-trigger span": "Advanced Parameters",
            "label[for='param-temp']": "Temperature",
            "label[for='param-tokens']": "Max Output Tokens",
            "label[for='param-topp']": "Top P",
            "label[for='param-topk']": "Top K",
            "label[for='param-penalty']": "Repeat Penalty",
            "label[for='param-force-json'] span:last-child": "Force JSON Output",
            "label[for='param-enable-thinking'] span:last-child": "Enable Reasoning (Thinking)",
            "label[for='param-show-thinking'] span:last-child": "Show <think> Block in Output",
            "#clear-chat-btn": "Clear Conversation",
            "#chat-textarea": { placeholder: "Type a message... (Enter to send, Shift+Enter for new line)" },
            "#log-search-input": { placeholder: "Filter by keyword..." },
            "label[for='log-timestamp-check'] span:last-child": "Timestamp",
            "label[for='log-level-check'] span:last-child": "Level",
            "label[for='log-compact-check'] span:last-child": "Compact",
            "label[for='log-autoscroll-check'] span:last-child": "Auto-scroll",
            "#clear-logs-btn": "Clear",
            "#download-logs-btn": "Download (.txt)",
            ".console-placeholder": "Waiting for server logs...",
            ".terminal-header-title span": "Command Execution Terminal",
            "#clear-terminal-btn": "Clear",
            ".terminal-suggestions-label": "Run:",
            "#terminal-command-input": { placeholder: "Type a command (e.g. ls -la, uname -a, cd ..) and press Enter..." },
            "#run-terminal-btn": "Send",
            "#log-line-count": "0 lines loaded",
            "#sse-indicator span:last-child": "Streaming Active",
            ".config-card .card-header h2": "Hardware Config Status",
            ".config-card .card-header p": "Modify inference engine parameters and perform an in-memory hot-reload of the model.",
            ".host-port-item:nth-child(1) .config-metric__label": "Host Binding",
            ".host-port-item:nth-child(3) .config-metric__label": "Server Port",
            "label[for='cfg-backend']": "Backend Engine",
            "label[for='cfg-ctx-size']": "Context Size (ctx_size)",
            "label[for='cfg-gpu-layers']": "GPU Layers (n_gpu_layers)",
            "label[for='cfg-threads']": "CPU Threads (n_threads)",
            "label[for='cfg-n-batch']": "Batch Size (n_batch)",
            "label[for='cfg-n-ubatch']": "Micro-batch (n_ubatch)",
            "label[for='cfg-timeout']": "Timeout (seconds)",
            ".toggle-control-card:nth-of-type(1) .toggle-control-label": "Offload KQV",
            ".toggle-control-card:nth-of-type(1) .toggle-control-description": "Offload K/V tensors to GPU memory",
            ".toggle-control-card:nth-of-type(2) .toggle-control-label": "Flash Attention",
            ".toggle-control-card:nth-of-type(2) .toggle-control-description": "Speed up inference with Flash Attention",
            ".toggle-control-card:nth-of-type(3) .toggle-control-label": "Use mmap",
            ".toggle-control-card:nth-of-type(3) .toggle-control-description": "Memory-mapped file loading for fast load",
            ".toggle-control-card:nth-of-type(4) .toggle-control-label": "Enable Thinking",
            ".toggle-control-card:nth-of-type(4) .toggle-control-description": "Reasoning mode for compatible models",
            ".toggle-control-card:nth-of-type(5) .toggle-control-label": "Show Thinking",
            ".toggle-control-card:nth-of-type(5) .toggle-control-description": "Show intermediate reasoning steps",
            ".toggle-control-card:nth-of-type(6) .toggle-control-label": "Verbose Logs",
            ".toggle-control-card:nth-of-type(6) .toggle-control-description": "Enable detailed server logs",
            ".path-metric .config-metric__label": "Model File Path",
            "#btn-reload-model span": "Save & Restart Model",
            ".registry-card .card-header h2": "Available Models Catalog",
            ".registry-card .card-header p": "View local models configured in the <code>models.yaml</code> file or ready to download.",
            ".models-grid__placeholder": "Loading models...",
            ".app-footer p": "Powered by <strong>llama-cpp-python</strong> &amp; <strong>ThreadingHTTPServer</strong>. Apple Silicon/NVIDIA hardware acceleration if available."
        }
    }
};

(function () {
    let currentLang = localStorage.getItem('app_lang') || 'it';

    function applyLanguage(lang) {
        currentLang = lang;
        localStorage.setItem('app_lang', lang);
        document.documentElement.setAttribute('lang', lang);

        const resource = I18N_RESOURCES[lang];
        if (!resource) return;

        // 1. Update flag icon in sidebar
        const flagEl = document.getElementById('lang-flag-icon');
        if (flagEl) {
            flagEl.textContent = resource.flag;
        }

        // 2. Update APP_CONFIG labels dynamically
        if (typeof APP_CONFIG !== 'undefined') {
            Object.assign(APP_CONFIG.labels, resource.labels);
            APP_CONFIG.terminal.welcomeMessage = resource.welcomeMessage;
        }

        // 3. Update all static DOM elements using the translation mapping
        for (const [selector, textVal] of Object.entries(resource.dom)) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (typeof textVal === 'string') {
                    // Check if it's title
                    if (selector === 'title') {
                        document.title = textVal;
                    } else {
                        el.innerHTML = textVal;
                    }
                } else if (typeof textVal === 'object') {
                    if (textVal.placeholder) {
                        el.setAttribute('placeholder', textVal.placeholder);
                    }
                    if (textVal.ariaLabel) {
                        el.setAttribute('aria-label', textVal.ariaLabel);
                    }
                }
            });
        }

        // Dispatch language change event for other components if needed
        window.dispatchEvent(new CustomEvent('app-lang-changed', { detail: { lang } }));
    }

    function initLangToggle() {
        const toggleBtn = document.getElementById('lang-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const nextLang = currentLang === 'it' ? 'en' : 'it';
                applyLanguage(nextLang);
            });
        }
        applyLanguage(currentLang);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLangToggle);
    } else {
        initLangToggle();
    }

    // Expose language helper to global scope
    window.AppI18n = {
        getLang: () => currentLang,
        apply: applyLanguage
    };
})();
