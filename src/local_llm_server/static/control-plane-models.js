(() => {
    const REFRESH_MS = 10000;
    let timer = null;
    let refreshing = false;

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

    function ensureSurface() {
        const panel = document.getElementById('registry-tab');
        if (!panel) return null;
        let surface = panel.querySelector('[data-control-plane-models]');
        if (surface) return surface;
        surface = document.createElement('section');
        surface.dataset.controlPlaneModels = 'true';
        surface.className = 'control-plane-models';
        panel.prepend(surface);
        return surface;
    }

    async function refresh() {
        if (refreshing) return;
        refreshing = true;
        const surface = ensureSurface();
        if (!surface) {
            refreshing = false;
            return;
        }

        try {
            const [residentResult, statusResult, catalogResult, resourceResult, evidenceResult, residencyResult] = await Promise.allSettled([
                fetchJson('/v1/models'),
                fetchJson('/status'),
                fetchJson('/api/v1/models/registry'),
                fetchJson('/api/v1/resources'),
                fetchJson('/api/v1/evidence'),
                fetchJson('/api/v1/residency'),
            ]);

            const residentPayload = residentResult.status === 'fulfilled' ? residentResult.value : null;
            const statusPayload = statusResult.status === 'fulfilled' ? statusResult.value : null;
            const catalogPayload = catalogResult.status === 'fulfilled' ? catalogResult.value : null;
            const resourcePayload = resourceResult.status === 'fulfilled' ? resourceResult.value : null;
            const evidencePayload = evidenceResult.status === 'fulfilled' ? evidenceResult.value : null;
            const residencyPayload = residencyResult.status === 'fulfilled' ? residencyResult.value : null;
            const residents = Array.isArray(residentPayload?.data) ? residentPayload.data : [];
            const runtimeStatus = statusPayload?.models && typeof statusPayload.models === 'object'
                ? statusPayload.models
                : {};
            const catalog = Array.isArray(catalogPayload?.models) ? catalogPayload.models : null;

            const residentByKey = new Map();
            residents.forEach((model) => {
                if (model?.key) residentByKey.set(String(model.key), model);
                if (model?.id) residentByKey.set(String(model.id), model);
            });

            const residencyByKey = new Map();
            if (Array.isArray(residencyPayload?.runtimes)) {
                residencyPayload.runtimes.forEach((runtime) => {
                    if (runtime?.key) residencyByKey.set(String(runtime.key), runtime);
                    if (runtime?.model) residencyByKey.set(String(runtime.model), runtime);
                });
            }

            const rows = catalog
                ? catalog.map((model) => buildRow(model, residentByKey, runtimeStatus, statusPayload?.default_model, residencyByKey, Boolean(residencyPayload)))
                : residents.map((model) => buildRow(model, residentByKey, runtimeStatus, statusPayload?.default_model, residencyByKey, Boolean(residencyPayload)));

            surface.innerHTML = `
                <div class="control-plane-header">
                    <div>
                        <h2>Models & Runtimes</h2>
                        <p>Configured identity, residency, capability, resource admission and runtime evidence from current server sources.</p>
                    </div>
                    ${statusBadge(catalog ? 'Catalog connected' : 'Resident view only', catalog ? 'ready' : 'unavailable')}
                </div>
                ${catalog ? '' : '<div class="ds-empty control-plane-models__notice">Configured catalog unavailable. The admin API may be disabled; only resident runtimes are shown.</div>'}
                <div class="ds-card control-plane-models__table-wrap">
                    <table class="ds-table control-plane-models__table">
                        <thead>
                            <tr>
                                <th>Model</th>
                                <th>Residency</th>
                                <th>Route</th>
                                <th>Backend</th>
                                <th>Runtime</th>
                                <th>Capabilities</th>
                                <th>Residency policy</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows.length ? rows.join('') : '<tr><td colspan="7">Unavailable — no model source returned data.</td></tr>'}
                        </tbody>
                    </table>
                </div>
                <div class="control-plane-grid control-plane-grid--two control-plane-models__details">
                    ${resourceCard(resourcePayload, resourceResult.status === 'fulfilled')}
                    ${fingerprintCard(evidencePayload, evidenceResult.status === 'fulfilled')}
                </div>
                <div class="ds-empty" data-model-action-status aria-live="polite">
                    ${residencyPayload ? 'Pinning controls affect automatic-eviction eligibility only; manual lifecycle controls remain explicit.' : 'Residency policy source unavailable; pin/unpin controls are disabled.'}
                </div>
                <div class="control-plane-actions">
                    <button type="button" class="ds-button" data-scroll-legacy-model-controls>Open lifecycle controls</button>
                </div>`;

            surface.querySelector('[data-scroll-legacy-model-controls]')?.addEventListener('click', () => {
                const legacy = [...surface.parentElement.children].find((node) => node !== surface && node.querySelector?.('#models-list-container'));
                (legacy || document.getElementById('models-list-container'))?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });

            surface.querySelectorAll('[data-pin-model]').forEach((button) => {
                button.addEventListener('click', async () => {
                    const statusHost = surface.querySelector('[data-model-action-status]');
                    button.disabled = true;
                    if (statusHost) statusHost.textContent = `${button.dataset.pinNext === 'true' ? 'Pinning' : 'Unpinning'} ${button.dataset.pinModel}…`;
                    try {
                        await fetchJson('/api/v1/residency/pin', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                model: button.dataset.pinModel,
                                pinned: button.dataset.pinNext === 'true',
                            }),
                        });
                        await refreshAfterAction();
                    } catch (error) {
                        button.disabled = false;
                        if (statusHost) statusHost.textContent = `Residency policy update failed: ${error?.message || 'unknown error'}`;
                    }
                });
            });
        } finally {
            refreshing = false;
        }
    }

    async function refreshAfterAction() {
        refreshing = false;
        await refresh();
    }

    function buildRow(model, residentByKey, runtimeStatus, defaultModel, residencyByKey, residencyAvailable) {
        const key = String(model?.key ?? model?.id ?? model?.model_id ?? 'unknown');
        const modelId = String(model?.model_id ?? model?.id ?? key);
        const resident = Boolean(model?.resident) || residentByKey.has(key) || residentByKey.has(modelId);
        const residentRecord = residentByKey.get(key) || residentByKey.get(modelId) || null;
        const status = model?.runtime_status || runtimeStatus[key] || runtimeStatus[residentRecord?.key] || null;
        const isDefault = Boolean(model?.default) || key === defaultModel || residentRecord?.default === true;
        const backend = model?.backend ?? residentRecord?.backend ?? status?.backend ?? null;
        const runtimeState = status?.state ?? (resident ? 'ready' : null);
        const active = Number.isInteger(status?.active_requests) && status.active_requests >= 0
            ? `${status.active_requests} active`
            : null;
        const capabilityText = capabilitySummary(model?.capabilities);
        const residency = residencyByKey.get(key) || residencyByKey.get(modelId) || null;

        return `
            <tr>
                <td><strong>${escapeHtml(modelId)}</strong><br><code>${escapeHtml(key)}</code></td>
                <td>${statusBadge(resident ? 'Resident' : 'Cold', resident ? 'resident' : 'cold')}</td>
                <td>${isDefault ? statusBadge('Default', 'ready') : '—'}</td>
                <td>${escapeHtml(backend ?? 'Unavailable')}</td>
                <td>${escapeHtml(runtimeState ?? 'Unavailable')}${active ? `<br><small>${escapeHtml(active)}</small>` : ''}</td>
                <td>${escapeHtml(capabilityText)}</td>
                <td>${residencyPolicyCell(key, resident, residency, residencyAvailable)}</td>
            </tr>`;
    }

    function residencyPolicyCell(key, resident, residency, residencyAvailable) {
        if (!resident) return '<span class="ds-status" data-status="cold">Cold</span>';
        if (!residencyAvailable || !residency) return 'Unavailable';
        const pinned = residency.pinned === true;
        const evictable = residency.evictable === true;
        const age = finiteNumber(residency.last_used_age_seconds);
        return `
            <div class="control-plane-models__policy-cell">
                ${statusBadge(pinned ? 'Pinned' : (evictable ? 'Evictable' : 'Protected now'), pinned ? 'warning' : (evictable ? 'ready' : 'unavailable'))}
                ${age === null ? '' : `<small>idle age ${escapeHtml(formatDuration(age))}</small>`}
                <button
                    type="button"
                    class="ds-button"
                    data-pin-model="${escapeHtml(key)}"
                    data-pin-next="${pinned ? 'false' : 'true'}"
                >${pinned ? 'Unpin' : 'Pin'}</button>
            </div>`;
    }

    function resourceCard(payload, sourceAvailable) {
        if (!sourceAvailable || !payload) {
            return `
                <article class="ds-card control-plane-card">
                    <h3>Resource admission</h3>
                    <div class="ds-empty control-plane-unavailable">Unavailable — resource policy source did not respond.</div>
                </article>`;
        }
        const enabled = payload.enabled === true;
        return `
            <article class="ds-card control-plane-card">
                <div class="control-plane-card__header">
                    <h3>Resource admission</h3>
                    ${statusBadge(enabled ? 'Configured' : 'Disabled', enabled ? 'ready' : 'unavailable')}
                </div>
                <dl class="evaluation-definition-list">
                    <div><dt>Usable budget</dt><dd>${escapeHtml(formatBytes(payload.usable_budget_bytes))}</dd></div>
                    <div><dt>Committed</dt><dd>${escapeHtml(formatBytes(payload.committed_bytes))}</dd></div>
                    <div><dt>Reserved</dt><dd>${escapeHtml(formatBytes(payload.reserved_bytes))}</dd></div>
                    <div><dt>Remaining</dt><dd>${escapeHtml(formatBytes(payload.remaining_bytes))}</dd></div>
                </dl>
            </article>`;
    }

    function fingerprintCard(payload, sourceAvailable) {
        if (!sourceAvailable || !payload) {
            return `
                <article class="ds-card control-plane-card">
                    <h3>Runtime fingerprint</h3>
                    <div class="ds-empty control-plane-unavailable">Unavailable — runtime evidence source did not respond.</div>
                </article>`;
        }
        const runtimes = Array.isArray(payload.runtimes) ? payload.runtimes : [];
        const rows = runtimes.map((item) => {
            const runtime = item?.runtime || {};
            const identity = item?.identity || null;
            return `
                <div class="control-plane-models__identity-row">
                    <span>${escapeHtml(runtime.model_id || runtime.key || 'Unknown runtime')}</span>
                    ${identity?.fingerprint
                        ? `<code title="${escapeHtml(identity.fingerprint)}">${escapeHtml(shortFingerprint(identity.fingerprint))}</code>`
                        : '<span class="ds-status" data-status="warning">Exploratory</span>'}
                </div>`;
        }).join('');
        return `
            <article class="ds-card control-plane-card">
                <div class="control-plane-card__header">
                    <h3>Runtime fingerprint</h3>
                    ${statusBadge(runtimes.some((item) => item?.identity?.fingerprint) ? 'Evidence available' : 'Exploratory', runtimes.some((item) => item?.identity?.fingerprint) ? 'ready' : 'warning')}
                </div>
                ${rows || '<div class="ds-empty">No resident runtime evidence.</div>'}
            </article>`;
    }

    function capabilitySummary(capabilities) {
        if (!capabilities || typeof capabilities !== 'object') return 'Unavailable';
        const tasks = Array.isArray(capabilities.tasks) ? capabilities.tasks : [];
        const inputs = Array.isArray(capabilities.input_modalities) ? capabilities.input_modalities : [];
        if (!tasks.length && !inputs.length) return 'Unavailable';
        const parts = [];
        if (tasks.length) parts.push(tasks.join(', '));
        if (inputs.length) parts.push(`inputs: ${inputs.join(', ')}`);
        return parts.join(' · ');
    }

    function finiteNumber(value) {
        if (value === null || value === undefined || value === '') return null;
        const number = Number(value);
        return Number.isFinite(number) ? number : null;
    }

    function formatBytes(value) {
        const number = finiteNumber(value);
        if (number === null) return 'Unavailable';
        if (number < 1024) return `${number} B`;
        const units = ['KiB', 'MiB', 'GiB', 'TiB'];
        let current = number;
        let index = -1;
        do {
            current /= 1024;
            index += 1;
        } while (current >= 1024 && index < units.length - 1);
        return `${current.toFixed(current >= 10 ? 1 : 2)} ${units[index]}`;
    }

    function formatDuration(seconds) {
        if (seconds < 60) return `${seconds.toFixed(1)}s`;
        if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
        return `${(seconds / 3600).toFixed(1)}h`;
    }

    function shortFingerprint(value) {
        const text = String(value);
        return text.length > 16 ? `${text.slice(0, 8)}…${text.slice(-8)}` : text;
    }

    function statusBadge(label, status) {
        return `<span class="ds-status" data-status="${escapeHtml(status)}">${escapeHtml(label)}</span>`;
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
        if (!ensureSurface()) {
            if (attempt < 20) setTimeout(() => boot(attempt + 1), 50);
            return;
        }
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
