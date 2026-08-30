(() => {
    const REFRESH_MS = 10000;
    const MAX_AUDIO_BYTES = 100 * 1024 * 1024;
    const TASKS = [
        { id: 'chat', descriptor: 'chat', label: 'Chat', hint: 'Text conversation' },
        { id: 'structured-output', descriptor: 'structured_generation', label: 'Structured output', hint: 'JSON and schema-constrained generation' },
        { id: 'vision-language', descriptor: 'vision_language', label: 'Vision-language', hint: 'Text + image understanding' },
        { id: 'transcription', descriptor: 'transcription', label: 'Transcription', hint: 'Audio → text' },
    ];
    let timer = null;
    let records = [];
    let recordByIdentity = new Map();
    let activeTask = 'chat';
    let capabilitySourcesAvailable = false;
    let activeRecordKey = null;

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
                downloaded: item.downloaded ?? previous.downloaded ?? null,
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

    function supportsTask(record, taskId) {
        const caps = record?.capabilities;
        if (!caps) return false;
        if (taskId === 'chat') return caps.tasks.includes('chat');
        if (taskId === 'structured-output') {
            return caps.tasks.includes('structured_generation') && caps.features.includes('structured_output');
        }
        if (taskId === 'vision-language') {
            return caps.tasks.includes('vision_language') && caps.inputs.includes('image');
        }
        if (taskId === 'transcription') {
            return caps.tasks.includes('transcription') && caps.inputs.includes('audio');
        }
        return false;
    }

    function endpointSupport(task) {
        return records.filter((record) => record.resident && record.capabilities?.tasks.includes(task));
    }

    function renderEndpoints(catalogAvailable) {
        const panel = document.getElementById('endpoints-tab');
        if (!panel) return;
        const sourceStatus = catalogAvailable ? 'Catalog + resident capability sources' : 'Resident capability source';

        panel.innerHTML = `
            <div class="control-plane-header">
                <div>
                    <span class="capability-eyebrow">Application contracts</span>
                    <h2>Endpoints</h2>
                    <p>Start from the task and integration contract. Compatibility remains derived from server-owned capability descriptors.</p>
                </div>
                <span class="ds-status" data-status="${records.length ? 'ready' : 'unavailable'}">${escapeHtml(sourceStatus)}</span>
            </div>
            <div class="capability-endpoint-grid">
                ${endpointCard('Chat', '/v1/chat/completions', 'chat', 'chat', 'Text conversation through the OpenAI-compatible chat surface.')}
                ${endpointCard('Vision language', '/v1/chat/completions', 'vision_language', 'vision-language', 'Text + image requests when image input is explicitly supported.')}
                ${endpointCard('Structured generation', '/v1/chat/completions', 'structured_generation', 'structured-output', 'JSON-constrained generation when structured output is declared.')}
                ${endpointCard('Transcription', '/v1/audio/transcriptions', 'transcription', 'transcription', 'Audio → text through the first-class multipart endpoint.')}
            </div>
            <div class="ds-card capability-model-matrix">
                <div class="capability-model-matrix__header">
                    <div>
                        <span class="capability-eyebrow">Compatibility detail</span>
                        <h3>Configured and resident models</h3>
                    </div>
                    <div class="control-plane-actions">
                        <a class="ds-button ds-link" href="/docs" target="_blank" rel="noreferrer">Open Swagger</a>
                        <a class="ds-button ds-link" href="/example" target="_blank" rel="noreferrer">Examples</a>
                    </div>
                </div>
                <div class="capability-table-wrap">
                    <table class="ds-table capability-table">
                        <thead><tr><th>Model</th><th>Residency</th><th>Tasks</th><th>Inputs</th><th>Outputs</th><th>Features</th></tr></thead>
                        <tbody>${records.length ? records.map(modelRow).join('') : '<tr><td colspan="6">Capability metadata unavailable.</td></tr>'}</tbody>
                    </table>
                </div>
            </div>`;
        bindEndpointTry(panel);
    }

    function endpointCard(title, path, descriptorTask, playgroundTask, detail) {
        const supported = endpointSupport(descriptorTask);
        const ready = supported.length > 0;
        const names = supported.map((record) => record.modelId || record.key).join(', ');
        return `
            <article class="ds-card capability-endpoint-card">
                <div class="capability-endpoint-card__top">
                    <div>
                        <span class="capability-eyebrow">${escapeHtml(descriptorTask)}</span>
                        <h3>${escapeHtml(title)}</h3>
                    </div>
                    <span class="ds-status" data-status="${ready ? 'ready' : 'unavailable'}">${ready ? `${supported.length} resident` : 'Unavailable'}</span>
                </div>
                <code>${escapeHtml(path)}</code>
                <p>${escapeHtml(detail)}</p>
                <small>${ready ? `Available now: ${escapeHtml(names)}` : 'No resident runtime currently declares this task.'}</small>
                <div class="capability-endpoint-actions">
                    <button type="button" class="ds-button" data-variant="primary" data-try-task="${escapeHtml(playgroundTask)}"${ready ? '' : ' disabled'}>Try in Playground</button>
                    <a class="ds-button ds-link" href="/docs" target="_blank" rel="noreferrer">API schema</a>
                </div>
            </article>`;
    }

    function bindEndpointTry(panel) {
        panel.querySelectorAll('[data-try-task]').forEach((button) => {
            button.addEventListener('click', () => {
                activeTask = button.dataset.tryTask;
                document.querySelector('.control-plane-tablist .nav-item[data-tab="chat-tab"]')?.click();
                window.setTimeout(() => applyPlaygroundTaskModel(), 0);
            });
        });
    }

    function modelRow(record) {
        const caps = record.capabilities;
        return `
            <tr>
                <td><strong>${escapeHtml(record.modelId || record.key)}</strong><br><code>${escapeHtml(record.key || '')}</code></td>
                <td><span class="ds-status" data-status="${record.resident ? 'resident' : 'cold'}">${record.resident ? 'Resident' : 'Cold'}</span></td>
                <td>${escapeHtml(caps?.tasks.join(', ') || 'Unavailable')}</td>
                <td>${escapeHtml(caps?.inputs.join(', ') || 'Unavailable')}</td>
                <td>${escapeHtml(caps?.outputs.join(', ') || 'Unavailable')}</td>
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
        surface.className = 'playground-task-surface';
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

    function compatibleRecords(taskId) {
        return records.filter((record) => supportsTask(record, taskId));
    }

    function preferredRecord(taskId) {
        const current = selectedRecord();
        if (current && current.resident && supportsTask(current, taskId)) return current;
        if (activeRecordKey) {
            const active = recordByIdentity.get(activeRecordKey);
            if (active?.resident && supportsTask(active, taskId)) return active;
        }
        return compatibleRecords(taskId).find((record) => record.resident) || null;
    }

    function applyPlaygroundTaskModel() {
        const surface = ensurePlaygroundCapabilitySurface();
        if (!surface) return;

        if (!capabilitySourcesAvailable || !records.some((record) => record.capabilities)) {
            surface.innerHTML = `
                <div class="playground-capability-header">
                    <div><span class="capability-eyebrow">Task execution</span><strong>Capability metadata unavailable</strong></div>
                    <span class="ds-status" data-status="unavailable">Unavailable</span>
                </div>
                <p>Legacy Playground behavior is preserved; controls are not disabled from inference or guessed metadata.</p>`;
            setCapabilityControlledState(null);
            setLegacyChatLayoutVisibility(true);
            setLegacyModelSelectVisibility(true);
            return;
        }

        const available = compatibleRecords(activeTask);
        const residents = available.filter((record) => record.resident);
        const cold = available.filter((record) => !record.resident);
        const selected = preferredRecord(activeTask);
        if (selected) {
            activeRecordKey = selected.key;
            syncLegacyModelSelect(selected);
        }

        surface.innerHTML = `
            <div class="control-plane-header playground-task-surface__header">
                <div>
                    <span class="capability-eyebrow">Task execution</span>
                    <h2>Playground</h2>
                    <p>Choose the task first, then use a compatible local runtime. Advanced model/backend detail stays secondary.</p>
                </div>
                <span class="ds-status" data-status="${residents.length ? 'ready' : (cold.length ? 'cold' : 'unavailable')}">${residents.length ? 'Ready' : (cold.length ? 'Load required' : 'Unavailable')}</span>
            </div>

            <div class="playground-task-selector" role="tablist" aria-label="Playground task">
                ${TASKS.map(taskButton).join('')}
            </div>

            <div class="playground-task-grid">
                <section class="ds-card playground-model-chooser" aria-labelledby="playground-model-heading">
                    <div class="playground-task-section-header">
                        <div>
                            <span class="capability-eyebrow">Step 1</span>
                            <h3 id="playground-model-heading">Compatible runtime</h3>
                        </div>
                        <small>${residents.length} resident · ${cold.length} cold</small>
                    </div>
                    ${residents.length ? `<div class="playground-model-list">${residents.map((record) => runtimeChoice(record, selected)).join('')}</div>` : '<div class="ds-empty">No compatible resident runtime.</div>'}
                    ${cold.length ? `<details class="playground-cold-models"><summary>${cold.length} compatible cold model${cold.length === 1 ? '' : 's'}</summary><div class="playground-model-list">${cold.map((record) => runtimeChoice(record, selected)).join('')}</div></details>` : ''}
                    ${!available.length ? '<div class="ds-empty">No configured model declares this task. Unsupported combinations fail closed.</div>' : ''}
                    <div class="playground-task-feedback" data-task-action-status aria-live="polite"></div>
                </section>

                <section class="ds-card playground-task-guidance">
                    <span class="capability-eyebrow">Step 2</span>
                    <h3>${escapeHtml(taskDefinition(activeTask)?.label || activeTask)}</h3>
                    <p>${escapeHtml(taskGuidance(activeTask, selected))}</p>
                    ${activeTask === 'transcription' ? transcriptionMarkup(selected) : composerGuidance(activeTask, selected)}
                </section>
            </div>`;

        bindTaskSurface(surface);
        setLegacyModelSelectVisibility(false);

        if (activeTask === 'transcription') {
            setCapabilityControlledState({ chatSupported: false, imageSupported: false, structuredSupported: false, thinkingSupported: false, task: activeTask });
            setLegacyChatLayoutVisibility(false);
            if (selected) bindTranscription(surface, selected);
        } else {
            setLegacyChatLayoutVisibility(true);
            const caps = selected?.capabilities || null;
            setCapabilityControlledState({
                chatSupported: Boolean(selected && caps),
                imageSupported: Boolean(selected && activeTask === 'vision-language'),
                structuredSupported: Boolean(selected && activeTask === 'structured-output'),
                thinkingSupported: Boolean(selected && caps?.features.includes('thinking')),
                task: activeTask,
            });
        }
    }

    function taskButton(task) {
        const active = task.id === activeTask;
        return `
            <button type="button"
                class="playground-task-selector__item"
                role="tab"
                aria-selected="${active ? 'true' : 'false'}"
                tabindex="${active ? '0' : '-1'}"
                data-playground-task="${escapeHtml(task.id)}">
                <strong>${escapeHtml(task.label)}</strong>
                <span>${escapeHtml(task.hint)}</span>
            </button>`;
    }

    function runtimeChoice(record, selected) {
        const isSelected = selected?.key === record.key;
        return `
            <article class="playground-model-choice ${isSelected ? 'playground-model-choice--selected' : ''}">
                <button type="button" class="playground-model-choice__select" data-select-task-model="${escapeHtml(record.key)}"${record.resident ? '' : ' disabled'}>
                    <span>
                        <strong>${escapeHtml(record.modelId || record.key)}</strong>
                        <small>${escapeHtml(record.backend || 'backend unavailable')}</small>
                    </span>
                    <span class="ds-status" data-status="${record.resident ? 'resident' : 'cold'}">${record.resident ? (isSelected ? 'Selected · Resident' : 'Resident') : 'Cold'}</span>
                </button>
                ${record.resident ? '' : `<button type="button" class="ds-button" data-variant="primary" data-load-and-use="${escapeHtml(record.key)}"${record.downloaded === false ? ' disabled title="Artifact is not available locally"' : ''}>Load & use</button>`}
            </article>`;
    }

    function composerGuidance(taskId, selected) {
        if (!selected) return '<div class="ds-empty">Load or select a compatible resident runtime to enable this task.</div>';
        if (taskId === 'structured-output') {
            return '<div class="playground-task-mode-note"><strong>Structured mode active.</strong><span>The existing composer will send a JSON response format; the task choice owns this mode.</span></div>';
        }
        if (taskId === 'vision-language') {
            return '<div class="playground-task-mode-note"><strong>Vision mode active.</strong><span>Attach a local image in the composer below, then enter the text instruction.</span></div>';
        }
        return '<div class="playground-task-mode-note"><strong>Chat mode active.</strong><span>Use the composer below. Only controls supported by the selected runtime remain available.</span></div>';
    }

    function taskGuidance(taskId, selected) {
        if (!selected) return 'A compatible resident runtime is required before this task can execute.';
        if (taskId === 'structured-output') return 'The task selector, rather than a hidden model heuristic, enables structured output for this run.';
        if (taskId === 'vision-language') return 'Image input is enabled because the selected runtime declares the vision-language task and image modality.';
        if (taskId === 'transcription') return 'Audio stays on the local endpoint; remote URLs are not introduced by this surface.';
        return 'The chat composer is ready with the selected resident runtime.';
    }

    function bindTaskSurface(surface) {
        surface.querySelectorAll('[data-playground-task]').forEach((button) => {
            button.addEventListener('click', () => {
                activeTask = button.dataset.playgroundTask;
                activeRecordKey = null;
                applyPlaygroundTaskModel();
            });
            button.addEventListener('keydown', handleTaskKeydown);
        });

        surface.querySelectorAll('[data-select-task-model]').forEach((button) => {
            button.addEventListener('click', () => {
                const record = recordByIdentity.get(button.dataset.selectTaskModel);
                if (!record?.resident) return;
                activeRecordKey = record.key;
                syncLegacyModelSelect(record);
                applyPlaygroundTaskModel();
            });
        });

        surface.querySelectorAll('[data-load-and-use]').forEach((button) => {
            button.addEventListener('click', async () => {
                const status = surface.querySelector('[data-task-action-status]');
                const key = button.dataset.loadAndUse;
                button.disabled = true;
                if (status) status.textContent = `Loading ${key}…`;
                try {
                    await fetchJson('/api/v1/models/load', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ model: key }),
                    });
                    activeRecordKey = key;
                    if (status) status.textContent = `${key} is resident.`;
                    await refreshCapabilitySources();
                } catch (error) {
                    button.disabled = false;
                    if (status) status.textContent = `Load failed: ${error?.message || 'unknown error'} Review Models & Runtimes for resource admission and recovery options.`;
                }
            });
        });
    }

    function handleTaskKeydown(event) {
        const surface = event.currentTarget.closest('[data-playground-capabilities]');
        const buttons = [...(surface?.querySelectorAll('[data-playground-task]') || [])];
        const index = buttons.indexOf(event.currentTarget);
        if (index < 0) return;
        let next = null;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % buttons.length;
        if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + buttons.length) % buttons.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = buttons.length - 1;
        if (next === null) return;
        event.preventDefault();
        buttons[next].click();
        window.setTimeout(() => {
            const refreshed = ensurePlaygroundCapabilitySurface();
            [...(refreshed?.querySelectorAll('[data-playground-task]') || [])][next]?.focus();
        }, 0);
    }

    function syncLegacyModelSelect(record) {
        const select = document.getElementById('model-select');
        if (!select || !record) return false;
        const aliases = new Set([record.key, record.modelId, ...(record.aliases || [])].filter(Boolean).map(String));
        const option = [...select.options].find((item) => aliases.has(String(item.value)))
            || [...select.options].find((item) => [...aliases].some((alias) => String(item.textContent || '').includes(alias)));
        if (!option) return false;
        if (select.value !== option.value) {
            select.value = option.value;
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }
        return true;
    }

    function setLegacyModelSelectVisibility(visible) {
        const select = document.getElementById('model-select');
        const group = select?.closest('.form-group') || select?.parentElement;
        if (!group) return;
        if (group.dataset.capabilityModelSelectManaged !== 'true') {
            group.dataset.capabilityModelSelectManaged = 'true';
            group.dataset.capabilityOriginalDisplay = group.style.display || '';
        }
        group.style.display = visible ? (group.dataset.capabilityOriginalDisplay || '') : 'none';
    }

    function setLegacyChatLayoutVisibility(visible) {
        const panel = document.getElementById('chat-tab');
        const layout = panel?.querySelector('.chat-layout');
        if (!layout) return;
        if (layout.dataset.capabilityManaged !== 'true') {
            layout.dataset.capabilityManaged = 'true';
            layout.dataset.capabilityOriginalDisplay = layout.style.display || '';
        }
        layout.style.display = visible ? (layout.dataset.capabilityOriginalDisplay || '') : 'none';
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
        if (!state.imageSupported && removeImage && imageInput?.files?.length) removeImage.click();

        if (json) {
            markManaged(json);
            const group = json.closest('.checkbox-group') || json.parentElement;
            markGroupManaged(group);
            if (state.structuredSupported) {
                json.checked = true;
                json.disabled = true;
                if (group) group.hidden = true;
                json.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
                if (json.checked) {
                    json.checked = false;
                    json.dispatchEvent(new Event('change', { bubbles: true }));
                }
                json.disabled = true;
                if (group) group.hidden = true;
            }
        }

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
            ? (textarea.dataset.capabilityOriginalPlaceholder || 'Write a message…')
            : 'Select or load a compatible resident runtime for this task.';
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

    function transcriptionMarkup(record) {
        if (!record) return '<div class="ds-empty">Load or select a compatible transcription runtime to continue.</div>';
        return `
            <div class="playground-transcription" data-playground-transcription>
                <div class="playground-transcription__heading">
                    <div><span class="capability-eyebrow">Local audio input</span><strong>${escapeHtml(record.modelId || record.key)}</strong></div>
                    <code>/v1/audio/transcriptions</code>
                </div>
                <div class="playground-transcription__fields">
                    <label class="ds-field"><span>Audio file</span><input type="file" accept="audio/*" data-transcription-file></label>
                    <label class="ds-field"><span>Language (optional)</span><input type="text" placeholder="it, en, es…" data-transcription-language></label>
                </div>
                <button type="button" class="ds-button" data-variant="primary" data-transcription-run>Transcribe locally</button>
                <p class="playground-privacy-note">Remote URLs are not accepted by this task surface. The file is submitted to the local transcription endpoint.</p>
                <div class="playground-transcription__result" data-transcription-result aria-live="polite">No transcription executed yet.</div>
            </div>`;
    }

    function bindTranscription(surface, record) {
        const host = surface.querySelector('[data-playground-transcription]');
        const fileInput = host?.querySelector('[data-transcription-file]');
        const languageInput = host?.querySelector('[data-transcription-language]');
        const button = host?.querySelector('[data-transcription-run]');
        const result = host?.querySelector('[data-transcription-result]');
        if (!host || !fileInput || !button || !result) return;

        button.addEventListener('click', async () => {
            const file = fileInput.files?.[0] || null;
            if (!file) {
                result.textContent = 'Choose an audio file before starting transcription.';
                return;
            }
            if (file.size > MAX_AUDIO_BYTES) {
                result.textContent = 'Audio file exceeds the 100 MB local upload limit.';
                return;
            }
            button.disabled = true;
            result.textContent = 'Transcribing locally…';
            const body = new FormData();
            body.append('file', file);
            body.append('model', record.key || record.modelId);
            const language = String(languageInput?.value || '').trim();
            if (language) body.append('language', language);
            try {
                const response = await fetch('/v1/audio/transcriptions', { method: 'POST', body });
                let payload = null;
                try { payload = await response.json(); } catch (_) { payload = null; }
                if (!response.ok) {
                    const detail = payload?.detail?.message || payload?.detail || `Transcription returned ${response.status}`;
                    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
                }
                result.textContent = typeof payload?.text === 'string'
                    ? payload.text
                    : 'Transcription completed; response text was unavailable.';
            } catch (error) {
                result.textContent = `Transcription failed: ${error?.message || 'unknown error'}`;
            } finally {
                button.disabled = false;
            }
        });
    }

    function taskDefinition(taskId) {
        return TASKS.find((item) => item.id === taskId) || null;
    }

    async function refreshCapabilitySources() {
        const [residentResult, catalogResult] = await Promise.allSettled([
            fetchJson('/v1/models'),
            fetchJson('/api/v1/models/registry'),
        ]);
        const residentPayload = residentResult.status === 'fulfilled' ? residentResult.value : null;
        const catalogPayload = catalogResult.status === 'fulfilled' ? catalogResult.value : null;
        capabilitySourcesAvailable = residentResult.status === 'fulfilled' || catalogResult.status === 'fulfilled';
        buildRecords(residentPayload, catalogPayload);
        renderEndpoints(catalogResult.status === 'fulfilled');
        applyPlaygroundTaskModel();
    }

    function bindModelSelect() {
        const select = document.getElementById('model-select');
        if (!select || select.dataset.capabilityBound === 'true') return;
        select.dataset.capabilityBound = 'true';
        select.addEventListener('change', () => {
            const current = selectedRecord();
            if (current?.resident && supportsTask(current, activeTask)) activeRecordKey = current.key;
            applyPlaygroundTaskModel();
        });
    }

    async function refresh() {
        try {
            await refreshCapabilitySources();
        } catch (_) {
            capabilitySourcesAvailable = false;
            applyPlaygroundTaskModel();
        }
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
        if (!document.getElementById('chat-tab') || !document.getElementById('endpoints-tab')) {
            if (attempt < 30) setTimeout(() => boot(attempt + 1), 50);
            return;
        }
        ensurePlaygroundCapabilitySurface();
        bindModelSelect();
        refresh();
        if (timer) clearInterval(timer);
        timer = setInterval(refresh, REFRESH_MS);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => boot(), { once: true });
    } else {
        boot();
    }
})();
