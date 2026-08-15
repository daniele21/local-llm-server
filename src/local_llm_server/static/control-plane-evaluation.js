(() => {
    let running = false;
    let importing = false;

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
        const usableTestSets = testSets.filter((item) => {
            const count = finiteNumber(item?.sample_count);
            return count !== null && count >= 10;
        });
        const selectedTest = usableTestSets[0] || null;
        const modelOptions = models.map((model) => `
            <option value="${escapeHtml(model.key || model.id)}">
                ${escapeHtml(model.id || model.key)} · ${escapeHtml(model.backend || 'backend unavailable')}
            </option>`).join('');
        const testOptions = usableTestSets.map((item, index) => {
            const count = finiteNumber(item.sample_count);
            const selector = `${item.id}@@${item.version}`;
            return `
                <option value="${escapeHtml(selector)}"
                        data-id="${escapeHtml(item.id)}"
                        data-version="${escapeHtml(item.version)}"
                        data-count="${count === null ? '' : count}"
                        data-source="${escapeHtml(item.source || 'unknown')}"
                        ${index === 0 ? 'selected' : ''}>
                    ${escapeHtml(item.id)} v${escapeHtml(item.version)} · ${count === null ? 'Unavailable' : count} samples · ${escapeHtml(item.source || 'source unavailable')}
                </option>`;
        }).join('');

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
                        Sample counts use valid multiples of 10 only. Built-in and uploaded sets use deterministic objective checks; no LLM judge is used.
                    </div>
                    <button class="ds-button ds-button--primary" type="submit" data-evaluation-start ${models.length && selectedTest ? '' : 'disabled'}>
                        Run evaluation
                    </button>

                    <div class="evaluation-import">
                        <div>
                            <span class="evaluation-eyebrow">Custom dataset</span>
                            <strong>Import a versioned JSON test set</strong>
                            <small>Data-only schema. Minimum 10 samples; supported checks are exact, exact_ci, contains, word_count, comma_count and json.</small>
                        </div>
                        <input type="file" accept="application/json,.json" data-evaluation-import-file>
                        <button class="ds-button" type="button" data-evaluation-import>Import test set</button>
                        <div class="evaluation-import-status" data-evaluation-import-status aria-live="polite"></div>
                    </div>
                </form>

                <aside class="ds-card evaluation-context">
                    <span class="evaluation-eyebrow">Evidence contract</span>
                    <h3>How to read a run</h3>
                    <dl class="evaluation-definition-list">
                        <div><dt>Quality</dt><dd>Mean deterministic scorer value across scored samples.</dd></div>
                        <div><dt>Success</dt><dd>Samples that completed inference, independently from whether the answer scored well.</dd></div>
                        <div><dt>Dataset identity</dt><dd>Includes version plus sample task, prompt and expected checks; changed content becomes a different identity.</dd></div>
                        <div><dt>Evidence-grade</dt><dd>Runtime fingerprint attached to the exact run.</dd></div>
                        <div><dt>Exploratory</dt><dd>Run executed successfully but exact runtime identity is incomplete.</dd></div>
                    </dl>
                    <div class="evaluation-history-summary">
                        <strong>${runIds.length}</strong> persisted run${runIds.length === 1 ? '' : 's'} on this machine
                    </div>
                </aside>
            </div>

            <section data-evaluation-result>
                <div class="ds-empty">No run executed in this session yet.</div>
            </section>`;

        const form = view.querySelector('[data-evaluation-form]');
        const testSelect = view.querySelector('[data-evaluation-test-set]');
        const sampleSelect = view.querySelector('[data-evaluation-samples]');
        const startButton = view.querySelector('[data-evaluation-start]');
        const importButton = view.querySelector('[data-evaluation-import]');
        syncSampleOptions(testSelect, sampleSelect);
        testSelect?.addEventListener('change', () => syncSampleOptions(testSelect, sampleSelect));
        importButton?.addEventListener('click', () => importTestSet(view));
        form?.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (running) return;
            const selectedOption = testSelect?.selectedOptions?.[0];
            const testSetId = selectedOption?.dataset?.id;
            const testSetVersion = selectedOption?.dataset?.version;
            if (!testSetId || !testSetVersion) return;

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
                const payload = await fetchJson('/api/v1/evaluation/runs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: view.querySelector('[data-evaluation-model]').value,
                        test_set_id: testSetId,
                        test_set_version: testSetVersion,
                        sample_count: Number(sampleSelect.value),
                        seed: Number(view.querySelector('[data-evaluation-seed]').value || 0),
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

    async function importTestSet(view) {
        if (importing) return;
        const fileInput = view.querySelector('[data-evaluation-import-file]');
        const button = view.querySelector('[data-evaluation-import]');
        const status = view.querySelector('[data-evaluation-import-status]');
        const file = fileInput?.files?.[0];
        if (!file) {
            if (status) status.textContent = 'Choose a JSON file first.';
            return;
        }
        importing = true;
        if (button) button.disabled = true;
        if (status) status.textContent = 'Validating and importing locally…';
        try {
            const body = new FormData();
            body.append('file', file);
            const payload = await fetchJson('/api/v1/evaluation/test-sets/import', {
                method: 'POST',
                body,
            });
            const testSet = payload?.test_set || {};
            if (status) status.textContent = `Imported ${testSet.id || 'test set'} v${testSet.version || ''}. Refreshing catalog…`;
            await boot();
        } catch (error) {
            if (status) status.textContent = `Import failed: ${error?.message || 'unknown error'}`;
        } finally {
            importing = false;
            if (button && document.body.contains(button)) button.disabled = false;
        }
    }

    function syncSampleOptions(testSelect, sampleSelect) {
        if (!testSelect || !sampleSelect) return;
        const option = testSelect.selectedOptions?.[0];
        const count = finiteNumber(option?.dataset?.count);
        const values = [];
        if (count !== null) {
            for (let value = 10; value <= count; value += 10) values.push(value);
        }
        sampleSelect.innerHTML = values.map((value) => `<option value="${value}" ${value === values.at(-1) ? 'selected' : ''}>${value}</option>`).join('');
        sampleSelect.disabled = values.length === 0;
    }

    function renderResult(host, payload) {
        const report = payload?.report || {};
        const manifest = report.manifest || {};
        const results = Array.isArray(report.results) ? report.results : [];
        const succeeded = results.filter((item) => item?.succeeded).length;
        const scores = results.flatMap((item) => Array.isArray(item?.scores) ? item.scores : [])
            .map((score) => finiteNumber(score?.value))
            .filter((value) => value !== null);
        const quality = scores.length ? scores.reduce((sum, value) => sum + value, 0) / scores.length : null;
        const wallTimes = results.map((item) => finiteNumber(item?.metrics?.wall_time_seconds))
            .filter((value) => value !== null && value >= 0);
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
                <div><span>Dataset identity</span><code>${escapeHtml(manifest.test_set_identity || 'Unavailable')}</code></div>
                <div><span>Model</span><strong>${escapeHtml(manifest.model || '')}</strong></div>
                <div><span>Seed</span><strong>${escapeHtml(manifest.seed ?? '')}</strong></div>
                <div><span>Runtime fingerprint</span><code>${escapeHtml(manifest.runtime_fingerprint || 'Unavailable')}</code></div>
            </div>
            <div class="ds-card evaluation-table-wrap">
                <table class="ds-table evaluation-table">
                    <thead><tr><th>Sample</th><th>Execution</th><th>Score</th><th>Wall time</th><th>Error</th></tr></thead>
                    <tbody>${results.map(sampleRow).join('')}</tbody>
                </table>
            </div>`;
    }

    function metricCard(label, value, detail) {
        return `<article class="ds-card evaluation-metric-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(detail)}</small></article>`;
    }

    function sampleRow(item) {
        const sampleScores = Array.isArray(item?.scores) ? item.scores : [];
        const values = sampleScores.map((score) => finiteNumber(score?.value)).filter((value) => value !== null);
        const score = values.length ? `${(values.reduce((sum, value) => sum + value, 0) / values.length * 100).toFixed(0)}%` : 'Unavailable';
        const wall = finiteNumber(item?.metrics?.wall_time_seconds);
        return `<tr>
            <td><code>${escapeHtml(item?.sample_id || '')}</code></td>
            <td>${statusBadge(item?.succeeded ? 'Succeeded' : 'Failed', item?.succeeded ? 'ready' : 'error')}</td>
            <td>${escapeHtml(score)}</td>
            <td>${wall !== null && wall >= 0 ? `${wall.toFixed(3)} s` : 'Unavailable'}</td>
            <td>${escapeHtml(item?.error_code || '—')}</td>
        </tr>`;
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
                const value = finiteNumber(metrics[key]);
                if (value !== null && value >= 0) {
                    total += value;
                    found = true;
                    break;
                }
            }
        });
        return found ? total : null;
    }

    function finiteNumber(value) {
        if (value === null || value === undefined || value === '') return null;
        const number = Number(value);
        return Number.isFinite(number) ? number : null;
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

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => boot(), { once: true });
    } else {
        boot();
    }
})();
