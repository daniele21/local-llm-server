(() => {
    let running = false;
    let importNotice = null;

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

    async function boot(attempt = 0) {
        const view = findView();
        if (!view) {
            if (attempt < 30) setTimeout(() => boot(attempt + 1), 50);
            return;
        }
        view.dataset.evaluationUi = 'true';
        renderLoading(view);

        const [testSetsResult, modelsResult, runsResult] = await Promise.allSettled([
            fetchJson('/api/v1/evaluation/test-sets'),
            fetchJson('/v1/models'),
            fetchJson('/api/v1/evaluation/runs'),
        ]);

        if (testSetsResult.status !== 'fulfilled') {
            renderUnavailable(view, testSetsResult.reason);
            return;
        }

        const testSets = Array.isArray(testSetsResult.value?.test_sets)
            ? testSetsResult.value.test_sets
            : [];
        const models = modelsResult.status === 'fulfilled' && Array.isArray(modelsResult.value?.data)
            ? modelsResult.value.data
            : [];
        const runIds = runsResult.status === 'fulfilled' && Array.isArray(runsResult.value?.run_ids)
            ? runsResult.value.run_ids
            : [];
        renderForm(view, testSets, models, runIds);
    }

    function renderLoading(view) {
        view.innerHTML = `
            <div class="control-plane-header">
                <div>
                    <h2>Benchmark & Evaluation</h2>
                    <p>Loading source-backed evaluation contracts…</p>
                </div>
            </div>
            <div class="ds-empty">Loading…</div>`;
    }

    function renderUnavailable(view, error) {
        const adminHint = error?.status === 404
            ? 'Enable the admin API to use the evaluation harness.'
            : 'The evaluation service is currently unavailable.';
        view.innerHTML = `
            <div class="control-plane-header">
                <div>
                    <h2>Benchmark & Evaluation</h2>
                    <p>Run reproducible task-oriented evaluations on resident local models.</p>
                </div>
                <span class="ds-status" data-status="unavailable">Unavailable</span>
            </div>
            <div class="ds-empty control-plane-unavailable">
                ${escapeHtml(adminHint)} No synthetic scores are displayed.
            </div>`;
    }

    function renderForm(view, testSets, models, runIds) {
        const usableTestSets = testSets.filter((item) => Number(item?.sample_count) >= 10);
        const selectedTest = usableTestSets[0] || null;
        const modelOptions = models.map((model) => `
            <option value="${escapeHtml(model.key || model.id)}">
                ${escapeHtml(model.id || model.key)} · ${escapeHtml(model.backend || 'backend unavailable')}
            </option>`).join('');
        const testOptions = usableTestSets.map((item) => {
            const source = item.source === 'custom' ? 'Custom' : 'Built-in';
            return `
                <option
                    value="${escapeHtml(`${item.id}::${item.version}`)}"
                    data-id="${escapeHtml(item.id)}"
                    data-version="${escapeHtml(item.version)}"
                    data-count="${Number(item.sample_count)}"
                    data-source="${escapeHtml(item.source || 'built-in')}"
                >
                    ${escapeHtml(item.id)} v${escapeHtml(item.version)} · ${source} · ${Number(item.sample_count)} samples
                </option>`;
        }).join('');
        const notice = importNotice;
        importNotice = null;

        view.innerHTML = `
            <div class="control-plane-header">
                <div>
                    <h2>Benchmark & Evaluation</h2>
                    <p>Measure task quality on a versioned test set. Runtime identity determines whether a run is exploratory or evidence-grade.</p>
                </div>
                <span class="ds-status" data-status="ready">Evaluation service ready</span>
            </div>

            <div class="evaluation-layout">
                <form class="ds-card evaluation-setup" data-evaluation-form>
                    <div>
                        <span class="evaluation-eyebrow">Run setup</span>
                        <h3>Evaluate a resident model</h3>
                    </div>
                    <label class="ds-field">
                        <span>Model</span>
                        <select data-evaluation-model required ${models.length ? '' : 'disabled'}>
                            ${modelOptions || '<option value="">No resident models available</option>'}
                        </select>
                    </label>
                    <label class="ds-field">
                        <span>Test set</span>
                        <select data-evaluation-test-set required ${usableTestSets.length ? '' : 'disabled'}>
                            ${testOptions || '<option value="">No test sets available</option>'}
                        </select>
                    </label>
                    <div class="evaluation-selected-dataset" data-evaluation-dataset-meta></div>
                    <div class="evaluation-field-grid">
                        <label class="ds-field">
                            <span>Samples</span>
                            <select data-evaluation-samples required></select>
                        </label>
                        <label class="ds-field">
                            <span>Seed</span>
                            <input data-evaluation-seed type="number" inputmode="numeric" value="0" step="1">
                        </label>
                    </div>
                    <div class="evaluation-note">
                        Sample counts use valid multiples of 10 only. Objective expectations are evaluated by the server; the browser does not execute scorers or dataset code.
                    </div>
                    <label class="evaluation-retention-option">
                        <input data-evaluation-retain-content type="checkbox" checked>
                        <span>
                            <strong>Save model outputs in local history</strong>
                            <small>Keep generated answers on this device for later inspection. Prompt and expected values remain linked to the test set.</small>
                        </span>
                    </label>
                    <button class="ds-button ds-button--primary" type="submit" data-evaluation-start ${models.length && selectedTest ? '' : 'disabled'}>
                        Run evaluation
                    </button>
                </form>

                <aside class="ds-card evaluation-context">
                    <span class="evaluation-eyebrow">Dataset library</span>
                    <h3>Import a custom test set</h3>
                    <p class="evaluation-context-copy">Import a validated JSON test set. Files are treated as data only; executable scorers, templates and plugins are not accepted.</p>
                    <label class="ds-field">
                        <span>JSON test set</span>
                        <input data-evaluation-import-file type="file" accept="application/json,.json">
                    </label>
                    <button class="ds-button" type="button" data-evaluation-import>Import test set</button>
                    <div class="evaluation-import-status" data-evaluation-import-status aria-live="polite">
                        ${notice ? escapeHtml(notice) : 'Duplicate id/version imports are rejected; existing datasets are never silently replaced.'}
                    </div>
                    <div class="evaluation-library-summary">
                        <strong>${usableTestSets.length}</strong> available test-set version${usableTestSets.length === 1 ? '' : 's'}
                    </div>
                    <div class="evaluation-history-summary">
                        <strong>${runIds.length}</strong> persisted run${runIds.length === 1 ? '' : 's'} on this machine
                    </div>
                </aside>
            </div>

            <section class="ds-card evaluation-context evaluation-contract-card">
                <span class="evaluation-eyebrow">Evidence contract</span>
                <dl class="evaluation-definition-list">
                    <div><dt>Quality</dt><dd>Mean deterministic scorer value across scored samples.</dd></div>
                    <div><dt>Success</dt><dd>Samples that completed inference, independently from whether the answer scored well.</dd></div>
                    <div><dt>Evidence-grade</dt><dd>Runtime fingerprint attached to the exact run.</dd></div>
                    <div><dt>Exploratory</dt><dd>Run executed successfully but exact runtime identity is incomplete.</dd></div>
                </dl>
            </section>

            <section data-evaluation-result>
                <div class="ds-empty">No run executed in this session yet.</div>
            </section>`;

        const form = view.querySelector('[data-evaluation-form]');
        const testSelect = view.querySelector('[data-evaluation-test-set]');
        const sampleSelect = view.querySelector('[data-evaluation-samples]');
        const startButton = view.querySelector('[data-evaluation-start]');
        const importButton = view.querySelector('[data-evaluation-import]');
        const importFile = view.querySelector('[data-evaluation-import-file]');
        const importStatus = view.querySelector('[data-evaluation-import-status]');

        syncSelectedTestSet(testSelect, sampleSelect, view);
        testSelect?.addEventListener('change', () => syncSelectedTestSet(testSelect, sampleSelect, view));

        importButton?.addEventListener('click', async () => {
            const file = importFile?.files?.[0];
            if (!file) {
                importStatus.textContent = 'Choose a JSON test-set file before importing.';
                return;
            }
            importButton.disabled = true;
            importFile.disabled = true;
            importStatus.textContent = 'Importing and validating dataset…';
            try {
                const body = new FormData();
                body.append('file', file);
                const payload = await fetchJson('/api/v1/evaluation/test-sets/import', {
                    method: 'POST',
                    body,
                });
                const imported = payload?.test_set || {};
                importNotice = `Imported ${imported.id || 'test set'} v${imported.version || '?'} with ${Number(imported.sample_count || 0)} samples.`;
                await boot();
            } catch (error) {
                const prefix = error?.status === 409 ? 'Dataset already exists' : 'Import failed';
                importStatus.textContent = `${prefix}: ${error?.message || 'unknown error'}`;
            } finally {
                importButton.disabled = false;
                importFile.disabled = false;
            }
        });

        form?.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (running) return;
            running = true;
            startButton.disabled = true;
            const resultHost = view.querySelector('[data-evaluation-result]');
            resultHost.innerHTML = `
                <div class="ds-card evaluation-running" aria-live="polite">
                    <span class="ds-status" data-status="loading">Running</span>
                    <div>
                        <strong>Evaluation in progress</strong>
                        <p>The service is executing the selected samples sequentially. No fabricated percentage complete is shown.</p>
                    </div>
                </div>`;
            try {
                const selectedOption = testSelect.selectedOptions?.[0];
                const payload = await fetchJson('/api/v1/evaluation/runs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: view.querySelector('[data-evaluation-model]').value,
                        test_set_id: selectedOption?.dataset?.id || '',
                        test_set_version: selectedOption?.dataset?.version || null,
                        sample_count: Number(sampleSelect.value),
                        seed: Number(view.querySelector('[data-evaluation-seed]').value || 0),
                        retain_content: view.querySelector('[data-evaluation-retain-content]').checked,
                    }),
                });
                renderResult(resultHost, payload);
            } catch (error) {
                resultHost.innerHTML = `
                    <div class="ds-empty control-plane-unavailable">
                        Evaluation failed: ${escapeHtml(error?.message || 'unknown error')}
                    </div>`;
            } finally {
                running = false;
                startButton.disabled = false;
            }
        });
    }

    function syncSelectedTestSet(testSelect, sampleSelect, view) {
        syncSampleOptions(testSelect, sampleSelect);
        const option = testSelect?.selectedOptions?.[0];
        const host = view.querySelector('[data-evaluation-dataset-meta]');
        if (!host) return;
        if (!option) {
            host.textContent = 'Dataset metadata unavailable.';
            return;
        }
        const source = option.dataset.source === 'custom' ? 'Custom dataset' : 'Built-in dataset';
        host.innerHTML = `
            <span class="ds-status" data-status="${option.dataset.source === 'custom' ? 'warning' : 'ready'}">${escapeHtml(source)}</span>
            <span>${escapeHtml(option.dataset.id || '')} v${escapeHtml(option.dataset.version || '')}</span>`;
    }

    function syncSampleOptions(testSelect, sampleSelect) {
        if (!testSelect || !sampleSelect) return;
        const option = testSelect.selectedOptions?.[0];
        const count = Number(option?.dataset?.count || 0);
        const values = [];
        for (let value = 10; value <= count; value += 10) values.push(value);
        sampleSelect.innerHTML = values.map((value) => `<option value="${value}" ${value === count ? 'selected' : ''}>${value}</option>`).join('');
        sampleSelect.disabled = values.length === 0;
    }

    function renderResult(host, payload) {
        const report = payload?.report || {};
        const manifest = report.manifest || {};
        const results = Array.isArray(report.results) ? report.results : [];
        const succeeded = results.filter((item) => item?.succeeded).length;
        const scores = results.flatMap((item) => Array.isArray(item?.scores) ? item.scores : [])
            .map((score) => Number(score?.value))
            .filter((value) => Number.isFinite(value));
        const quality = scores.length ? scores.reduce((sum, value) => sum + value, 0) / scores.length : null;
        const wallTimes = results.map((item) => Number(item?.metrics?.wall_time_seconds))
            .filter((value) => Number.isFinite(value) && value >= 0);
        const avgWall = wallTimes.length ? wallTimes.reduce((sum, value) => sum + value, 0) / wallTimes.length : null;
        const inputTokens = sumMetric(results, 'prompt_tokens', 'input_tokens');
        const outputTokens = sumMetric(results, 'completion_tokens', 'output_tokens');
        const evidenceGrade = payload?.evidence_grade === true;

        host.innerHTML = `
            <div class="control-plane-header evaluation-result-header">
                <div>
                    <span class="evaluation-eyebrow">Run ${escapeHtml(manifest.run_id || '')}</span>
                    <h3>Evaluation result</h3>
                </div>
                <span class="ds-status" data-status="${evidenceGrade ? 'ready' : 'warning'}">
                    ${evidenceGrade ? 'Evidence-grade' : 'Exploratory'}
                </span>
            </div>
            <div class="evaluation-metrics">
                ${metricCard('Objective quality', quality === null ? 'Unavailable' : `${(quality * 100).toFixed(1)}%`, `${scores.length} scored checks`)}
                ${metricCard('Inference success', results.length ? `${succeeded}/${results.length}` : 'Unavailable', 'Completed samples')}
                ${metricCard('Avg. wall time', avgWall === null ? 'Unavailable' : `${avgWall.toFixed(3)} s`, 'Per sample, report metric')}
                ${metricCard('Token usage', inputTokens === null && outputTokens === null ? 'Unavailable' : `${formatMaybe(inputTokens)} in / ${formatMaybe(outputTokens)} out`, 'Only when backend usage exists')}
            </div>
            <div class="ds-card evaluation-manifest">
                <div><span>Test set</span><strong>${escapeHtml(manifest.test_set_id || '')} v${escapeHtml(manifest.test_set_version || '')}</strong></div>
                <div><span>Model</span><strong>${escapeHtml(manifest.model || '')}</strong></div>
                <div><span>Seed</span><strong>${escapeHtml(manifest.seed ?? '')}</strong></div>
                <div><span>Runtime fingerprint</span><code>${escapeHtml(manifest.runtime_fingerprint || 'Unavailable')}</code></div>
            </div>
            <div class="ds-card evaluation-table-wrap">
                <table class="ds-table evaluation-table">
                    <thead><tr><th>Sample</th><th>Execution</th><th>Score</th><th>Wall time</th><th>Error</th><th>Details</th></tr></thead>
                    <tbody>${renderSampleRows(results, `run-${manifest.run_id || 'latest'}`)}</tbody>
                </table>
            </div>`;
        bindSampleDetails(host);
    }

    function metricCard(label, value, detail) {
        return `<article class="ds-card evaluation-metric-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(detail)}</small></article>`;
    }

    function renderSampleRows(results, namespace = 'evaluation') {
        return results.map((item, index) => sampleRows(item, `${namespace}-${index}`)).join('');
    }

    function sampleRows(item, detailId) {
        const sampleScores = Array.isArray(item?.scores) ? item.scores : [];
        const values = sampleScores.map((score) => Number(score?.value)).filter(Number.isFinite);
        const score = values.length ? `${(values.reduce((sum, value) => sum + value, 0) / values.length * 100).toFixed(0)}%` : 'Unavailable';
        const wall = Number(item?.metrics?.wall_time_seconds);
        return `<tr>
            <td><code>${escapeHtml(item?.sample_id || '')}</code></td>
            <td>${statusBadge(item?.succeeded ? 'Succeeded' : 'Failed', item?.succeeded ? 'ready' : 'error')}</td>
            <td>${escapeHtml(score)}</td>
            <td>${Number.isFinite(wall) ? `${wall.toFixed(3)} s` : 'Unavailable'}</td>
            <td>${escapeHtml(item?.error_code || '—')}</td>
            <td><button type="button" class="ds-button ds-button--small evaluation-detail-toggle" data-sample-details-toggle aria-expanded="false" aria-controls="${escapeHtml(detailId)}">Inspect</button></td>
        </tr>
        <tr id="${escapeHtml(detailId)}" class="evaluation-detail-row" data-sample-details hidden>
            <td colspan="6">${sampleDetail(item)}</td>
        </tr>`;
    }

    function sampleDetail(item) {
        const scores = Array.isArray(item?.scores) ? item.scores : [];
        const metrics = item?.metrics && typeof item.metrics === 'object' ? item.metrics : {};
        const hasContent = item?.content && typeof item.content === 'object';
        const content = hasContent ? item.content : {};
        const hasInput = hasContent && hasOwn(content, 'input');
        const hasExpected = hasContent && hasOwn(content, 'expected');
        const hasOutput = hasContent && hasOwn(content, 'output');
        const contextStatus = item?.dataset_context_status || 'unavailable';
        const contentNotice = detailAvailabilityNotice({
            contextStatus,
            hasInput,
            hasExpected,
            hasOutput,
        });
        return `<div class="evaluation-sample-detail">
            ${contentNotice}
            <div class="evaluation-content-grid">
                ${detailBlock('Prompt', content.input, hasInput)}
                ${detailBlock('Expected', content.expected, hasExpected, true)}
                ${detailBlock('Model output', content.output, hasOutput)}
            </div>
            <div class="evaluation-detail-section">
                <h4>Checks</h4>
                ${scores.length ? `<div class="evaluation-check-list">${scores.map(scoreDetail).join('')}</div>` : '<p>No scored checks were produced.</p>'}
            </div>
            <div class="evaluation-detail-section">
                <h4>Raw metrics</h4>
                <pre><code>${escapeHtml(prettyValue(metrics))}</code></pre>
            </div>
        </div>`;
    }

    function detailAvailabilityNotice({ contextStatus, hasInput, hasExpected, hasOutput }) {
        if (hasInput && hasExpected && hasOutput) return '';
        let message = 'Some sample context is unavailable.';
        if (hasInput && hasExpected && !hasOutput) {
            message = 'Prompt and expected value come from the matching test set. Model output was not saved for this run.';
        } else if (contextStatus === 'identity_mismatch') {
            message = 'The available test set does not match this run identity, so prompt and expected value cannot be reconstructed safely.';
        } else if (contextStatus === 'dataset_missing') {
            message = 'The original test set is no longer available, so prompt and expected value cannot be reconstructed.';
        }
        return `<p class="evaluation-content-notice">${escapeHtml(message)} Checks and metrics remain available.</p>`;
    }

    function detailBlock(label, value, available, forceJson = false) {
        const rendered = !available
            ? 'Not retained'
            : value === null || value === undefined || value === ''
                ? 'Unavailable'
                : forceJson || typeof value === 'object' ? prettyValue(value) : String(value);
        return `<section class="evaluation-content-block"><h4>${escapeHtml(label)}</h4><pre><code>${escapeHtml(rendered)}</code></pre></section>`;
    }

    function scoreDetail(score) {
        const passed = score?.passed;
        const state = passed === true ? 'ready' : passed === false ? 'error' : 'warning';
        const label = passed === true ? 'Passed' : passed === false ? 'Failed' : 'Not classified';
        const value = Number(score?.value);
        const details = score?.details && Object.keys(score.details).length
            ? `<pre><code>${escapeHtml(prettyValue(score.details))}</code></pre>`
            : '';
        return `<article class="evaluation-check">
            <div><strong>${escapeHtml(score?.name || 'Unnamed check')}</strong>${statusBadge(label, state)}</div>
            <span>${Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : 'Unavailable'}</span>
            ${details}
        </article>`;
    }

    function prettyValue(value) {
        if (typeof value === 'string') return value;
        try { return JSON.stringify(value, null, 2); } catch (_) { return String(value); }
    }

    function hasOwn(value, key) {
        return Object.prototype.hasOwnProperty.call(value, key);
    }

    function bindSampleDetails(host) {
        if (!host || host.dataset.sampleDetailsBound === 'true') return;
        host.dataset.sampleDetailsBound = 'true';
        host.addEventListener('click', (event) => {
            const button = event.target.closest('[data-sample-details-toggle]');
            if (!button || !host.contains(button)) return;
            const detail = host.querySelector(`#${cssEscape(button.getAttribute('aria-controls') || '')}`);
            if (!detail) return;
            const expanded = button.getAttribute('aria-expanded') === 'true';
            button.setAttribute('aria-expanded', String(!expanded));
            button.textContent = expanded ? 'Inspect' : 'Hide';
            detail.hidden = expanded;
        });
    }

    function cssEscape(value) {
        if (window.CSS?.escape) return window.CSS.escape(value);
        return String(value).replace(/[^a-zA-Z0-9_-]/g, '\\$&');
    }

    function statusBadge(label, status) {
        return `<span class="ds-status" data-status="${escapeHtml(status)}">${escapeHtml(label)}</span>`;
    }

    function sumMetric(results, ...keys) {
        let found = false;
        let total = 0;
        results.forEach((item) => {
            const metrics = item?.metrics || {};
            for (const key of keys) {
                const value = Number(metrics[key]);
                if (Number.isFinite(value) && value >= 0) {
                    total += value;
                    found = true;
                    break;
                }
            }
        });
        return found ? total : null;
    }

    function formatMaybe(value) {
        return value === null ? '?' : String(value);
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    window.localLlmEvaluationUi = {
        bindSampleDetails,
        renderSampleRows,
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => boot(), { once: true });
    } else {
        boot();
    }
})();
