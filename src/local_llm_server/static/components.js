/**
 * components.js — Reusable UI Components for Local LLM Studio
 *
 * Provides encapsulated, configurable component modules to orchestrate UI states
 * and decouple DOM manipulations from the main application flow.
 */

/* ═══════════════════════════════════════════════════════════════════════════════
   TOAST NOTIFICATION SYSTEM
   ═══════════════════════════════════════════════════════════════════════════════ */
const Toast = (() => {
    let container = null;

    function _ensureContainer() {
        if (container) return;
        container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
    }

    /**
     * Show a toast message.
     * @param {string} message 
     * @param {'success'|'error'|'warning'|'info'} type 
     */
    function show(message, type = 'success') {
        _ensureContainer();
        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        
        const icons = {
            success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
            error: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            info: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
        };

        toast.innerHTML = `
            <span class="toast__icon">${icons[type] || icons.success}</span>
            <span class="toast__message">${message}</span>
        `;

        container.appendChild(toast);
        
        // Triggers entrance animation
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });

        // Dismiss sequence
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(12px)';
            toast.addEventListener('transitionend', () => toast.remove(), { once: true });
        }, APP_CONFIG.toast.durationMs);
    }

    return { show };
})();

/* ═══════════════════════════════════════════════════════════════════════════════
   COLLAPSIBLE PANEL HELPER (Progressive Disclosure)
   ═══════════════════════════════════════════════════════════════════════════════ */
const CollapsiblePanel = (() => {
    function init() {
        document.querySelectorAll('[data-collapsible-trigger]').forEach(trigger => {
            // Avoid duplicate bindings
            if (trigger.getAttribute('data-collapsible-bound') === 'true') return;
            trigger.setAttribute('data-collapsible-bound', 'true');

            const targetId = trigger.getAttribute('data-collapsible-trigger');
            const targetEl = document.getElementById(targetId);
            if (!targetEl) return;

            // Set initial state
            if (targetEl.classList.contains('collapsible--collapsed')) {
                targetEl.style.maxHeight = '0px';
                targetEl.style.overflow = 'hidden';
            } else {
                targetEl.style.maxHeight = 'none';
            }

            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                toggle(trigger, targetEl);
            });
        });
    }

    function toggle(trigger, panel) {
        const isCollapsed = panel.classList.contains('collapsible--collapsed');
        
        if (isCollapsed) {
            panel.classList.remove('collapsible--collapsed');
            panel.style.maxHeight = panel.scrollHeight + 'px';
            trigger.classList.add('collapsible-trigger--open');
            
            const handleTransitionEnd = (e) => {
                if (e.propertyName === 'max-height') {
                    panel.style.maxHeight = 'none';
                    panel.removeEventListener('transitionend', handleTransitionEnd);
                }
            };
            panel.addEventListener('transitionend', handleTransitionEnd);
        } else {
            panel.style.maxHeight = panel.scrollHeight + 'px';
            // Force browser reflow
            panel.offsetHeight; 
            
            requestAnimationFrame(() => {
                panel.style.maxHeight = '0px';
                panel.classList.add('collapsible--collapsed');
                trigger.classList.remove('collapsible-trigger--open');
            });
        }
    }

    return { init, toggle };
})();

/* ═══════════════════════════════════════════════════════════════════════════════
   SERVER LOGS CONSOLE COMPONENT
   ═══════════════════════════════════════════════════════════════════════════════ */
const LogConsole = (() => {
    let rawLogs = [];
    let showTimestamps = true;
    let showLevels = true;
    let visualCompact = false;
    let searchFilter = "";

    const dom = {
        body: null,
        count: null,
        autoscroll: null,
        search: null,
        sseIndicator: null,
        sseIndicatorDot: null
    };

    function bind(elements) {
        Object.assign(dom, elements);
        rawLogs = [];
        _setupEventListeners();
    }

    function _setupEventListeners() {
        if (dom.search) {
            dom.search.addEventListener('input', (e) => {
                searchFilter = e.target.value;
                renderAll();
            });
        }
    }

    function clear() {
        rawLogs = [];
        if (dom.body) dom.body.innerHTML = '';
        _updateStats();
        Toast.show(APP_CONFIG.labels.toastLogsCleared, 'success');
    }

    function addLine(lineText) {
        if (rawLogs.length >= APP_CONFIG.logs.maxBufferLines) {
            rawLogs.shift();
            if (dom.body && dom.body.firstChild) {
                dom.body.firstChild.remove();
            }
        }
        
        rawLogs.push(lineText);
        _updateStats();

        // Single line append
        if (dom.body) {
            const row = _createRow(lineText);
            if (row) {
                dom.body.appendChild(row);
                if (dom.autoscroll && dom.autoscroll.checked) {
                    dom.body.scrollTop = dom.body.scrollHeight;
                }
            }
        }
    }

    function toggleTimestamps(show) {
        showTimestamps = show;
        renderAll();
    }

    function toggleLevels(show) {
        showLevels = show;
        renderAll();
    }

    function toggleCompact(compact) {
        visualCompact = compact;
        renderAll();
    }

    function renderAll() {
        if (!dom.body) return;
        dom.body.innerHTML = '';

        rawLogs.forEach(line => {
            const row = _createRow(line);
            if (row) dom.body.appendChild(row);
        });

        if (dom.autoscroll && dom.autoscroll.checked) {
            dom.body.scrollTop = dom.body.scrollHeight;
        }
    }

    function _createRow(lineText) {
        const query = searchFilter.toLowerCase();
        if (query && !lineText.toLowerCase().includes(query)) {
            return null;
        }

        const div = document.createElement('div');
        div.className = 'log-line';

        // Strip ANSI codes just for regex matching
        const strippedForRegex = lineText.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');

        // Parse structures
        // [17:34:25] INFO [local-llm.server]: log message
        const logRegex = /^\[(\d{2}:\d{2}:\d{2})\]\s+([A-Z]+)\s+\[([^\]]+)\]:\s+(.*)$/;
        const match = strippedForRegex.match(logRegex);

        if (match) {
            const [_, time, level, loggerName, strippedMsg] = match;
            
            // Extract the original message (retaining ANSI colors)
            const prefixMarker = `[${loggerName}]: `;
            const markerIndex = lineText.indexOf(prefixMarker);
            let rawMsg = strippedMsg;
            if (markerIndex !== -1) {
                rawMsg = lineText.substring(markerIndex + prefixMarker.length);
            }
            
            // Format options
            const timeSpan = showTimestamps ? `<span class="log-line--timestamp">[${time}]</span> ` : '';
            const levelSpan = showLevels ? `<span class="log-level-tag log-level-tag--${level.toLowerCase()}">${level}</span> ` : '';
            const scopeSpan = visualCompact ? '' : `<span class="log-line--logger">[${loggerName}]:</span> `;
            
            div.innerHTML = `${timeSpan}${levelSpan}${scopeSpan}<span class="log-line--message">${_ansiToHTML(rawMsg)}</span>`;
            div.classList.add(`log-row--${level.toLowerCase()}`);
        } else {
            // General format or access log fallback
            let formatted = _ansiToHTML(lineText);
            formatted = formatted.replace(/^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} - - \[[^\]]+\])/, '<span class="log-line--timestamp">$1</span>');
            div.innerHTML = formatted;

            if (strippedForRegex.includes('INFO')) div.classList.add('log-row--info');
            else if (strippedForRegex.includes('ERROR') || strippedForRegex.includes('failed')) div.classList.add('log-row--error');
            else if (strippedForRegex.includes('WARNING') || strippedForRegex.includes('warn')) div.classList.add('log-row--warning');
            else if (strippedForRegex.includes('DEBUG')) div.classList.add('log-row--debug');
            else if (strippedForRegex.includes('inference') || strippedForRegex.includes('generating')) div.classList.add('log-row--inference');
        }

        return div;
    }

    function _updateStats() {
        if (dom.count) {
            const isIt = window.AppI18n ? window.AppI18n.getLang() === 'it' : true;
            dom.count.textContent = isIt 
                ? `${rawLogs.length} righe caricate` 
                : `${rawLogs.length} lines loaded`;
        }
    }

    function getRawLogs() {
        return rawLogs;
    }

    function setStreamStatus(status) {
        if (!dom.sseIndicator || !dom.sseIndicatorDot) return;
        
        if (status === 'connected') {
            dom.sseIndicator.style.color = 'var(--color-accent)';
            dom.sseIndicatorDot.style.backgroundColor = 'var(--color-accent)';
            dom.sseIndicatorDot.className = 'active-sse-badge__dot';
        } else if (status === 'error') {
            dom.sseIndicator.style.color = 'var(--color-danger)';
            dom.sseIndicatorDot.style.backgroundColor = 'var(--color-danger)';
            dom.sseIndicatorDot.className = 'active-sse-badge__dot';
        } else {
            dom.sseIndicator.style.color = 'var(--text-muted)';
            dom.sseIndicatorDot.style.backgroundColor = 'var(--text-muted)';
            dom.sseIndicatorDot.className = 'active-sse-badge__dot';
        }
    }

    function _escapeHTML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function _ansiToHTML(text) {
        const ansiRegex = /[\u001b\u009b]\[([0-9;]*)m/g;
        let html = "";
        let lastIndex = 0;
        let spanOpen = false;
        
        // Map ANSI codes to classes
        const codeMap = {
            '0': 'reset',
            '90': 'ansi-gray',
            '91': 'ansi-red',
            '92': 'ansi-green',
            '93': 'ansi-yellow',
            '94': 'ansi-blue',
            '95': 'ansi-magenta',
            '96': 'ansi-cyan',
            '97': 'ansi-white',
            '30': 'ansi-black',
            '31': 'ansi-red',
            '32': 'ansi-green',
            '33': 'ansi-yellow',
            '34': 'ansi-blue',
            '35': 'ansi-magenta',
            '36': 'ansi-cyan',
            '37': 'ansi-white'
        };

        let match;
        while ((match = ansiRegex.exec(text)) !== null) {
            // Append raw text before the match
            const rawText = text.substring(lastIndex, match.index);
            html += _escapeHTML(rawText);
            
            const codes = match[1].split(';');
            
            let isReset = codes.includes('0') || codes.includes('');
            let colorClass = "";
            
            for (const code of codes) {
                if (codeMap[code] && codeMap[code] !== 'reset') {
                    colorClass = codeMap[code];
                }
            }
            
            if (isReset || colorClass) {
                if (spanOpen) {
                    html += "</span>";
                    spanOpen = false;
                }
                if (colorClass) {
                    html += `<span class="${colorClass}">`;
                    spanOpen = true;
                }
            }
            
            lastIndex = ansiRegex.lastIndex;
        }
        
        // Append remaining text
        html += _escapeHTML(text.substring(lastIndex));
        
        // Close any unclosed span
        if (spanOpen) {
            html += "</span>";
        }
        
        return html;
    }

    return { bind, clear, addLine, toggleTimestamps, toggleLevels, toggleCompact, renderAll, getRawLogs, setStreamStatus };
})();

/* ═══════════════════════════════════════════════════════════════════════════════
   MODEL CATALOG COMPONENT
   ═══════════════════════════════════════════════════════════════════════════════ */
const ModelCatalog = (() => {
    let domContainer = null;
    let onSelectModel = null;

    function init(container, onSelect) {
        domContainer = container;
        onSelectModel = onSelect;
    }

    const escapeHtml = (value) => String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');

    function render(models) {
        if (!domContainer) return;
        domContainer.innerHTML = '';

        if (!models || models.length === 0) {
            domContainer.innerHTML = `<div class="models-grid__placeholder">Nessun modello registrato nel file models.yaml.</div>`;
            return;
        }

        models.forEach(model => {
            const card = document.createElement('div');
            const isResident = Boolean(model.resident);
            const isDefault = Boolean(model.default);
            const isBusy = Boolean(model.runtime_status?.active);
            card.className = `model-card ${isResident ? 'model-card--resident' : ''} ${isDefault ? 'model-card--active' : ''}`;

            const availabilityBadge = model.downloaded
                ? `<span class="tag-badge tag-badge--downloaded">Disponibile</span>`
                : `<span class="tag-badge tag-badge--missing">Non scaricato</span>`;
            const runtimeBadge = isResident
                ? `<span class="tag-badge tag-badge--resident">${isBusy ? 'In uso' : 'In memoria'}</span>`
                : '';
            const tagsHtml = (model.tags || []).slice(0, 3).map(t => `<span class="tag-badge">${escapeHtml(t)}</span>`).join('');
            
            const detailId = `model-detail-${String(model.key).replace(/[^a-zA-Z0-9_-]/g, '-')}`;

            card.innerHTML = `
                <div class="model-card__header">
                    <div>
                        <h4 class="model-card__title">${escapeHtml(model.key)}</h4>
                        <div class="model-card__tags">
                            ${runtimeBadge}
                            ${availabilityBadge}
                            ${tagsHtml}
                        </div>
                    </div>
                    ${isDefault ? '<span class="active-indicator-pulse">Predefinito</span>' : ''}
                </div>

                <div class="model-card__body">
                    <div class="compact-info-row">
                        <span>${escapeHtml(model.backend)} · <strong>${model.size_gb ? model.size_gb + ' GB' : 'Dimensione N/A'}</strong></span>
                        <button class="btn btn--link btn--sm p-0 collapsible-trigger-link" data-collapsible-trigger="${detailId}">
                            Dettagli parametri
                            <svg class="chevron-icon" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="6 9 12 15 18 9"/></svg>
                        </button>
                    </div>

                    <!-- Hidden parameter details (Progressive Disclosure) -->
                    <div id="${detailId}" class="collapsible-details-panel collapsible--collapsed">
                        <div class="model-technical-details">
                            <div class="technical-row">
                                <span>ID Modello:</span>
                                <code class="technical-code">${escapeHtml(model.model_id)}</code>
                            </div>
                            <div class="technical-row">
                                <span>Percorso locale:</span>
                                <code class="technical-code technical-code--path" title="${escapeHtml(model.path)}">${escapeHtml(model.path)}</code>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="model-card__actions">
                    <button type="button" class="btn btn--secondary btn--sm btn--copy-id" data-model-id="${escapeHtml(model.key)}">
                        Copia ID
                    </button>
                    ${model.downloaded && !isResident ? `
                        <button type="button" class="btn btn--primary btn--sm" data-model-action="load" data-model-key="${escapeHtml(model.key)}">
                            Carica in memoria
                        </button>
                    ` : ''}
                    ${isResident && !isDefault ? `
                        <button type="button" class="btn btn--primary btn--sm" data-model-action="default" data-model-key="${escapeHtml(model.key)}">
                            Imposta predefinito
                        </button>
                    ` : ''}
                    ${isResident ? `
                        <button type="button" class="btn btn--secondary btn--sm" data-model-action="configure" data-model-key="${escapeHtml(model.key)}">
                            Configura
                        </button>
                    ` : ''}
                    ${isResident ? `
                        <button type="button" class="btn btn--danger-subtle btn--sm" data-model-action="unload" data-model-key="${escapeHtml(model.key)}" ${isBusy ? 'disabled title="Modello in uso"' : ''}>
                            Scarica memoria
                        </button>
                    ` : ''}
                    ${!model.downloaded ? `
                        <a href="https://huggingface.co" target="_blank" class="btn btn--secondary btn--sm">
                            Scarica manuale
                        </a>
                    ` : ''}
                </div>
            `;

            // Bind click for copy action
            card.querySelector('.btn--copy-id').addEventListener('click', () => {
                navigator.clipboard.writeText(model.key).then(() => {
                    Toast.show(APP_CONFIG.labels.toastCopySuccess, 'success');
                }).catch(() => {
                    Toast.show(APP_CONFIG.labels.toastCopyError, 'error');
                });
            });

            card.querySelectorAll('[data-model-action]').forEach(button => {
                button.addEventListener('click', async () => {
                    if (!onSelectModel) return;
                    button.disabled = true;
                    button.classList.add('btn--loading');
                    try {
                        await onSelectModel(button.dataset.modelAction, model.key);
                    } finally {
                        button.disabled = false;
                        button.classList.remove('btn--loading');
                    }
                });
            });

            domContainer.appendChild(card);
        });

        // Re-initialize collapsing accordion panels
        CollapsiblePanel.init();
    }

    return { init, render };
})();

/* ═══════════════════════════════════════════════════════════════════════════════
   CHAT WINDOW COMPONENT (Inference UI & Markdown Parser)
   ═══════════════════════════════════════════════════════════════════════════════ */
const ChatWindow = (() => {
    let container = null;
    let showThinking = true;

    function bind(element, optShowThinking = true) {
        container = element;
        showThinking = optShowThinking;
    }

    function setShowThinking(val) {
        showThinking = val;
    }

    function clearChat(welcomeText) {
        if (!container) return;
        container.innerHTML = `
            <div class="message message--assistant animate-message-in">
                <div class="message__avatar">AI</div>
                <div class="message__content">
                    <div class="assistant-response">
                        <p>${welcomeText}</p>
                    </div>
                </div>
            </div>
        `;
    }

    function appendMessage(role, text, thinking = '', stats = {}, imageUrl = '') {
        if (!container) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = `message message--${role} animate-message-in`;

        const avatar = role === 'user' ? 'ME' : 'AI';
        let contentHtml = '';

        if (role === 'assistant') {
            // Progressive disclosure of thinking accordion
            if (showThinking && thinking && thinking.trim()) {
                const thinkId = `think-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
                contentHtml += `
                    <div class="think-details-card">
                        <div class="think-summary-header" data-collapsible-trigger="${thinkId}">
                            <span>Ragionamento (Thinking Process)</span>
                            <svg class="chevron-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
                        </div>
                        <div id="${thinkId}" class="think-content-panel collapsible--collapsed">
                            <div class="think-inner-text">${_formatMarkdown(thinking)}</div>
                        </div>
                    </div>
                `;
            }

            const cleanText = _cleanJsonResponse(text);
            contentHtml += `<div class="assistant-response">${_formatMarkdown(cleanText)}</div>`;

            // Display performance statistics
            if (stats.tokens_per_second || stats.time_total_seconds) {
                const speed = stats.tokens_per_second ? stats.tokens_per_second.toFixed(1) : '-';
                const time = stats.time_total_seconds ? stats.time_total_seconds.toFixed(2) : '-';
                const tokens = stats.output_tokens || stats.total_tokens || '-';
                
                contentHtml += `
                    <div class="message-meta-badge">
                        <span><strong>${tokens}</strong> tokens</span>
                        <span class="meta-dot"></span>
                        <span><strong>${time}s</strong> impiegati</span>
                        <span class="meta-dot"></span>
                        <span><strong>${speed}</strong> t/s</span>
                    </div>
                `;
            }
        } else {
            contentHtml = `<div class="user-response">`;
            if (imageUrl) {
                contentHtml += `<div class="user-attached-image-wrapper"><img src="${imageUrl}" class="user-attached-image" alt="Immagine allegata"></div>`;
            }
            contentHtml += `<p>${_escapeHTML(text)}</p></div>`;
        }

        msgDiv.innerHTML = `
            <div class="message__avatar">${avatar}</div>
            <div class="message__content">${contentHtml}</div>
        `;

        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;

        // Auto-initialize collapsible on the thinking container
        CollapsiblePanel.init();

        // Bind copy buttons inside code blocks
        _bindCodeCopyButtons(msgDiv);
        return msgDiv;
    }

    function updateAssistantMessage(messageEl, text) {
        if (!messageEl) return;
        const response = messageEl.querySelector('.assistant-response');
        if (!response) return;
        response.innerHTML = _formatMarkdown(text);
        container.scrollTop = container.scrollHeight;
    }

    function _bindCodeCopyButtons(messageEl) {
        messageEl.querySelectorAll('.code-block-header__copy').forEach(btn => {
            btn.addEventListener('click', () => {
                const pre = btn.closest('.code-block-container').querySelector('pre');
                if (pre) {
                    navigator.clipboard.writeText(pre.innerText).then(() => {
                        const isIt = window.AppI18n ? window.AppI18n.getLang() === 'it' : true;
                        btn.textContent = isIt ? "Copiato!" : "Copied!";
                        btn.classList.add('code-block-header__copy--success');
                        setTimeout(() => {
                            btn.textContent = isIt ? "Copia" : "Copy";
                            btn.classList.remove('code-block-header__copy--success');
                        }, 2000);
                    }).catch(() => {
                        Toast.show(APP_CONFIG.labels.toastCopyError, 'error');
                    });
                }
            });
        });
    }

    function _formatMarkdown(text) {
        let esc = _escapeHTML(text);

        // Code blocks: ```language\ncode\n```
        esc = esc.replace(/```([a-zA-Z0-9+#-]+)?\n([\s\S]+?)\n```/g, (match, lang, code) => {
            const displayLang = lang ? lang.toUpperCase() : 'CODE';
            return `
                <div class="code-block-container">
                    <div class="code-block-header">
                        <span class="code-block-header__lang">${displayLang}</span>
                        <button class="code-block-header__copy">Copia</button>
                    </div>
                    <pre><code class="language-${lang || 'txt'}">${code}</code></pre>
                </div>
            `;
        });

        // Inline code: `code`
        esc = esc.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');

        // Bold formatting: **text**
        esc = esc.replace(/\*\*([\s\S]+?)\*\*/g, '<strong>$1</strong>');

        // Convert double newlines to paragraphs
        esc = esc.split('\n\n').map(p => {
            if (p.trim().startsWith('<div class="code-block-container"')) {
                return p; // don't wrap code containers in paragraphs
            }
            return `<p>${p.replace(/\n/g, '<br>')}</p>`;
        }).join('');

        return esc;
    }

    function _cleanJsonResponse(rawText) {
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
                            .join('\n\n');
                    }
                }
            } catch (e) {
                // Return original on JSON parse fail
            }
        }
        return rawText;
    }

    function _escapeHTML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    return { bind, clearChat, appendMessage, updateAssistantMessage, setShowThinking };
})();
