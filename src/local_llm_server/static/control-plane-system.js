(() => {
    const REFRESH_MS = 10000;
    let timer = null;
    let refreshing = false;

    async function fetchJson(path) {
        const response = await fetch(path, { headers: { Accept: 'application/json' } });
        let payload = null;
        try { payload = await response.json(); } catch (_) { payload = null; }
        if (!response.ok) throw new Error(`${path} returned ${response.status}`);
        return payload;
    }

    function ensureDiagnosticsSurface() {
        const panel = document.getElementById('logs-tab');
        if (!panel) return null;
        let surface = panel.querySelector('[data-control-plane-diagnostics]');
        if (surface) return surface;
        surface = document.createElement('section');
        surface.dataset.controlPlaneDiagnostics = 'true';
        surface.className = 'control-plane-system-surface';
        panel.prepend(surface);
        return surface;
    }

    function settingsSurface() {
        return document.getElementById('settings-tab');
    }

    async function refresh() {
        if (refreshing) return;
        refreshing = true;
        try {
            const [policyResult, resourceResult, residencyResult, schedulerResult, evidenceResult] = await Promise.allSettled([
                fetchJson('/api/v1/policies'),
                fetchJson('/api/v1/resources'),
                fetchJson('/api/v1/residency'),
                fetchJson('/api/v1/scheduler'),
                fetchJson('/api/v1/evidence'),
            ]);
            renderSettings(
                settingsSurface(),
                fulfilled(policyResult),
                fulfilled(resourceResult),
                fulfilled(residencyResult),
                fulfilled(schedulerResult),
            );
            renderDiagnostics(
                ensureDiagnosticsSurface(),
                fulfilled(resourceResult),
                fulfilled(schedulerResult),
                fulfilled(evidenceResult),
            );
        } finally {
            refreshing = false;
        }
    }

    function fulfilled(result) {
        return result.status === 'fulfilled' ? result.value : null;
    }

    function renderSettings(host, policy, resources, residency, scheduler) {
        if (!host) return;
        const runtimePolicies = Array.isArray(policy?.runtimes) ? policy.runtimes : [];
        const schedulerEnabled = scheduler?.policy?.enabled === true;
        const residencyRuntimes = Array.isArray(residency?.runtimes) ? residency.runtimes : [];
        const pinnedCount = residencyRuntimes.filter((item) => item?.pinned === true).length;
        const evictableCount = residencyRuntimes.filter((item) => item?.evictable === true).length;

        host.innerHTML = `
            <div class="control-plane-header">
                <div>
                    <h2>Settings</h2>
                    <p>Effective local policy state. This view is read-only: it does not invent configuration mutations that the server does not own yet.</p>
                </div>
                ${statusBadge(policy ? 'Policy evidence connected' : 'Policy evidence unavailable', policy ? 'ready' : 'unavailable')}
            </div>
            <div class="control-plane-grid control-plane-grid--two system-policy-grid">
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card__header">
                        <h3>Request privacy</h3>
                        ${statusBadge(policy?.canonical_request_policy_installed === true ? 'Enforced' : 'Unavailable', policy?.canonical_request_policy_installed === true ? 'ready' : 'unavailable')}
                    </div>
                    ${policy ? `
                        <dl class="system-definition-list">
                            <div><dt>Remote media default</dt><dd>${escapeHtml(policy.remote_media_default || 'Unavailable')}</dd></div>
                            <div><dt>Remote model code default</dt><dd>${policy.trust_remote_code_default === false ? 'Blocked' : 'Unavailable'}</dd></div>
                        </dl>
                        ${runtimePolicyTable(runtimePolicies)}
                    ` : unavailable('Policy evidence source did not respond. No fallback policy value is displayed.')}
                </article>
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card__header">
                        <h3>Resource budget</h3>
                        ${resources ? statusBadge(resources.enabled === true ? 'Configured' : 'Disabled', resources.enabled === true ? 'ready' : 'unavailable') : statusBadge('Unavailable', 'unavailable')}
                    </div>
                    ${resources ? `
                        <dl class="system-definition-list">
                            <div><dt>Limit</dt><dd>${escapeHtml(formatBytes(resources.memory_limit_bytes))}</dd></div>
                            <div><dt>Headroom</dt><dd>${escapeHtml(formatBytes(resources.headroom_bytes))}</dd></div>
                            <div><dt>Committed</dt><dd>${escapeHtml(formatBytes(resources.committed_bytes))}</dd></div>
                            <div><dt>Remaining</dt><dd>${escapeHtml(formatBytes(resources.remaining_bytes))}</dd></div>
                        </dl>
                    ` : unavailable('Resource policy source did not respond.')}
                </article>
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card__header">
                        <h3>Residency policy</h3>
                        ${residency ? statusBadge(`${residencyRuntimes.length} resident`, 'ready') : statusBadge('Unavailable', 'unavailable')}
                    </div>
                    ${residency ? `
                        <dl class="system-definition-list">
                            <div><dt>Pinned</dt><dd>${pinnedCount}</dd></div>
                            <div><dt>Evictable now</dt><dd>${evictableCount}</dd></div>
                            <div><dt>Cold</dt><dd>${residency.cold === true ? 'Yes' : 'No'}</dd></div>
                            <div><dt>Default route</dt><dd>${escapeHtml(residency.resident_default_model || 'Unavailable')}</dd></div>
                        </dl>
                        <p class="system-policy-note">Pinning and explicit LRU/TTL selection are residency policy only. They do not prove host-memory reclamation.</p>
                    ` : unavailable('Residency policy source did not respond.')}
                </article>
                <article class="ds-card control-plane-card">
                    <div class="control-plane-card__header">
                        <h3>Request scheduler</h3>
                        ${scheduler ? statusBadge(schedulerEnabled ? 'Enabled' : 'Disabled', schedulerEnabled ? 'ready' : 'unavailable') : statusBadge('Unavailable', 'unavailable')}
                    </div>
                    ${scheduler ? schedulerPolicyMarkup(scheduler.policy) : unavailable('Scheduler policy source did not respond.')}
                </article>
            </div>`;
    }

    function renderDiagnostics(host, resources, scheduler, evidence) {
        if (!host) return;
        const runtimes = Array.isArray(evidence?.runtimes) ? evidence.runtimes : [];
        const schedulerRuntimes = Array.isArray(scheduler?.runtimes) ? scheduler.runtimes : [];
        const verified = evidence ? runtimes.filter((item) => Boolean(item?.identity?.fingerprint)).length : null;
        const active = evidence ? sumComplete(runtimes, (item) => item?.runtime?.active_requests) : null;
        const schedulerEnabled = scheduler?.policy?.enabled === true;
        const queued = schedulerEnabled ? sumComplete(schedulerRuntimes, (item) => item?.queued) : null;
        const inflight = schedulerEnabled ? sumComplete(schedulerRuntimes, (item) => item?.inflight) : null;

        host.innerHTML = `
            <div class="control-plane-header">
                <div>
                    <h2>System / Diagnostics</h2>
                    <p>Source-backed operational summary above the existing live server logs. Prompt and generated content are not copied into this evidence layer.</p>
                </div>
                ${statusBadge(evidence ? (evidence.cold === true ? 'Cold / healthy' : 'Runtime evidence connected') : 'Evidence unavailable', evidence ? 'ready' : 'unavailable')}
            </div>
            <div class="control-plane-grid system-diagnostics-grid">
                ${diagnosticCard('Resident runtimes', evidence ? formatMaybeNumber(evidence.runtime_count ?? runtimes.length) : 'Unavailable', evidence ? `${formatMaybeNumber(active)} active request(s)` : 'Runtime evidence source unavailable')}
                ${diagnosticCard('Verified identity', evidence ? `${verified}/${runtimes.length}` : 'Unavailable', 'Exact runtime fingerprints currently attached')}
                ${diagnosticCard('Scheduler', scheduler ? (schedulerEnabled ? `${formatMaybeNumber(inflight)} inflight / ${formatMaybeNumber(queued)} queued` : 'Disabled') : 'Unavailable', schedulerEnabled ? 'Bounded admission enabled' : (scheduler ? 'Admission queue disabled' : 'Scheduler source unavailable'))}
                ${diagnosticCard('Resource remaining', resources ? formatBytes(resources.remaining_bytes) : 'Unavailable', resources?.enabled === true ? 'Configured AI memory budget' : (resources ? 'Resource budget disabled' : 'Resource source unavailable'))}
            </div>
            <div class="system-runtime-evidence">
                ${runtimes.length ? runtimes.map(runtimeEvidenceRow).join('') : '<div class="ds-empty">No resident runtime evidence.</div>'}
            </div>`;
    }

    function runtimePolicyTable(runtimes) {
        if (!runtimes.length) return '<div class="ds-empty">No resident runtime policy overrides.</div>';
        return `
            <div class="system-table-wrap">
                <table class="ds-table system-policy-table">
                    <thead><tr><th>Runtime</th><th>Remote media</th><th>Remote code</th></tr></thead>
                    <tbody>${runtimes.map((item) => `
                        <tr>
                            <td>${escapeHtml(item.model || item.key || 'Unknown')}</td>
                            <td>${statusBadge(item.allow_remote_media === true ? 'Allowed' : 'Blocked', item.allow_remote_media === true ? 'warning' : 'ready')}</td>
                            <td>${statusBadge(item.trust_remote_code === true ? 'Allowed' : 'Blocked', item.trust_remote_code === true ? 'warning' : 'ready')}</td>
                        </tr>`).join('')}</tbody>
                </table>
            </div>`;
    }

    function schedulerPolicyMarkup(policy) {
        if (!policy || typeof policy !== 'object') return unavailable('Scheduler policy metadata unavailable.');
        return `
            <dl class="system-definition-list">
                <div><dt>Queue capacity</dt><dd>${formatMaybeNumber(policy.queue_capacity)}</dd></div>
                <div><dt>Default wait timeout</dt><dd>${formatMaybeMs(policy.default_queue_timeout_ms)}</dd></div>
                <div><dt>Timeout scope</dt><dd>${escapeHtml(policy.timeout_scope || 'Unavailable')}</dd></div>
            </dl>`;
    }

    function runtimeEvidenceRow(item) {
        const runtime = item?.runtime || {};
        const metrics = item?.metrics || {};
        const durations = metrics?.durations_ms || {};
        const throughput = metrics?.throughput || {};
        const fingerprint = item?.identity?.fingerprint || null;
        return `
            <article class="ds-card system-runtime-row">
                <div>
                    <strong>${escapeHtml(runtime.model_id || runtime.key || 'Unknown runtime')}</strong>
                    <small>${escapeHtml(runtime.backend || 'Backend unavailable')} · ${escapeHtml(runtime.state || 'state unavailable')}</small>
                </div>
                <div><span>Fingerprint</span><code>${fingerprint ? escapeHtml(shortFingerprint(fingerprint)) : 'Unavailable'}</code></div>
                <div><span>Queue wait</span><strong>${formatMaybeMs(durations.queue_wait)}</strong></div>
                <div><span>TTFT</span><strong>${formatMaybeMs(durations.ttft)}</strong></div>
                <div><span>Decode rate</span><strong>${formatRate(throughput.decode_tokens_per_second)}</strong></div>
            </article>`;
    }

    function diagnosticCard(label, value, detail) {
        return `<article class="ds-card control-plane-card"><span class="capability-eyebrow">${escapeHtml(label)}</span><strong class="system-diagnostic-value">${escapeHtml(value)}</strong><small>${escapeHtml(detail)}</small></article>`;
    }

    function unavailable(message) {
        return `<div class="ds-empty control-plane-unavailable">${escapeHtml(message)}</div>`;
    }

    function statusBadge(label, status) {
        return `<span class="ds-status" data-status="${escapeHtml(status)}">${escapeHtml(label)}</span>`;
    }

    function nullableNumber(value) {
        if (value === null || value === undefined || value === '') return null;
        const number = Number(value);
        return Number.isFinite(number) ? number : null;
    }

    function sumComplete(items, getValue) {
        let total = 0;
        for (const item of items) {
            const value = nullableNumber(getValue(item));
            if (value === null) return null;
            total += value;
        }
        return total;
    }

    function formatBytes(value) {
        const number = nullableNumber(value);
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

    function formatMaybeNumber(value) {
        const number = nullableNumber(value);
        return number === null ? 'Unavailable' : String(number);
    }

    function formatMaybeMs(value) {
        const number = nullableNumber(value);
        return number === null ? 'Unavailable' : `${number.toFixed(number >= 10 ? 1 : 2)} ms`;
    }

    function formatRate(value) {
        const number = nullableNumber(value);
        return number === null ? 'Unavailable' : `${number.toFixed(2)} tok/s`;
    }

    function shortFingerprint(value) {
        const text = String(value);
        return text.length > 16 ? `${text.slice(0, 8)}…${text.slice(-8)}` : text;
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
        if (!settingsSurface() || !ensureDiagnosticsSurface()) {
            if (attempt < 30) setTimeout(() => boot(attempt + 1), 50);
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
