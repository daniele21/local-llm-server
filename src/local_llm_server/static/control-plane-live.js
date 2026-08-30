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

    function primaryMetric(label, value, detail = '') {
        const rendered = value === null || value === undefined || value === '' ? 'Unavailable' : String(value);
        return `
            <div class="overview-primary-metric">
                <span class="overview-primary-metric__label">${escapeHtml(label)}</span>
                <strong class="overview-primary-metric__value">${escapeHtml(rendered)}</strong>
                ${detail ? `<span class="overview-primary-metric__detail">${escapeHtml(detail)}</span>` : ''}
            </div>`;
    }

    function evidenceMetric(label, value, source) {
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
            [...panel.children].forEach((child) => {
                if (child !== surface && child.classList?.contains('ds-empty')) child.remove();
            });
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
        const serverReady = health?.ok === true;
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
        const schedulerEnabled = scheduler?.policy?.enabled === true;
        const schedulerRuntimes = Array.isArray(scheduler?.runtimes) ? scheduler.runtimes : [];
        const schedulerQueued = schedulerEnabled ? sumIntegerField(schedulerRuntimes, 'queued') : null;
        const schedulerInflight = schedulerEnabled ? sumIntegerField(schedulerRuntimes, 'inflight') : null;
        const capacity = capacityState(resources);
        const readiness = readinessState(health, capacity);
        const budget = finiteNumber(resources?.usable_budget_bytes);
        const committed = finiteNumber(resources?.committed_bytes);
        const reserved = finiteNumber(resources?.reserved_bytes);
        const remaining = finiteNumber(resources?.remaining_bytes);
        const accounted = committed !== null && reserved !== null ? committed + reserved : null;

        updateHeaderStatus(readiness);

        surface.innerHTML = `
            <section class="overview-readiness" aria-labelledby="overview-readiness-title">
                <div class="overview-readiness__heading">
                    <div>
                        <span class="overview-eyebrow">Current state</span>
                        <h3 id="overview-readiness-title">${escapeHtml(readiness.title)}</h3>
                        <p>${escapeHtml(readiness.copy)}</p>
                    </div>
                    ${statusBadge(readiness.badge, readiness.status)}
                </div>
                <div class="overview-readiness-strip">
                    ${primaryMetric('Readiness', readiness.badge, serverState ? `Server state: ${serverState}` : 'Health source unavailable')}
                    ${primaryMetric('Resident', residentCount === null ? null : `${residentCount} runtime${residentCount === 1 ? '' : 's'}`, defaultModel ? `Default: ${defaultModel}` : 'Default route unavailable')}
                    ${primaryMetric('AI budget', budgetLabel(accounted, budget), remaining === null ? 'Accounting headroom unavailable' : `${formatBytes(remaining)} headroom`)}
                    ${primaryMetric('Workload', workloadLabel(activeRequests, schedulerQueued), schedulerEnabled ? 'Scheduler enabled' : scheduler ? 'Scheduler disabled' : 'Scheduler unavailable')}
                    ${primaryMetric('Capacity', capacity.label, capacity.shortCopy)}
                </div>
            </section>

            <div class="control-plane-grid control-plane-grid--two overview-decision-grid">
                <article class="ds-card control-plane-card overview-resource-card">
                    <div class="control-plane-card-heading">
                        <div>
                            <span class="overview-eyebrow">Resource & residency</span>
                            <h3>What can run next?</h3>
                        </div>
                        ${statusBadge(capacity.label, capacity.status)}
                    </div>
                    ${budgetProgress(accounted, budget)}
                    <dl class="overview-decision-list">
                        <div><dt>Accounted</dt><dd>${escapeHtml(formatBytes(accounted) || 'Unavailable')}</dd></div>
                        <div><dt>Headroom</dt><dd>${escapeHtml(formatBytes(remaining) || 'Unavailable')}</dd></div>
                        <div><dt>Resident default</dt><dd>${escapeHtml(defaultModel || 'Unavailable')}</dd></div>
                    </dl>
                    <p class="overview-decision-copy">${escapeHtml(capacity.copy)}</p>
                    ${residentSummary(models)}
                    <div class="control-plane-actions">
                        <button type="button" class="ds-button" data-variant="primary" data-open-control-plane="registry-tab">Manage runtimes</button>
                        ${capacity.needsAction ? '<span class="overview-action-note">Load feasibility and explicit unload recovery are available in Models & Runtimes.</span>' : ''}
                    </div>
                </article>

                <article class="ds-card control-plane-card overview-workload-card">
                    <div class="control-plane-card-heading">
                        <div>
                            <span class="overview-eyebrow">Live workload</span>
                            <h3>What is using the runtime?</h3>
                        </div>
                        ${statusBadge(scheduler ? (schedulerEnabled ? 'Scheduler on' : 'Scheduler off') : 'Unavailable', scheduler ? (schedulerEnabled ? 'ready' : 'cold') : 'unavailable')}
                    </div>
                    <dl class="overview-decision-list">
                        <div><dt>Active requests</dt><dd>${escapeHtml(renderNumber(activeRequests))}</dd></div>
                        <div><dt>Queued requests</dt><dd>${escapeHtml(renderNumber(schedulerQueued))}</dd></div>
                        <div><dt>Inflight admissions</dt><dd>${escapeHtml(renderNumber(schedulerInflight))}</dd></div>
                    </dl>
                    <p class="overview-decision-copy">${scheduler
                        ? (schedulerEnabled
                            ? 'Queue state is source-backed. Open System for scheduler policy and diagnostic detail.'
                            : 'The request scheduler is disabled; no queue state is inferred.')
                        : 'Scheduler evidence is unavailable. No queue state is fabricated.'}</p>
                    <div class="control-plane-actions">
                        <button type="button" class="ds-button" data-open-control-plane="chat-tab">Open Playground</button>
                        <button type="button" class="ds-button" data-open-control-plane="logs-tab">Open System</button>
                    </div>
                </article>
            </div>

            <details class="ds-card overview-evidence-details">
                <summary>Runtime evidence & provenance</summary>
                <p>Advanced evidence stays available without competing with readiness and resource decisions in the first scan.</p>
                <div class="control-plane-grid control-plane-grid--two control-plane-evidence-grid">
                    <article class="control-plane-card">
                        <div class="control-plane-card-heading">
                            <h3>Latest runtime evidence</h3>
                            ${statusBadge(canonicalMetrics ? 'Connected' : 'Unavailable', canonicalMetrics ? 'ready' : 'unavailable')}
                        </div>
                        ${evidenceMetric('Queue wait', formatMs(canonicalMetrics?.durations_ms?.queue_wait), metricSource(canonicalMetrics, 'queue_wait_ms'))}
                        ${evidenceMetric('Input tokens', canonicalMetrics?.counts?.input_tokens ?? null, metricSource(canonicalMetrics, 'input_tokens'))}
                        ${evidenceMetric('Output tokens', canonicalMetrics?.counts?.output_tokens ?? null, metricSource(canonicalMetrics, 'output_tokens'))}
                        ${evidenceMetric('Output chunks', canonicalMetrics?.counts?.output_chunks ?? null, metricSource(canonicalMetrics, 'output_chunks'))}
                        ${evidenceMetric('Prefill', formatMs(canonicalMetrics?.durations_ms?.prompt_prefill), metricSource(canonicalMetrics, 'prompt_prefill_ms'))}
                        ${evidenceMetric('TTFT', formatMs(canonicalMetrics?.durations_ms?.ttft), metricSource(canonicalMetrics, 'ttft_ms'))}
                        ${evidenceMetric('Decode', formatMs(canonicalMetrics?.durations_ms?.decode), metricSource(canonicalMetrics, 'decode_ms'))}
                        ${evidenceMetric('Decode throughput', formatRate(canonicalMetrics?.throughput?.decode_tokens_per_second, 'tok/s'), metricSource(canonicalMetrics, 'decode_tokens_per_second'))}
                    </article>
                    <article class="control-plane-card">
                        <div class="control-plane-card-heading">
                            <h3>Execution identity</h3>
                            ${statusBadge(identity ? 'Captured' : 'Unavailable', identity ? 'ready' : 'unavailable')}
                        </div>
                        ${evidenceMetric('Configured default', configuredDefault, health || evidence ? '/health · /api/v1/evidence' : 'source unavailable')}
                        ${evidenceMetric('Runtime fingerprint', identity?.fingerprint ?? null, identity ? '/api/v1/evidence' : 'source unavailable')}
                        ${evidenceMetric('Captured at', formatTimestamp(identity?.captured_at), identity ? '/api/v1/evidence' : 'source unavailable')}
                        ${evidenceMetric('Admission', resourceAdmission?.decision ?? null, resourceAdmission ? '/api/v1/evidence' : 'source unavailable')}
                        ${evidenceMetric('Load estimate', formatBytes(resourceAdmission?.estimate_bytes), resourceAdmission ? '/api/v1/evidence' : 'source unavailable')}
                    </article>
                </div>
            </details>

            ${resources === null || evidence === null || scheduler === null ? `
                <div class="ds-empty control-plane-unavailable">
                    Some advanced control-plane sources are unavailable. Enable the admin API to expose them; no fallback values are fabricated.
                </div>` : ''}`;

        bindActions(surface);
    }

    function readinessState(health, capacity) {
        if (!health) {
            return {
                title: 'Readiness unavailable',
                badge: 'Unavailable',
                status: 'unavailable',
                copy: 'The health source could not be read, so local execution readiness is not inferred.',
            };
        }
        if (health.ok !== true) {
            return {
                title: 'Local AI needs attention',
                badge: 'Not ready',
                status: 'error',
                copy: 'The server health contract is not ready. Open System for the owning diagnostic evidence.',
            };
        }
        if (health.state === 'cold') {
            return {
                title: 'Local AI is ready but cold',
                badge: 'Cold',
                status: 'cold',
                copy: 'The control plane is healthy, but an executable resident runtime may still need to be loaded.',
            };
        }
        if (capacity.needsAction) {
            return {
                title: 'Local AI is ready with constrained capacity',
                badge: 'Ready · constrained',
                status: 'warning',
                copy: 'The server is ready, but the accounting envelope may constrain the next model load. No physical-memory pressure claim is inferred.',
            };
        }
        return {
            title: 'Local AI is ready',
            badge: 'Ready',
            status: 'ready',
            copy: 'The server health contract is ready. Capacity status below is based only on the configured accounting envelope.',
        };
    }

    function capacityState(resources) {
        if (!resources) {
            return {
                label: 'Unavailable',
                status: 'unavailable',
                shortCopy: 'Resource source unavailable',
                copy: 'Resource accounting is unavailable, so load feasibility cannot be inferred here. The server remains the admission authority.',
                needsAction: false,
            };
        }
        if (resources.policy_state !== 'configured') {
            return {
                label: 'Admission disabled',
                status: 'cold',
                shortCopy: 'No configured AI envelope',
                copy: 'The product resource envelope is not configured. This is not interpreted as unlimited capacity.',
                needsAction: false,
            };
        }
        const budget = finiteNumber(resources.usable_budget_bytes);
        const remaining = finiteNumber(resources.remaining_bytes);
        if (budget === null || remaining === null) {
            return {
                label: 'Unavailable',
                status: 'unavailable',
                shortCopy: 'Accounting evidence incomplete',
                copy: 'The resource policy is configured, but budget/headroom evidence is incomplete. Load admission remains server-owned.',
                needsAction: false,
            };
        }
        if (remaining < 0) {
            return {
                label: 'Over budget',
                status: 'error',
                shortCopy: `${formatBytes(Math.abs(remaining))} deficit`,
                copy: 'Accounted commitments exceed the configured AI budget. Review resident runtimes before loading another model.',
                needsAction: true,
            };
        }
        if (remaining === 0) {
            return {
                label: 'No headroom',
                status: 'warning',
                shortCopy: '0 B accounting headroom',
                copy: 'The configured accounting envelope has no remaining headroom. Use explicit lifecycle actions before another load.',
                needsAction: true,
            };
        }
        if (budget > 0 && remaining / budget <= 0.1) {
            return {
                label: 'Low headroom',
                status: 'warning',
                shortCopy: `${formatBytes(remaining)} remains`,
                copy: 'Accounting headroom is low. Check per-model load feasibility before changing residency.',
                needsAction: true,
            };
        }
        return {
            label: 'Headroom available',
            status: 'ready',
            shortCopy: `${formatBytes(remaining)} remains`,
            copy: 'The configured accounting envelope has headroom. This is not a claim about observed physical-memory pressure.',
            needsAction: false,
        };
    }

    function budgetProgress(accounted, budget) {
        if (accounted === null || budget === null || budget <= 0) {
            return '<div class="ds-empty overview-budget-unavailable">Budget utilization unavailable.</div>';
        }
        const value = Math.max(0, Math.min(accounted, budget));
        return `
            <div class="overview-budget">
                <div class="overview-budget__labels"><span>Accounted AI budget</span><strong>${escapeHtml(formatBytes(accounted))} / ${escapeHtml(formatBytes(budget))}</strong></div>
                <progress value="${value}" max="${budget}" aria-label="Accounted AI resource budget"></progress>
            </div>`;
    }

    function residentSummary(models) {
        if (!models) return '<div class="ds-empty">Resident runtime source unavailable.</div>';
        if (!models.length) return '<div class="ds-empty">No resident runtimes are currently reported.</div>';
        const items = models.slice(0, 4).map((model) => {
            const identity = model?.key || model?.id || model?.model_id || 'Unavailable';
            const backend = model?.backend || 'backend unavailable';
            return `<li><strong>${escapeHtml(identity)}</strong><span>${escapeHtml(backend)}</span></li>`;
        }).join('');
        return `<ul class="overview-resident-list">${items}</ul>`;
    }

    function bindActions(surface) {
        surface.querySelectorAll('[data-open-control-plane]').forEach((button) => {
            button.addEventListener('click', () => {
                const id = button.dataset.openControlPlane;
                if (window.localLlmControlPlane?.navigate) {
                    window.localLlmControlPlane.navigate(id);
                    return;
                }
                document.querySelector(`.sidebar-nav .nav-item[data-tab="${id}"]`)?.click();
            });
        });
    }

    function updateHeaderStatus(readiness) {
        const badge = document.querySelector('#overview-tab .control-plane-header .ds-status');
        if (!badge) return;
        badge.dataset.status = readiness.status;
        badge.textContent = readiness.badge;
    }

    function budgetLabel(accounted, budget) {
        if (accounted === null || budget === null) return null;
        return `${formatBytes(accounted)} / ${formatBytes(budget)}`;
    }

    function workloadLabel(active, queued) {
        if (active === null && queued === null) return null;
        const activeText = active === null ? 'active unavailable' : `${active} active`;
        const queuedText = queued === null ? 'queue unavailable' : `${queued} queued`;
        return `${activeText} · ${queuedText}`;
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

    function renderNumber(value) {
        return value === null || value === undefined ? 'Unavailable' : String(value);
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