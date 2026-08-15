(() => {
    const REFRESH_MS = 10000;
    let refreshTimer = null;
    let comparisonRunning = false;

    async function fetchJson(path, options = {}) {
        const response = await fetch(path, {
            headers: { Accept: 'application/json', ...(options.headers || {}) },
            ...options,
        });
        let payload = null;
        try { payload = await response.json(); } catch (_) { payload = null; }
        if (!response.ok) {
            const message = payload?.detail?.message || payload?.detail || `${path} returned ${response.status}`;
            const error = new Error(typeof message === 'string' ? message : JSON.stringify(message));
            error.status = response.status;
            throw error;
        }
        return payload;
    }

    function findView() {
        return document.getElementById('benchmark-tab');
    }

    function ensureHost() {
        const view = findView();
        if (!view?.querySelector('[data-evaluation-form]')) return null;
        let host = view.querySelector('[data-evaluation-history]');
        if (host) return host;
        host = document.createElement('section');
        host.dataset.evaluationHistory = 'true';
        host.className = 'evaluation-history';
        const resultHost = view.querySelector('[data-evaluation-result]');
        if (resultHost) resultHost.insertAdjacentElement('afterend', host);
        else view.appendChild(host);
        return host;
    }

    async function refreshHistory({ preserveComparison = true } = {}) {
        const host = ensureHost();
        if (!host) return;
        const comparisonHtml = preserveComparison
            ? host.querySelector('[data-evaluation-comparison-result]')?.outerHTML || ''
            : '';
        try {
            const payload = await fetchJson('/api/v1/evaluation/history');
            const runs = Array.isArray(payload?.runs) ? payload.runs : [];
            renderHistory(host, runs, comparisonHtml);
        } catch (error) {
            renderUnavailable(host, error);
        }
    }

    function renderUnavailable(host, error) {
        host.innerHTML = `
            <div class="control-plane-header evaluation-history-header">
                <div>
                    <span class="evaluation-eyebrow">Regression workflow</span>
                    <h3>Run history</h3>
                    <p>Persisted evaluation history is unavailable. No comparison is inferred.</p>
                </div>
                <span class="ds-status" data-status="unavailable">Unavailable</span>
            </div>
            <div class="ds-empty control-plane-unavailable">
                ${escapeHtml(error?.message || 'History source unavailable')}
            </div>`;
    }

    function renderHistory(host, runs, comparisonHtml = '') {
        const recent = runs.slice(0, 20);
        const options = recent.map((run) => `
            <option value="${escapeHtml(run.run_id)}">
                ${escapeHtml(shortRun(run.run_id))} · ${escapeHtml(run.model || 'model unavailable')} · ${Number(run.sample_count || 0)} samples
            </option>`).join('');

        host.innerHTML = `
            <div class="control-plane-header evaluation-history-header">
                <div>
                    <span class="evaluation-eyebrow">Regression workflow</span>
                    <h3>Run history</h3>
                    <p>Compare persisted runs only when dataset and selected sample identity allow it.</p>
                </div>
                <span class="ds-status" data-status="${runs.length ? 'resident' : 'unavailable'}">
                    ${runs.length} persisted run${runs.length === 1 ? '' : 's'}
                </span>
            </div>

            ${recent.length ? `
                <div class="ds-card evaluation-history-table-wrap">
                    <table class="ds-table evaluation-history-table">
                        <thead>
                            <tr><th>Run</th><th>Model</th><th>Samples</th><th>Quality</th><th>Success</th><th>Identity</th><th>Stored</th><th></th></tr>
                        </thead>
                        <tbody>${recent.map(historyRow).join('')}</tbody>
                    </table>
                </div>
            ` : '<div class="ds-empty">No persisted evaluation runs yet.</div>'}

            ${recent.length >= 2 ? `
                <form class="ds-card evaluation-comparison-form" data-evaluation-compare-form>
                    <div>
                        <span class="evaluation-eyebrow">Run comparison</span>
                        <h3>Baseline vs candidate</h3>
                        <p>Delta values are descriptive. They are never converted automatically into a better/worse verdict.</p>
                    </div>
                    <div class="evaluation-comparison-selectors">
                        <label class="ds-field">
                            <span>Baseline</span>
                            <select data-evaluation-baseline required>${options}</select>
                        </label>
                        <label class="ds-field">
                            <span>Candidate</span>
                            <select data-evaluation-candidate required>${options}</select>
                        </label>
                    </div>
                    <button class="ds-button" type="submit" data-evaluation-compare>Compare runs</button>
                </form>
                <div data-evaluation-comparison-result>${comparisonHtml}</div>
            ` : ''}

            <div data-evaluation-history-detail></div>`;

        const baseline = host.querySelector('[data-evaluation-baseline]');
        const candidate = host.querySelector('[data-evaluation-candidate]');
        if (candidate && candidate.options.length > 1) candidate.selectedIndex = 1;

        host.querySelector('[data-evaluation-compare-form]')?.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (comparisonRunning || !baseline || !candidate) return;
            const resultHost = host.querySelector('[data-evaluation-comparison-result]');
            const button = host.querySelector('[data-evaluation-compare]');
            if (baseline.value === candidate.value) {
                resultHost.innerHTML = '<div class="ds-empty control-plane-unavailable">Baseline and candidate must be different runs.</div>';
                return;
            }
            comparisonRunning = true;
            button.disabled = true;
            resultHost.innerHTML = '<div class="ds-empty">Comparing persisted run evidence…</div>';
            try {
                const payload = await fetchJson(
                    `/api/v1/evaluation/history/compare?baseline=${encodeURIComponent(baseline.value)}&candidate=${encodeURIComponent(candidate.value)}`
                );
                renderComparison(resultHost, payload);
            } catch (error) {
                resultHost.innerHTML = `<div class="ds-empty control-plane-unavailable">Comparison failed: ${escapeHtml(error?.message || 'unknown error')}</div>`;
            } finally {
                comparisonRunning = false;
                button.disabled = false;
            }
        });

        host.querySelectorAll('[data-evaluation-inspect]').forEach((button) => {
            button.addEventListener('click', () => inspectRun(host, button.dataset.evaluationInspect));
        });
    }

    function historyRow(run) {
        const quality = finite(run?.objective_quality_mean);
        const success = finite(run?.execution_success_rate);
        const evidenceGrade = Boolean(run?.runtime_fingerprint);
        return `<tr>
            <td><code title="${escapeHtml(run?.run_id || '')}">${escapeHtml(shortRun(run?.run_id || ''))}</code></td>
            <td>${escapeHtml(run?.model || 'Unavailable')}</td>
            <td>${escapeHtml(run?.sample_count ?? 'Unavailable')}</td>
            <td>${quality === null ? 'Unavailable' : `${(quality * 100).toFixed(1)}%`}</td>
            <td>${success === null ? 'Unavailable' : `${(success * 100).toFixed(1)}%`}</td>
            <td>${statusBadge(evidenceGrade ? 'Evidence-grade' : 'Exploratory', evidenceGrade ? 'ready' : 'warning')}</td>
            <td>${escapeHtml(formatStoredAt(run?.stored_at))}</td>
            <td><button type="button" class="ds-button ds-button--small" data-evaluation-inspect="${escapeHtml(run?.run_id || '')}">Inspect</button></td>
        </tr>`;
    }

    async function inspectRun(host, runId) {
        const detail = host.querySelector('[data-evaluation-history-detail]');
        if (!detail || !runId) return;
        detail.innerHTML = '<div class="ds-empty">Loading persisted run…</div>';
        try {
            const report = await fetchJson(`/api/v1/evaluation/history/${encodeURIComponent(runId)}`);
            const manifest = report?.manifest || {};
            const results = Array.isArray(report?.results) ? report.results : [];
            detail.innerHTML = `
                <div class="ds-card evaluation-history-detail-card">
                    <div class="control-plane-header">
                        <div>
                            <span class="evaluation-eyebrow">Persisted report</span>
                            <h3>${escapeHtml(shortRun(manifest.run_id || runId))}</h3>
                        </div>
                        ${statusBadge(report?.complete ? 'Complete' : 'Incomplete', report?.complete ? 'ready' : 'warning')}
                    </div>
                    <div class="evaluation-manifest">
                        <div><span>Model</span><strong>${escapeHtml(manifest.model || 'Unavailable')}</strong></div>
                        <div><span>Test set</span><strong>${escapeHtml(manifest.test_set_id || '')} v${escapeHtml(manifest.test_set_version || '')}</strong></div>
                        <div><span>Seed</span><strong>${escapeHtml(manifest.seed ?? 'Unavailable')}</strong></div>
                        <div><span>Runtime fingerprint</span><code>${escapeHtml(manifest.runtime_fingerprint || 'Unavailable')}</code></div>
                    </div>
                    <p class="evaluation-history-detail-note">${results.length} persisted sample result${results.length === 1 ? '' : 's'}. Prompts and generated output are not exposed by the history summary surface.</p>
                </div>`;
        } catch (error) {
            detail.innerHTML = `<div class="ds-empty control-plane-unavailable">Unable to load run: ${escapeHtml(error?.message || 'unknown error')}</div>`;
        }
    }

    function renderComparison(host, comparison) {
        const comparable = comparison?.comparable === true;
        const evidenceGrade = comparison?.evidence_grade === true;
        const attributionSafe = comparison?.attribution_safe === true;
        let label = 'Not comparable';
        let status = 'error';
        if (comparable && attributionSafe) {
            label = 'Attribution-safe';
            status = 'ready';
        } else if (comparable && evidenceGrade) {
            label = 'Descriptive only';
            status = 'warning';
        } else if (comparable) {
            label = 'Exploratory comparison';
            status = 'warning';
        }

        const reasons = Array.isArray(comparison?.reasons) ? comparison.reasons : [];
        const deltas = comparison?.deltas || {};
        host.innerHTML = `
            <div class="ds-card evaluation-comparison-result-card">
                <div class="control-plane-header">
                    <div>
                        <span class="evaluation-eyebrow">Comparison evidence</span>
                        <h3>${escapeHtml(shortRun(comparison?.baseline_run_id || ''))} → ${escapeHtml(shortRun(comparison?.candidate_run_id || ''))}</h3>
                    </div>
                    ${statusBadge(label, status)}
                </div>
                <div class="evaluation-comparison-deltas">
                    ${deltaCard('Objective quality', deltas.objective_quality_mean, 'percentage')}
                    ${deltaCard('Execution success', deltas.execution_success_rate, 'percentage')}
                    ${deltaCard('Mean wall time', deltas.mean_wall_time_seconds, 'seconds')}
                    ${deltaCard('Output tokens', deltas.total_output_tokens, 'integer')}
                </div>
                ${reasons.length ? `<ul class="evaluation-comparison-reasons">${reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join('')}</ul>` : '<p class="evaluation-comparison-note">Dataset, selected samples, model and runtime fingerprint match. Delta attribution is safe within this evidence contract.</p>'}
                <p class="evaluation-comparison-note">Positive and negative deltas are shown without semantic coloring because direction alone does not determine whether a change is beneficial.</p>
            </div>`;
    }

    function deltaCard(label, rawValue, kind) {
        const value = finite(rawValue);
        let rendered = 'Unavailable';
        if (value !== null) {
            const sign = value > 0 ? '+' : '';
            if (kind === 'percentage') rendered = `${sign}${(value * 100).toFixed(2)} pp`;
            else if (kind === 'seconds') rendered = `${sign}${value.toFixed(4)} s`;
            else rendered = `${sign}${Math.round(value)}`;
        }
        return `<div class="evaluation-comparison-delta"><span>${escapeHtml(label)}</span><strong>${escapeHtml(rendered)}</strong></div>`;
    }

    function finite(value) {
        const numeric = Number(value);
        return Number.isFinite(numeric) ? numeric : null;
    }

    function shortRun(runId) {
        const text = String(runId || '');
        return text.length > 12 ? `${text.slice(0, 12)}…` : text;
    }

    function formatStoredAt(value) {
        const numeric = Number(value);
        if (!Number.isFinite(numeric) || numeric <= 0) return 'Unavailable';
        try { return new Date(numeric * 1000).toLocaleString(); } catch (_) { return 'Unavailable'; }
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
        if (!ensureHost()) {
            if (attempt < 80) setTimeout(() => boot(attempt + 1), 100);
            return;
        }
        refreshHistory({ preserveComparison: false });
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(() => refreshHistory({ preserveComparison: true }), REFRESH_MS);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => boot(), { once: true });
    } else {
        boot();
    }
})();
