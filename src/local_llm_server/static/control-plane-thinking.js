(() => {
    const REGISTRY_ENDPOINT = '/api/v1/models/registry';
    const CHAT_PATHS = new Set(['/v1/chat/completions', '/api/v1/chat']);
    let records = new Map();
    let defaultRecord = null;
    let refreshPromise = null;

    const originalFetch = window.fetch.bind(window);

    function normalizedMode(value) {
        const mode = String(value || '').trim();
        return ['none', 'switchable', 'always'].includes(mode) ? mode : null;
    }

    function indexRecord(item) {
        if (!item || typeof item !== 'object') return;
        const capabilities = item.capabilities && typeof item.capabilities === 'object'
            ? item.capabilities
            : null;
        const mode = normalizedMode(capabilities?.thinking_mode);
        if (!mode) return;
        const record = {
            key: String(item.key || '').trim(),
            modelId: String(item.model_id || item.id || '').trim(),
            mode,
            resident: item.resident === true,
            isDefault: item.default === true,
        };
        [record.key, record.modelId].filter(Boolean).forEach((identity) => records.set(identity, record));
        if (record.isDefault) defaultRecord = record;
    }

    async function refreshRecords() {
        if (refreshPromise) return refreshPromise;
        refreshPromise = (async () => {
            try {
                const response = await originalFetch(REGISTRY_ENDPOINT, { headers: { Accept: 'application/json' } });
                if (!response.ok) return;
                const payload = await response.json();
                records = new Map();
                defaultRecord = null;
                (Array.isArray(payload?.models) ? payload.models : []).forEach(indexRecord);
            } catch (_) {
                // Capability metadata is progressive enhancement. Legacy behavior
                // remains untouched when the admin catalog is unavailable.
            } finally {
                refreshPromise = null;
            }
            applyThinkingControlState();
        })();
        return refreshPromise;
    }

    function selectedRecord() {
        const select = document.getElementById('model-select');
        const value = String(select?.value || '').trim();
        if (value && records.has(value)) return records.get(value);
        if (!value && defaultRecord) return defaultRecord;
        const selectedText = String(select?.selectedOptions?.[0]?.textContent || '').trim();
        for (const record of new Set(records.values())) {
            if (selectedText && (selectedText.includes(record.modelId) || selectedText.includes(record.key))) {
                return record;
            }
        }
        return null;
    }

    function controls() {
        const enable = document.getElementById('param-enable-thinking');
        const show = document.getElementById('param-show-thinking');
        return {
            enable,
            show,
            enableGroup: enable?.closest('.checkbox-group') || null,
            showGroup: show?.closest('.checkbox-group') || null,
        };
    }

    function ensureSemanticsHint(enableGroup, showGroup) {
        if (enableGroup && !enableGroup.querySelector('[data-thinking-execution-hint]')) {
            const hint = document.createElement('small');
            hint.dataset.thinkingExecutionHint = 'true';
            hint.className = 'thinking-control-hint';
            hint.textContent = 'Controls whether the model performs reasoning for this request.';
            enableGroup.appendChild(hint);
        }
        if (showGroup && !showGroup.querySelector('[data-thinking-visibility-hint]')) {
            const hint = document.createElement('small');
            hint.dataset.thinkingVisibilityHint = 'true';
            hint.className = 'thinking-control-hint';
            hint.textContent = 'Display only: does not enable or disable model reasoning.';
            showGroup.appendChild(hint);
        }
    }

    function applyThinkingControlState() {
        const record = selectedRecord();
        const mode = record?.mode || null;
        const { enable, show, enableGroup, showGroup } = controls();
        if (!enable || !show || !mode) return;

        ensureSemanticsHint(enableGroup, showGroup);
        enable.dataset.thinkingMode = mode;
        show.dataset.thinkingMode = mode;

        if (mode === 'none') {
            enable.checked = false;
            enable.disabled = true;
            show.checked = false;
            show.disabled = true;
            if (enableGroup) enableGroup.style.display = 'none';
            if (showGroup) showGroup.style.display = 'none';
            return;
        }

        if (enableGroup) enableGroup.style.display = 'block';
        if (showGroup) showGroup.style.display = 'block';
        show.disabled = false;

        if (mode === 'always') {
            enable.checked = true;
            enable.disabled = true;
            enable.title = 'Reasoning is always enabled by this runtime and cannot be changed per request.';
        } else {
            enable.disabled = false;
            enable.title = 'Enable or disable model reasoning for this request.';
        }
        show.title = 'Controls visibility only; model reasoning execution is unchanged.';
    }

    function chatRequestPath(input) {
        try {
            const raw = typeof input === 'string' ? input : input?.url;
            if (!raw) return null;
            return new URL(raw, window.location.origin).pathname;
        } catch (_) {
            return null;
        }
    }

    function rewriteChatOptions(input, options = {}) {
        const path = chatRequestPath(input);
        if (!CHAT_PATHS.has(path) || typeof options.body !== 'string') return options;
        let payload;
        try { payload = JSON.parse(options.body); } catch (_) { return options; }
        if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return options;

        const record = selectedRecord();
        const mode = record?.mode || null;
        if (!mode) return options;
        const { enable, show } = controls();

        if (mode === 'switchable' && enable) {
            // Explicit false is intentional: an unchecked control must override a
            // runtime default of true rather than silently omitting the field.
            payload.enable_thinking = Boolean(enable.checked);
        } else {
            delete payload.enable_thinking;
            delete payload.enable_reasoning;
        }

        if (mode !== 'none' && show) {
            // Rendering preference is independent from execution policy.
            payload.show_thinking = Boolean(show.checked);
        } else {
            delete payload.show_thinking;
            delete payload.show_reasoning;
        }

        return { ...options, body: JSON.stringify(payload) };
    }

    window.fetch = function thinkingAwareFetch(input, options = {}) {
        return originalFetch(input, rewriteChatOptions(input, options));
    };

    function bind() {
        const select = document.getElementById('model-select');
        if (select) {
            select.addEventListener('change', () => {
                // app.js also owns a legacy change handler; run after its synchronous
                // visibility changes so the server-owned thinking_mode wins.
                setTimeout(applyThinkingControlState, 0);
            });
        }
        refreshRecords();
        window.setInterval(refreshRecords, 10000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind, { once: true });
    } else {
        bind();
    }

    window.localLlmThinkingControls = {
        refresh: refreshRecords,
        selectedMode: () => selectedRecord()?.mode || null,
        rewriteChatOptions,
    };
})();
