(() => {
    const REFRESH_MS = 10000;
    let timer = null;

    async function fetchJson(path) {
        const response = await fetch(path, { headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error(`${path} returned ${response.status}`);
        return response.json();
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
        const surface = ensureSurface();
        if (!surface) return;

        const [residentResult, statusResult, catalogResult] = await Promise.allSettled([
            fetchJson('/v1/models'),
            fetchJson('/status'),
            fetchJson('/api/v1/models/registry'),
        ]);

        const residentPayload = residentResult.status === 'fulfilled' ? residentResult.value : null;
        const statusPayload = statusResult.status === 'fulfilled' ? statusResult.value : null;
        const catalogPayload = catalogResult.status === 'fulfilled' ? catalogResult.value : null;
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

        const rows = catalog
            ? catalog.map((model) => buildRow(model, residentByKey, runtimeStatus, statusPayload?.default_model))
            : residents.map((model) => buildRow(model, residentByKey, runtimeStatus, statusPayload?.default_model));

        surface.innerHTML = `
            <div class="control-plane-header">
                <div>
                    <h2>Models & Runtimes</h2>
                    <p>Configured identity, residency and active runtime state from current server sources. Missing control-plane sources remain explicit.</p>
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
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.length ? rows.join('') : '<tr><td colspan="6">Unavailable — no model source returned data.</td></tr>'}
                    </tbody>
                </table>
            </div>
            <div class="control-plane-grid control-plane-grid--two control-plane-models__details">
                <article class="ds-card control-plane-card">
                    <h3>Resource admission</h3>
                    <div class="ds-empty control-plane-unavailable">Unavailable until B1/B2 resource state is exposed by the product API.</div>
                </article>
                <article class="ds-card control-plane-card">
                    <h3>Runtime fingerprint</h3>
                    <div class="ds-empty control-plane-unavailable">Unavailable until D3 identity snapshots are attached and exposed.</div>
                </article>
            </div>
            <div class="control-plane-actions">
                <button type="button" class="ds-button" data-scroll-legacy-model-controls>Open lifecycle controls</button>
            </div>`;

        surface.querySelector('[data-scroll-legacy-model-controls]')?.addEventListener('click', () => {
            const legacy = [...surface.parentElement.children].find((node) => node !== surface && node.querySelector?.('#models-list-container'));
            (legacy || document.getElementById('models-list-container'))?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    function buildRow(model, residentByKey, runtimeStatus, defaultModel) {
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

        return `
            <tr>
                <td><strong>${escapeHtml(modelId)}</strong><br><code>${escapeHtml(key)}</code></td>
                <td>${statusBadge(resident ? 'Resident' : 'Cold', resident ? 'resident' : 'cold')}</td>
                <td>${isDefault ? statusBadge('Default', 'ready') : '—'}</td>
                <td>${escapeHtml(backend ?? 'Unavailable')}</td>
                <td>${escapeHtml(runtimeState ?? 'Unavailable')}${active ? `<br><small>${escapeHtml(active)}</small>` : ''}</td>
                <td>${escapeHtml(capabilityText)}</td>
            </tr>`;
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
