(() => {
    const REFRESH_MS = 10000;
    let timer = null;

    async function fetchJson(path) {
        const response = await fetch(path, { headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error(`${path} returned ${response.status}`);
        return response.json();
    }

    function statusBadge(label, status) {
        return `<span class="ds-status" data-status="${escapeHtml(status)}">${escapeHtml(label)}</span>`;
    }

    function metric(label, value, source) {
        const rendered = value === null || value === undefined || value === '' ? 'Unavailable' : String(value);
        return `
            <div class="ds-metric">
                <span class="ds-metric__label">${escapeHtml(label)}</span>
                <span class="ds-metric__value">${escapeHtml(rendered)}</span>
                <span class="ds-metric__source">${escapeHtml(source)}</span>
            </div>`;
    }

    function ensureOverviewSurface() {
        const panel = document.getElementById('overview-tab');
        if (!panel) return null;
        let surface = panel.querySelector('[data-control-plane-live-overview]');
        if (!surface) {
            surface = document.createElement('div');
            surface.dataset.controlPlaneLiveOverview = 'true';
            surface.className = 'control-plane-live-overview';
            const header = panel.querySelector('.control-plane-header');
            if (header) header.insertAdjacentElement('afterend', surface);
            else panel.prepend(surface);
        }
        return surface;
    }

    async function refresh() {
        const surface = ensureOverviewSurface();
        if (!surface) return;

        const results = await Promise.allSettled([
            fetchJson('/health'),
            fetchJson('/status'),
            fetchJson('/v1/models'),
        ]);
        const health = results[0].status === 'fulfilled' ? results[0].value : null;
        const runtimeStatus = results[1].status === 'fulfilled' ? results[1].value : null;
        const modelsPayload = results[2].status === 'fulfilled' ? results[2].value : null;

        const models = Array.isArray(modelsPayload?.data) ? modelsPayload.data : null;
        const serverReady = Boolean(health?.ok);
        const defaultModel = health?.default_model ?? runtimeStatus?.default_model ?? null;
        const residentCount = models ? models.length : null;
        const activeRequests = aggregateActiveRequests(runtimeStatus?.models);

        surface.innerHTML = `
            <div class="control-plane-grid">
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Server</h3>
                        ${statusBadge(serverReady ? 'Ready' : 'Unavailable', serverReady ? 'ready' : 'unavailable')}
                    </div>
                    ${metric('Backend', health?.backend ?? null, health ? '/health' : 'source unavailable')}
                    ${metric('Default route', defaultModel, health || runtimeStatus ? '/health · /status' : 'source unavailable')}
                </article>
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Resident runtimes</h3>
                        ${statusBadge(models ? 'Source connected' : 'Unavailable', models ? 'resident' : 'unavailable')}
                    </div>
                    ${metric('Resident count', residentCount, models ? '/v1/models' : 'source unavailable')}
                    ${metric('Active requests', activeRequests, runtimeStatus ? '/status' : 'source unavailable')}
                </article>
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Resource pressure</h3>
                        ${statusBadge('Unavailable', 'unavailable')}
                    </div>
                    <p>Resource contracts exist, but runtime resource observation is not yet exposed through a product API.</p>
                </article>
            </div>
            <div class="control-plane-actions">
                <button type="button" class="ds-button" data-open-control-plane="registry-tab">Open Models & Runtimes</button>
                <button type="button" class="ds-button" data-open-control-plane="logs-tab">Open Diagnostics</button>
            </div>`;

        surface.querySelectorAll('[data-open-control-plane]').forEach((button) => {
            button.addEventListener('click', () => {
                const id = button.dataset.openControlPlane;
                document.querySelector(`.sidebar-nav .nav-item[data-tab="${id}"]`)?.click();
            });
        });
    }

    function aggregateActiveRequests(models) {
        if (!models || typeof models !== 'object') return null;
        const values = Object.values(models);
        if (!values.length) return 0;
        let total = 0;
        for (const model of values) {
            const value = model?.active_requests;
            if (!Number.isInteger(value) || value < 0) return null;
            total += value;
        }
        return total;
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
        if (!ensureOverviewSurface()) {
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
