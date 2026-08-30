/**
 * config.js — Frontend Configuration for Local LLM Studio
 */

(function ensureControlPlaneAssets() {
    if (typeof document === 'undefined') return;

    const stylesheets = [
        ['data-local-llm-design-system', '/static/design-system.css'],
        ['data-local-llm-control-plane-shell', '/static/control-plane-shell.css'],
        ['data-local-llm-control-plane-models', '/static/control-plane-models.css'],
        ['data-local-llm-control-plane-capabilities', '/static/control-plane-capabilities.css'],
        ['data-local-llm-control-plane-system', '/static/control-plane-system.css'],
        ['data-local-llm-control-plane-evaluation', '/static/control-plane-evaluation.css'],
        ['data-local-llm-control-plane-evaluation-history', '/static/control-plane-evaluation-history.css'],
    ];
    stylesheets.forEach(([marker, href]) => {
        if (document.querySelector(`link[${marker}]`)) return;
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        link.setAttribute(marker, 'true');
        document.head.appendChild(link);
    });

    const scripts = [
        ['localLlmControlPlaneShell', '/static/control-plane-shell.js'],
        ['localLlmControlPlaneLive', '/static/control-plane-live.js'],
        ['localLlmControlPlaneModels', '/static/control-plane-models.js'],
        ['localLlmControlPlaneCapabilities', '/static/control-plane-capabilities.js'],
        ['localLlmThinkingControls', '/static/control-plane-thinking.js'],
        ['localLlmControlPlaneSystem', '/static/control-plane-system.js'],
        ['localLlmControlPlaneEvaluation', '/static/control-plane-evaluation.js'],
        ['localLlmControlPlaneEvaluationHistory', '/static/control-plane-evaluation-history.js'],
        ['localLlmEvaluationReasoning', '/static/control-plane-evaluation-reasoning.js'],
    ];
    scripts.forEach(([marker, src]) => {
        if (document.querySelector(`script[data-${marker.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`)}]`)) return;
        const script = document.createElement('script');
        script.src = src;
        script.defer = true;
        script.dataset[marker] = 'true';
        document.head.appendChild(script);
    });
})();

const APP_CONFIG = {
    theme: {
        default: 'dark',
        storageKey: 'theme'
    },
    polling: {
        serverHealth: 10000,
        statusUpdate: 300
    },
    logs: {
        maxBufferLines: 2000,
        sseRetryMs: 5000
    },
    toast: {
        durationMs: 4000
    },
    chat: {
        maxContextHistory: 10,
        defaultSystemPrompt: "Sei un assistente utile e sintetico."
    },
    terminal: {
        welcomeMessage: "Digita un comando e premi Invio. Esempi: <code>uname -a</code>, <code>ls -la</code> o <code>python --version</code>. Digita <code>help</code> per i comandi speciali.",
        defaultPrompt: "$",
        timeoutSeconds: 15,
        maxLines: 100
    },
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
        typingGenerating: (chunks, speed) => `Generazione in corso: ${chunks} chunk (${speed} chunk/s)`,
        inferenceError: "Errore durante l'elaborazione dell'inferenza:",
        terminalRunning: "In esecuzione..."
    }
};
