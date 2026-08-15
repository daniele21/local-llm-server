(() => {
    const REFRESH_MS = 10000;
    const MAX_AUDIO_BYTES = 100 * 1024 * 1024;
    let timer = null;
    let records = [];
    let recordByIdentity = new Map();

    async function fetchJson(path, options = {}) {
        const response = await fetch(path, {
            headers: { Accept: 'application/json', ...(options.headers || {}) },
            ...options,
        });
        let payload = null;
        try { payload = await response.json(); } catch (_) { payload = null; }
        if (!response.ok) {
            const detail = payload?.detail?.message || payload?.detail || `${path} returned ${response.status}`;
            const error = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
            error.status = response.status;
            throw error;
        }
        return payload;
    }

    function normalizeCapabilities(value) {
        if (!value || typeof value !== 'object') return null;
        const tasks = Array.isArray(value.tasks) ? value.tasks.map(String) : [];
        const inputs = Array.isArray(value.input_modalities) ? value.input_modalities.map(String) : [];
        const outputs = Array.isArray(value.output_modalities) ? value.output_modalities.map(String) : [];
        const features = Array.isArray(value.features) ? value.features.map(String) : [];
        if (!tasks.length || !inputs.length || !outputs.length) return null;
        return { tasks, inputs, outputs, features };
    }

    function buildRecords(residentPayload, catalogPayload) {
        const residents = Array.isArray(residentPayload?.data) ? residentPayload.data : [];
        const catalog = Array.isArray(catalogPayload?.models) ? catalogPayload.models : [];
        const residentIds = new Set();
        residents.forEach((item) => {
            [item?.key, item?.id, item?.model_id].filter(Boolean).forEach((value) => residentIds.add(String(value)));
        });

        const map = new Map();
        const merge = (item, configured) => {
            if (!item || typeof item !== 'object') return;
            const key = String(item.key ?? item.id ?? item.model_id ?? '').trim();
            const modelId = String(item.model_id ?? item.id ?? item.key ?? '').trim();
            if (!key && !modelId) return;
            const identity = key || modelId;
            const previous = map.get(identity) || {};
            const caps = normalizeCapabilities(item.capabilities) || previous.capabilities || null;
            const aliases = new Set([...(previous.aliases || []), key, modelId].filter(Boolean));
            const resident = previous.resident === true || Boolean(item.resident) || residentIds.has(key) || residentIds.has(modelId);
            map.set(identity, {
                key: key || previous.key || modelId,
                modelId: modelId || previous.modelId || key,
                backend: item.backend ?? previous.backend ?? null,
                capabilities: caps,
                capabilitySource: item.capability_source ?? previous.capabilitySource ?? null,
                resident,
                configured: previous.configured === true || configured,
                aliases: [...aliases],
            });
        };

        catalog.forEach((item) => merge(item, true));
        residents.forEach((item) => merge(item, false));

        const result = [...map.values()];
        const index = new Map();
        result.forEach((record) => {
            [record.key, record.modelId, ...(record.aliases || [])].filter(Boolean).forEach((value) => {
                index.set(String(value), record);
            });
        });
        records = result;
        recordByIdentity = index;
    }

    function endpointSupport(task) {
        return records.filter((record) => record.resident && record.capabilities?.tasks.includes(task));
    }

    function renderEndpoints(catalogAvailable) {
        const panel = document.getElementById('endpoints-tab');
        if (!panel) return;

        const chat = endpointSupport('chat');
        const vision = endpointSupport('vision_language');
        const structured = endpointSupport('structured_generation');
        const transcription = endpointSupport('transcription');
        const sourceStatus = catalogAvailable ? 'Catalog + resident capability sources' : 'Resident capability source';

        panel.innerHTML = `
            <div class="control-plane-header">
                <div>
                    <h2>Endpoints</h2>
                    <p>Task compatibility is derived from server-owned capability descriptors. Cold/configured models are not presented as immediately executable.</p>
                </div>
                <span class="ds-status" data-status="${records.length ? 'ready' : 'unavailable'}">${escapeHtml(sourceStatus)}</span>
            </div>
            <div class="capability-endpoint-grid">
                ${endpointCard('Chat', '/v1/chat/completions', 'chat', chat, 'Text conversation through the OpenAI-compatible chat surface.')}
                ${endpointCard('Vision language', '/v1/chat/completions', 'vision_language', vision, 'Text + image requests through the chat surface when image input is explicitly supported.')}
                ${endpointCard('Structured generation', '/v1/chat/completions', 'structured_generation', structured, 'JSON-constrained generation through response_format when structured output is declared.')}
                ${endpointCard('Transcription', '/v1/audio/transcriptions', 'transcription', transcription, 'Audio → text through the first-class multipart transcription endpoint.')}
            </div>
            <div class="ds-card capability-model-matrix">
                <div class="capability-model-matrix__header">
                    <div>
                        <span class="capability-eyebrow">Runtime compatibility</span>
                        <h3>Configured and resident models</h3>
                    </div>
                    <div class="control-plane-actions">
                        <a class="ds-button ds-link" href="/docs" target="_blank" rel="noreferrer">Open Swagger</a>
                        <a class="ds-button ds-link" href="/example" target="_blank" rel="noreferrer">Examples</a>
                    </div>
                </div>
                <div class="capability-table-wrap">
                    <table class="ds-table capability-table">
                        <thead><tr><th>Model</th><th>Residency</th><th>Tasks</th><th>Inputs</th><th>Features</th></tr></thead>
                        <tbody>${records.length ? records.map(modelRow).join('') : '<tr><td colspan="5">Capability metadata unavailable.</td></tr>'}</tbody>
                    </table>
                </div>
            </div>`;
    }

    function endpointCard(title, path, task, supported, detail) {
        const ready = supported.length > 0;
        const names = supported.map((record) => record.modelId || record.key).join(', ');
        return `
            <article class="ds-card capability-endpoint-card">
                <div class="capability-endpoint-card__top">
                    <div>
                        <span class="capability-eyebrow">${escapeHtml(task)}</span>
                        <h3>${escapeHtml(title)}</h3>
                    </div>
                    <span class="ds-status" data-status="${ready ? 'ready' : 'unavailable'}">${ready ? `${supported.length} resident` : 'Unavailable'}</span>
                </div>
                <code>${escapeHtml(path)}</code>
                <p>${escapeHtml(detail)}</p>
                <small>${ready ? `Available now: ${escapeHtml(names)}` : 'No resident runtime currently declares this task.'}</small>
            </article>`;
    }

    function modelRow(record) {
        const caps = record.capabilities;
        return `
            <tr>
                <td><strong>${escapeHtml(record.modelId || record.key)}</strong><br><code>${escapeHtml(record.key || '')}</code></td>
                <td><span class="ds-status" data-status="${record.resident ? 'resident' : 'cold'}">${record.resident ? 'Resident' : 'Cold'}</span></td>
                <td>${escapeHtml(caps?.tasks.join(', ') || 'Unavailable')}</td>
                <td>${escapeHtml(caps?.inputs.join(', ') || 'Unavailable')}</td>
                <td>${escapeHtml(caps?.features.join(', ') || 'Unavailable')}</td>
            </tr>`;
    }

    function ensurePlaygroundCapabilitySurface() {
        const panel = document.getElementById('chat-tab');
        if (!panel) return null;
        let surface = panel.querySelector('[data-playground-capabilities]');
        if (surface) return surface;
        surface = document.createElement('section');
        surface.dataset.playgroundCapabilities = 'true';
        surface.className = 'ds-card playground-capability-surface';
        panel.prepend(surface);
        return surface;
    }

    function selectedRecord() {
        const select = document.getElementById('model-select');
        if (!select) return null;
        const value = String(select.value || '').trim();
        if (value && recordByIdentity.has(value)) return recordByIdentity.get(value);
        const optionText = String(select.selectedOptions?.[0]?.textContent || '').trim();
        return records.find((record) => optionText.includes(record.modelId) || optionText.includes(record.key)) || null;
    }

    function applyPlaygroundCapabilities() {
        const surface = ensurePlaygroundCapabilitySurface();
        if (!surface) return;
        const record = selectedRecord();
        const caps = record?.capabilities || null;

        if (!record || !caps) {
            surface.innerHTML = `
                <div class="playground-capability-header">
                    <div><span class="capability-eyebrow">Capability contract</span><strong>Metadata unavailable for the selected model</strong></div>
                    <span class="ds-status" data-status="unavailable">Unavailable</span>
                </div>
                <p>Legacy Playground behavior is preserved; controls are not disabled from inference or guessed metadata.</p>`;
            setCapabilityControlledState(null);
            return;
        }

        const tasks = new Set(caps.tasks);
        const chatSupported = ['chat', 'vision_language', 'structured_generation'].some((task) => tasks.has(task));
        const imageSupported = caps.inputs.includes('image') && tasks.has('vision_language');
        const structuredSupported = tasks.has('structured_generation') && caps.features.includes('structured_output');
        const thinkingSupported = caps.features.includes('thinking');
        const transcriptionSupported = tasks.has('transcription') && caps.inputs.includes('audio');

        surface.innerHTML = `
            <div class="playground-capability-header">
                <div>
                    <span class="capability-eyebrow">Selected runtime</span>
                    <strong>${escapeHtml(record.modelId || record.key)}</strong>
                </div>
                <span class="ds-status" data-status="${record.resident ? 'resident' : 'cold'}">${record.resident ? 'Resident' : 'Cold'}</span>
            </div>
            <div class="playground-capability-chips">
                ${caps.tasks.map((task) => `<span class="capability-chip">${escapeHtml(task)}</span>`).join('')}
                ${caps.inputs.map((input) => `<span class="capability-chip capability-chip--muted">input:${escapeHtml(input)}</span>`).join('')}
            </div>
            <p>${chatSupported ? 'Chat composer availability follows this descriptor.' : 'This runtime does not declare a chat-compatible task; the chat composer is disabled.'}</p>
            ${transcriptionSupported ? transcriptionMarkup() : ''}`;

        setCapabilityControlledState({ chatSupported, imageSupported, structuredSupported, thinkingSupported });
        if (transcriptionSupported) bindTranscription(surface, record);
    }

    function setCapabilityControlledState(state) {
        const attach = document.getElementById('attach-image-btn');
        const imageInput = document.getElementById('chat-image-input');
        const removeImage = document.getElementById('remove-image-btn');
        const json = document.getElementById('param-force-json');
        const thinking = document.getElementById('param-enable-thinking');
        const showThinking = document.getElementById('param-show-thinking');
        const textarea = document.getElementById('chat-textarea');
        const send = document.getElementById('send-chat-btn');

        if (state === null) {
            [attach, imageInput, json, thinking, showThinking, textarea, send].forEach((control) => restoreCapabilityControl(control));
            return;
        }

        setButtonVisibility(attach, state.imageSupported);
        setSimpleAvailability(imageInput, state.imageSupported);
        if (!state.imageSupported && removeImage) removeImage.click();
        setCheckboxAvailability(json, state.structuredSupported);
        setCheckboxAvailability(thinking, state.thinkingSupported);
        setCheckboxAvailability(showThinking, state.thinkingSupported);
        setComposerAvailability(textarea, send, state.chatSupported);
    }

    function markManaged(control) {
        if (!control) return;
        if (control.dataset.capabilityManaged !== 'true') {
            control.dataset.capabilityManaged = 'true';
            control.dataset.capabilityOriginalDisabled = control.disabled ? 'true' : 'false';
            if (control.id === 'attach-image-btn') {
                control.dataset.capabilityOriginalDisplay = control.style.display || '';
            }
            if (control.id === 'chat-textarea') {
                control.dataset.capabilityOriginalPlaceholder = control.placeholder || '';
            }
        }
    }

    function markGroupManaged(group) {
        if (!group || group.dataset.capabilityManaged === 'true') return;
        group.dataset.capabilityManaged = 'true';
        group.dataset.capabilityOriginalHidden = group.hidden ? 'true' : 'false';
    }

    function setButtonVisibility(button, supported) {
        if (!button) return;
        markManaged(button);
        button.style.display = supported ? 'inline-flex' : 'none';
        button.disabled = !supported;
    }

    function setSimpleAvailability(control, supported) {
        if (!control) return;
        markManaged(control);
        control.disabled = !supported;
    }

    function setCheckboxAvailability(control, supported) {
        if (!control) return;
        markManaged(control);
        control.disabled = !supported;
        const group = control.closest('.checkbox-group') || control.parentElement;
        markGroupManaged(group);
        if (group) group.hidden = !supported;
        if (!supported && control.checked) {
            control.checked = false;
            control.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    function setComposerAvailability(textarea, send, supported) {
        [textarea, send].forEach((control) => {
            if (!control) return;
            markManaged(control);
            control.disabled = !supported;
        });
        if (textarea) textarea.placeholder = supported
            ? (textarea.dataset.capabilityOriginalPlaceholder || 'Scrivi un messaggio…')
            : 'Il runtime selezionato non espone un task chat compatibile.';
    }

    function restoreCapabilityControl(control) {
        if (!control || control.dataset.capabilityManaged !== 'true') return;
        control.disabled = control.dataset.capabilityOriginalDisabled === 'true';
        if (control.id === 'attach-image-btn') {
            control.style.display = control.dataset.capabilityOriginalDisplay || '';
        }
        if (control.id === 'chat-textarea') {
            control.placeholder = control.dataset.capabilityOriginalPlaceholder || '';
        }
        const group = control.closest?.('.checkbox-group') || null;
        if (group?.dataset.capabilityManaged === 'true') {
            group.hidden = group.dataset.capabilityOriginalHidden === 'true';
            delete group.dataset.capabilityManaged;
            delete group.dataset.capabilityOriginalHidden;
        }
        delete control.dataset.capabilityManaged;
        delete control.dataset.capabilityOriginalDisabled;
        delete control.dataset.capabilityOriginalDisplay;
        delete control.dataset.capabilityOriginalPlaceholder;
    }

    function transcriptionMarkup() {
        return `
            <div class="playground-transcription" data-playground-transcription>
                <div class="playground-transcription__heading">
                    <div><span class="capability-eyebrow">Transcription playground</span><strong>Audio → text</strong></div>
                    <code>/v1/audio/transcriptions</code>
                </div>
                <div class="playground-transcription__fields">
                    <label class="ds-field"><span>Audio file</span><input type="file" accept="audio/*" data-transcription-file></label>
                    <label class="ds-field"><span>Language (optional)</span><input type="text" placeholder="it, en, es…" data-transcription-language></label>
                </div>
                <button type="button" class="ds-button ds-button--primary" data-transcription-run>Transcribe locally</button>
                <div class="playground-transcription__result" data-transcription-result aria-live="polite">No transcription executed yet.</div>
            </div>`;
    }

    function bindTranscription(surface, record) {
        const host = surface.querySelector('[data-playground-transcription]');
        const fileInput = host?.querySelector('[data-transcription-file]');
        const languageInput = host?.querySelector('[data-transcription-language]');
        const runButton = host?.querySelector('[data-transcription-run]');
        const result = host?.querySelector('[data-transcription-result]');
        if (!runButton || !fileInput || !result) return;

        runButton.addEventListener('click', async () => {
            const file = fileInput.files?.[0];
            if (!file) {
                result.textContent = 'Choose an audio file before transcribing.';
                return;
            }
            if (file.size > MAX_AUDIO_BYTES) {
                result.textContent = 'Audio file exceeds the 100 MiB server upload limit.';
                return;
            }
            const body = new FormData();
            body.append('file', file);
            body.append('model', record.key || record.modelId);
            const language = String(languageInput?.value || '').trim();
            if (language) body.append('language', language);

            runButton.disabled = true;
            result.textContent = 'Transcribing locally…';
            try {
                const payload = await fetchJson('/v1/audio/transcriptions', { method: 'POST', body });
                result.textContent = typeof payload?.text === 'string' && payload.text
                    ? payload.text
                    : 'Transcription completed but no text was returned.';
            } catch (error) {
                result.textContent = `Transcription failed: ${error?.message || 'unknown error'}`;
            } finally {
                runButton.disabled = false;
            }
        });
    }

    async function refresh() {
        const [residentResult, catalogResult] = await Promise.allSettled([
            fetchJson('/v1/models'),
            fetchJson('/api/v1/models/registry'),
        ]);
        const residentPayload = residentResult.status === 'fulfilled' ? residentResult.value : null;
        const catalogPayload = catalogResult.status === 'fulfilled' ? catalogResult.value : null;
        buildRecords(residentPayload, catalogPayload);
        renderEndpoints(catalogResult.status === 'fulfilled');
        applyPlaygroundCapabilities();
    }

    function bindModelSelection() {
        const select = document.getElementById('model-select');
        if (!select || select.dataset.capabilityListener === 'true') return;
        select.dataset.capabilityListener = 'true';
        select.addEventListener('change', () => setTimeout(applyPlaygroundCapabilities, 0));
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function boot(attempt = 0) {
        const endpoints = document.getElementById('endpoints-tab');
        const playground = document.getElementById('chat-tab');
        if (!endpoints || !playground) {
            if (attempt < 30) setTimeout(() => boot(attempt + 1), 50);
            return;
        }
        bindModelSelection();
        refresh();
        if (timer) clearInterval(timer);
        timer = setInterval(() => {
            bindModelSelection();
            refresh();
        }, REFRESH_MS);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => boot(), { once: true });
    } else {
        boot();
    }
})();
