/**
 * tour.js — Guided Tour & Demo Mode Engine
 *
 * Implements the interactive walkthrough overlay, highlight spotlight, auto-tab switching,
 * pre-filling demo prompt, and simulating SSE logs and markdown generation.
 * Supports Italian and English language toggles.
 */

(function () {
    let currentStep = 0;
    let tourMode = 'simulated'; // 'simulated' or 'real'
    let isExecutingDemo = false;
    let currentLang = window.AppI18n ? window.AppI18n.getLang() : 'it'; // 'it' or 'en'

    // Elements created dynamically
    let overlayMask = null;
    let spotlight = null;
    let tooltipCard = null;
    let interactiveBlocker = null;

    const TOUR_STEPS = [
        {
            target: ".sidebar-brand",
            title: {
                it: "Benvenuto in Local LLM Studio",
                en: "Welcome to Local LLM Studio"
            },
            body: {
                it: "Questo tour guidato mostra come un'applicazione locale (come ClosedRoom) può integrarsi ed esporre modelli AI on-device tramite un layer server robusto, configurabile e compatibile con le API standard di OpenAI.",
                en: "This guided tour shows how a local application (like ClosedRoom) can integrate and expose on-device AI models through a robust, configurable server layer compatible with standard OpenAI APIs."
            },
            setup: () => {
                showModeSelector(true);
            }
        },
        {
            target: ".status-summary-card",
            title: {
                it: "Stato del server sempre visibile",
                en: "Server status always visible"
            },
            body: {
                it: "La barra laterale indica in tempo reale se l'infrastruttura locale è attiva, quale modello è correntemente caricato in memoria RAM/VRAM, quale backend è in esecuzione e su quale porta risponde.",
                en: "The sidebar indicates in real-time whether the local infrastructure is active, which model is currently loaded in RAM/VRAM, which backend is running, and on which port it responds."
            },
            setup: () => {
                showModeSelector(false);
            }
        },
        {
            target: ".nav-item[data-tab='chat-tab']",
            title: {
                it: "Chat Studio integrato",
                en: "Integrated Chat Studio"
            },
            body: {
                it: "L'area Chat Studio consente agli sviluppatori e al team di validare le performance dei prompt e la qualità del modello caricato prima di collegare qualsiasi applicazione client esterna.",
                en: "The Chat Studio area allows developers and the team to validate prompt performance and the quality of the loaded model before connecting any external client application."
            },
            setup: () => {
                switchTab('chat-tab');
            }
        },
        {
            target: ".params-panel",
            title: {
                it: "Parametri di inferenza rapidi",
                en: "Quick inference parameters"
            },
            body: {
                it: "È possibile selezionare al volo il modello da utilizzare e modificare il system prompt per istruire il comportamento dell'assistente.",
                en: "You can select the model to use on the fly and modify the system prompt to instruct the assistant's behavior."
            },
            setup: () => {
                closeAdvancedParams();
            }
        },
        {
            target: "#advanced-params-trigger",
            title: {
                it: "Opzioni tecniche avanzate",
                en: "Advanced technical options"
            },
            body: {
                it: "I parametri avanzati rimangono nascosti per default ma sono pronti per essere sintonizzati: temperatura per determinismo, JSON Mode per output strutturato e parametri di context window.",
                en: "Advanced parameters remain hidden by default but are ready to be tuned: temperature for determinism, JSON Mode for structured output, and context window parameters."
            },
            setup: () => {
                openAdvancedParams();
            }
        },
        {
            target: "#chat-textarea",
            title: {
                it: "Caso d'uso reale: ClosedRoom",
                en: "Real use case: ClosedRoom"
            },
            body: {
                it: "Immaginiamo di voler analizzare una trascrizione grezza di un meeting locale per estrarre summary, decisioni e action item strutturati in formato JSON.",
                en: "Let's imagine we want to analyze a raw local meeting transcript to extract a structured summary, decisions, and action items in JSON format."
            },
            setup: () => {
                closeAdvancedParams();
                prefillDemoPrompt();
                showActionBtn(true, currentLang === 'it' ? "Avvia Demo" : "Start Demo", executeDemoWorkflow);
            }
        },
        {
            target: ".nav-item[data-tab='logs-tab']",
            title: {
                it: "Osservabilità totale",
                en: "Total observability"
            },
            body: {
                it: "Un sistema locale non deve essere una black box. I log del server mostrano in tempo reale ogni richiesta API ricevuta e l'avanzamento dei processi del motore.",
                en: "A local system shouldn't be a black box. Server logs show in real-time each received API request and the engine's process progress."
            },
            setup: () => {
                switchTab('logs-tab');
            }
        },
        {
            target: "#server-logs-body",
            title: {
                it: "Log del server in tempo reale",
                en: "Real-time server logs"
            },
            body: {
                it: "Qui viene mostrato il caricamento in memoria, le metriche di velocità (tokens/sec), l'impiego dei core CPU/GPU e gli indicatori dello stream SSE.",
                en: "Here you can see the model loading into memory, speed metrics (tokens/sec), CPU/GPU core usage, and SSE stream indicators."
            },
            setup: () => {
                // Done
            }
        },
        {
            target: "#terminal-command-input",
            title: {
                it: "Terminale diagnostico rapido",
                en: "Quick diagnostic terminal"
            },
            body: {
                it: "Per il debug o i controlli rapidi del sistema operativo locale, è disponibile un terminale sandbox senza uscire dal browser.",
                en: "For debugging or quick checks of the local operating system, a sandbox terminal is available without leaving the browser."
            },
            setup: () => {
                // Done
            }
        },
        {
            target: ".nav-item[data-tab='registry-tab']",
            title: {
                it: "Configurazione flessibile",
                en: "Flexible configuration"
            },
            body: {
                it: "Spostiamoci sull'area Modelli e Config per vedere come configurare l'hardware per l'esecuzione.",
                en: "Let's move to the Models and Config area to see how to configure the hardware for execution."
            },
            setup: () => {
                switchTab('registry-tab');
            }
        },
        {
            target: "#hardware-config-form",
            title: {
                it: "Regolazione hardware",
                en: "Hardware adjustment"
            },
            body: {
                it: "Da qui è possibile impostare il backend (llama-cpp-python o MLX), definire i thread CPU da allocare, il numero di layer da scaricare sulla GPU, e riavviare il modello.",
                en: "From here you can set the backend (llama-cpp-python or MLX), define the CPU threads to allocate, the number of layers to offload to the GPU, and reload the model."
            },
            setup: () => {
                // Done
            }
        },
        {
            target: "#models-list-container .model-card",
            title: {
                it: "Catalogo modelli locali",
                en: "Local model catalog"
            },
            body: {
                it: "Il registry dei modelli organizza i pesi scaricati e indica cosa è installato o pronto all'uso, astraendo la complessità per le app esterne.",
                en: "The model registry organizes downloaded weights and shows what is installed or ready to use, abstracting complexity for external apps."
            },
            setup: () => {
                // Done
            }
        },
        {
            target: ".sidebar-footer",
            title: {
                it: "Pronto per l'integrazione",
                en: "Ready for integration"
            },
            body: {
                it: "L'infrastruttura espone endpoint compatibili con lo standard OpenAI. Gli sviluppatori possono accedere a Swagger ed esempi di chiamata con un clic.",
                en: "The infrastructure exposes endpoints compatible with the OpenAI standard. Developers can access Swagger and call examples with one click."
            },
            setup: () => {
                // Done
            }
        },
        {
            target: ".sidebar-brand",
            title: {
                it: "Fine del tour!",
                en: "End of the tour!"
            },
            body: {
                it: "Ora sai come local-llm-server abilita ClosedRoom a eseguire intelligenza artificiale on-device in modo sicuro, performante e osservabile. Vuoi ripetere il tour?",
                en: "Now you know how local-llm-server enables ClosedRoom to run on-device artificial intelligence securely, performantly, and observably. Do you want to repeat the tour?"
            },
            setup: () => {
                showActionBtn(true, currentLang === 'it' ? "Riavvia Tour" : "Restart Tour", () => startTour());
            }
        }
    ];

    // Helper: switch dashboard tabs
    function switchTab(tabId) {
        const navItem = document.querySelector(`.nav-item[data-tab='${tabId}']`);
        if (navItem) {
            navItem.click();
        }
    }

    // Helper: expand advanced params panel
    function openAdvancedParams() {
        const panel = document.getElementById('advanced-params-panel');
        const trigger = document.getElementById('advanced-params-trigger');
        if (panel && panel.classList.contains('collapsible--collapsed')) {
            trigger.click();
        }
    }

    // Helper: collapse advanced params panel
    function closeAdvancedParams() {
        const panel = document.getElementById('advanced-params-panel');
        const trigger = document.getElementById('advanced-params-trigger');
        if (panel && !panel.classList.contains('collapsible--collapsed')) {
            trigger.click();
        }
    }

    // Helper: fill chat textarea with demo data
    function prefillDemoPrompt() {
        const textarea = document.getElementById('chat-textarea');
        if (textarea) {
            textarea.value = DEMO_DATA[currentLang].prompt;
            textarea.dispatchEvent(new Event('input'));
        }
    }

    // Show/hide mode selector inside Step 1 tooltip
    function showModeSelector(show) {
        let selector = tooltipCard.querySelector('.tour-mode-selector');
        if (!selector && show) {
            selector = document.createElement('div');
            selector.className = 'tour-mode-selector';
            if (currentLang === 'it') {
                selector.innerHTML = `
                    <label class="tour-mode-option">
                        <input type="radio" name="tour-mode-choice" value="simulated" ${tourMode === 'simulated' ? 'checked' : ''}>
                        <span class="tour-mode-option-text">
                            <span class="tour-mode-option-title">Demo Simulata (Consigliata)</span>
                            <span class="tour-mode-option-desc">Usa dati mock, log simulati. Veloce, stabile e non richiede un modello caricato sul server.</span>
                        </span>
                    </label>
                    <label class="tour-mode-option" style="margin-top: 8px;">
                        <input type="radio" name="tour-mode-choice" value="real" ${tourMode === 'real' ? 'checked' : ''}>
                        <span class="tour-mode-option-text">
                            <span class="tour-mode-option-title">Demo Reale (Interattiva)</span>
                            <span class="tour-mode-option-desc">Invia la richiesta al server locale. Richiede che ci sia un modello attivo pronto all'uso.</span>
                        </span>
                    </label>
                `;
            } else {
                selector.innerHTML = `
                    <label class="tour-mode-option">
                        <input type="radio" name="tour-mode-choice" value="simulated" ${tourMode === 'simulated' ? 'checked' : ''}>
                        <span class="tour-mode-option-text">
                            <span class="tour-mode-option-title">Simulated Demo (Recommended)</span>
                            <span class="tour-mode-option-desc">Uses mock data, simulated logs. Fast, stable, and does not require a model loaded on the server.</span>
                        </span>
                    </label>
                    <label class="tour-mode-option" style="margin-top: 8px;">
                        <input type="radio" name="tour-mode-choice" value="real" ${tourMode === 'real' ? 'checked' : ''}>
                        <span class="tour-mode-option-text">
                            <span class="tour-mode-option-title">Real Demo (Interactive)</span>
                            <span class="tour-mode-option-desc">Sends the request to the local server. Requires an active model ready to use.</span>
                        </span>
                    </label>
                `;
            }
            const body = tooltipCard.querySelector('.tour-tooltip-body');
            body.appendChild(selector);

            // Bind change
            selector.querySelectorAll('input[name="tour-mode-choice"]').forEach(radio => {
                radio.addEventListener('change', (e) => {
                    tourMode = e.target.value;
                });
            });
        } else if (selector && !show) {
            selector.remove();
        }
    }

    // Toggle special CTA action button inside current step tooltip
    function showActionBtn(show, text = "", callback = null) {
        const actionBtn = tooltipCard.querySelector('#tour-action-btn');
        const nextBtn = tooltipCard.querySelector('#tour-next-btn');

        if (show) {
            actionBtn.style.display = 'inline-block';
            actionBtn.textContent = text;
            nextBtn.style.display = 'none';
            
            // Rebind click listener
            const newBtn = actionBtn.cloneNode(true);
            actionBtn.parentNode.replaceChild(newBtn, actionBtn);
            newBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (callback) callback();
            });
        } else {
            actionBtn.style.display = 'none';
            nextBtn.style.display = 'inline-block';
        }
    }

    // Execute the demo workflow
    async function executeDemoWorkflow() {
        isExecutingDemo = true;
        showActionBtn(false);
        tooltipCard.querySelector('#tour-prev-btn').style.display = 'none';
        tooltipCard.querySelector('.tour-close-btn').style.display = 'none';

        // Add visual indicator blocker to prevent click interference during simulation
        interactiveBlocker = document.createElement('div');
        interactiveBlocker.className = 'tour-interactive-overlay';
        document.body.appendChild(interactiveBlocker);

        if (tourMode === 'simulated') {
            // Simulated Flow
            const textarea = document.getElementById('chat-textarea');
            const clearChatBtn = document.getElementById('clear-chat-btn');
            
            if (clearChatBtn) clearChatBtn.click();
            
            // Clear text inputs
            if (textarea) {
                textarea.value = '';
                textarea.style.height = 'auto';
            }

            // Append User prompt to chat
            ChatWindow.appendMessage('user', DEMO_DATA[currentLang].prompt);

            // Enable thinking status
            const typingStatus = document.getElementById('typing-status');
            const typingText = document.getElementById('typing-text');
            if (typingStatus && typingText) {
                typingText.textContent = currentLang === 'it' 
                    ? "L'LLM sta pensando (Simulazione)..." 
                    : "The LLM is thinking (Simulation)...";
                typingStatus.style.display = 'flex';
            }

            // Stream logs in background
            let logIndex = 0;
            const logInterval = setInterval(() => {
                if (logIndex < DEMO_DATA[currentLang].serverLogs.length) {
                    LogConsole.addLine(DEMO_DATA[currentLang].serverLogs[logIndex]);
                    logIndex++;
                } else {
                    clearInterval(logInterval);
                }
            }, 800);

            // Fake thinking delay
            await new Promise(resolve => setTimeout(resolve, 2000));
            if (typingText) {
                typingText.textContent = currentLang === 'it' 
                    ? "Generazione risposta strutturata in corso..." 
                    : "Generating structured response...";
            }

            await new Promise(resolve => setTimeout(resolve, 2500));

            // Append mock assistant response
            if (typingStatus) typingStatus.style.display = 'none';
            ChatWindow.appendMessage('assistant', DEMO_DATA[currentLang].response, DEMO_DATA[currentLang].thinking, DEMO_DATA[currentLang].stats);

            Toast.show(
                currentLang === 'it' ? "Simulazione completata con successo!" : "Simulation completed successfully!", 
                "success"
            );
            cleanupBlocker();

            // Unlock next step navigation
            isExecutingDemo = false;
            tooltipCard.querySelector('#tour-prev-btn').style.display = 'inline-block';
            tooltipCard.querySelector('.tour-close-btn').style.display = 'flex';
            showActionBtn(true, currentLang === 'it' ? "Vedi i Log Generati" : "View Generated Logs", () => {
                showActionBtn(false);
                nextStep();
            });

        } else {
            // Real Flow
            const sendBtn = document.getElementById('send-chat-btn');
            if (sendBtn) {
                sendBtn.click();
                Toast.show(
                    currentLang === 'it' ? "Richiesta inviata al server!" : "Request sent to the server!", 
                    "info"
                );
            }
            cleanupBlocker();
            isExecutingDemo = false;
            tooltipCard.querySelector('#tour-prev-btn').style.display = 'inline-block';
            tooltipCard.querySelector('.tour-close-btn').style.display = 'flex';
            nextStep();
        }
    }

    function cleanupBlocker() {
        if (interactiveBlocker) {
            interactiveBlocker.remove();
            interactiveBlocker = null;
        }
    }

    // Create spotlight mask layout
    function ensureOverlay() {
        if (!overlayMask) {
            overlayMask = document.createElement('div');
            overlayMask.className = 'tour-overlay-mask';
            document.body.appendChild(overlayMask);
        }
        if (!spotlight) {
            spotlight = document.createElement('div');
            spotlight.className = 'tour-spotlight';
            overlayMask.appendChild(spotlight);
        }
        if (!tooltipCard) {
            tooltipCard = document.createElement('div');
            tooltipCard.className = 'tour-tooltip-card';
            tooltipCard.innerHTML = `
                <div class="tour-tooltip-header">
                    <h4 class="tour-tooltip-title"></h4>
                    <span class="tour-tooltip-badge">Tour</span>
                    <div class="tour-lang-selector">
                        <button class="tour-lang-btn active" data-lang="it">IT</button>
                        <button class="tour-lang-btn" data-lang="en">EN</button>
                    </div>
                    <button class="tour-close-btn" aria-label="Chiudi">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="tour-tooltip-body"></div>
                <div class="tour-tooltip-footer">
                    <span class="tour-step-indicator"></span>
                    <div class="tour-nav-buttons">
                        <button class="tour-btn tour-btn--prev" id="tour-prev-btn">Indietro</button>
                        <button class="tour-btn tour-btn--action" id="tour-action-btn" style="display: none;"></button>
                        <button class="tour-btn tour-btn--next" id="tour-next-btn">Avanti</button>
                    </div>
                </div>
            `;
            overlayMask.appendChild(tooltipCard);

            // Bind global controls
            tooltipCard.querySelector('.tour-close-btn').addEventListener('click', stopTour);
            tooltipCard.querySelector('#tour-prev-btn').addEventListener('click', prevStep);
            tooltipCard.querySelector('#tour-next-btn').addEventListener('click', nextStep);

            // Bind language switcher
            tooltipCard.querySelectorAll('.tour-lang-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const lang = btn.getAttribute('data-lang');
                    if (lang !== currentLang) {
                        if (window.AppI18n) {
                            window.AppI18n.apply(lang);
                        } else {
                            currentLang = lang;
                            tooltipCard.querySelectorAll('.tour-lang-btn').forEach(b => {
                                b.classList.toggle('active', b.getAttribute('data-lang') === currentLang);
                            });
                            renderStep(currentStep);
                        }
                    }
                });
            });
        }
    }

    function removeOverlay() {
        cleanupBlocker();
        if (overlayMask) {
            overlayMask.remove();
            overlayMask = null;
            spotlight = null;
            tooltipCard = null;
        }
        document.body.classList.remove('tour-active');
        const badge = document.getElementById('demo-mode-indicator-badge');
        if (badge) badge.remove();
    }

    function startTour() {
        currentStep = 0;
        ensureOverlay();
        document.body.classList.add('tour-active');

        // Append a Demo Mode visual flag in sidebar status
        const serverStatus = document.getElementById('server-status');
        if (serverStatus && !document.getElementById('demo-mode-indicator-badge')) {
            const badge = document.createElement('span');
            badge.id = 'demo-mode-indicator-badge';
            badge.className = 'sidebar-tour-badge';
            badge.style.marginLeft = '8px';
            badge.textContent = 'Demo';
            serverStatus.parentNode.appendChild(badge);
        }

        renderStep(currentStep);
    }

    function stopTour() {
        removeOverlay();
        Toast.show(
            currentLang === 'it' ? "Tour guidato concluso" : "Guided tour finished", 
            "info"
        );
    }

    function nextStep() {
        if (isExecutingDemo) return;
        if (currentStep < TOUR_STEPS.length - 1) {
            currentStep++;
            renderStep(currentStep);
        } else {
            stopTour();
        }
    }

    function prevStep() {
        if (isExecutingDemo) return;
        if (currentStep > 0) {
            currentStep--;
            renderStep(currentStep);
        }
    }

    function renderStep(index) {
        const step = TOUR_STEPS[index];
        let targetEl = document.querySelector(step.target);

        // Fallback for model cards list
        if (!targetEl && step.target === "#models-list-container .model-card") {
            targetEl = document.querySelector("#models-list-container");
        }

        // Standard actions reset
        showActionBtn(false);

        // If target is missing, skip step gracefully
        if (!targetEl) {
            console.warn(`Tour target not found: ${step.target}`);
            if (index > currentStep) nextStep();
            else prevStep();
            return;
        }

        // Run tab-switching or specific setups first
        if (step.setup) {
            step.setup();
        }

        // Delay positioning slightly to let rendering/transitions complete
        setTimeout(() => {
            positionOverlayAndCard(targetEl, step, index);
        }, 150);
    }

    function positionOverlayAndCard(target, step, index) {
        if (!tooltipCard || !spotlight) return;

        // Position spotlight
        const rect = target.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        // Expand spotlight bounds slightly for padding
        const pad = 6;
        spotlight.style.top = `${rect.top + scrollTop - pad}px`;
        spotlight.style.left = `${rect.left + scrollLeft - pad}px`;
        spotlight.style.width = `${rect.width + (pad * 2)}px`;
        spotlight.style.height = `${rect.height + (pad * 2)}px`;
        spotlight.classList.add('active');

        // Fill tooltip card fields
        tooltipCard.querySelector('.tour-tooltip-title').textContent = step.title[currentLang];
        
        // Retain text but clear mode selector
        const bodyEl = tooltipCard.querySelector('.tour-tooltip-body');
        bodyEl.innerHTML = `<p>${step.body[currentLang]}</p>`;
        
        // Let setups run again for selector if step 0
        if (step.setup) step.setup();

        tooltipCard.querySelector('.tour-step-indicator').textContent = `${index + 1} ${currentLang === 'it' ? 'di' : 'of'} ${TOUR_STEPS.length}`;

        // Hide/Show Back button on step 0
        const prevBtn = tooltipCard.querySelector('#tour-prev-btn');
        prevBtn.textContent = currentLang === 'it' ? 'Indietro' : 'Back';
        prevBtn.style.display = index === 0 ? 'none' : 'inline-block';

        // Set Next/Finish label
        const nextBtn = tooltipCard.querySelector('#tour-next-btn');
        nextBtn.textContent = index === TOUR_STEPS.length - 1 
            ? (currentLang === 'it' ? 'Fine' : 'Finish') 
            : (currentLang === 'it' ? 'Avanti' : 'Next');

        // Calculate card positioning (top, bottom, left or right)
        // Position below target by default, check viewport boundaries
        let cardTop = rect.bottom + scrollTop + 14;
        let cardLeft = rect.left + scrollLeft;

        // Keep inside screen boundaries
        const viewportWidth = window.innerWidth;
        if (cardLeft + 350 > viewportWidth) {
            cardLeft = viewportWidth - 370;
        }
        if (cardLeft < 10) cardLeft = 10;

        // If card falls off screen bottom, put it above target
        const cardHeight = tooltipCard.offsetHeight || 180;
        if (rect.bottom + cardHeight + 40 > window.innerHeight) {
            cardTop = rect.top + scrollTop - cardHeight - 14;
        }

        // Prevent tooltip from going above the current viewport top
        const minTop = scrollTop + 10;
        if (cardTop < minTop) {
            // Reposition below the top edge of the target
            cardTop = rect.top + scrollTop + 14;
        }

        tooltipCard.style.top = `${cardTop}px`;
        tooltipCard.style.left = `${cardLeft}px`;
        tooltipCard.classList.add('active');

        // Auto-scroll screen to keep highlighted item centered
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Register starting listener once DOM is loaded
    function bindStartButton() {
        const startBtn = document.getElementById('start-tour-btn');
        if (startBtn) {
            startBtn.addEventListener('click', startTour);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindStartButton);
    } else {
        bindStartButton();
    }

    // Listen to global language changes
    window.addEventListener('app-lang-changed', (e) => {
        currentLang = e.detail.lang;
        if (tooltipCard) {
            tooltipCard.querySelectorAll('.tour-lang-btn').forEach(b => {
                b.classList.toggle('active', b.getAttribute('data-lang') === currentLang);
            });
            if (tooltipCard.classList.contains('active')) {
                renderStep(currentStep);
            }
        }
    });

    // Expose control to global scope just in case
    window.StudioTour = {
        start: startTour,
        stop: stopTour
    };
})();
