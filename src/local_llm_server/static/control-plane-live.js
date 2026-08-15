(() => {
    const REFRESH_MS = 10000;
    let timer = null;

    async function fetchJson(path) {
        const response = await fetch(path, { headers: { Accept: 'application/json' } });
        if (!response.ok) {
            const error = new Error(`${path} returned ${response.status}`);
            error.status = response.status;
            throw error;
        }
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
            fetchJson('/api/v1/resources'),
            fetchJson('/api/v1/evidence'),
            fetchJson('/api/v1/scheduler'),
        ]);
        const health = fulfilled(results[0]);
        const runtimeStatus = fulfilled(results[1]);
        const modelsPayload = fulfilled(results[2]);
        const resources = fulfilled(results[3]);
        const evidence = fulfilled(results[4]);
        const scheduler = fulfilled(results[5]);

        const models = Array.isArray(modelsPayload?.data) ? modelsPayload.data : null;
        const serverReady = Boolean(health?.ok);
        const serverState = health?.state || (serverReady ? 'ready' : null);
        const configuredDefault = health?.configured_default_model
            ?? evidence?.configured_default_model
            ?? null;
        const defaultModel = health?.default_model
            ?? runtimeStatus?.default_model
            ?? evidence?.default_model
            ?? null;
        const residentCount = models ? models.length : numberOrNull(evidence?.runtime_count);
        const activeRequests = aggregateActiveRequests(runtimeStatus?.models);
        const defaultEvidence = chooseDefaultEvidence(evidence, defaultModel);
        const canonicalMetrics = defaultEvidence?.metrics || null;
        const identity = defaultEvidence?.identity || null;
        const resourceAdmission = defaultEvidence?.resource_admission || null;
        const resourceConfigured = resources?.policy_state === 'configured';
        const resourceAvailable = resources !== null;
        const schedulerAvailable = scheduler !== null;
        const schedulerEnabled = scheduler?.policy?.enabled === true;
        const schedulerRuntimes = Array.isArray(scheduler?.runtimes) ? scheduler.runtimes : [];
        const schedulerQueued = schedulerEnabled ? sumIntegerField(schedulerRuntimes, 'queued') : null;
        const schedulerInflight = schedulerEnabled ? sumIntegerField(schedulerRuntimes, 'inflight') : null;

        surface.innerHTML = `
            <div class="control-plane-grid">
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Server</h3>
                        ${statusBadge(
                            serverReady ? capitalize(serverState || 'ready') : 'Unavailable',
                            serverReady ? (serverState === 'cold' ? 'cold' : 'ready') : 'unavailable'
                        )}
                    </div>
                    ${metric('Backend', health?.backend ?? null, health ? '/health' : 'source unavailable')}
                    ${metric('Resident default', defaultModel, health || runtimeStatus ? '/health · /status' : 'source unavailable')}
                    ${metric('Configured default', configuredDefault, health || evidence ? '/health · /api/v1/evidence' : 'source unavailable')}
                </article>

                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Resident runtimes</h3>
                        ${statusBadge(models || evidence ? 'Source connected' : 'Unavailable', models || evidence ? 'resident' : 'unavailable')}
                    </div>
                    ${metric('Resident count', residentCount, models ? '/v1/models' : evidence ? '/api/v1/evidence' : 'source unavailable')}
                    ${metric('Active requests', activeRequests, runtimeStatus ? '/status' : 'source unavailable')}
                </article>

                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Resource policy</h3>
                        ${statusBadge(
                            resourceAvailable ? (resourceConfigured ? 'Configured' : 'Disabled') : 'Unavailable',
                            resourceAvailable ? (resourceConfigured ? 'ready' : 'cold') : 'unavailable'
                        )}
                    </div>
                    ${metric('Usable budget', formatBytes(resources?.usable_budget_bytes), resources ? '/api/v1/resources' : 'source unavailable')}
                    ${metric('Committed', formatBytes(resources?.committed_bytes), resources ? '/api/v1/resources' : 'source unavailable')}
                    ${metric('Reserved', formatBytes(resources?.reserved_bytes), resources ? '/api/v1/resources' : 'source unavailable')}
                    ${metric('Remaining', formatBytes(resources?.remaining_bytes), resources ? '/api/v1/resources' : 'source unavailable')}
                </article>

                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Request scheduler</h3>
                        ${statusBadge(
                            schedulerAvailable ? (schedulerEnabled ? 'Enabled' : 'Disabled') : 'Unavailable',
                            schedulerAvailable ? (schedulerEnabled ? 'ready' : 'cold') : 'unavailable'
                        )}
                    </div>
                    ${metric('Queue capacity / runtime', schedulerEnabled ? scheduler?.policy?.queue_capacity ?? null : null, scheduler ? '/api/v1/scheduler' : 'source unavailable')}
                    ${metric('Default queue timeout', schedulerEnabled ? formatMs(scheduler?.policy?.default_queue_timeout_ms) : null, scheduler ? '/api/v1/scheduler' : 'source unavailable')}
                    ${metric('Inflight admissions', schedulerInflight, scheduler ? '/api/v1/scheduler' : 'source unavailable')}
                    ${metric('Queued requests', schedulerQueued, scheduler ? '/api/v1/scheduler' : 'source unavailable')}
                </article>
            </div>

            <div class="control-plane-grid control-plane-grid--two control-plane-evidence-grid">
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Latest runtime evidence</h3>
                        ${statusBadge(canonicalMetrics ? 'Source connected' : 'Unavailable', canonicalMetrics ? 'ready' : 'unavailable')}
                    </div>
                    ${metric('Queue wait', formatMs(canonicalMetrics?.durations_ms?.queue_wait), metricSource(canonicalMetrics, 'queue_wait_ms'))}
                    ${metric('Input tokens', canonicalMetrics?.counts?.input_tokens ?? null, metricSource(canonicalMetrics, 'input_tokens'))}
                    ${metric('Output tokens', canonicalMetrics?.counts?.output_tokens ?? null, metricSource(canonicalMetrics, 'output_tokens'))}
                    ${metric('Output chunks', canonicalMetrics?.counts?.output_chunks ?? null, metricSource(canonicalMetrics, 'output_chunks'))}
                    ${metric('Prefill', formatMs(canonicalMetrics?.durations_ms?.prompt_prefill), metricSource(canonicalMetrics, 'prompt_prefill_ms'))}
                    ${metric('TTFT', formatMs(canonicalMetrics?.durations_ms?.ttft), metricSource(canonicalMetrics, 'ttft_ms'))}
                    ${metric('Decode', formatMs(canonicalMetrics?.durations_ms?.decode), metricSource(canonicalMetrics, 'decode_ms'))}
                    ${metric('Decode throughput', formatRate(canonicalMetrics?.throughput?.decode_tokens_per_second, 'tok/s'), metricSource(canonicalMetrics, 'decode_tokens_per_second'))}
                </article>

                <article class="ds-card control-plane-card">
                    <div class="control-plane-card-heading">
                        <h3>Execution identity</h3>
                        ${statusBadge(identity ? 'Captured' : 'Unavailable', identity ? 'ready' : 'unavailable')}
                    </div>
                    ${metric('Runtime fingerprint', identity?.fingerprint ?? null, identity ? '/api/v1/evidence' : 'source unavailable')}
                    ${metric('Captured at', formatTimestamp(identity?.captured_at), identity ? '/api/v1/evidence' : 'source unavailable')}
                    ${metric('Admission', resourceAdmission?.decision ?? null, resourceAdmission ? '/api/v1/evidence' : 'source unavailable')}
                    ${metric('Load estimate', formatBytes(resourceAdmission?.estimate_bytes), resourceAdmission ? '/api/v1/evidence' : 'source unavailable')}
                </article>
            </div>

            ${resources === null || evidence === null || scheduler === null ? `
                <div class="ds-empty control-plane-unavailable">
                    Resource/evidence/scheduler control-plane sources are unavailable. Enable the admin API to expose them; no fallback values are fabricated.
                </div>` : ''}

            <div class="control-plane-actions">
                <button type="button" class="ds-button" data-open-control-plane="registry-tab">Open Models & Runtimes</button>
                <button type="button" class="ds-button" data-open-control-plane="logs-tab">Open Diagnostics</button>
                <button type="button" class="ds-button" data-open-control-plane="benchmark-tab">Open Evaluation</button>
            </div>`;

        surface.querySelectorAll('[data-open-control-plane]').forEach((button) => {
            button.addEventListener('click', () => {
                const id = button.dataset.openControlPlane;
                document.querySelector(`.sidebar-nav .nav-item[data-tab="${id}"]`)?.click();
            });
        });
    }

    function fulfilled(result) {
        return result?.status === 'fulfilled' ? result.value : null;
    }

    function chooseDefaultEvidence(evidence, defaultModel) {
        const runtimes = Array.isArray(evidence?.runtimes) ? evidence.runtimes : [];
        if (!runtimes.length) return null;
        if (!defaultModel) return runtimes[0];
        return runtimes.find((item) => {
            const runtime = item?.runtime || {};
            return runtime.key === defaultModel || runtime.model_id === defaultModel;
        }) || runtimes[0];
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

    function sumIntegerField(items, field) {
        let total = 0;
        for (const item of items) {
            const value = item?.[field];
            if (!Number.isInteger(value) || value < 0) return null;
            total += value;
        }
        return total;
    }

    function metricSource(metrics, field) {
        if (!metrics) return 'source unavailable';
        return metrics.sources?.[field] || '/api/v1/evidence · unavailable source detail';
    }

    function finiteNumber(value) {
        if (value === null || value === undefined || value === '') return null;
        const number = Number(value);
        return Number.isFinite(number) ? number : null;
    }

    function numberOrNull(value) {
        return finiteNumber(value);
    }

    function formatBytes(value) {
        const number = finiteNumber(value);
        if (number === null || number < 0) return null;
        if (number >= 1024 ** 3) return `${(number / 1024 ** 3).toFixed(2)} GiB`;
        if (number >= 1024 ** 2) return `${(number / 1024 ** 2).toFixed(1)} MiB`;
        if (number >= 1024) return `${(number / 1024).toFixed(1)} KiB`;
        return `${number} B`;
    }

    function formatMs(value) {
        const number = finiteNumber(value);
        return number !== null && number >= 0 ? `${number.toFixed(1)} ms` : null;
    }

    function formatRate(value, unit) {
        const number = finiteNumber(value);
        return number !== null && number >= 0 ? `${number.toFixed(2)} ${unit}` : null;
    }

    function formatTimestamp(value) {
        const number = finiteNumber(value);
        if (number === null || number < 0) return null;
        const date = new Date(number * 1000);
        return Number.isNaN(date.getTime()) ? null : date.toLocaleString();
    }

    function capitalize(value) {
        const text = String(value || '');
        return text ? `${text[0].toUpperCase()}${text.slice(1)}` : text;
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
