/**
 * config.js — Frontend Configuration for Local LLM Studio
 */

const APP_CONFIG = {
    // Basic settings
    theme: {
        default: 'dark',
        storageKey: 'theme'
    },

    // Polling intervals in milliseconds
    polling: {
        serverHealth: 10000, // check health every 10s
        statusUpdate: 300   // poll generation status every 300ms during inference
    },

    // Log Console configurations
    logs: {
        maxBufferLines: 2000, // limit cached lines to prevent memory bloating
        sseRetryMs: 5000       // retry SSE connection after 5 seconds if failed
    },

    // Toast Notifications
    toast: {
        durationMs: 4000
    },

    // Default chat settings (if not overridden by backend)
    chat: {
        maxContextHistory: 10, // how many past messages to keep in prompt payload
        defaultSystemPrompt: "Sei un assistente utile e sintetico."
    },

    // Terminal settings
    terminal: {
        welcomeMessage: "Digita un comando e premi Invio. Esempi: <code>uname -a</code>, <code>ls -la</code> o <code>python --version</code>. Digita <code>help</code> per i comandi speciali.",
        defaultPrompt: "$",
        timeoutSeconds: 15,
        maxLines: 100
    },

    // UI Translation Labels
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
    }
};
